"""
Business Lead Finder - FastAPI Application Entrypoint.
Compatible with local Uvicorn development, Vercel Serverless Functions, and Render.
"""
from datetime import datetime, timezone
from typing import List
from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from api.categories import CATEGORIES
from api.models import (
    CategoryItem,
    HealthResponse,
    SearchResponse,
    ExportFilteredRequest,
)
from api.osm_service import search_business_leads
from api.csv_exporter import generate_leads_csv

app = FastAPI(
    title="Business Lead Finder API",
    description="Search OpenStreetMap business leads by category and location",
    version="1.0.0",
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
        service="Business Lead Finder API",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/categories", response_model=List[CategoryItem])
async def list_categories():
    """Returns list of supported business categories and their documented OSM tags."""
    return [
        CategoryItem(
            id=cat["id"],
            label=cat["label"],
            description=cat["description"],
            display_tags=cat["display_tags"],
        )
        for cat in CATEGORIES.values()
    ]


@app.get("/api/search", response_model=SearchResponse)
async def search_leads(
    location: str = Query(..., description="City or area name (e.g. Kolkata, Dallas, London)"),
    category: str = Query(..., description="Business category ID (e.g. distributors, accounting)"),
):
    """
    Search OpenStreetMap for business leads matching category in the specified location.
    Results are cached in memory for repeat queries.
    """
    return await search_business_leads(location=location, category=category)


@app.get("/api/export")
async def export_leads_csv(
    location: str = Query(..., description="City or area name"),
    category: str = Query(..., description="Business category ID"),
):
    """
    Exports search results as a downloadable CSV.
    Uses cached search results if recently queried to prevent duplicate Overpass requests.
    Includes formula injection mitigation and UTF-8-sig encoding.
    """
    search_result = await search_business_leads(location=location, category=category)
    csv_bytes = generate_leads_csv(search_result.listings)
    
    clean_loc = "".join(c for c in location if c.isalnum() or c in ("-", "_")).lower()
    filename = f"leads_{clean_loc}_{category}.csv"
    
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@app.post("/api/export-filtered")
async def export_filtered_leads_csv(payload: ExportFilteredRequest):
    """
    Exports client-filtered records as a downloadable CSV.
    Allows non-technical business owner to export only their refined selections.
    """
    csv_bytes = generate_leads_csv(payload.listings)
    
    clean_loc = "".join(c for c in payload.location if c.isalnum() or c in ("-", "_")).lower()
    filename = f"leads_filtered_{clean_loc}_{payload.category}.csv"
    
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


# Root fallback endpoint
@app.get("/")
async def root():
    return {
        "message": "Business Lead Finder API is running.",
        "health": "/api/health",
        "docs": "/api/docs",
    }
