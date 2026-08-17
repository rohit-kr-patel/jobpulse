"""Tests for app.fetchers.lever_fetcher, using respx to mock HTTP."""

import httpx
import respx

from app.core.config import Settings
from app.fetchers import lever_fetcher

_SAMPLE_RESPONSE = [
    {
        "id": "abc-123",
        "text": "Senior Backend Engineer",
        "categories": {
            "location": "Remote",
            "team": "Engineering",
            "commitment": "Full-time",
        },
        "descriptionPlain": "Join our backend team.",
        "applyUrl": "https://jobs.lever.co/acme/abc-123/apply",
        "hostedUrl": "https://jobs.lever.co/acme/abc-123",
        "createdAt": 1785600000000,
    },
    {
        "id": "def-456",
        "text": "Product Designer",
        "categories": {
            "location": "New York, NY",
            "team": "Design",
            "commitment": "Full-time",
        },
        "descriptionPlain": "Design delightful things.",
        "applyUrl": "https://jobs.lever.co/acme/def-456/apply",
        "hostedUrl": "https://jobs.lever.co/acme/def-456",
        "createdAt": 1785600000000,
    },
]


def test_fetch_returns_empty_list_when_no_company_slugs_configured():
    settings = Settings(lever_company_slugs="")
    with httpx.Client() as client:
        assert lever_fetcher.fetch(settings, client) == []


@respx.mock
def test_fetch_normalizes_postings_from_configured_company():
    respx.get("https://api.lever.co/v0/postings/acme", params={"mode": "json"}).mock(
        return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
    )
    settings = Settings(lever_company_slugs="acme")

    with httpx.Client() as client:
        jobs = lever_fetcher.fetch(settings, client)

    assert len(jobs) == 2
    first = jobs[0]
    assert first.source == "lever"
    assert first.external_id == "abc-123"
    assert first.title == "Senior Backend Engineer"
    assert first.company == "Acme"
    assert first.location == "Remote"
    assert first.is_remote is True
    assert first.description == "Join our backend team."
    assert first.apply_url == "https://jobs.lever.co/acme/abc-123/apply"
    assert first.posted_at is not None

    second = jobs[1]
    assert second.is_remote is False


@respx.mock
def test_fetch_handles_unexpected_response_shape_gracefully():
    respx.get("https://api.lever.co/v0/postings/acme", params={"mode": "json"}).mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"})
    )
    settings = Settings(lever_company_slugs="acme")

    with httpx.Client() as client:
        jobs = lever_fetcher.fetch(settings, client)

    assert jobs == []
