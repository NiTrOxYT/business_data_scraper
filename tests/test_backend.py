"""
Comprehensive Automated Test Suite for Business Lead Finder Backend.
Mocks external Nominatim and Overpass network calls to ensure deterministic, fast testing.
"""
import io
import csv
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from api.index import app
from api.categories import (
    is_valid_category,
    get_category_definition,
    build_overpass_category_query,
    CATEGORIES,
)
from api.osm_service import (
    validate_location_input,
    validate_category_input,
    normalize_osm_element,
    geocode_location,
    search_business_leads,
    _clean_cache,
    _GEOCODE_CACHE,
    _SEARCH_CACHE,
)
from api.csv_exporter import sanitize_cell_value, generate_leads_csv
from api.models import BusinessLead, SearchResponse

client = TestClient(app)


# -------------------------------------------------------------------------
# 1. Category Validation Tests
# -------------------------------------------------------------------------
def test_valid_categories():
    assert is_valid_category("distributors") is True
    assert is_valid_category("accounting") is True
    assert is_valid_category("electronics") is True
    assert is_valid_category("computers") is True
    assert is_valid_category("marketing_advertising") is True

    definition = get_category_definition("distributors")
    assert "Distributors & Wholesalers" in definition["label"]
    assert len(definition["osm_tags"]) > 0


def test_invalid_category_validation():
    assert is_valid_category("non_existent_category") is False
    with pytest.raises(Exception):
        validate_category_input("spaceship_dealers")


def test_overpass_query_builder():
    query = build_overpass_category_query("distributors", 22.5, 88.3, 22.6, 88.4, timeout=25, max_results=300)
    assert "[out:json][timeout:25]" in query
    assert "[bbox:22.500000,88.300000,22.600000,88.400000];" in query
    assert "shop" in query or "wholesale" in query
    assert "out center tags 300;" in query


# -------------------------------------------------------------------------
# 2. Location Validation Tests
# -------------------------------------------------------------------------
def test_location_validation_valid():
    assert validate_location_input("Kolkata") == "Kolkata"
    assert validate_location_input("  New York, NY  ") == "New York, NY"


def test_location_validation_empty_or_short():
    with pytest.raises(Exception) as exc:
        validate_location_input("")
    assert exc.value.status_code == 400

    with pytest.raises(Exception) as exc:
        validate_location_input("a")
    assert exc.value.status_code == 400


def test_location_validation_too_long():
    with pytest.raises(Exception) as exc:
        validate_location_input("A" * 105)
    assert exc.value.status_code == 400


# -------------------------------------------------------------------------
# 3. Business Normalization & Missing Field Tests
# -------------------------------------------------------------------------
def test_business_normalization_node_complete():
    raw_node = {
        "type": "node",
        "id": 123456,
        "lat": 22.5726,
        "lon": 88.3639,
        "tags": {
            "name": "Apex Wholesale Traders",
            "shop": "wholesale",
            "phone": "+91 33 2222 1111",
            "website": "www.apexwholesalers.com",
            "addr:housenumber": "42",
            "addr:street": "Strand Road",
            "addr:city": "Kolkata",
            "addr:postcode": "700001",
        },
    }
    lead = normalize_osm_element(raw_node, "distributors", "Distributors & Wholesalers")
    assert lead is not None
    assert lead.id == "node/123456"
    assert lead.name == "Apex Wholesale Traders"
    assert lead.category == "distributors"
    assert lead.phone == "+91 33 2222 1111"
    # Should normalize missing protocol
    assert lead.website == "https://www.apexwholesalers.com"
    assert "42 Strand Road" in lead.address
    assert lead.city == "Kolkata"
    assert lead.postcode == "700001"
    assert lead.lat == 22.5726
    assert lead.lon == 88.3639
    assert lead.osm_url == "https://www.openstreetmap.org/node/123456"


