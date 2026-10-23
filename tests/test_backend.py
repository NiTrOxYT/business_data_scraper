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
    assert "[out:json][timeout:25];" in query
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
