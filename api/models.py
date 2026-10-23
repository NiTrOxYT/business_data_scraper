"""
Pydantic Schemas for Free Business Data Scraper API.
Includes robust field validations, search area metadata, and diagnostics.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class CategoryItem(BaseModel):
    id: str
    label: str
    description: str
    display_tags: List[str]


class BusinessLead(BaseModel):
    id: str = Field(description="Unique identifier e.g. node/123456")
    name: str = Field(default="", description="Business name, empty if not mapped")
    category: str = Field(description="Category key e.g. distributors")
    category_label: str = Field(description="Human readable category name")
    phone: str = Field(default="", description="Contact phone, empty if not mapped")
    website: str = Field(default="", description="Official website URL, empty if not mapped")
    email: str = Field(default="", description="Public business email, only if explicitly mapped in source")
    address: str = Field(default="", description="Formatted street address, empty if not mapped")
    city: str = Field(default="", description="City or district name")
    postcode: str = Field(default="", description="Postal code or ZIP")
    lat: Optional[float] = Field(default=None, description="Latitude coordinate")
    lon: Optional[float] = Field(default=None, description="Longitude coordinate")
    osm_type: str = Field(description="node, way, or relation")
    osm_id: int = Field(description="OpenStreetMap numeric entity ID")
    osm_url: str = Field(description="Direct URL to OpenStreetMap entity")
    data_source: str = Field(default="OpenStreetMap", description="Identified data source")
    search_timestamp: str = Field(default="", description="Search execution timestamp in UTC")
    tags: Dict[str, str] = Field(default_factory=dict, description="Raw relevant OSM tags")


class SearchDiagnostics(BaseModel):
    cache_hit: bool
    data_source: str
    upstream_count: int
    parsed_count: int
    deduplicated_count: int
    final_count: int
    bounding_box: List[float]
    search_area_type: str = "administrative_boundary"
    search_area_description: str = ""
    resolved_location: str = ""
    center_coordinates: Optional[List[float]] = None
    radius_km: Optional[float] = None


class SearchResponse(BaseModel):
    location: str
    resolved_location: str
    category: str
    category_label: str
    keyword: Optional[str] = None
    radius_km: Optional[float] = None
    search_area_type: str = "administrative_boundary"
    bounding_box: List[float] = Field(description="[south, west, north, east]")
    total_found: int
    listings: List[BusinessLead]
    attribution: str = "Data © OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright)"
    notice: str = (
        "OpenStreetMap is a community-driven open database. Listing coverage, commercial details, and contact "
        "information depend on voluntary community tagging and may be incomplete, unverified, or outdated compared "
        "to proprietary directories. This service is not affiliated with or extracted from Google Maps."
    )
    cached: bool = False
    diagnostics: Optional[SearchDiagnostics] = None


class SearchJob(BaseModel):
    id: str
    status: str  # "running" | "completed" | "failed"
    location: str
    category: str
    category_label: str
    keyword: Optional[str] = None
    radius_km: Optional[float] = None
    limit: int
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    records_found: int = 0
    duplicates_removed: int = 0
    data_source: str = "OpenStreetMap"
    cached: bool = False
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class ExportFilteredRequest(BaseModel):
    location: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    format: str = Field(default="csv", pattern="^(csv|excel)$")
    listings: List[BusinessLead] = Field(..., min_length=1, max_length=2000)
