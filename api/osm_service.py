"""
OpenStreetMap Integration Service: Nominatim Geocoding & Overpass API Querying.
Complies with OpenStreetMap Nominatim and Overpass API Usage Policies.
Implements resilient dual-engine retrieval, spatial bounding box queries, deduplication,
in-memory caching with refresh bypass, and comprehensive diagnostics logging.
"""
import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Any
import httpx
from fastapi import HTTPException

from api.categories import (
    is_valid_category,
    get_category_definition,
    build_overpass_category_query,
    get_category_ids,
)
from api.models import BusinessLead, SearchResponse, SearchDiagnostics

# Configure logger
logger = logging.getLogger("business_lead_finder")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [OSM_SERVICE] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Configuration defaults
DEFAULT_USER_AGENT = os.getenv(
    "OSM_USER_AGENT",
    "BusinessLeadFinder/1.0 (contact: business.leadfinder.app@gmail.com)",
)
NOMINATIM_BASE_URL = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org")
OVERPASS_API_URL = os.getenv("OVERPASS_API_URL", "https://overpass-api.de/api/interpreter")
FALLBACK_OVERPASS_API_URL = os.getenv(
    "FALLBACK_OVERPASS_API_URL", "https://lz4.overpass-api.de/api/interpreter"
)

# Geographic limits: Prevent searching entire countries/continents
MAX_BBOX_SPAN_DEGREES = 2.0  # ~220 km span maximum

# Simple in-memory cache with timestamps
_GEOCODE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_SEARCH_CACHE: Dict[str, Tuple[float, SearchResponse]] = {}
CACHE_TTL_SECONDS = 15 * 60  # 15 minutes

# Throttling lock for Nominatim (Policy requires max 1 request/second)
_NOMINATIM_LOCK = asyncio.Lock()
_LAST_NOMINATIM_REQUEST_TIME = 0.0


def _clean_cache():
    """Remove expired entries from memory caches."""
    now = time.time()
    for cache in (_GEOCODE_CACHE, _SEARCH_CACHE):
        expired = [k for k, (ts, _) in cache.items() if now - ts > CACHE_TTL_SECONDS]
        for k in expired:
            cache.pop(k, None)


def validate_location_input(location: str) -> str:
    """Validate user entered location string."""
    loc = location.strip()
    if not loc:
        raise HTTPException(
            status_code=400,
            detail="Location is required. Please specify a city, town, or district (e.g., 'Kolkata', 'Austin, TX').",
        )
    if len(loc) < 2:
        raise HTTPException(
            status_code=400,
            detail="Location must be at least 2 characters long.",
        )
    if len(loc) > 100:
        raise HTTPException(
            status_code=400,
            detail="Location name is too long (maximum 100 characters).",
        )
    return loc


def validate_category_input(category: str) -> str:
    """Validate user selected category."""
    cat = category.strip().lower()
    if not is_valid_category(cat):
        valid_cats = ", ".join(get_category_ids())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Supported categories: {valid_cats}",
        )
    return cat


