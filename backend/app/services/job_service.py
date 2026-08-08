"""Business logic for job fetching and retrieval.

Pipeline (per docs/07_JOB_FETCHER_DESIGN.md): Fetch -> Normalize ->
Deduplicate -> Store. Deduplication is by (source, external_id): a
re-fetch of an already-known job updates it in place rather than
inserting a duplicate row. Cross-source duplicates (the same job
posted on two different boards) are not detected - see the design doc
for this known limitation.

Each source is fetched and committed independently so that one
source's failure never rolls back another source's already-fetched
jobs, and never blocks the whole run. Every run - per source - is
recorded to `fetch_logs` in that same commit, giving visibility into
fetch history over time (see app/repositories/fetch_log_repository.py).
"""

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import JobNotFoundError
from app.fetchers import arbeitnow_fetcher, greenhouse_fetcher, lever_fetcher, remotive_fetcher
from app.fetchers.base import NormalizedJob
from app.models.fetch_log import FetchLog
from app.models.job import Job
from app.repositories import fetch_log_repository, job_repository
from app.schemas.job import JobFetchSummary

logger = logging.getLogger(__name__)

_FETCHERS = (
    greenhouse_fetcher,
    lever_fetcher,
    remotive_fetcher,
    arbeitnow_fetcher,
)


def _normalized_job_to_values(job: NormalizedJob) -> dict:
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "is_remote": job.is_remote,
        "description": job.description,
        "apply_url": job.apply_url,
        "posted_at": job.posted_at,
    }


def _run_one_source(db: Session, fetcher_module, settings: Settings, client: httpx.Client) -> JobFetchSummary:
    source = fetcher_module.SOURCE
    started_at = datetime.now(timezone.utc)

    try:
        normalized_jobs = fetcher_module.fetch(settings, client)
    except Exception:  # noqa: BLE001 - one source's bug must never break the whole run
        logger.exception("Job fetch failed unexpectedly for source=%s", source)
        finished_at = datetime.now(timezone.utc)
        fetch_log_repository.create(
            db,
            source=source,
            fetched_count=0,
            created_count=0,
            updated_count=0,
            failed=True,
            started_at=started_at,
            finished_at=finished_at,
        )
        db.commit()
        return JobFetchSummary(source=source, fetched=0, created=0, updated=0, failed=True)

    created = 0
    updated = 0
    for job in normalized_jobs:
        _, was_created = job_repository.upsert(
            db,
            source=job.source,
            external_id=job.external_id,
            values=_normalized_job_to_values(job),
        )
        created += int(was_created)
        updated += int(not was_created)

    finished_at = datetime.now(timezone.utc)
    fetch_log_repository.create(
        db,
        source=source,
        fetched_count=len(normalized_jobs),
        created_count=created,
        updated_count=updated,
        failed=False,
        started_at=started_at,
        finished_at=finished_at,
    )
    db.commit()
    logger.info(
        "Job fetch complete for source=%s fetched=%d created=%d updated=%d",
        source,
        len(normalized_jobs),
        created,
        updated,
    )
    return JobFetchSummary(
        source=source, fetched=len(normalized_jobs), created=created, updated=updated, failed=False
    )


def fetch_and_store_all(db: Session, settings: Settings) -> list[JobFetchSummary]:
    """Run every configured fetcher, normalizing and upserting results.

    Returns one JobFetchSummary per source, regardless of whether that
    source succeeded or failed.
    """
    summaries = []
    with httpx.Client() as client:
        for fetcher_module in _FETCHERS:
            summaries.append(_run_one_source(db, fetcher_module, settings, client))
    return summaries


def list_jobs(db: Session, *, source: str | None = None, limit: int = 50, offset: int = 0) -> list[Job]:
    """List stored jobs, most recently fetched first."""
    return job_repository.list_jobs(db, source=source, limit=limit, offset=offset)


def get_job(db: Session, job_id: int) -> Job:
    """Return a single job by id.

    Raises:
        JobNotFoundError: if no job exists with that id.
    """
    job = job_repository.get_by_id(db, job_id)
    if job is None:
        raise JobNotFoundError(f"No job found with id {job_id}")
    return job


def list_fetch_logs(db: Session, *, source: str | None = None, limit: int = 50) -> list[FetchLog]:
    """List recent fetch log entries, most recent first."""
    return fetch_log_repository.list_recent(db, source=source, limit=limit)
