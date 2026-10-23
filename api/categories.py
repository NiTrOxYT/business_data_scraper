"""
Controlled Business Categories Registry for OpenStreetMap Queries.
Maps business categories to documented OSM key-value tags and Overpass QL builders.
"""
from typing import Dict, List, Any


CATEGORIES: Dict[str, Dict[str, Any]] = {
    "distributors": {
        "id": "distributors",
        "label": "Distributors & Wholesalers",
        "description": "Wholesale businesses, trade distributors, and bulk suppliers.",
        "nwr_selectors": [
            'nwr["shop"="wholesale"]',
            'nwr["office"="wholesale"]',
            'nwr["wholesale"="yes"]',
            'nwr["trade"="wholesale"]',
            'nwr["trade"="building_supplies"]',
        ],
        "osm_tags": [("shop", "wholesale"), ("office", "wholesale"), ("wholesale", "yes"), ("trade", "wholesale")],
        "display_tags": ["shop=wholesale", "office=wholesale", "wholesale=yes", "trade=wholesale"],
        "search_keywords": ["wholesale", "distributor", "wholesaler", "bulk supplier"],
    },
    "marketing_advertising": {
        "id": "marketing_advertising",
        "label": "Marketing & Advertising Agencies",
        "description": "Advertising agencies, digital marketing, PR, and media consulting.",
        "nwr_selectors": [
            'nwr["office"="advertising"]',
            'nwr["office"="marketing"]',
            'nwr["office"="public_relations"]',
            'nwr["office"="media"]',
        ],
        "osm_tags": [("office", "advertising"), ("office", "marketing"), ("office", "public_relations"), ("office", "media")],
        "display_tags": ["office=advertising", "office=marketing", "office=public_relations", "office=media"],
        "search_keywords": ["advertising agency", "marketing agency", "public relations", "digital marketing"],
    },
    "recruitment": {
        "id": "recruitment",
        "label": "Recruitment & Employment Agencies",
        "description": "Staffing agencies, executive search, and recruitment consultants.",
        "nwr_selectors": [
            'nwr["office"="employment_agency"]',
            'nwr["office"="recruiter"]',
        ],
        "osm_tags": [("office", "employment_agency"), ("office", "recruiter")],
        "display_tags": ["office=employment_agency", "office=recruiter"],
        "search_keywords": ["recruitment agency", "employment agency", "staffing agency", "job agency"],
    },
    "accounting": {
        "id": "accounting",
        "label": "Accounting & Tax Firms",
        "description": "Chartered accountants, tax advisors, auditors, and bookkeeping services.",
        "nwr_selectors": [
            'nwr["office"="accountant"]',
            'nwr["office"="tax_advisor"]',
            'nwr["office"="bookkeeper"]',
            'nwr["office"="financial_advisor"]',
        ],
        "osm_tags": [("office", "accountant"), ("office", "tax_advisor"), ("office", "bookkeeper"), ("office", "financial_advisor")],
        "display_tags": ["office=accountant", "office=tax_advisor", "office=bookkeeper", "office=financial_advisor"],
        "search_keywords": ["accountant", "tax consultant", "chartered accountant", "accounting firm", "bookkeeper"],
    },
    "electronics": {
        "id": "electronics",
        "label": "Electronics Shops & Suppliers",
        "description": "Retailers and component suppliers for electronics and electrical equipment.",
        "nwr_selectors": [
            'nwr["shop"="electronics"]',
            'nwr["shop"="electrical"]',
        ],
        "osm_tags": [("shop", "electronics"), ("shop", "electrical")],
        "display_tags": ["shop=electronics", "shop=electrical"],
        "search_keywords": ["electronics shop", "electrical supplier", "electronics store", "electrical supplies"],
    },
    "computers": {
        "id": "computers",
        "label": "Computer & IT Equipment Shops",
        "description": "Computer retailers, IT hardware vendors, and computer repair centers.",
        "nwr_selectors": [
            'nwr["shop"="computer"]',
            'nwr["shop"="computer_repair"]',
            'nwr["office"="it"]',
        ],
        "osm_tags": [("shop", "computer"), ("shop", "computer_repair"), ("office", "it")],
        "display_tags": ["shop=computer", "shop=computer_repair", "office=it"],
        "search_keywords": ["computer shop", "computer repair", "it hardware", "it supplier"],
    },
    "logistics": {
        "id": "logistics",
        "label": "Logistics & Freight Services",
        "description": "Freight forwarding, cargo transport, and courier management offices.",
        "nwr_selectors": [
            'nwr["office"="logistics"]',
            'nwr["office"="freight"]',
            'nwr["office"="courier"]',
        ],
        "osm_tags": [("office", "logistics"), ("office", "freight"), ("office", "courier")],
        "display_tags": ["office=logistics", "office=freight", "office=courier"],
        "search_keywords": ["logistics", "freight forwarding", "courier service", "cargo transport"],
    },
    "manufacturing": {
        "id": "manufacturing",
        "label": "Industrial & Manufacturing",
        "description": "Manufacturing workshops, industrial production facilities, and fabricators.",
        "nwr_selectors": [
            'nwr["landuse"="industrial"]',
            'nwr["man_made"="works"]',
            'nwr["industrial"="factory"]',
        ],
        "osm_tags": [("landuse", "industrial"), ("man_made", "works"), ("industrial", "factory")],
        "display_tags": ["landuse=industrial", "man_made=works", "industrial=factory"],
        "search_keywords": ["manufacturer", "factory", "industrial works", "manufacturing workshop"],
    },
}


def get_category_ids() -> List[str]:
    """Returns list of all valid category identifiers."""
    return list(CATEGORIES.keys())


def is_valid_category(category_id: str) -> bool:
    """Check if given category identifier is registered."""
    return category_id in CATEGORIES


def get_category_definition(category_id: str) -> Dict[str, Any]:
    """Get category configuration by ID."""
    if not is_valid_category(category_id):
        raise ValueError(f"Unsupported category '{category_id}'. Valid categories: {get_category_ids()}")
    return CATEGORIES[category_id]


def build_overpass_category_query(
    category_id: str,
    south: float,
    west: float,
    north: float,
    east: float,
    timeout: int = 15,
    max_results: int = 300,
) -> str:
    """
    Constructs an optimized Overpass QL query string with global bounding box constraints.
    Uses nwr (nodes, ways, relations) to leverage spatial index efficiently.
    """
    cat = get_category_definition(category_id)
    selectors = cat.get("nwr_selectors", [])
    
    # Global bbox in settings block activates spatial index in Overpass parser
    clauses = "\n".join(f"  {sel};" for sel in selectors)
    overpass_query = f"""[out:json][timeout:{timeout}][bbox:{south:.6f},{west:.6f},{north:.6f},{east:.6f}];
(
{clauses}
);
out center tags {max_results};
"""
    return overpass_query