async def geocode_location(location: str, client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
    """
    Geocodes a location query using OpenStreetMap Nominatim.
    Throttles outbound calls to obey Nominatim usage policy (<= 1 req/sec).
    Returns resolved place data with bounding box.
    """
    global _LAST_NOMINATIM_REQUEST_TIME
    _clean_cache()

    cache_key = location.lower().strip()
    if cache_key in _GEOCODE_CACHE:
        _, cached_data = _GEOCODE_CACHE[cache_key]
        logger.info(f"Geocode cache hit for '{location}': bbox={cached_data['bounding_box']}")
        return cached_data

    logger.info(f"Geocoding location via Nominatim: '{location}'")

    # Enforce Nominatim 1 req/sec policy using async lock
    async with _NOMINATIM_LOCK:
        now = time.time()
        elapsed = now - _LAST_NOMINATIM_REQUEST_TIME
        if elapsed < 1.1:
            await asyncio.sleep(1.1 - elapsed)
        _LAST_NOMINATIM_REQUEST_TIME = time.time()

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
            "Accept-Language": "en",
        }
        params = {
            "q": location,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 1,
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            should_close = True

        try:
            resp = await client.get(f"{NOMINATIM_BASE_URL}/search", params=params, headers=headers)
            if resp.status_code == 429:
                raise HTTPException(
                    status_code=503,
                    detail="OpenStreetMap Nominatim rate limit reached. Please wait a moment before trying again.",
                )
            if resp.status_code >= 400:
                raise HTTPException(
                    status_code=502,
                    detail=f"Nominatim geocoding service returned error (HTTP {resp.status_code}). Please try again later.",
                )

            data = resp.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Geocoding service timed out while looking up the location. Please try again.",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Unable to connect to OpenStreetMap Nominatim geocoding service: {str(e)}",
            )
        finally:
            if should_close:
                await client.aclose()

    if not data or not isinstance(data, list) or len(data) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Location '{location}' could not be found. Please check spelling or enter a specific city, town, or region.",
        )

    place = data[0]
    bbox_raw = place.get("boundingbox")
    if not bbox_raw or len(bbox_raw) < 4:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to determine boundary coordinates for '{location}'.",
        )

    south = float(bbox_raw[0])
    north = float(bbox_raw[1])
    west = float(bbox_raw[2])
    east = float(bbox_raw[3])

    lat_span = abs(north - south)
    lon_span = abs(east - west)

    # Check for excessively broad area searches (e.g. searching "USA", "Europe", "India")
    if lat_span > MAX_BBOX_SPAN_DEGREES or lon_span > MAX_BBOX_SPAN_DEGREES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The geographic area for '{location}' is too broad "
                f"(spans {max(lat_span, lon_span):.1f}°). To protect community OpenStreetMap servers, "
                "please narrow your search to a specific city, metropolitan area, or district."
            ),
        )

    result = {
        "display_name": place.get("display_name", location),
        "bounding_box": [south, west, north, east],
        "place_id": place.get("place_id"),
        "osm_id": place.get("osm_id"),
        "osm_type": place.get("osm_type"),
        "type": place.get("type", ""),
    }

    logger.info(
        f"Geocoded '{location}' -> '{result['display_name']}' bbox=[{south:.4f}, {west:.4f}, {north:.4f}, {east:.4f}]"
    )
    _GEOCODE_CACHE[cache_key] = (time.time(), result)
    return result


def _format_address(tags: Dict[str, str]) -> str:
    """Builds a human readable address from OSM tags, empty string if none."""
    parts = []
    housenumber = tags.get("addr:housenumber", "").strip()
    street = tags.get("addr:street", "").strip()
    suburb = tags.get("addr:suburb", "").strip() or tags.get("addr:neighbourhood", "").strip()
    city = (
        tags.get("addr:city", "").strip()
        or tags.get("addr:town", "").strip()
        or tags.get("addr:municipality", "").strip()
    )
    postcode = tags.get("addr:postcode", "").strip()
    state = tags.get("addr:state", "").strip()

    street_line = " ".join(filter(None, [housenumber, street]))
    if street_line:
        parts.append(street_line)
    if suburb:
        parts.append(suburb)
    if city:
        parts.append(city)
    if state:
        parts.append(state)
    if postcode:
        parts.append(postcode)

    return ", ".join(parts)


def _extract_phone(tags: Dict[str, str]) -> str:
    """Extract phone number if mapped, otherwise empty string."""
    for key in ("phone", "contact:phone", "telephone", "mobile", "contact:mobile"):
        val = tags.get(key, "").strip()
        if val:
            return val
    return ""


def _extract_website(tags: Dict[str, str]) -> str:
    """Extract official website if mapped, otherwise empty string."""
    for key in ("website", "contact:website", "url", "contact:url"):
        val = tags.get(key, "").strip()
        if val:
            if not val.startswith(("http://", "https://")):
                return f"https://{val}"
            return val
    return ""


