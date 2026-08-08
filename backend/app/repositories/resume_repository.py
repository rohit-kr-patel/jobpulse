"""Data access for the Resume model."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.resume import Resume


def create(
    db: Session,
    *,
    user_id: int,
    original_filename: str,
    stored_path: str,
    content_type: str,
    size_bytes: int,
    parsed_skills: list[str] | None = None,
    parsed_education: list[str] | None = None,
    parsed_experience_years: float | None = None,
    parsed_at: datetime | None = None,
) -> Resume:
    """Insert a new resume metadata row and return it."""
    resume = Resume(
        user_id=user_id,
        original_filename=original_filename,
        stored_path=stored_path,
        content_type=content_type,
        size_bytes=size_bytes,
        parsed_skills=parsed_skills,
        parsed_education=parsed_education,
        parsed_experience_years=parsed_experience_years,
        parsed_at=parsed_at,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume
