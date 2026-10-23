"""
Controlled Business Categories Registry for OpenStreetMap Queries.
Maps business categories to documented OSM key-value tags.
"""
from typing import Dict, List, Any


CATEGORIES: Dict[str, Dict[str, Any]] = {
    "distributors": {
        "id": "distributors",
        "label": "Distributors & Wholesalers",
        "description": "Wholesale businesses, trade distributors, and bulk suppliers.",
        "osm_tags": [
            'node["shop"="wholesale"]',
            'way["shop"="wholesale"]',
            'node["office"="wholesale"]',
            'way["office"="wholesale"]',
            'node["wholesale"="yes"]',
            'way["wholesale"="yes"]',
            'node["trade"]',
            'way["trade"]',
        ],
        "display_tags": ["shop=wholesale", "office=wholesale", "wholesale=yes", "trade=*"],
        "search_keywords": ["wholesale", "distributor", "trade supplier"],
    },
    "marketing_advertising": {
        "id": "marketing_advertising",
        "label": "Marketing & Advertising Agencies",
        "description": "Advertising agencies, digital marketing, PR, and media consulting.",
        "osm_tags": [
            'node["office"="advertising"]',
            'way["office"="advertising"]',
            'node["office"="marketing"]',
            'way["office"="marketing"]',
            'node["office"="public_relations"]',
            'way["office"="public_relations"]',
            'node["office"="media"]',
            'way["office"="media"]',
        ],
        "display_tags": ["office=advertising", "office=marketing", "office=public_relations", "office=media"],
        "search_keywords": ["advertising agency", "marketing agency", "public relations"],
    },
    "recruitment": {
        "id": "recruitment",
        "label": "Recruitment & Employment Agencies",
        "description": "Staffing agencies, executive search, and recruitment consultants.",
        "osm_tags": [
            'node["office"="employment_agency"]',
            'way["office"="employment_agency"]',
            'node["office"="recruiter"]',
            'way["office"="recruiter"]',
        ],
        "display_tags": ["office=employment_agency", "office=recruiter"],
        "search_keywords": ["employment agency", "recruitment agency", "staffing"],
    },
    "accounting": {
        "id": "accounting",
        "label": "Accounting & Tax Firms",
        "description": "Chartered accountants, tax advisors, auditors, and bookkeeping services.",
        "osm_tags": [
            'node["office"="accountant"]',
            'way["office"="accountant"]',
            'node["office"="tax_advisor"]',
            'way["office"="tax_advisor"]',
            'node["office"="bookkeeper"]',
            'way["office"="bookkeeper"]',
            'node["office"="financial_advisor"]',
            'way["office"="financial_advisor"]',
        ],
        "display_tags": ["office=accountant", "office=tax_advisor", "office=bookkeeper", "office=financial_advisor"],
        "search_keywords": ["accountant", "tax consultant", "chartered accountant", "bookkeeper"],
    },
    "electronics": {
        "id": "electronics",
        "label": "Electronics Shops & Suppliers",
        "description": "Retailers and component suppliers for electronics and electrical equipment.",
        "osm_tags": [
            'node["shop"="electronics"]',
            'way["shop"="electronics"]',
            'node["shop"="electrical"]',
            'way["shop"="electrical"]',
        ],
        "display_tags": ["shop=electronics", "shop=electrical"],
        "search_keywords": ["electronics shop", "electrical supplier", "electronics store"],
    },
    "computers": {
        "id": "computers",
        "label": "Computer & IT Equipment Shops",
        "description": "Computer retailers, IT hardware vendors, and computer repair centers.",
        "osm_tags": [
            'node["shop"="computer"]',
            'way["shop"="computer"]',
            'node["shop"="computer_repair"]',
            'way["shop"="computer_repair"]',
            'node["office"="it"]',
            'way["office"="it"]',
        ],
        "display_tags": ["shop=computer", "shop=computer_repair", "office=it"],
        "search_keywords": ["computer shop", "computer repair", "hardware vendor"],
    },
    "logistics": {
        "id": "logistics",
        "label": "Logistics & Freight Services",
        "description": "Freight forwarding, cargo transport, and courier management offices.",
        "osm_tags": [
            'node["office"="logistics"]',
            'way["office"="logistics"]',
            'node["office"="freight"]',
            'way["office"="freight"]',
            'node["office"="courier"]',
            'way["office"="courier"]',
        ],
        "display_tags": ["office=logistics", "office=freight", "office=courier"],
        "search_keywords": ["logistics", "freight forwarding", "courier service"],
    },
    "manufacturing": {
        "id": "manufacturing",
        "label": "Industrial & Manufacturing",
        "description": "Manufacturing workshops, industrial production facilities, and fabricators.",
        "osm_tags": [
            'node["landuse"="industrial"]',
            'way["landuse"="industrial"]',
            'node["man_made"="works"]',
            'way["man_made"="works"]',
            'node["craft"]',
            'way["craft"]',
        ],
        "display_tags": ["landuse=industrial", "man_made=works", "craft=*"],
        "search_keywords": ["industrial works", "manufacturing plant", "workshop"],
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


def build_overpass_category_query(category_id: str, south: float, west: float, north: float, east: float, timeout: int = 25, max_results: int = 300) -> str:
    """
    Constructs an Overpass QL query string with bounding box constraints.
    Applies strict timeout and result limits.
    """
    cat = get_category_definition(category_id)
    bbox_str = f"({south:.6f},{west:.6f},{north:.6f},{east:.6f})"
    
    query_parts = []
    for tag_selector in cat["osm_tags"]:
        query_parts.append(f"  {tag_selector}{bbox_str};")
        
    clauses = "\n".join(query_parts)
    overpass_query = f"""[out:json][timeout:{timeout}];
(
{clauses}
);
out center tags {max_results};
"""
    return overpass_query
