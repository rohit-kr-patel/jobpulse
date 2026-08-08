"""Shared types for job fetchers."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class NormalizedJob:
    """A job posting normalized into JobPulse's common schema.

    Every fetcher (Greenhouse, Lever, Remotive, Arbeitnow) produces a
    list of these, regardless of how different the source's raw
    response shape is.
    """

    source: str
    external_id: str
    title: str
    company: str
    location: str | None
    is_remote: bool
    description: str
    apply_url: str
    posted_at: datetime | None
