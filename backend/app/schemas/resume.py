"""Response schema for resume upload."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    """Resume metadata as returned by the API after a successful upload."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime

    parsed_skills: list[str] | None
    parsed_education: list[str] | None
    parsed_experience_years: float | None
    parsed_at: datetime | None
