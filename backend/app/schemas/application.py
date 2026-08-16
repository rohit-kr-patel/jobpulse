"""Request/response schemas for the application tracker."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStatus
from app.schemas.job import JobResponse


class ApplicationCreateRequest(BaseModel):
    """Payload to start tracking a job."""

    job_id: int
    status: ApplicationStatus = ApplicationStatus.SAVED
    notes: str | None = Field(None, max_length=5000)


class ApplicationUpdateRequest(BaseModel):
    """Payload for a partial update. Both fields are optional.

    `notes` uses a three-state distinction: omitted from the request
    body entirely means "leave unchanged"; explicit `null` means
    "clear the notes". The route reads the raw request body to tell
    these apart (see routes/applications.py).
    """

    status: ApplicationStatus | None = None
    notes: str | None = Field(None, max_length=5000)


class ApplicationResponse(BaseModel):
    """A tracked application, with the job embedded for display convenience."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job: JobResponse
    status: ApplicationStatus
    notes: str | None
    applied_at: datetime | None
    rejected_at: datetime | None
    created_at: datetime
    updated_at: datetime