def test_business_normalization_way_with_center():
    raw_way = {
        "type": "way",
        "id": 98765,
        "center": {"lat": 22.5800, "lon": 88.3700},
        "tags": {
            "name": "Delta Tech Supplies",
            "office": "it",
        },
    }
    lead = normalize_osm_element(raw_way, "computers", "Computer & IT Equipment")
    assert lead is not None
    assert lead.id == "way/98765"
    assert lead.lat == 22.5800
    assert lead.lon == 88.3700


def test_business_normalization_missing_fields_not_fabricated():
    raw_node = {
        "type": "node",
        "id": 777,
        "lat": 10.0,
        "lon": 20.0,
        "tags": {
            "shop": "electronics"
        },
    }
    lead = normalize_osm_element(raw_node, "electronics", "Electronics Shops")
    assert lead is not None
    # Must be empty strings, NEVER fabricated phone numbers or URLs
    assert lead.name == ""
    assert lead.phone == ""
    assert lead.website == ""
    assert lead.address == ""
    assert lead.city == ""
    assert lead.postcode == ""


# -------------------------------------------------------------------------
# 4. Duplicate Removal Tests
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_duplicate_removal_in_search():
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    mock_geocode = {
        "display_name": "Test City",
        "bounding_box": [20.0, 80.0, 20.5, 80.5],
        "place_id": 1,
        "type": "city",
    }
    # Two identical elements from Overpass
    mock_elements = [
        {"type": "node", "id": 100, "lat": 20.1, "lon": 80.1, "tags": {"name": "Biz One", "shop": "wholesale"}},
        {"type": "node", "id": 100, "lat": 20.1, "lon": 80.1, "tags": {"name": "Biz One", "shop": "wholesale"}},
        {"type": "node", "id": 200, "lat": 20.2, "lon": 80.2, "tags": {"name": "Biz Two", "shop": "wholesale"}},
    ]

    with patch("api.osm_service.geocode_location", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = mock_geocode
        with patch("api.osm_service.execute_overpass_query", new_callable=AsyncMock) as mock_overpass:
            mock_overpass.return_value = mock_elements

            res = await search_business_leads("Test City", "distributors")
            assert res.total_found == 2
            ids = [l.id for l in res.listings]
            assert ids == ["node/100", "node/200"]


# -------------------------------------------------------------------------
# 5. Empty Results Handling
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_empty_results_handling():
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    mock_geocode = {
        "display_name": "Desert Island",
        "bounding_box": [10.0, 70.0, 10.1, 70.1],
        "place_id": 2,
        "type": "island",
    }

    with patch("api.osm_service.geocode_location", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = mock_geocode
        with patch("api.osm_service.execute_overpass_query", new_callable=AsyncMock) as mock_overpass:
            mock_overpass.return_value = []

            res = await search_business_leads("Desert Island", "distributors")
            assert res.total_found == 0
            assert len(res.listings) == 0
            assert "Data © OpenStreetMap" in res.attribution


# -------------------------------------------------------------------------
# 6. Upstream API Errors & Area Size Limitation
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_location_too_broad_rejection():
    mock_client = AsyncMock()
    # Mock Nominatim returning a bounding box for an entire country (span > 2 degrees)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{
        "display_name": "India",
        "boundingbox": ["6.5", "35.5", "68.1", "97.4"],
        "place_id": 10,
        "type": "country",
    }]
    mock_client.get = AsyncMock(return_value=mock_resp)

    _GEOCODE_CACHE.clear()
    with pytest.raises(Exception) as exc:
        await geocode_location("India", client=mock_client)
    assert exc.value.status_code == 400
    assert "too broad" in exc.value.detail.lower()


