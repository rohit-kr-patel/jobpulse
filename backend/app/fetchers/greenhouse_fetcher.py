"""Greenhouse job fetcher.

Greenhouse's public Job Board API (https://boards-api.greenhouse.io)
is per-company - there's no directory of all companies using
Greenhouse, so the companies to check are configured explicitly via
`settings.greenhouse_board_tokens` (comma-separated board tokens, e.g.
the "acme" in boards.greenhouse.io/acme).
"""

import logging

import httpx

from app.core.config import Settings
from app.fetchers.base import NormalizedJob
from app.fetchers.utils import display_company_name, html_to_text, looks_remote, parse_csv_list, parse_iso_datetime

logger = logging.getLogger(__name__)

SOURCE = "greenhouse"
_BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


def fetch(settings: Settings, client: httpx.Client) -> list[NormalizedJob]:
    """Fetch and normalize open jobs from every configured Greenhouse board."""
    board_tokens = parse_csv_list(settings.greenhouse_board_tokens)
    if not board_tokens:
        logger.info("No Greenhouse board tokens configured; skipping Greenhouse fetch")
        return []

    jobs: list[NormalizedJob] = []
    for token in board_tokens:
        jobs.extend(_fetch_board(token, settings, client))
    return jobs


def _fetch_board(board_token: str, settings: Settings, client: httpx.Client) -> list[NormalizedJob]:
    try:
        response = client.get(
            f"{_BASE_URL}/{board_token}/jobs",
            params={"content": "true"},
            timeout=settings.job_fetch_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError:
        logger.exception("Greenhouse fetch failed for board_token=%s", board_token)
        return []

    return [_normalize(raw, board_token) for raw in payload.get("jobs", [])]


def _normalize(raw: dict, board_token: str) -> NormalizedJob:
    location = (raw.get("location") or {}).get("name")
    return NormalizedJob(
        source=SOURCE,
        external_id=str(raw["id"]),
        title=(raw.get("title") or "").strip(),
        company=display_company_name(board_token),
        location=location,
        is_remote=looks_remote(location),
        description=html_to_text(raw.get("content") or ""),
        apply_url=raw.get("absolute_url") or "",
        posted_at=parse_iso_datetime(raw.get("updated_at")),
    )
