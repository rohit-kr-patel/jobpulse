"""Response schema for notifications."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """A single notification, as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int | None
    message: str
    is_read: bool
    created_at: datetime
