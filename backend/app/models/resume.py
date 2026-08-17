"""Resume model.

Stores metadata about an uploaded resume PDF. The file itself lives on
disk under `settings.resume_upload_dir`; only the path and metadata are
persisted here. `parsed_*` fields hold rule-based extraction results
(see app/parsing/resume_parser.py) and are nullable since extraction
is best-effort and may find nothing.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Resume(Base):
    """Metadata (and parsed content) for a single uploaded resume file."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    parsed_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    parsed_education: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    parsed_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="resumes")  # noqa: F821
