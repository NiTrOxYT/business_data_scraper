"""
In-Memory Search Job / Run Registry for Apify-Style Execution Tracking.
Maintains history of scraping jobs with status, duration, record counts, and parameters.
Lightweight, zero external database requirements.
"""
from datetime import datetime, timezone
import time
import uuid
from typing import List, Optional, Dict
from api.models import SearchJob

# Maximum jobs to preserve in memory
MAX_JOBS_STORED = 50

_JOBS: Dict[str, SearchJob] = {}
_JOB_START_TIMES: Dict[str, float] = {}


def generate_job_id() -> str:
    """Generates human-readable job ID e.g. job_20261023_a1b2c3d4."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand = uuid.uuid4().hex[:6]
    return f"job_{ts}_{rand}"


def start_search_job(
    location: str,
    category: str,
    category_label: str,
    limit: int,
    keyword: Optional[str] = None,
    radius_km: Optional[float] = None,
) -> SearchJob:
    """Registers a new search run in running status."""
    job_id = generate_job_id()
    now_iso = datetime.now(timezone.utc).isoformat()
    _JOB_START_TIMES[job_id] = time.time()

    job = SearchJob(
        id=job_id,
        status="running",
        location=location,
        category=category,
        category_label=category_label,
        keyword=keyword,
        radius_km=radius_km,
        limit=limit,
        started_at=now_iso,
        records_found=0,
        duplicates_removed=0,
    )

    _JOBS[job_id] = job
    _prune_jobs()
    return job


def complete_search_job(
    job_id: str,
    records_found: int,
    duplicates_removed: int,
    data_source: str,
    cached: bool = False,
) -> Optional[SearchJob]:
    """Marks a search job as successfully completed."""
    if job_id not in _JOBS:
        return None

    job = _JOBS[job_id]
    start_time = _JOB_START_TIMES.get(job_id, time.time())
    duration = round(time.time() - start_time, 2)
    now_iso = datetime.now(timezone.utc).isoformat()

    updated = job.model_copy(
        update={
            "status": "completed",
            "completed_at": now_iso,
            "duration_seconds": duration,
            "records_found": records_found,
            "duplicates_removed": duplicates_removed,
            "data_source": data_source,
            "cached": cached,
        }
    )
    _JOBS[job_id] = updated
    return updated


def fail_search_job(job_id: str, error_message: str) -> Optional[SearchJob]:
    """Marks a search job as failed."""
    if job_id not in _JOBS:
        return None

    job = _JOBS[job_id]
    start_time = _JOB_START_TIMES.get(job_id, time.time())
    duration = round(time.time() - start_time, 2)
    now_iso = datetime.now(timezone.utc).isoformat()

    updated = job.model_copy(
        update={
            "status": "failed",
            "completed_at": now_iso,
            "duration_seconds": duration,
            "error": error_message,
        }
    )
    _JOBS[job_id] = updated
    return updated


def get_all_jobs() -> List[SearchJob]:
    """Returns all jobs ordered by start time descending."""
    return sorted(_JOBS.values(), key=lambda j: j.started_at, reverse=True)


def get_job_by_id(job_id: str) -> Optional[SearchJob]:
    """Retrieve specific job by identifier."""
    return _JOBS.get(job_id)


def _prune_jobs():
    """Keeps the job history capped at MAX_JOBS_STORED."""
    global _JOBS, _JOB_START_TIMES
    if len(_JOBS) > MAX_JOBS_STORED:
        sorted_keys = sorted(_JOBS.keys(), key=lambda k: _JOBS[k].started_at)
        keys_to_remove = sorted_keys[: len(_JOBS) - MAX_JOBS_STORED]
        for k in keys_to_remove:
            _JOBS.pop(k, None)
            _JOB_START_TIMES.pop(k, None)
