"""Data access for the Job model."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.job import Job


def get_by_source_and_external_id(db: Session, source: str, external_id: str) -> Job | None:
    """Return the job matching this source/external_id pair, if any."""
    return db.query(Job).filter(Job.source == source, Job.external_id == external_id).one_or_none()


def get_by_id(db: Session, job_id: int) -> Job | None:
    """Return the job with the given id, or None if not found."""
    return db.get(Job, job_id)


def list_jobs(
    db: Session,
    *,
    source: str | None = None,
    include_expired: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Job]:
    """List jobs, most recently fetched first.

    Excludes expired jobs by default - pass `include_expired=True` to
    see them too (e.g. for a job the user already tracked before it expired).
    """
    query = db.query(Job)
    if source is not None:
        query = query.filter(Job.source == source)
    if not include_expired:
        query = query.filter(Job.is_expired.is_(False))
    return query.order_by(Job.fetched_at.desc(), Job.id.desc()).offset(offset).limit(limit).all()


def upsert(db: Session, *, source: str, external_id: str, values: dict) -> tuple[Job, bool]:
    """Create or update the job matching (source, external_id).

    Does not commit - callers batch-commit across many upserts in one
    fetch run for efficiency (see app/services/job_service.py).

    Returns:
        A (job, created) tuple, where `created` is True for a new row
        and False for an update to an existing one.
    """
    existing = get_by_source_and_external_id(db, source, external_id)
    now = datetime.now(UTC)

    if existing is None:
        job = Job(source=source, external_id=external_id, fetched_at=now, **values)
        db.add(job)
        return job, True

    for field_name, value in values.items():
        setattr(existing, field_name, value)
    existing.fetched_at = now
    return existing, False


def mark_stale_as_expired(db: Session, *, source: str, cutoff: datetime) -> int:
    """Mark jobs of a source as expired if they haven't been re-fetched since `cutoff`.

    Does not commit - callers batch-commit alongside that source's
    upserts (see app/services/job_service.py). Returns the count marked.

    Uses `synchronize_session=False`: the default in-memory evaluator
    SQLAlchemy would otherwise use to update already-loaded objects in
    this session can't compare naive vs. timezone-aware datetimes
    (hit under SQLite, which doesn't store tzinfo - Postgres wouldn't
    have this issue, but the fix is dialect-independent and simpler
    either way). Callers holding an already-loaded Job that this
    update affects should `db.refresh()` it to see the change.
    """
    return (
        db.query(Job)
        .filter(Job.source == source, Job.is_expired.is_(False), Job.fetched_at < cutoff)
        .update({"is_expired": True}, synchronize_session=False)
    )