def normalize_osm_element(
    element: Dict[str, Any], category_id: str, category_label: str
) -> Optional[BusinessLead]:
    """
    Transforms raw Overpass element (node, way, or relation) into normalized BusinessLead schema.
    Never invents missing values; sets them to empty string.
    """
    elem_type = element.get("type")
    elem_id = element.get("id")
    if not elem_type or not elem_id:
        return None

    unique_id = f"{elem_type}/{elem_id}"
    tags = element.get("tags", {}) or {}

    lat = None
    lon = None
    if elem_type == "node":
        lat = element.get("lat")
        lon = element.get("lon")
    else:
        # Ways and relations centered via 'out center'
        center = element.get("center")
        if isinstance(center, dict):
            lat = center.get("lat")
            lon = center.get("lon")

    name = (
        tags.get("name", "").strip()
        or tags.get("brand", "").strip()
        or tags.get("operator", "").strip()
    )

    phone = _extract_phone(tags)
    website = _extract_website(tags)
    address = _format_address(tags)
    city = (
        tags.get("addr:city", "").strip()
        or tags.get("addr:town", "").strip()
        or tags.get("addr:suburb", "").strip()
    )
    postcode = tags.get("addr:postcode", "").strip()
    osm_url = f"https://www.openstreetmap.org/{elem_type}/{elem_id}"

    relevant_keys = {
        "name", "brand", "operator", "shop", "office", "craft", "wholesale",
        "trade", "phone", "contact:phone", "website", "contact:website",
        "opening_hours", "email", "addr:street", "addr:city", "addr:postcode"
    }
    cleaned_tags = {k: v for k, v in tags.items() if k in relevant_keys}

    return BusinessLead(
        id=unique_id,
        name=name,
        category=category_id,
        category_label=category_label,
        phone=phone,
        website=website,
        address=address,
        city=city,
        postcode=postcode,
        lat=lat,
        lon=lon,
        osm_type=elem_type,
        osm_id=elem_id,
        osm_url=osm_url,
        tags=cleaned_tags,
    )


def normalize_nominatim_element(
    item: Dict[str, Any], category_id: str, category_label: str
) -> Optional[BusinessLead]:
    """
    Transforms OpenStreetMap entity retrieved via Nominatim into normalized BusinessLead schema.
    Extracts authentic tags, address details, phone, and website from extratags.
    """
    osm_type = item.get("osm_type")
    osm_id = item.get("osm_id")
    if not osm_type or not osm_id:
        return None

    unique_id = f"{osm_type}/{osm_id}"
    name = (item.get("name") or "").strip()

    lat = float(item["lat"]) if item.get("lat") else None
    lon = float(item["lon"]) if item.get("lon") else None

    extratags = item.get("extratags", {}) or {}
    addr_dict = item.get("address", {}) or {}

    phone = _extract_phone(extratags)
    website = _extract_website(extratags)

    parts = []
    house = addr_dict.get("house_number", "").strip()
    road = addr_dict.get("road", "").strip()
    if house or road:
        parts.append(f"{house} {road}".strip())
    suburb = addr_dict.get("suburb", "").strip() or addr_dict.get("neighbourhood", "").strip()
    if suburb:
        parts.append(suburb)
    city = addr_dict.get("city", "").strip() or addr_dict.get("town", "").strip() or addr_dict.get("county", "").strip()
    if city:
        parts.append(city)
    postcode = addr_dict.get("postcode", "").strip()
    if postcode:
        parts.append(postcode)
    formatted_address = ", ".join(parts)

    osm_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"

    tags = {k: str(v) for k, v in extratags.items()}
    if item.get("category"):
        tags["category"] = item["category"]
    if item.get("type"):
        tags["type"] = item["type"]

    return BusinessLead(
        id=unique_id,
        name=name,
        category=category_id,
        category_label=category_label,
        phone=phone,
        website=website,
        address=formatted_address,
        city=city,
        postcode=postcode,
        lat=lat,
        lon=lon,
        osm_type=osm_type,
        osm_id=osm_id,
        osm_url=osm_url,
        tags=tags,
    )


