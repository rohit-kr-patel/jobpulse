"""Data access for the FetchLog model."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.fetch_log import FetchLog


def create(
    db: Session,
    *,
    source: str,
    fetched_count: int,
    created_count: int,
    updated_count: int,
    failed: bool,
    started_at: datetime,
    finished_at: datetime,
) -> FetchLog:
    """Insert a fetch log row. Does not commit - callers batch-commit per fetch run."""
    log_entry = FetchLog(
        source=source,
        fetched_count=fetched_count,
        created_count=created_count,
        updated_count=updated_count,
        failed=failed,
        started_at=started_at,
        finished_at=finished_at,
    )
    db.add(log_entry)
    return log_entry


def list_recent(db: Session, *, source: str | None = None, limit: int = 50) -> list[FetchLog]:
    """List fetch log entries, most recent first, optionally filtered by source."""
    query = db.query(FetchLog)
    if source is not None:
        query = query.filter(FetchLog.source == source)
    return query.order_by(FetchLog.started_at.desc(), FetchLog.id.desc()).limit(limit).all()
