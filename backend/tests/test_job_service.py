"""Tests for app.services.job_service, focused on dedup/upsert behavior.

Uses a monkeypatched fetcher module so these tests don't depend on
real network access - HTTP-shape correctness is covered separately in
tests/test_*_fetcher.py.
"""

from datetime import UTC, datetime

import pytest

from app.core.config import Settings
from app.core.exceptions import JobNotFoundError
from app.fetchers.base import NormalizedJob
from app.repositories import fetch_log_repository
from app.services import job_service


def _make_job(external_id: str, title: str, source: str = "greenhouse") -> NormalizedJob:
    return NormalizedJob(
        source=source,
        external_id=external_id,
        title=title,
        company="Acme",
        location="Remote",
        is_remote=True,
        description="A great job.",
        apply_url=f"https://example.com/jobs/{external_id}",
        posted_at=datetime(2026, 8, 1, tzinfo=UTC),
    )


@pytest.fixture()
def db_session(client):  # noqa: ARG001 - reuse the `client` fixture's DB setup
    """A DB session bound to the same in-memory SQLite engine as `client`."""
    from app.db import session as db_session_module

    session = db_session_module.SessionLocal()
    yield session
    session.close()


def test_fetch_and_store_all_creates_and_updates_across_two_runs(monkeypatch, db_session):
    first_run_jobs = [
        _make_job("1", "Backend Engineer"),
        _make_job("2", "Frontend Engineer"),
    ]
    second_run_jobs = [
        _make_job("1", "Senior Backend Engineer"),
        _make_job("3", "Data Engineer"),
    ]

    calls = {"count": 0}

    def fake_fetch(_settings, _client):
        calls["count"] += 1
        return first_run_jobs if calls["count"] == 1 else second_run_jobs

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", fake_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    settings = Settings()

    first_summaries = job_service.fetch_and_store_all(db_session, settings)
    greenhouse_summary_1 = next(s for s in first_summaries if s.source == "greenhouse")
    assert greenhouse_summary_1.fetched == 2
    assert greenhouse_summary_1.created == 2
    assert greenhouse_summary_1.updated == 0
    assert greenhouse_summary_1.failed is False

    second_summaries = job_service.fetch_and_store_all(db_session, settings)
    greenhouse_summary_2 = next(s for s in second_summaries if s.source == "greenhouse")
    assert greenhouse_summary_2.fetched == 2
    assert greenhouse_summary_2.created == 1  # job "3" is new
    assert greenhouse_summary_2.updated == 1  # job "1" already existed

    all_jobs = job_service.list_jobs(db_session, limit=50)
    assert len(all_jobs) == 3  # jobs "1", "2", "3" - no duplicates from re-fetching "1"

    updated_job = next(j for j in all_jobs if j.external_id == "1")
    assert updated_job.title == "Senior Backend Engineer"  # updated in place


def test_fetch_and_store_all_isolates_a_failing_source(monkeypatch, db_session):
    def broken_fetch(_settings, _client):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", broken_fetch)
    monkeypatch.setattr(
        job_service.lever_fetcher,
        "fetch",
        lambda *_: [_make_job("l1", "Lever Job", source="lever")],
    )
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    settings = Settings()
    summaries = job_service.fetch_and_store_all(db_session, settings)

    greenhouse_summary = next(s for s in summaries if s.source == "greenhouse")
    lever_summary = next(s for s in summaries if s.source == "lever")
    assert greenhouse_summary.failed is True
    assert lever_summary.failed is False
    assert lever_summary.created == 1

    # The failing source shouldn't block the working one from being stored.
    stored = job_service.list_jobs(db_session, source="lever")
    assert len(stored) == 1


def test_list_jobs_filters_by_source(monkeypatch, db_session):
    monkeypatch.setattr(
        job_service.greenhouse_fetcher,
        "fetch",
        lambda *_: [_make_job("g1", "GH Job", source="greenhouse")],
    )
    monkeypatch.setattr(
        job_service.lever_fetcher,
        "fetch",
        lambda *_: [_make_job("l1", "Lever Job", source="lever")],
    )
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    job_service.fetch_and_store_all(db_session, Settings())

    greenhouse_only = job_service.list_jobs(db_session, source="greenhouse")
    assert len(greenhouse_only) == 1
    assert greenhouse_only[0].source == "greenhouse"


def test_get_job_raises_not_found_for_missing_id(db_session):
    with pytest.raises(JobNotFoundError):
        job_service.get_job(db_session, 999999)


def test_fetch_and_store_all_records_a_fetch_log_per_source(monkeypatch, db_session):
    monkeypatch.setattr(
        job_service.greenhouse_fetcher,
        "fetch",
        lambda *_: [
            _make_job("1", "Backend Engineer"),
            _make_job("2", "Frontend Engineer"),
        ],
    )
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    job_service.fetch_and_store_all(db_session, Settings())

    logs = fetch_log_repository.list_recent(db_session)
    assert len(logs) == 4  # one per source, even the empty ones

    greenhouse_log = next(log for log in logs if log.source == "greenhouse")
    assert greenhouse_log.fetched_count == 2
    assert greenhouse_log.created_count == 2
    assert greenhouse_log.updated_count == 0
    assert greenhouse_log.failed is False
    assert greenhouse_log.finished_at >= greenhouse_log.started_at


def test_fetch_and_store_all_records_a_failed_fetch_log(monkeypatch, db_session):
    def broken_fetch(_settings, _client):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", broken_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    job_service.fetch_and_store_all(db_session, Settings())

    greenhouse_log = next(
        log for log in fetch_log_repository.list_recent(db_session) if log.source == "greenhouse"
    )
    assert greenhouse_log.failed is True
    assert greenhouse_log.fetched_count == 0


def test_list_fetch_logs_filters_by_source(monkeypatch, db_session):
    monkeypatch.setattr(
        job_service.greenhouse_fetcher, "fetch", lambda *_: [_make_job("1", "GH Job")]
    )
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    job_service.fetch_and_store_all(db_session, Settings())

    greenhouse_logs = job_service.list_fetch_logs(db_session, source="greenhouse")
    lever_logs = job_service.list_fetch_logs(db_session, source="lever")
    assert len(greenhouse_logs) == 1
    assert len(lever_logs) == 1
    assert lever_logs[0].fetched_count == 0