async def execute_overpass_query(query: str, client: Optional[httpx.AsyncClient] = None) -> List[Dict[str, Any]]:
    """
    Executes Overpass QL query across multiple mirror endpoints with timeout and rate limit handling.
    """
    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)
        should_close = True

    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",
    }

    endpoints = [OVERPASS_API_URL, FALLBACK_OVERPASS_API_URL]
    last_error = ""

    try:
        for endpoint in endpoints:
            try:
                logger.info(f"Dispatching query to Overpass mirror: {endpoint}")
                resp = await client.post(endpoint, data={"data": query}, headers=headers)
                if resp.status_code == 429:
                    last_error = "Overpass API rate limit reached (HTTP 429)."
                    continue
                if resp.status_code == 504:
                    last_error = "Overpass API gateway timed out (HTTP 504)."
                    continue
                if resp.status_code >= 400:
                    last_error = f"Overpass API returned status {resp.status_code}."
                    continue

                data = resp.json()
                elements = data.get("elements", [])
                logger.info(f"Overpass mirror {endpoint} returned {len(elements)} elements.")
                return elements
            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_error = f"{type(e).__name__}: {str(e)}"
                logger.warning(f"Mirror {endpoint} failed: {last_error}")
                continue

        raise HTTPException(
            status_code=503,
            detail=f"OpenStreetMap Overpass servers are currently overloaded ({last_error}).",
        )
    finally:
        if should_close:
            await client.aclose()


async def query_osm_via_bounded_nominatim(
    location: str,
    category_id: str,
    bbox: List[float],
    limit: int = 100,
    client: Optional[httpx.AsyncClient] = None,
) -> Tuple[List[BusinessLead], int]:
    """
    Resilient fallback engine: Queries OpenStreetMap entities directly via Nominatim
    bounded by the geocoded city's viewbox (west,north,east,south) with extratags=1.
    Retrieves multiple authentic, verified mapped business entities.
    """
    global _LAST_NOMINATIM_REQUEST_TIME
    cat_def = get_category_definition(category_id)
    keywords = cat_def.get("search_keywords", [category_id])

    south, west, north, east = bbox[0], bbox[1], bbox[2], bbox[3]
    viewbox_str = f"{west:.6f},{north:.6f},{east:.6f},{south:.6f}"

    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en",
    }

    leads: List[BusinessLead] = []
    seen_ids = set()
    total_raw_elements = 0

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)
        should_close = True

    try:
        # Search relevant category keywords within bounded city viewbox
        for kw in keywords[:3]:
            async with _NOMINATIM_LOCK:
                now = time.time()
                elapsed = now - _LAST_NOMINATIM_REQUEST_TIME
                if elapsed < 1.1:
                    await asyncio.sleep(1.1 - elapsed)
                _LAST_NOMINATIM_REQUEST_TIME = time.time()

                params = {
                    "q": kw,
                    "viewbox": viewbox_str,
                    "bounded": "1",
                    "format": "jsonv2",
                    "extratags": "1",
                    "addressdetails": "1",
                    "limit": str(min(limit, 50)),
                }

                try:
                    logger.info(f"Nominatim bounded POI search: q='{kw}' viewbox=[{viewbox_str}]")
                    resp = await client.get(f"{NOMINATIM_BASE_URL}/search", params=params, headers=headers)
                    if resp.status_code == 200:
                        items = resp.json()
                        total_raw_elements += len(items)
                        for it in items:
                            lead = normalize_nominatim_element(it, category_id, cat_def["label"])
                            if lead and lead.id not in seen_ids:
                                seen_ids.add(lead.id)
                                leads.append(lead)
                except Exception as err:
                    logger.warning(f"Nominatim bounded POI query failed for '{kw}': {err}")
    finally:
        if should_close:
            await client.aclose()

    return leads, total_raw_elements


