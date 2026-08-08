"""Data access for the Job model."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.job import Job


def get_by_source_and_external_id(db: Session, source: str, external_id: str) -> Job | None:
    """Return the job matching this source/external_id pair, if any."""
    return (
        db.query(Job)
        .filter(Job.source == source, Job.external_id == external_id)
        .one_or_none()
    )


def get_by_id(db: Session, job_id: int) -> Job | None:
    """Return the job with the given id, or None if not found."""
    return db.get(Job, job_id)


def list_jobs(db: Session, *, source: str | None = None, limit: int = 50, offset: int = 0) -> list[Job]:
    """List jobs, most recently fetched first, optionally filtered by source."""
    query = db.query(Job)
    if source is not None:
        query = query.filter(Job.source == source)
    return (
        query.order_by(Job.fetched_at.desc(), Job.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def upsert(db: Session, *, source: str, external_id: str, values: dict) -> tuple[Job, bool]:
    """Create or update the job matching (source, external_id).

    Does not commit - callers batch-commit across many upserts in one
    fetch run for efficiency (see app/services/job_service.py).

    Returns:
        A (job, created) tuple, where `created` is True for a new row
        and False for an update to an existing one.
    """
    existing = get_by_source_and_external_id(db, source, external_id)
    now = datetime.now(timezone.utc)

    if existing is None:
        job = Job(source=source, external_id=external_id, fetched_at=now, **values)
        db.add(job)
        return job, True

    for field_name, value in values.items():
        setattr(existing, field_name, value)
    existing.fetched_at = now
    return existing, False
