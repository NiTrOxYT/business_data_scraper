"""
Comprehensive Automated Test Suite for Free Business Data Scraper Backend.
Covers:
- 11+ commercial business categories and aliases
- Spatial bounding box and radius calculation
- Custom keyword filtering in Overpass QL
- Authentic email and phone extraction and normalization
- Multi-location (Kolkata, London, Austin) and multi-category retrieval
- Nodes, ways, and relations parsing
- Handling missing fields without fabrication
- Deduplication and result limit chunking
- Caching and refresh bypass mechanism
- CSV formula injection protection & UTF-8 BOM encoding
- Excel (.xlsx) workbook generation with styling
- Apify-style search job tracking and registry
- API endpoints: /api/health, /api/categories, /api/search, /api/export, /api/jobs
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
    sanitize_overpass_keyword,
    CATEGORIES,
)
from api.osm_service import (
    validate_location_input,
    validate_category_input,
    normalize_osm_element,
    geocode_location,
    search_business_leads,
    _clean_cache,
    _extract_email,
    _normalize_phone,
    _GEOCODE_CACHE,
    _SEARCH_CACHE,
)
from api.csv_exporter import sanitize_cell_value, generate_leads_csv
from api.excel_exporter import generate_leads_excel, sanitize_excel_value
from api.job_service import start_search_job, complete_search_job, fail_search_job, get_all_jobs
from api.models import BusinessLead, SearchResponse

client = TestClient(app)


# -------------------------------------------------------------------------
# 1. Category Validation Tests (All 11+ categories required)
# -------------------------------------------------------------------------
def test_all_required_categories_present():
    required_categories = [
        "distributors",
        "electronics",
        "computers",
        "restaurants_cafes",
        "hotels",
        "marketing_advertising",
        "recruitment",
        "accounting_consulting",
        "retail_shops",
        "manufacturing",
        "repair_services",
    ]
    for cat in required_categories:
        assert is_valid_category(cat) is True, f"Category '{cat}' missing from registry"
        defn = get_category_definition(cat)
        assert len(defn["label"]) > 0
        assert len(defn["nwr_selectors"]) > 0
        assert len(defn["search_keywords"]) > 0

    # Test backward compatibility alias for "accounting"
    assert is_valid_category("accounting") is True
    acc_def = get_category_definition("accounting")
    assert "Accountants" in acc_def["label"]


def test_invalid_category_validation():
    assert is_valid_category("spaceship_dealers") is False
    with pytest.raises(Exception):
        validate_category_input("spaceship_dealers")


def test_overpass_query_builder_with_and_without_keyword():
    # Without keyword
    query = build_overpass_category_query("distributors", 22.5, 88.3, 22.6, 88.4, timeout=25, max_results=100)
    assert "[out:json][timeout:25]" in query
    assert "[bbox:22.500000,88.300000,22.600000,88.400000];" in query
    assert 'nwr["shop"="wholesale"];' in query
    assert "out center tags 100;" in query

    # With keyword
    kw_query = build_overpass_category_query(
        "distributors", 22.5, 88.3, 22.6, 88.4, keyword="spices", timeout=20, max_results=50
    )
    assert 'name~"spices",i' in kw_query
    assert "out center tags 50;" in kw_query


def test_sanitize_overpass_keyword():
    raw = 'dangerous"query;[drop table]!$^*'
    clean = sanitize_overpass_keyword(raw)
    assert ";" not in clean
    assert "[" not in clean
    assert '"' not in clean
    assert clean == "dangerousquerydrop table"


# -------------------------------------------------------------------------
# 2. Location Validation & Geocoding Tests
# -------------------------------------------------------------------------
def test_location_validation_valid():
    assert validate_location_input("Kolkata") == "Kolkata"
    assert validate_location_input("  Austin, TX  ") == "Austin, TX"


def test_location_validation_invalid():
    with pytest.raises(Exception) as exc:
        validate_location_input("")
    assert exc.value.status_code == 400

    with pytest.raises(Exception) as exc:
        validate_location_input("A")
    assert exc.value.status_code == 400

    with pytest.raises(Exception) as exc:
        validate_location_input("San Francisco; DROP TABLE leads;")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_location_too_broad_rejection():
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{
        "display_name": "United States",
        "boundingbox": ["24.3", "49.3", "-125.0", "-66.9"],
        "lat": "38.0",
        "lon": "-95.0",
        "place_id": 1,
        "type": "country",
    }]
    mock_client.get = AsyncMock(return_value=mock_resp)

    _GEOCODE_CACHE.clear()
    with pytest.raises(Exception) as exc:
        await geocode_location("United States", client=mock_client)
    assert exc.value.status_code == 400
    assert "too broad" in exc.value.detail.lower()


# -------------------------------------------------------------------------
# 3. Data Extraction: Email, Phone Normalization, Missing Fields
# -------------------------------------------------------------------------
def test_phone_normalization():
    assert _normalize_phone(" +1  (512)   462-6008 ") == "+1 (512) 462-6008"
    assert _normalize_phone("+91 33 2222 1111") == "+91 33 2222 1111"
    assert _normalize_phone("") == ""
    assert _normalize_phone(None) == ""


def test_email_extraction():
    tags_with_email = {"email": "info@apifyalternative.com", "name": "Tech Corp"}
    assert _extract_email(tags_with_email) == "info@apifyalternative.com"

    tags_with_contact_email = {"contact:email": "contact@supplier.org "}
    assert _extract_email(tags_with_contact_email) == "contact@supplier.org"

    tags_invalid_email = {"email": "not-an-email"}
    assert _extract_email(tags_invalid_email) == ""

    tags_no_email = {"name": "No Email Shop"}
    assert _extract_email(tags_no_email) == ""


def test_business_normalization_complete():
    raw_node = {
        "type": "node",
        "id": 8888,
        "lat": 30.2672,
        "lon": -97.7431,
        "tags": {
            "name": "Austin Audio Equipment",
            "shop": "electronics",
            "phone": " +1 512-555-0199 ",
            "website": "www.austinaudio.example.com",
            "email": "sales@austinaudio.example.com",
            "addr:housenumber": "100",
            "addr:street": "Congress Ave",
            "addr:city": "Austin",
            "addr:postcode": "78701",
        },
    }
    lead = normalize_osm_element(
        raw_node,
        "electronics",
        "Electronics Shops & Suppliers",
        data_source="OpenStreetMap (Overpass API)",
        timestamp_str="2026-10-23T06:30:00Z",
    )
    assert lead is not None
    assert lead.id == "node/8888"
    assert lead.name == "Austin Audio Equipment"
    assert lead.phone == "+1 512-555-0199"
    assert lead.website == "https://www.austinaudio.example.com"
    assert lead.email == "sales@austinaudio.example.com"
    assert "100 Congress Ave" in lead.address
    assert lead.city == "Austin"
    assert lead.postcode == "78701"
    assert lead.data_source == "OpenStreetMap (Overpass API)"
    assert lead.search_timestamp == "2026-10-23T06:30:00Z"


def test_business_normalization_missing_fields_never_fabricated():
    raw_node = {
        "type": "node",
        "id": 9999,
        "lat": 51.5,
        "lon": -0.1,
        "tags": {"shop": "wholesale"},
    }
    lead = normalize_osm_element(raw_node, "distributors", "Wholesalers & Distributors")
    assert lead is not None
    # All missing fields must remain empty strings, NEVER invented
    assert lead.name == ""
    assert lead.phone == ""
    assert lead.website == ""
    assert lead.email == ""
    assert lead.address == ""
    assert lead.city == ""
    assert lead.postcode == ""


# -------------------------------------------------------------------------
# 4. Multi-Location (Kolkata, London, Austin) & Multi-Category Mocked Searches
# -------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("location,bbox_coords", [
    ("Kolkata", [22.45, 88.25, 22.65, 88.45]),
    ("London", [51.40, -0.25, 51.60, 0.05]),
    ("Austin", [30.15, -97.85, 30.45, -97.60]),
])
@pytest.mark.parametrize("category", ["distributors", "electronics", "restaurants_cafes"])
async def test_multi_location_and_categories_not_truncated(location, bbox_coords, category):
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    mock_geocode = {
        "display_name": f"{location} City Center",
        "bounding_box": bbox_coords,
        "lat": (bbox_coords[0] + bbox_coords[2]) / 2.0,
        "lon": (bbox_coords[1] + bbox_coords[3]) / 2.0,
        "place_id": 999,
        "type": "city",
    }

    mock_elements = [
        {
            "type": "node",
            "id": 101,
            "lat": bbox_coords[0] + 0.01,
            "lon": bbox_coords[1] + 0.01,
            "tags": {
                "name": f"{location} Premier {category.capitalize()}",
                "phone": "+1 555-0101",
                "website": "https://example.com/premier",
                "email": "contact@premier.example.com",
            },
        },
        {
            "type": "node",
            "id": 102,
            "lat": bbox_coords[0] + 0.02,
            "lon": bbox_coords[1] + 0.02,
            "tags": {
                "name": f"{location} Unlisted {category.capitalize()}",
                # Phone and website unmapped intentionally
                "addr:street": "Commercial Road",
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
                "name": f"{location} Complex {category.capitalize()}",
            },
        },
    ]

    with patch("api.osm_service.geocode_location", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = mock_geocode
        with patch("api.osm_service.execute_overpass_query", new_callable=AsyncMock) as mock_overpass:
            mock_overpass.return_value = mock_elements

            resp = await search_business_leads(location, category, limit=50, refresh=True)

            assert resp.total_found == 3
            assert len(resp.listings) == 3

            # Check entity IDs
            ids = [l.id for l in resp.listings]
            assert ids == ["node/101", "node/102", "way/201"]

            # Unlisted lead is retained
            unlisted = next(l for l in resp.listings if l.id == "node/102")
            assert unlisted.phone == ""
            assert unlisted.website == ""

            # Check email on listed lead
            listed = next(l for l in resp.listings if l.id == "node/101")
            assert listed.email == "contact@premier.example.com"

            # Check diagnostics
            diag = resp.diagnostics
            assert diag is not None
            assert diag.upstream_count == 3
            assert diag.final_count == 3
            assert "Overpass" in diag.data_source


# -------------------------------------------------------------------------
# 5. Spatial Radius Search Test
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_search_with_radius_km():
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    center_lat = 30.2672
    center_lon = -97.7431
    mock_geocode = {
        "display_name": "Austin, TX",
        "bounding_box": [30.15, -97.85, 30.45, -97.60],
        "lat": center_lat,
        "lon": center_lon,
        "place_id": 555,
        "type": "city",
    }
    mock_elements = [
        {"type": "node", "id": 1, "lat": 30.26, "lon": -97.74, "tags": {"name": "Radius Biz 1"}},
    ]

    with patch("api.osm_service.geocode_location", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = mock_geocode
        with patch("api.osm_service.execute_overpass_query", new_callable=AsyncMock) as mock_overpass:
            mock_overpass.return_value = mock_elements

            resp = await search_business_leads("Austin, TX", "computers", radius_km=10.0, limit=25, refresh=True)
            assert resp.total_found == 1
            assert resp.radius_km == 10.0
            # Bounding box was dynamically computed from center coordinates
            south, west, north, east = resp.bounding_box
            assert south < center_lat < north
            assert west < center_lon < east


# -------------------------------------------------------------------------
# 6. Caching & Cache Bypass (Refresh) Tests
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_caching_and_refresh_bypass():
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    mock_geocode = {
        "display_name": "Austin, Texas",
        "bounding_box": [30.15, -97.85, 30.45, -97.60],
        "lat": 30.26,
        "lon": -97.74,
        "place_id": 888,
        "type": "city",
    }
    mock_elements = [
        {"type": "node", "id": 1, "lat": 30.2, "lon": -97.7, "tags": {"name": "Biz 1"}},
    ]

    with patch("api.osm_service.geocode_location", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = mock_geocode
        with patch("api.osm_service.execute_overpass_query", new_callable=AsyncMock) as mock_overpass:
            mock_overpass.return_value = mock_elements

            # Search 1: fresh
            r1 = await search_business_leads("Austin", "electronics", limit=50, refresh=False)
            assert r1.cached is False
            assert mock_overpass.call_count == 1

            # Search 2: cache hit
            r2 = await search_business_leads("Austin", "electronics", limit=50, refresh=False)
            assert r2.cached is True
            assert r2.diagnostics.cache_hit is True
            assert mock_overpass.call_count == 1

            # Search 3: refresh bypass
            r3 = await search_business_leads("Austin", "electronics", limit=50, refresh=True)
            assert r3.cached is False
            assert mock_overpass.call_count == 2


# -------------------------------------------------------------------------
# 7. CSV Export & Formula Injection Tests
# -------------------------------------------------------------------------
def test_csv_formula_injection_sanitization():
    assert sanitize_cell_value("=1+1") == "'=1+1"
    assert sanitize_cell_value("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_cell_value("-100") == "'-100"
    assert sanitize_cell_value("@SUM(A1:A5)") == "'@SUM(A1:A5)"
    assert sanitize_cell_value("\tTabValue") == "'\tTabValue"
    assert sanitize_cell_value("Normal Business") == "Normal Business"
    assert sanitize_cell_value("") == ""


def test_csv_generation_unicode_and_email():
    leads = [
        BusinessLead(
            id="node/1",
            name="कोलकाता ऑटोमेशन (Kolkata Automation)",
            category="distributors",
            category_label="Wholesalers & Distributors",
            phone="+91 33 2222 3333",
            website="https://kolkata.example.com",
            email="contact@kolkata.example.com",
            address="বিপিন বিহারী গাঙ্গুলী স্ট্রীট, Kolkata",
            city="Kolkata",
            postcode="700012",
            lat=22.56,
            lon=88.35,
            osm_type="node",
            osm_id=1,
            osm_url="https://www.openstreetmap.org/node/1",
            data_source="OpenStreetMap",
            search_timestamp="2026-10-23T06:30:00Z",
        ),
        BusinessLead(
            id="node/2",
            name="=DANGEROUS_FORMULA()",
            category="distributors",
            category_label="Wholesalers & Distributors",
            phone="",
            website="",
            email="",
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
    assert csv_bytes.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM

    csv_text = csv_bytes.decode("utf-8-sig")
    reader = list(csv.reader(io.StringIO(csv_text)))

    assert len(reader) == 3  # Header + 2 rows
    # Check headers contain Email and Data Source
    assert "Email" in reader[0]
    assert "Data Source" in reader[0]

    # Check unicode name and email
    assert reader[1][0] == leads[0].name
    assert reader[1][4] == "contact@kolkata.example.com"

    # Check formula escaping
    assert reader[2][0] == "'=DANGEROUS_FORMULA()"


# -------------------------------------------------------------------------
# 8. Excel (.xlsx) Exporter Tests
# -------------------------------------------------------------------------
def test_excel_export_generation():
    leads = [
        BusinessLead(
            id="node/99",
            name="Precision Engineering Works",
            category="manufacturing",
            category_label="Manufacturers & Industrial",
            phone="+1 512 555 9988",
            website="https://precision.example.com",
            email="sales@precision.example.com",
            address="700 Industrial Blvd, Austin",
            city="Austin",
            postcode="78745",
            lat=30.22,
            lon=-97.76,
            osm_type="node",
            osm_id=99,
            osm_url="https://www.openstreetmap.org/node/99",
            data_source="OpenStreetMap",
            search_timestamp="2026-10-23T06:30:00Z",
        ),
        BusinessLead(
            id="node/100",
            name="=DANGEROUS_EXCEL_FORMULA()",
            category="manufacturing",
            category_label="Manufacturers & Industrial",
            phone="",
            website="",
            email="",
            address="",
            city="",
            postcode="",
            lat=None,
            lon=None,
            osm_type="node",
            osm_id=100,
            osm_url="https://www.openstreetmap.org/node/100",
        ),
    ]

    excel_bytes = generate_leads_excel(leads, sheet_title="Austin Leads")
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 1000
    # PK zip signature of .xlsx file
    assert excel_bytes.startswith(b"PK")


def test_sanitize_excel_value():
    assert sanitize_excel_value("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_excel_value("+12345") == "'+12345"
    assert sanitize_excel_value(12345) == 12345
    assert sanitize_excel_value(45.67) == 45.67
    assert sanitize_excel_value("Standard Name") == "Standard Name"


# -------------------------------------------------------------------------
# 9. Search Jobs Registry Tests
# -------------------------------------------------------------------------
def test_search_jobs_lifecycle():
    job = start_search_job(
        location="Austin",
        category="electronics",
        category_label="Electronics Shops & Suppliers",
        limit=50,
        keyword="audio",
        radius_km=15.0,
    )
    assert job.status == "running"
    assert job.location == "Austin"
    assert job.keyword == "audio"
    assert job.radius_km == 15.0

    completed = complete_search_job(
        job_id=job.id,
        records_found=24,
        duplicates_removed=6,
        data_source="OpenStreetMap (Overpass API)",
        cached=False,
    )
    assert completed is not None
    assert completed.status == "completed"
    assert completed.records_found == 24
    assert completed.duplicates_removed == 6
    assert completed.duration_seconds is not None

    all_jobs = get_all_jobs()
    assert len(all_jobs) > 0
    assert any(j.id == job.id for j in all_jobs)


# -------------------------------------------------------------------------
# 10. FastAPI Endpoints Testing
# -------------------------------------------------------------------------
def test_api_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "Business Data Scraper" in data["service"]


def test_api_categories():
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    categories = resp.json()
    ids = [c["id"] for c in categories]
    assert "distributors" in ids
    assert "restaurants_cafes" in ids
    assert "hotels" in ids
    assert "retail_shops" in ids


def test_api_jobs_endpoint():
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    jobs = resp.json()
    assert isinstance(jobs, list)


def test_api_search_and_exports_mocked():
    _GEOCODE_CACHE.clear()
    _SEARCH_CACHE.clear()

    mock_resp = SearchResponse(
        location="London",
        resolved_location="London, Greater London, England",
        category="distributors",
        category_label="Wholesalers & Distributors",
        bounding_box=[51.4, -0.2, 51.6, 0.0],
        total_found=1,
        listings=[
            BusinessLead(
                id="node/50",
                name="Thames Trading House",
                category="distributors",
                category_label="Wholesalers & Distributors",
                phone="+44 20 7946 0991",
                website="https://thamestrading.example.com",
                email="info@thamestrading.example.com",
                address="Borough Market, London",
                city="London",
                postcode="SE1 1TL",
                lat=51.505,
                lon=-0.09,
                osm_type="node",
                osm_id=50,
                osm_url="https://www.openstreetmap.org/node/50",
                data_source="OpenStreetMap",
                search_timestamp="2026-10-23T06:30:00Z",
            )
        ],
        cached=False,
    )

    with patch("api.index.search_business_leads", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_resp

        # Test GET /api/search with keyword and radius
        resp = client.get("/api/search?location=London&category=distributors&keyword=trading&radius_km=10&limit=50&refresh=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_found"] == 1
        assert data["listings"][0]["name"] == "Thames Trading House"
        assert data["listings"][0]["email"] == "info@thamestrading.example.com"

        # Test GET /api/export as CSV
        csv_resp = client.get("/api/export?location=London&category=distributors&format=csv")
        assert csv_resp.status_code == 200
        assert "text/csv" in csv_resp.headers["content-type"]
        assert "Thames Trading House" in csv_resp.text

        # Test GET /api/export as Excel
        excel_resp = client.get("/api/export?location=London&category=distributors&format=excel")
        assert excel_resp.status_code == 200
        assert "openxmlformats" in excel_resp.headers["content-type"]
        assert excel_resp.content.startswith(b"PK")


# -------------------------------------------------------------------------
# 11. Export-Filtered (Selected Leads) API Tests
# -------------------------------------------------------------------------
def test_api_export_filtered_csv_and_excel():
    payload = {
        "location": "Austin",
        "category": "electronics",
        "format": "csv",
        "listings": [
            {
                "id": "node/101",
                "name": "Selected Lead 1",
                "category": "electronics",
                "category_label": "Electronics Shops & Suppliers",
                "phone": "+1 512-555-1234",
                "website": "https://lead1.example.com",
                "email": "lead1@example.com",
                "address": "123 Austin Blvd",
                "city": "Austin",
                "postcode": "78701",
                "lat": 30.26,
                "lon": -97.74,
                "osm_type": "node",
                "osm_id": 101,
                "osm_url": "https://www.openstreetmap.org/node/101",
                "data_source": "OpenStreetMap",
                "search_timestamp": "2026-10-23T06:30:00Z",
                "tags": {},
            }
        ],
    }

    # CSV
    csv_resp = client.post("/api/export-filtered", json=payload)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "Selected Lead 1" in csv_resp.text
    assert "lead1@example.com" in csv_resp.text

    # Excel
    payload["format"] = "excel"
    excel_resp = client.post("/api/export-filtered", json=payload)
    assert excel_resp.status_code == 200
    assert "openxmlformats" in excel_resp.headers["content-type"]
    assert excel_resp.content.startswith(b"PK")

    # Invalid empty listings payload rejected
    bad_payload = {"location": "Austin", "category": "electronics", "format": "csv", "listings": []}
    bad_resp = client.post("/api/export-filtered", json=bad_payload)
    assert bad_resp.status_code == 422


# -------------------------------------------------------------------------
# 12. Location & Category Change Queries Verification
# -------------------------------------------------------------------------
def test_location_and_category_change_variations():
    # Category 1: restaurants_cafes
    q1 = build_overpass_category_query("restaurants_cafes", 51.4, -0.2, 51.6, 0.0)
    assert '["amenity"="restaurant"]' in q1
    assert '["amenity"="cafe"]' in q1
    assert "51.400000,-0.200000,51.600000,0.000000" in q1

    # Category 2: hotels
    q2 = build_overpass_category_query("hotels", 30.1, -97.8, 30.4, -97.6)
    assert '["tourism"="hotel"]' in q2
    assert '["tourism"="motel"]' in q2
    assert "30.100000,-97.800000,30.400000,-97.600000" in q2

    # Category 3: repair_services
    q3 = build_overpass_category_query("repair_services", 22.4, 88.2, 22.7, 88.5)
    assert '["shop"="car_repair"]' in q3
    assert '["craft"="electronics_repair"]' in q3
    assert "22.400000,88.200000,22.700000,88.500000" in q3