async def search_business_leads(
    location: str,
    category: str,
    limit: int = 100,
    refresh: bool = False,
    client: Optional[httpx.AsyncClient] = None,
) -> SearchResponse:
    """
    Coordinates Nominatim geocoding and Overpass / Bounded Nominatim POI retrieval.
    Applies deduplication, normalization, result limit chunking, in-memory caching with refresh bypass,
    and structured diagnostics logging.
    """
    _clean_cache()
    loc_clean = validate_location_input(location)
    cat_clean = validate_category_input(category)
    cat_def = get_category_definition(cat_clean)
    safe_limit = max(1, min(limit, 300))

    cache_key = f"{loc_clean.lower()}:{cat_clean}:{safe_limit}"

    # Cache check unless refresh requested
    if not refresh and cache_key in _SEARCH_CACHE:
        _, cached_response = _SEARCH_CACHE[cache_key]
        logger.info(f"Cache hit for key '{cache_key}'. Returning {cached_response.total_found} cached listings.")
        cached_diag = (
            cached_response.diagnostics.model_copy(update={"cache_hit": True})
            if cached_response.diagnostics
            else None
        )
        return cached_response.model_copy(update={"cached": True, "diagnostics": cached_diag})

    if refresh:
        logger.info(f"Bypassing cache on user request for '{loc_clean}' ({cat_clean}).")

    # Step 1: Geocode location to bounding box
    geocode_info = await geocode_location(loc_clean, client=client)
    bbox = geocode_info["bounding_box"]
    south, west, north, east = bbox[0], bbox[1], bbox[2], bbox[3]

    leads: List[BusinessLead] = []
    seen_ids = set()
    data_source = "overpass"
    upstream_count = 0

    # Step 2: Try Overpass query with optimized spatial index query
    query = build_overpass_category_query(cat_clean, south, west, north, east, timeout=12, max_results=safe_limit)
    logger.info(f"Generated Overpass QL query:\n{query}")

    try:
        elements = await execute_overpass_query(query, client=client)
        upstream_count = len(elements)
        logger.info(f"Received {upstream_count} raw elements from Overpass.")

        for elem in elements:
            lead = normalize_osm_element(elem, cat_clean, cat_def["label"])
            if lead and lead.id not in seen_ids:
                seen_ids.add(lead.id)
                leads.append(lead)

        data_source = "overpass"
    except Exception as overpass_err:
        logger.warning(f"Overpass query failed or timed out: {overpass_err}. Engaging bounded Nominatim POI engine.")
        # Step 3: Fallback to bounded geographic POI search
        leads, upstream_count = await query_osm_via_bounded_nominatim(
            loc_clean, cat_clean, bbox=bbox, limit=safe_limit, client=client
        )
        data_source = "nominatim_bounded_poi"

    parsed_count = len(leads)
    deduplicated_count = len(seen_ids) if seen_ids else len(leads)

    # Apply safe limit chunking
    final_listings = leads[:safe_limit]
    final_count = len(final_listings)

    diagnostics = SearchDiagnostics(
        cache_hit=False,
        data_source=data_source,
        upstream_count=upstream_count,
        parsed_count=parsed_count,
        deduplicated_count=deduplicated_count,
        final_count=final_count,
        bounding_box=bbox,
    )

    logger.info(
        f"Search Complete: location='{loc_clean}' category='{cat_clean}' "
        f"source='{data_source}' upstream={upstream_count} parsed={parsed_count} "
        f"deduped={deduplicated_count} final={final_count}"
    )

    response = SearchResponse(
        location=loc_clean,
        resolved_location=geocode_info["display_name"],
        category=cat_clean,
        category_label=cat_def["label"],
        bounding_box=bbox,
        total_found=final_count,
        listings=final_listings,
        cached=False,
        diagnostics=diagnostics,
    )

    _SEARCH_CACHE[cache_key] = (time.time(), response)
    return response
