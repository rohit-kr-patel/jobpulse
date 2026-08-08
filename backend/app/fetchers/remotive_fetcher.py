"""Remotive job fetcher.

Remotive (https://remotive.com/api/remote-jobs) is a general remote-job
board covering many companies in one request - unlike Greenhouse/Lever,
no per-company configuration is needed. Filtered to
`settings.remotive_category` (default "software-dev"). Every job on
Remotive is remote by definition.
"""

import logging

import httpx

from app.core.config import Settings
from app.fetchers.base import NormalizedJob
from app.fetchers.utils import html_to_text, parse_iso_datetime

logger = logging.getLogger(__name__)

SOURCE = "remotive"
_URL = "https://remotive.com/api/remote-jobs"


def fetch(settings: Settings, client: httpx.Client) -> list[NormalizedJob]:
    """Fetch and normalize active listings from Remotive."""
    params = {}
    if settings.remotive_category:
        params["category"] = settings.remotive_category

    try:
        response = client.get(_URL, params=params, timeout=settings.job_fetch_timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError:
        logger.exception("Remotive fetch failed")
        return []

    return [_normalize(raw) for raw in payload.get("jobs", [])]


def _normalize(raw: dict) -> NormalizedJob:
    return NormalizedJob(
        source=SOURCE,
        external_id=str(raw["id"]),
        title=(raw.get("title") or "").strip(),
        company=(raw.get("company_name") or "").strip(),
        location=raw.get("candidate_required_location"),
        is_remote=True,
        description=html_to_text(raw.get("description") or ""),
        apply_url=raw.get("url") or "",
        posted_at=parse_iso_datetime(raw.get("publication_date")),
    )
