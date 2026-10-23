"""
Controlled Business Categories Registry for OpenStreetMap Queries.
Maps business categories to documented OSM key-value tags and Overpass QL builders.
Supports all required commercial sectors, custom keyword filtering, and backward-compatible aliases.
"""
import re
from typing import Dict, List, Any, Optional


CATEGORIES: Dict[str, Dict[str, Any]] = {
    "distributors": {
        "id": "distributors",
        "label": "Wholesalers & Distributors",
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
        "search_keywords": ["wholesale", "distributor", "wholesaler", "bulk supplier", "trade supplies"],
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
        "label": "Computer & IT Services",
        "description": "Computer retailers, IT hardware vendors, software consultants, and repair centers.",
        "nwr_selectors": [
            'nwr["shop"="computer"]',
            'nwr["shop"="computer_repair"]',
            'nwr["office"="it"]',
            'nwr["office"="telecommunication"]',
        ],
        "osm_tags": [("shop", "computer"), ("shop", "computer_repair"), ("office", "it")],
        "display_tags": ["shop=computer", "shop=computer_repair", "office=it"],
        "search_keywords": ["computer shop", "computer repair", "it hardware", "it services", "it supplier"],
    },
    "restaurants_cafes": {
        "id": "restaurants_cafes",
        "label": "Restaurants & Cafes",
        "description": "Dining establishments, coffee shops, eateries, and food service venues.",
        "nwr_selectors": [
            'nwr["amenity"="restaurant"]',
            'nwr["amenity"="cafe"]',
            'nwr["amenity"="fast_food"]',
            'nwr["amenity"="bar"]',
            'nwr["amenity"="pub"]',
        ],
        "osm_tags": [("amenity", "restaurant"), ("amenity", "cafe"), ("amenity", "fast_food")],
        "display_tags": ["amenity=restaurant", "amenity=cafe", "amenity=fast_food", "amenity=bar"],
        "search_keywords": ["restaurant", "cafe", "coffee shop", "eatery", "bistro", "diner"],
    },
    "hotels": {
        "id": "hotels",
        "label": "Hotels & Lodging",
        "description": "Hotels, motels, guest houses, and commercial hospitality accommodations.",
        "nwr_selectors": [
            'nwr["tourism"="hotel"]',
            'nwr["tourism"="motel"]',
            'nwr["tourism"="guest_house"]',
            'nwr["tourism"="hostel"]',
        ],
        "osm_tags": [("tourism", "hotel"), ("tourism", "motel"), ("tourism", "guest_house")],
        "display_tags": ["tourism=hotel", "tourism=motel", "tourism=guest_house", "tourism=hostel"],
        "search_keywords": ["hotel", "motel", "lodging", "guest house", "resort"],
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
    "accounting_consulting": {
        "id": "accounting_consulting",
        "label": "Accountants & Consultants",
        "description": "Chartered accountants, tax advisors, management consultants, and financial firms.",
        "nwr_selectors": [
            'nwr["office"="accountant"]',
            'nwr["office"="tax_advisor"]',
            'nwr["office"="bookkeeper"]',
            'nwr["office"="financial_advisor"]',
            'nwr["office"="consulting"]',
            'nwr["office"="management_consulting"]',
        ],
        "osm_tags": [("office", "accountant"), ("office", "tax_advisor"), ("office", "consulting")],
        "display_tags": ["office=accountant", "office=tax_advisor", "office=consulting", "office=financial_advisor"],
        "search_keywords": ["accountant", "tax consultant", "accounting firm", "management consulting", "bookkeeper"],
    },
    "retail_shops": {
        "id": "retail_shops",
        "label": "Retail Shops & General Stores",
        "description": "Supermarkets, convenience stores, department stores, and specialty retailers.",
        "nwr_selectors": [
            'nwr["shop"="supermarket"]',
            'nwr["shop"="convenience"]',
            'nwr["shop"="department_store"]',
            'nwr["shop"="general"]',
            'nwr["shop"="clothes"]',
            'nwr["shop"="hardware"]',
        ],
        "osm_tags": [("shop", "supermarket"), ("shop", "convenience"), ("shop", "department_store")],
        "display_tags": ["shop=supermarket", "shop=convenience", "shop=department_store", "shop=hardware"],
        "search_keywords": ["supermarket", "retail shop", "department store", "general store", "grocery store"],
    },
    "manufacturing": {
        "id": "manufacturing",
        "label": "Manufacturers & Industrial",
        "description": "Manufacturing workshops, industrial production facilities, and fabricators.",
        "nwr_selectors": [
            'nwr["landuse"="industrial"]',
            'nwr["man_made"="works"]',
            'nwr["industrial"="factory"]',
            'nwr["craft"="metal_construction"]',
        ],
        "osm_tags": [("landuse", "industrial"), ("man_made", "works"), ("industrial", "factory")],
        "display_tags": ["landuse=industrial", "man_made=works", "industrial=factory"],
        "search_keywords": ["manufacturer", "factory", "industrial works", "manufacturing workshop", "fabricator"],
    },
    "repair_services": {
        "id": "repair_services",
        "label": "Repair & Maintenance Services",
        "description": "Automotive repair shops, electronics repair, electricians, and maintenance contractors.",
        "nwr_selectors": [
            'nwr["shop"="car_repair"]',
            'nwr["shop"="motorcycle_repair"]',
            'nwr["craft"="electronics_repair"]',
            'nwr["craft"="electrician"]',
            'nwr["craft"="plumber"]',
            'nwr["craft"="hvac"]',
        ],
        "osm_tags": [("shop", "car_repair"), ("craft", "electronics_repair"), ("craft", "electrician")],
        "display_tags": ["shop=car_repair", "craft=electronics_repair", "craft=electrician", "craft=plumber"],
        "search_keywords": ["car repair", "auto repair", "electronics repair", "electrician", "plumber", "hvac repair"],
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
}

# Alias "accounting" for backward compatibility with previous version
CATEGORIES["accounting"] = {
    **CATEGORIES["accounting_consulting"],
    "id": "accounting",
}


def get_category_ids() -> List[str]:
    """Returns list of valid unique category identifiers."""
    return list(CATEGORIES.keys())


def is_valid_category(category_id: str) -> bool:
    """Check if given category identifier is registered."""
    return category_id in CATEGORIES


def get_category_definition(category_id: str) -> Dict[str, Any]:
    """Get category configuration by ID."""
    if not is_valid_category(category_id):
        raise ValueError(f"Unsupported category '{category_id}'. Valid categories: {get_category_ids()}")
    return CATEGORIES[category_id]


def sanitize_overpass_keyword(keyword: str) -> str:
    """Sanitizes user keyword to prevent Overpass QL regex injection."""
    clean = re.sub(r'[\"\'\\/\[\]\(\)\{\}\^\$\*\+\?\.\<\>\:\;\=\!\|]', '', keyword).strip()
    return clean[:50]


def build_overpass_category_query(
    category_id: str,
    south: float,
    west: float,
    north: float,
    east: float,
    keyword: Optional[str] = None,
    timeout: int = 15,
    max_results: int = 300,
) -> str:
    """
    Constructs an optimized Overpass QL query string with global bounding box constraints.
    Uses nwr (nodes, ways, relations) to leverage spatial index efficiently.
    If a custom keyword is provided, injects regex filter on the name tag.
    """
    cat = get_category_definition(category_id)
    selectors = cat.get("nwr_selectors", [])
    
    clauses: List[str] = []
    clean_kw = sanitize_overpass_keyword(keyword) if keyword else ""
    
    if clean_kw:
        for sel in selectors:
            # Overpass QL tag condition with regex name match
            clauses.append(f'  {sel}[name~"{clean_kw}",i];')
        # Also include generic entity matching name inside the bounding box
        clauses.append(f'  nwr[name~"{clean_kw}",i];')
    else:
        for sel in selectors:
            clauses.append(f'  {sel};')

    clauses_str = "\n".join(clauses)
    overpass_query = f"""[out:json][timeout:{timeout}][bbox:{south:.6f},{west:.6f},{north:.6f},{east:.6f}];
(
{clauses_str}
);
out center tags {max_results};
"""
    return overpass_query
