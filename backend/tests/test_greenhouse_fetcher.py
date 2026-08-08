"""Tests for app.fetchers.greenhouse_fetcher, using respx to mock HTTP."""

import httpx
import respx

from app.core.config import Settings
from app.fetchers import greenhouse_fetcher

_SAMPLE_RESPONSE = {
    "jobs": [
        {
            "id": 4020123,
            "title": "Backend Engineer",
            "location": {"name": "Remote - US"},
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/4020123",
            "updated_at": "2026-08-01T12:00:00-04:00",
            "content": "<p>Build our <strong>API</strong>.</p>",
        },
        {
            "id": 4020124,
            "title": "Platform Engineer",
            "location": {"name": "Berlin, Germany"},
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/4020124",
            "updated_at": "2026-08-02T09:00:00-04:00",
            "content": "<p>Own our platform.</p>",
        },
    ]
}


def test_fetch_returns_empty_list_when_no_board_tokens_configured():
    settings = Settings(greenhouse_board_tokens="")
    with httpx.Client() as client:
        assert greenhouse_fetcher.fetch(settings, client) == []


@respx.mock
def test_fetch_normalizes_jobs_from_configured_board():
    respx.get("https://boards-api.greenhouse.io/v1/boards/acme/jobs").mock(
        return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
    )
    settings = Settings(greenhouse_board_tokens="acme")

    with httpx.Client() as client:
        jobs = greenhouse_fetcher.fetch(settings, client)

    assert len(jobs) == 2
    first = jobs[0]
    assert first.source == "greenhouse"
    assert first.external_id == "4020123"
    assert first.title == "Backend Engineer"
    assert first.company == "Acme"
    assert first.location == "Remote - US"
    assert first.is_remote is True
    assert first.description == "Build our API ."
    assert first.apply_url == "https://boards.greenhouse.io/acme/jobs/4020123"
    assert first.posted_at is not None

    second = jobs[1]
    assert second.is_remote is False


@respx.mock
def test_fetch_queries_every_configured_board_and_skips_a_failing_one():
    respx.get("https://boards-api.greenhouse.io/v1/boards/acme/jobs").mock(
        return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
    )
    respx.get("https://boards-api.greenhouse.io/v1/boards/broken/jobs").mock(
        return_value=httpx.Response(500)
    )
    settings = Settings(greenhouse_board_tokens="acme,broken")

    with httpx.Client() as client:
        jobs = greenhouse_fetcher.fetch(settings, client)

    # Only the working board's 2 jobs should come through.
    assert len(jobs) == 2
