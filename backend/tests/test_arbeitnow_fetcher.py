"""Tests for app.fetchers.arbeitnow_fetcher, using respx to mock HTTP."""

import httpx
import respx

from app.core.config import Settings
from app.fetchers import arbeitnow_fetcher

_PAGE_1 = {
    "data": [
        {
            "slug": "backend-engineer-acme-123",
            "company_name": "acme",
            "title": "Backend Engineer",
            "description": "<p>Build things.</p>",
            "remote": True,
            "url": "https://www.arbeitnow.com/jobs/companies/acme/backend-engineer-acme-123",
            "tags": ["Engineering"],
            "job_types": ["Full Time"],
            "location": "",
            "created_at": 1785600000,
        }
    ],
    "links": {"next": "https://www.arbeitnow.com/api/job-board-api?page=2"},
}

_PAGE_2 = {
    "data": [
        {
            "slug": "frontend-engineer-acme-456",
            "company_name": "acme",
            "title": "Frontend Engineer",
            "description": "<p>Build UIs.</p>",
            "remote": False,
            "url": "https://www.arbeitnow.com/jobs/companies/acme/frontend-engineer-acme-456",
            "tags": ["Engineering"],
            "job_types": ["Full Time"],
            "location": "Berlin, Berlin",
            "created_at": 1785600000,
        }
    ],
    "links": {"next": None},
}


@respx.mock
def test_fetch_normalizes_a_single_page_by_default():
    respx.get("https://www.arbeitnow.com/api/job-board-api").mock(
        return_value=httpx.Response(200, json=_PAGE_1)
    )
    settings = Settings(arbeitnow_max_pages=1)

    with httpx.Client() as client:
        jobs = arbeitnow_fetcher.fetch(settings, client)

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == "arbeitnow"
    assert job.external_id == "backend-engineer-acme-123"
    assert job.title == "Backend Engineer"
    assert job.company == "acme"
    assert job.location is None
    assert job.is_remote is True
    assert job.description == "Build things."
    assert job.posted_at is not None


@respx.mock
def test_fetch_follows_pagination_up_to_the_configured_page_limit():
    # The more specific (page=2) route must be registered first: respx
    # matches in registration order, and a route with no params
    # constraint otherwise matches any query string, including ?page=2.
    respx.get("https://www.arbeitnow.com/api/job-board-api", params={"page": "2"}).mock(
        return_value=httpx.Response(200, json=_PAGE_2)
    )
    respx.get("https://www.arbeitnow.com/api/job-board-api").mock(
        return_value=httpx.Response(200, json=_PAGE_1)
    )
    settings = Settings(arbeitnow_max_pages=2)

    with httpx.Client() as client:
        jobs = arbeitnow_fetcher.fetch(settings, client)

    assert len(jobs) == 2
    assert {job.external_id for job in jobs} == {
        "backend-engineer-acme-123",
        "frontend-engineer-acme-456",
    }


@respx.mock
def test_fetch_stops_at_page_limit_even_if_more_pages_exist():
    respx.get("https://www.arbeitnow.com/api/job-board-api").mock(
        return_value=httpx.Response(200, json=_PAGE_1)
    )
    settings = Settings(arbeitnow_max_pages=1)

    with httpx.Client() as client:
        jobs = arbeitnow_fetcher.fetch(settings, client)

    # Page 1 links to page 2, but max_pages=1 means we never fetch it.
    assert len(jobs) == 1
