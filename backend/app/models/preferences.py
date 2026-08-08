"""Preferences model.

One row per user (enforced via a unique constraint on `user_id`).
List-like fields (roles, skills, locations) are stored as JSON arrays
rather than PostgreSQL ARRAY columns so the schema stays portable
across dialects (e.g. SQLite in tests).
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class WorkMode(str, enum.Enum):
    """Preferred working arrangement."""

    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    ANY = "any"


class Preferences(Base):
    """A user's job-search preferences. Exactly one row per user."""

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    target_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    locations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)
    min_ctc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_ctc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_mode: Mapped[WorkMode] = mapped_column(
        Enum(WorkMode, native_enum=False, length=20), nullable=False
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

    user: Mapped["User"] = relationship(back_populates="preferences")  # noqa: F821
