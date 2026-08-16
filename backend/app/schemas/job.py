"""Response schemas for job endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    """A single normalized job posting, as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: str
    title: str
    company: str
    location: str | None
    is_remote: bool
    description: str
    apply_url: str
    is_expired: bool
    posted_at: datetime | None
    fetched_at: datetime


class JobFetchSummary(BaseModel):
    """Summary of a manual job-fetch run, per source."""

    source: str
    fetched: int
    created: int
    updated: int
    failed: bool