# -------------------------------------------------------------------------
# 7. CSV Formula Injection Mitigation
# -------------------------------------------------------------------------
def test_csv_formula_injection_sanitization():
    # Dangerous spreadsheet formulas must be prefixed with a single quote
    assert sanitize_cell_value("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert sanitize_cell_value("+12345-CMD") == "'+12345-CMD"
    assert sanitize_cell_value("-100+200") == "'-100+200"
    assert sanitize_cell_value("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_cell_value("\tTabbed") == "'\tTabbed"

    # Benign string unchanged
    assert sanitize_cell_value("Normal Business Name") == "Normal Business Name"
    assert sanitize_cell_value("") == ""
    assert sanitize_cell_value(None) == ""


# -------------------------------------------------------------------------
# 8. CSV Generation & Unicode Preservation
# -------------------------------------------------------------------------
def test_csv_generation_unicode_preservation():
    leads = [
        BusinessLead(
            id="node/1",
            name="कोलकाता ऑटोमेशन & टेक्नोलॉजी (Kolkata Automation)",
            category="distributors",
            category_label="Distributors & Wholesalers",
            phone="+91 98765 43210",
            website="https://kolkata-auto.example.com",
            address="১২ বিপিন বিহারী গাঙ্গুলী স্ট্রীট, Kolkata",
            city="Kolkata",
            postcode="700012",
            lat=22.5697,
            lon=88.3582,
            osm_type="node",
            osm_id=1,
            osm_url="https://www.openstreetmap.org/node/1",
        ),
        BusinessLead(
            id="node/2",
            name="=DANGEROUS_FORMULA()",
            category="distributors",
            category_label="Distributors & Wholesalers",
            phone="",
            website="",
            address="",
            city="",
            postcode="",
            lat=None,
            lon=None,
            osm_type="node",
            osm_id=2,
            osm_url="https://www.openstreetmap.org/node/2",
        ),
    ]

    csv_bytes = generate_leads_csv(leads)
    # Check UTF-8 BOM prefix
    assert csv_bytes.startswith(b"\xef\xbb\xbf")

    # Decode and parse CSV
    csv_text = csv_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    assert len(rows) == 3  # Header + 2 rows
    # Row 1 check Unicode
    assert rows[1][0] == leads[0].name
    assert rows[1][4] == leads[0].address

    # Row 2 check formula escaping
    assert rows[2][0] == "'=DANGEROUS_FORMULA()"


# -------------------------------------------------------------------------
# 9. FastAPI Endpoints Testing
# -------------------------------------------------------------------------
def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "Business Lead Finder" in data["service"]


def test_categories_endpoint():
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    categories = resp.json()
    assert len(categories) >= 6
    ids = [c["id"] for c in categories]
    assert "distributors" in ids
    assert "accounting" in ids


def test_search_and_export_endpoints_mocked():
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    mock_resp = SearchResponse(
        location="Kolkata",
        resolved_location="Kolkata, West Bengal, India",
        category="distributors",
        category_label="Distributors & Wholesalers",
        bounding_box=[22.4, 88.2, 22.7, 88.5],
        total_found=1,
        listings=[
            BusinessLead(
                id="node/555",
                name="Bengal Trading Corp",
                category="distributors",
                category_label="Distributors & Wholesalers",
                phone="+91 33 2233 4455",
                website="https://bengaltrading.example.com",
                address="Burrabazar, Kolkata",
                city="Kolkata",
                postcode="700007",
                lat=22.585,
                lon=88.355,
                osm_type="node",
                osm_id=555,
                osm_url="https://www.openstreetmap.org/node/555",
            )
        ],
        cached=False,
    )

    with patch("api.index.search_business_leads", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_resp

        # Test search
        resp = client.get("/api/search?location=Kolkata&category=distributors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 1
        assert data["listings"][0]["name"] == "Bengal Trading Corp"

        # Test export
        export_resp = client.get("/api/export?location=Kolkata&category=distributors")
        assert export_resp.status_code == 200
        assert export_resp.headers["content-type"].startswith("text/csv")
        assert "attachment; filename=" in export_resp.headers["content-disposition"]
        assert "Bengal Trading Corp" in export_resp.text


# -------------------------------------------------------------------------
# 10. Multi-Location & Multi-Category Comprehensive Retrieval Tests
# -------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("location,bbox_coords", [
    ("Kolkata", [22.45, 88.25, 22.65, 88.45]),
    ("London", [51.40, -0.25, 51.60, 0.05]),
    ("Austin", [30.15, -97.85, 30.45, -97.60]),
])
@pytest.mark.parametrize("category", ["distributors", "electronics"])
async def test_multi_location_and_categories_not_truncated(location, bbox_coords, category):
    """
    Verifies that searches across 3 distinct locations and 2 categories:
    1. Return multiple distinct businesses (not truncated to 1 or single-record).
    2. Correctly parse and retain nodes, ways, and relations.
    3. Retain valid businesses even when phone or website is unmapped.
    4. Provide full diagnostics payloads with upstream, parsed, deduped, and final counts.
    """
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    mock_geocode = {
        "display_name": f"{location} City Center",
        "bounding_box": bbox_coords,
        "place_id": 999,
        "type": "city",
    }

    # Diverse collection of OSM elements: node with full details, node with NO phone/website, way, and relation
    mock_elements = [
        {
            "type": "node",
            "id": 101,
            "lat": bbox_coords[0] + 0.01,
            "lon": bbox_coords[1] + 0.01,
            "tags": {
                "name": f"{location} Primary {category.capitalize()}",
                "phone": "+1 555-0101",
                "website": "https://example.com/primary",
                "addr:street": "Main Street",
                "addr:city": location,
            },
        },
        {
            "type": "node",
            "id": 102,
            "lat": bbox_coords[0] + 0.02,
            "lon": bbox_coords[1] + 0.02,
            "tags": {
                "name": f"{location} Unlisted Phone {category.capitalize()}",
                # Phone and website omitted intentionally to verify record is NOT discarded
                "addr:street": "Market Alley",
                "addr:city": location,
            },
        },
        {
            "type": "way",
            "id": 201,
            "center": {
                "lat": bbox_coords[0] + 0.03,
                "lon": bbox_coords[1] + 0.03,
            },
            "tags": {
                "name": f"{location} Center {category.capitalize()} Warehouse",
                "phone": "+1 555-0202",
                "addr:city": location,
            },
        },
        {
            "type": "relation",
            "id": 301,
            "center": {
                "lat": bbox_coords[0] + 0.04,
                "lon": bbox_coords[1] + 0.04,
            },
            "tags": {
                "name": f"{location} Regional Complex",
                "website": "https://complex.example.com",
            },
        },
    ]

    with patch("api.osm_service.geocode_location", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = mock_geocode
        with patch("api.osm_service.execute_overpass_query", new_callable=AsyncMock) as mock_overpass:
            mock_overpass.return_value = mock_elements

            resp = await search_business_leads(location, category, limit=100, refresh=True)

            # Verification 1: Multiple records returned (MUST NOT be 1 or truncated)
            assert resp.total_found == 4, f"Expected 4 records for {location}-{category}, got {resp.total_found}"
            assert len(resp.listings) == 4

            # Verification 2: Check ID prefixes and deduplication keys
            ids = [l.id for l in resp.listings]
            assert ids == ["node/101", "node/102", "way/201", "relation/301"]

            # Verification 3: Verify record without phone or website was kept
            unlisted_lead = next(l for l in resp.listings if l.id == "node/102")
            assert unlisted_lead.name == f"{location} Unlisted Phone {category.capitalize()}"
            assert unlisted_lead.phone == ""
            assert unlisted_lead.website == ""

            # Verification 4: Diagnostics payload populated
            diag = resp.diagnostics
            assert diag is not None
            assert diag.upstream_count == 4
            assert diag.parsed_count == 4
            assert diag.deduplicated_count == 4
            assert diag.final_count == 4
            assert diag.data_source == "overpass"
            assert diag.cache_hit is False
            assert diag.bounding_box == bbox_coords


# -------------------------------------------------------------------------
# 11. Caching & Cache Bypass (Refresh) Tests
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_caching_and_refresh_bypass():
    """Verifies that cache keys include limit and that refresh=True forces a fresh query."""
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    mock_geocode = {
        "display_name": "Austin, Texas",
        "bounding_box": [30.15, -97.85, 30.45, -97.60],
        "place_id": 888,
        "type": "city",
    }
    mock_elements = [
        {"type": "node", "id": 1, "lat": 30.2, "lon": -97.7, "tags": {"name": "Biz 1"}},
        {"type": "node", "id": 2, "lat": 30.3, "lon": -97.7, "tags": {"name": "Biz 2"}},
    ]

    with patch("api.osm_service.geocode_location", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = mock_geocode
        with patch("api.osm_service.execute_overpass_query", new_callable=AsyncMock) as mock_overpass:
            mock_overpass.return_value = mock_elements

            # Request 1: Fresh search (cache miss)
            res1 = await search_business_leads("Austin", "electronics", limit=50, refresh=False)
            assert res1.cached is False
            assert res1.diagnostics.cache_hit is False
            assert mock_overpass.call_count == 1

            # Request 2: Repeat with same params (cache hit)
            res2 = await search_business_leads("Austin", "electronics", limit=50, refresh=False)
            assert res2.cached is True
            assert res2.diagnostics.cache_hit is True
            # Overpass was NOT called again
            assert mock_overpass.call_count == 1

            # Request 3: Different limit (cache miss because cache key includes limit)
            res3 = await search_business_leads("Austin", "electronics", limit=25, refresh=False)
            assert res3.cached is False
            assert mock_overpass.call_count == 2

            # Request 4: Refresh flag passed (forces cache bypass)
            res4 = await search_business_leads("Austin", "electronics", limit=50, refresh=True)
            assert res4.cached is False
            assert res4.diagnostics.cache_hit is False
            # Overpass was called again because cache was bypassed
            assert mock_overpass.call_count == 3


# -------------------------------------------------------------------------
# 12. Full FastAPI Search Endpoint Query Parameters Test
# -------------------------------------------------------------------------
def test_api_search_endpoint_with_refresh_and_limit():
    """Verifies that the /api/search route receives and forwards limit and refresh params."""
    with patch("api.index.search_business_leads", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = SearchResponse(
            location="London",
            resolved_location="London, Greater London, England",
            category="distributors",
            category_label="Distributors & Wholesalers",
            bounding_box=[51.4, -0.2, 51.6, 0.0],
            total_found=2,
            listings=[
                BusinessLead(
                    id="node/10",
                    name="London Wholesale Co",
                    category="distributors",
                    category_label="Distributors & Wholesalers",
                    phone="",
                    website="",
                    address="",
                    city="London",
                    postcode="",
                    lat=51.5,
                    lon=-0.1,
                    osm_type="node",
                    osm_id=10,
                    osm_url="https://www.openstreetmap.org/node/10",
                ),
                BusinessLead(
                    id="node/11",
                    name="Thames Trading Ltd",
                    category="distributors",
                    category_label="Distributors & Wholesalers",
                    phone="+44 20 7946 0991",
                    website="",
                    address="",
                    city="London",
                    postcode="",
                    lat=51.51,
                    lon=-0.12,
                    osm_type="node",
                    osm_id=11,
                    osm_url="https://www.openstreetmap.org/node/11",
                ),
            ],
            cached=False,
        )

        resp = client.get("/api/search?location=London&category=distributors&limit=25&refresh=true")
        assert resp.status_code == 200
        mock_search.assert_called_once_with(
            location="London",
            category="distributors",
            limit=25,
            refresh=True,
        )
        data = resp.json()
        assert data["total_found"] == 2
        assert len(data["listings"]) == 2
