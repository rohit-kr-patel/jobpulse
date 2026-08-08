"""FetchLog model.

Persists the per-source summary already computed by
app/services/job_service.fetch_and_store_all on every run (whether
triggered manually via POST /jobs/fetch now, or by the scheduler in
Phase 8), giving visibility into fetch history over time.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class FetchLog(Base):
    """A record of one source's results from one fetch run."""

    __tablename__ = "fetch_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fetched_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False)
    failed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
