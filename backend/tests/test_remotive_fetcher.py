"""Tests for app.fetchers.remotive_fetcher, using respx to mock HTTP."""

import httpx
import respx

from app.core.config import Settings
from app.fetchers import remotive_fetcher

_SAMPLE_RESPONSE = {
    "0-legal-notice": "Remotive API Legal Notice",
    "job-count": 1,
    "jobs": [
        {
            "id": 123,
            "url": "https://remotive.com/remote-jobs/product/lead-developer-123",
            "title": "Lead Developer",
            "company_name": "Remotive",
            "company_logo": "https://remotive.com/job/123/logo",
            "category": "Software Development",
            "job_type": "full_time",
            "publication_date": "2026-08-01T10:23:26",
            "candidate_required_location": "Worldwide",
            "salary": "$40,000 - $50,000",
            "description": "<p>The full <em>HTML</em> job description here</p>",
        }
    ],
}


@respx.mock
def test_fetch_normalizes_remotive_jobs():
    respx.get("https://remotive.com/api/remote-jobs").mock(
        return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
    )
    settings = Settings(remotive_category="software-dev")

    with httpx.Client() as client:
        jobs = remotive_fetcher.fetch(settings, client)

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == "remotive"
    assert job.external_id == "123"
    assert job.title == "Lead Developer"
    assert job.company == "Remotive"
    assert job.location == "Worldwide"
    assert job.is_remote is True
    assert job.description == "The full HTML job description here"
    assert job.apply_url == "https://remotive.com/remote-jobs/product/lead-developer-123"
    assert job.posted_at is not None


@respx.mock
def test_fetch_returns_empty_list_on_http_error():
    respx.get("https://remotive.com/api/remote-jobs").mock(return_value=httpx.Response(503))
    settings = Settings(remotive_category="software-dev")

    with httpx.Client() as client:
        jobs = remotive_fetcher.fetch(settings, client)

    assert jobs == []
