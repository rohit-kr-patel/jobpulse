"""Fetch log endpoint.

Not in the original API spec's endpoint list - added because
app/services/job_service already computes a per-source summary on
every fetch run (see POST /jobs/fetch); this just makes that history
visible instead of discarding it after the response.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fetch_log import FetchLogResponse
from app.services import job_service

router = APIRouter(tags=["fetch-logs"])


@router.get("/fetch-logs", response_model=list[FetchLogResponse])
def list_fetch_logs(
    source: str | None = Query(None, description="Filter by source, e.g. 'greenhouse'"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[FetchLogResponse]:
    """List recent job-fetch run history, most recent first."""
    logs = job_service.list_fetch_logs(db, source=source, limit=limit)
    return [FetchLogResponse.model_validate(log) for log in logs]
