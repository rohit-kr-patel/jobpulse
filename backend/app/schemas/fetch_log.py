"""Response schema for fetch log entries."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FetchLogResponse(BaseModel):
    """A single source's summary from one fetch run, as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    fetched_count: int
    created_count: int
    updated_count: int
    failed: bool
    started_at: datetime
    finished_at: datetime
