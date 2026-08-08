"""Arbeitnow job fetcher.

Arbeitnow (https://www.arbeitnow.com/api/job-board-api) is a general
Europe/remote job board covering many companies in one paginated
response - no per-company configuration needed. Bounded by
`settings.arbeitnow_max_pages` (default 1) to stay a courteous,
predictable citizen of a free public API.
"""

import logging

import httpx

from app.core.config import Settings
from app.fetchers.base import NormalizedJob
from app.fetchers.utils import html_to_text, parse_epoch_seconds

logger = logging.getLogger(__name__)

SOURCE = "arbeitnow"
_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch(settings: Settings, client: httpx.Client) -> list[NormalizedJob]:
    """Fetch and normalize listings from Arbeitnow, up to the configured page limit."""
    jobs: list[NormalizedJob] = []
    url: str | None = _URL
    pages_fetched = 0

    while url and pages_fetched < settings.arbeitnow_max_pages:
        try:
            response = client.get(url, timeout=settings.job_fetch_timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            logger.exception("Arbeitnow fetch failed (page=%d)", pages_fetched + 1)
            break

        jobs.extend(_normalize(raw) for raw in payload.get("data", []))
        pages_fetched += 1
        url = (payload.get("links") or {}).get("next")

    return jobs


def _normalize(raw: dict) -> NormalizedJob:
    return NormalizedJob(
        source=SOURCE,
        external_id=raw.get("slug") or "",
        title=(raw.get("title") or "").strip(),
        company=(raw.get("company_name") or "").strip(),
        location=raw.get("location") or None,
        is_remote=bool(raw.get("remote", False)),
        description=html_to_text(raw.get("description") or ""),
        apply_url=raw.get("url") or "",
        posted_at=parse_epoch_seconds(raw.get("created_at")),
    )
