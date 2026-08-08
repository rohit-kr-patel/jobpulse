"""Job endpoints.

GET /jobs and GET /jobs/{id} are documented in
docs/05_API_SPECIFICATION.md. POST /jobs/fetch is a manual trigger for
the fetch pipeline built here in Phase 4; Phase 8 wires this same
pipeline to a daily APScheduler run instead of requiring a manual call.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import JobNotFoundError
from app.db.session import get_db
from app.schemas.job import JobFetchSummary, JobResponse
from app.services import job_service

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    source: str | None = Query(None, description="Filter by source, e.g. 'greenhouse'"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[JobResponse]:
    """List stored jobs, most recently fetched first."""
    jobs = job_service.list_jobs(db, source=source, limit=limit, offset=offset)
    return [JobResponse.model_validate(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    """Return a single job by id. 404s if it doesn't exist."""
    try:
        job = job_service.get_job(db, job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return JobResponse.model_validate(job)


@router.post("/jobs/fetch", response_model=list[JobFetchSummary])
def trigger_fetch(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[JobFetchSummary]:
    """Manually run the fetch pipeline for every configured source.

    A source with no companies configured (Greenhouse/Lever) or that
    fails outright still returns a summary - it just reports 0 fetched
    or `failed: true` rather than being silently skipped.
    """
    return job_service.fetch_and_store_all(db, settings)
