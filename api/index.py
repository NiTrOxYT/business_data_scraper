"""
Free Business Data Scraper - FastAPI Application Entrypoint.
Apify-style data extraction platform for OpenStreetMap business data.
Supports category queries, custom keyword filtering, radius constraints,
dual CSV / Excel exports, and search job tracking without paid APIs.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Query, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.categories import CATEGORIES
from api.models import (
    CategoryItem,
    HealthResponse,
    SearchResponse,
    SearchJob,
    ExportFilteredRequest,
)
from api.osm_service import search_business_leads
from api.csv_exporter import generate_leads_csv
from api.excel_exporter import generate_leads_excel
from api.job_service import get_all_jobs, get_job_by_id

app = FastAPI(
    title="Business Data Scraper API",
    description="Free Apify-style OpenStreetMap business data scraper and lead finder",
    version="1.2.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Enable CORS for local Vite dev and cloud deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def get_health():
    """Health check endpoint to verify API uptime and version."""
    return HealthResponse(
        status="ok",
        service="Business Data Scraper API",
        version="1.2.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/categories", response_model=List[CategoryItem])
async def list_categories():
    """Returns list of supported business categories and their documented OSM tags."""
    # Deduplicate aliases like accounting vs accounting_consulting
    seen_ids = set()
    items = []
    for cat in CATEGORIES.values():
        if cat["id"] not in seen_ids:
            seen_ids.add(cat["id"])
            items.append(
                CategoryItem(
                    id=cat["id"],
                    label=cat["label"],
                    description=cat["description"],
                    display_tags=cat["display_tags"],
                )
            )
    return items


@app.get("/api/search", response_model=SearchResponse)
async def search_leads(
    location: str = Query(..., description="City or area name (e.g. Kolkata, Austin, London)"),
    category: str = Query(..., description="Business category ID (e.g. distributors, electronics)"),
    keyword: Optional[str] = Query(default=None, description="Optional custom search keyword"),
    radius_km: Optional[float] = Query(default=None, ge=1, le=100, description="Optional radius in kilometers"),
    limit: int = Query(default=100, ge=1, le=300, description="Maximum number of business leads to return"),
    refresh: bool = Query(default=False, description="Set to true to bypass cache and query fresh data"),
):
    """
    Search OpenStreetMap for business leads matching category and optional keyword in the specified location.
    Supports configurable result limits, spatial radius boundaries, refresh cache bypass, and job logging.
    """
    return await search_business_leads(
        location=location,
        category=category,
        keyword=keyword,
        radius_km=radius_km,
        limit=limit,
        refresh=refresh,
    )


@app.get("/api/export")
async def export_leads(
    location: str = Query(..., description="City or area name"),
    category: str = Query(..., description="Business category ID"),
    keyword: Optional[str] = Query(default=None, description="Optional custom keyword"),
    radius_km: Optional[float] = Query(default=None, ge=1, le=100, description="Optional radius in kilometers"),
    limit: int = Query(default=100, ge=1, le=300),
    refresh: bool = Query(default=False),
    format: str = Query(default="csv", description="Export format: 'csv' or 'excel'"),
):
    """
    Exports search results as downloadable CSV or Excel (.xlsx).
    Uses cached search results if available to prevent duplicate upstream requests.
    Features spreadsheet formula injection protection and unicode preservation.
    """
    search_result = await search_business_leads(
        location=location,
        category=category,
        keyword=keyword,
        radius_km=radius_km,
        limit=limit,
        refresh=refresh,
    )

    clean_loc = "".join(c for c in location if c.isalnum() or c in ("-", "_")).lower()
    
    if format.lower() == "excel":
        file_bytes = generate_leads_excel(search_result.listings, sheet_title=f"Leads - {clean_loc}")
        filename = f"leads_{clean_loc}_{category}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        file_bytes = generate_leads_csv(search_result.listings)
        filename = f"leads_{clean_loc}_{category}.csv"
        media_type = "text/csv; charset=utf-8"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@app.post("/api/export-filtered")
async def export_filtered_leads(payload: ExportFilteredRequest):
    """
    Exports client-filtered or individually selected records as downloadable CSV or Excel.
    Allows users to export precisely refined prospect lists.
    """
    clean_loc = "".join(c for c in payload.location if c.isalnum() or c in ("-", "_")).lower()

    if payload.format.lower() == "excel":
        file_bytes = generate_leads_excel(payload.listings, sheet_title="Selected Leads")
        filename = f"leads_selected_{clean_loc}_{payload.category}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        file_bytes = generate_leads_csv(payload.listings)
        filename = f"leads_selected_{clean_loc}_{payload.category}.csv"
        media_type = "text/csv; charset=utf-8"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@app.get("/api/jobs", response_model=List[SearchJob])
async def list_jobs():
    """
    Lists recent search jobs with status, duration, record counts, and parameters.
    Apify-style job tracking without external database dependencies.
    """
    return get_all_jobs()


@app.get("/api/jobs/{job_id}", response_model=SearchJob)
async def get_job(job_id: str):
    """Retrieve details for a specific search job."""
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job


# Root fallback endpoint
@app.get("/")
async def root():
    return {
        "message": "Business Data Scraper API is running.",
        "version": "1.2.0",
        "health": "/api/health",
        "docs": "/api/docs",
    }
