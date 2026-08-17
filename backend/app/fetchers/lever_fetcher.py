"""Lever job fetcher.

Lever's public Postings API (https://api.lever.co/v0/postings) is
per-company, with no directory endpoint - the companies to check are
configured explicitly via `settings.lever_company_slugs`
(comma-separated, e.g. the "acme" in jobs.lever.co/acme).
"""

import logging

import httpx

from app.core.config import Settings
from app.fetchers.base import NormalizedJob
from app.fetchers.utils import (
    display_company_name,
    html_to_text,
    looks_remote,
    parse_csv_list,
    parse_epoch_millis,
)

logger = logging.getLogger(__name__)

SOURCE = "lever"
_BASE_URL = "https://api.lever.co/v0/postings"


def fetch(settings: Settings, client: httpx.Client) -> list[NormalizedJob]:
    """Fetch and normalize open postings from every configured Lever company."""
    company_slugs = parse_csv_list(settings.lever_company_slugs)
    if not company_slugs:
        logger.info("No Lever company slugs configured; skipping Lever fetch")
        return []

    jobs: list[NormalizedJob] = []
    for slug in company_slugs:
        jobs.extend(_fetch_company(slug, settings, client))
    return jobs


def _fetch_company(
    company_slug: str, settings: Settings, client: httpx.Client
) -> list[NormalizedJob]:
    try:
        response = client.get(
            f"{_BASE_URL}/{company_slug}",
            params={"mode": "json"},
            timeout=settings.job_fetch_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError:
        logger.exception("Lever fetch failed for company_slug=%s", company_slug)
        return []

    if not isinstance(payload, list):
        logger.warning("Unexpected Lever response shape for company_slug=%s", company_slug)
        return []

    return [_normalize(raw, company_slug) for raw in payload]


def _normalize(raw: dict, company_slug: str) -> NormalizedJob:
    categories = raw.get("categories") or {}
    location = categories.get("location")
    commitment = (categories.get("commitment") or "").lower()
    description = raw.get("descriptionPlain") or html_to_text(raw.get("description") or "")

    return NormalizedJob(
        source=SOURCE,
        external_id=str(raw["id"]),
        title=(raw.get("text") or "").strip(),
        company=display_company_name(company_slug),
        location=location,
        is_remote=looks_remote(location) or "remote" in commitment,
        description=description,
        apply_url=raw.get("applyUrl") or raw.get("hostedUrl") or "",
        posted_at=parse_epoch_millis(raw.get("createdAt")),
    )
