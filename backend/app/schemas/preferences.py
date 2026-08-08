"""Request/response schemas for user preferences."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.preferences import WorkMode


def _validate_non_empty_string_list(value: list[str], field_name: str) -> list[str]:
    """Strip whitespace and reject empty/blank entries in a string list."""
    cleaned = [item.strip() for item in value if item.strip()]
    if not cleaned:
        raise ValueError(f"{field_name} must contain at least one non-empty value")
    return cleaned


class PreferencesRequest(BaseModel):
    """Payload for creating or updating a user's preferences."""

    target_roles: list[str] = Field(
        ..., min_length=1, description="Job titles the user is targeting, e.g. 'Backend Engineer'"
    )
    skills: list[str] = Field(..., min_length=1, description="Skills/technologies the user knows")
    locations: list[str] = Field(
        ..., min_length=1, description="Preferred job locations, e.g. 'Bangalore', 'Remote'"
    )
    experience_years: int = Field(..., ge=0, le=60, description="Years of professional experience")
    min_ctc: int | None = Field(None, ge=0, description="Minimum acceptable annual CTC")
    max_ctc: int | None = Field(None, ge=0, description="Maximum expected annual CTC")
    work_mode: WorkMode = Field(..., description="Preferred working arrangement")

    @field_validator("target_roles")
    @classmethod
    def validate_target_roles(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_string_list(value, "target_roles")

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_string_list(value, "skills")

    @field_validator("locations")
    @classmethod
    def validate_locations(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_string_list(value, "locations")

    @model_validator(mode="after")
    def validate_ctc_range(self) -> "PreferencesRequest":
        if self.min_ctc is not None and self.max_ctc is not None and self.max_ctc < self.min_ctc:
            raise ValueError("max_ctc must be greater than or equal to min_ctc")
        return self


class PreferencesResponse(BaseModel):
    """Preferences as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    target_roles: list[str]
    skills: list[str]
    locations: list[str]
    experience_years: int
    min_ctc: int | None
    max_ctc: int | None
    work_mode: WorkMode
    created_at: datetime
    updated_at: datetime
