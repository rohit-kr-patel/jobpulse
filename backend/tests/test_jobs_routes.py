"""Tests for GET /jobs, GET /jobs/{id}, and POST /jobs/fetch."""

from app.core.config import Settings, get_settings
from app.fetchers.base import NormalizedJob
from app.main import app
from app.services import job_service


def test_list_jobs_returns_empty_list_when_none_fetched(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    assert response.json() == []


def test_get_job_returns_404_for_missing_id(client):
    response = client.get("/jobs/999999")
    assert response.status_code == 404


def test_trigger_fetch_populates_jobs_and_list_returns_them(client, monkeypatch):
    def fake_greenhouse_fetch(_settings, _http_client):
        return [
            NormalizedJob(
                source="greenhouse",
                external_id="1",
                title="Backend Engineer",
                company="Acme",
                location="Remote",
                is_remote=True,
                description="Great job.",
                apply_url="https://example.com/jobs/1",
                posted_at=None,
            )
        ]

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", fake_greenhouse_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    fetch_response = client.post("/jobs/fetch")
    assert fetch_response.status_code == 200
    summaries = fetch_response.json()
    assert len(summaries) == 4
    greenhouse_summary = next(s for s in summaries if s["source"] == "greenhouse")
    assert greenhouse_summary["created"] == 1
    assert greenhouse_summary["failed"] is False

    list_response = client.get("/jobs")
    assert list_response.status_code == 200
    jobs = list_response.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Engineer"
    assert jobs[0]["source"] == "greenhouse"

    job_id = jobs[0]["id"]
    detail_response = client.get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["external_id"] == "1"


def test_list_jobs_respects_source_filter_and_limit(client, monkeypatch):
    def fake_greenhouse_fetch(_settings, _http_client):
        return [
            NormalizedJob(
                source="greenhouse",
                external_id=str(i),
                title=f"Job {i}",
                company="Acme",
                location="Remote",
                is_remote=True,
                description="Job.",
                apply_url=f"https://example.com/jobs/{i}",
                posted_at=None,
            )
            for i in range(3)
        ]

    def fake_lever_fetch(_settings, _http_client):
        return [
            NormalizedJob(
                source="lever",
                external_id="l1",
                title="Lever Job",
                company="Acme",
                location="Remote",
                is_remote=True,
                description="Job.",
                apply_url="https://example.com/jobs/l1",
                posted_at=None,
            )
        ]

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", fake_greenhouse_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", fake_lever_fetch)
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    client.post("/jobs/fetch")

    all_jobs = client.get("/jobs").json()
    assert len(all_jobs) == 4

    lever_only = client.get("/jobs", params={"source": "lever"}).json()
    assert len(lever_only) == 1
    assert lever_only[0]["source"] == "lever"

    limited = client.get("/jobs", params={"limit": 2}).json()
    assert len(limited) == 2


def test_trigger_fetch_reports_failure_for_a_broken_source_without_500(client, monkeypatch):
    def broken_fetch(_settings, _http_client):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", broken_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    response = client.post("/jobs/fetch")

    assert response.status_code == 200
    summaries = response.json()
    greenhouse_summary = next(s for s in summaries if s["source"] == "greenhouse")
    assert greenhouse_summary["failed"] is True
