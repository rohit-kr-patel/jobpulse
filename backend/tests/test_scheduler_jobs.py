"""Tests for app.scheduler.jobs.run_daily_pipeline.

Uses the same monkeypatched-fetcher approach as tests/test_job_service.py
so these run without real network access, and patches SessionLocal the
same way tests/conftest.py's `client` fixture does, since this pipeline
opens its own DB session rather than using the `get_db` dependency.
"""

from datetime import UTC, datetime

from app.core.config import Settings
from app.fetchers.base import NormalizedJob
from app.scheduler import jobs as scheduler_jobs
from app.services import job_service


def _make_job(external_id: str, title: str) -> NormalizedJob:
    return NormalizedJob(
        source="greenhouse",
        external_id=external_id,
        title=title,
        company="Acme",
        location="Remote",
        is_remote=True,
        description=f"{title} role. Python and Docker required.",
        apply_url=f"https://example.com/{external_id}",
        posted_at=datetime(2026, 8, 1, tzinfo=UTC),
    )


def test_run_daily_pipeline_fetches_jobs_and_skips_ranking_without_preferences(
    monkeypatch, client, caplog
):
    monkeypatch.setattr(
        job_service.greenhouse_fetcher,
        "fetch",
        lambda *_: [_make_job("1", "Backend Engineer")],
    )
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    with caplog.at_level("INFO"):
        scheduler_jobs.run_daily_pipeline(Settings())

    assert "no preferences set yet" in caplog.text.lower()

    jobs = client.get("/jobs").json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Engineer"


def test_run_daily_pipeline_refreshes_rankings_once_preferences_exist(monkeypatch, client, caplog):
    client.post(
        "/preferences",
        json={
            "target_roles": ["Backend Engineer"],
            "skills": ["Python", "Docker"],
            "locations": ["Remote"],
            "experience_years": 3,
            "work_mode": "remote",
        },
    )

    monkeypatch.setattr(
        job_service.greenhouse_fetcher,
        "fetch",
        lambda *_: [_make_job("1", "Backend Engineer")],
    )
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    with caplog.at_level("INFO"):
        scheduler_jobs.run_daily_pipeline(Settings())

    assert "ranking refresh complete" in caplog.text.lower()
    assert "backend engineer" in caplog.text.lower()


def test_run_daily_pipeline_never_raises_even_if_a_source_is_broken(monkeypatch, client, caplog):
    def broken_fetch(_settings, _client):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", broken_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    # Should not raise.
    with caplog.at_level("INFO"):
        scheduler_jobs.run_daily_pipeline(Settings())

    assert "scheduled fetch complete" in caplog.text.lower()


def test_run_daily_pipeline_handles_no_jobs_to_rank(monkeypatch, client, caplog):
    client.post(
        "/preferences",
        json={
            "target_roles": ["Backend Engineer"],
            "skills": ["Python"],
            "locations": ["Remote"],
            "experience_years": 3,
            "work_mode": "remote",
        },
    )
    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    with caplog.at_level("INFO"):
        scheduler_jobs.run_daily_pipeline(Settings())

    assert "no jobs to rank yet" in caplog.text.lower()
