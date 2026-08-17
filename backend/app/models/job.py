"""Job model.

Stores normalized job postings fetched from external sources
(Greenhouse, Lever, Remotive, Arbeitnow - see app/fetchers/). The
`(source, external_id)` pair is unique so re-fetching the same job
updates the existing row instead of creating a duplicate. Cross-source
duplicates (the same job posted on two different boards) are not
detected - see docs/07_JOB_FETCHER_DESIGN.md for known limitations.

`is_expired` is set by app/services/job_service after each fetch run -
see docs/18_APPLICATION_TRACKER.md for the detection rule.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Job(Base):
    """A single normalized job posting from an external source."""

    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    apply_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
