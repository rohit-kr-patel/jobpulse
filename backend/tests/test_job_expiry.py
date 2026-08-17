"""Tests for expired-job detection (Phase 10) in app.services.job_service."""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import Settings
from app.fetchers.base import NormalizedJob
from app.models.job import Job
from app.services import job_service


@pytest.fixture()
def db_session(client):  # noqa: ARG001 - reuse the `client` fixture's DB setup
    from app.db import session as db_session_module

    session = db_session_module.SessionLocal()
    yield session
    session.close()


def _seed_stale_job(db_session, *, external_id: str, days_old: int) -> Job:
    job = Job(
        source="greenhouse",
        external_id=external_id,
        title="Old Job",
        company="Acme",
        location="Remote",
        is_remote=True,
        description="An old job posting.",
        apply_url="https://example.com",
        posted_at=None,
        fetched_at=datetime.now(UTC) - timedelta(days=days_old),
        created_at=datetime.now(UTC) - timedelta(days=days_old),
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_job_older_than_threshold_and_not_refetched_is_marked_expired(monkeypatch, db_session):
    stale_job = _seed_stale_job(db_session, external_id="stale", days_old=10)

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    job_service.fetch_and_store_all(db_session, Settings(job_expire_after_days=3))

    db_session.refresh(stale_job)
    assert stale_job.is_expired is True


def test_job_within_threshold_is_not_marked_expired(monkeypatch, db_session):
    recent_job = _seed_stale_job(db_session, external_id="recent", days_old=1)

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    job_service.fetch_and_store_all(db_session, Settings(job_expire_after_days=3))

    db_session.refresh(recent_job)
    assert recent_job.is_expired is False


def test_expired_job_reappearing_in_a_fetch_is_un_expired(monkeypatch, db_session):
    stale_job = _seed_stale_job(db_session, external_id="1", days_old=10)
    stale_job.is_expired = True
    db_session.commit()

    def fake_fetch(_settings, _client):
        return [
            NormalizedJob(
                source="greenhouse",
                external_id="1",
                title="Old Job",
                company="Acme",
                location="Remote",
                is_remote=True,
                description="Back again.",
                apply_url="https://example.com",
                posted_at=None,
            )
        ]

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", fake_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    job_service.fetch_and_store_all(db_session, Settings(job_expire_after_days=3))

    db_session.refresh(stale_job)
    assert stale_job.is_expired is False


def test_expired_jobs_excluded_from_list_jobs_by_default(client, db_session):
    _seed_stale_job(db_session, external_id="1", days_old=1)
    stale_job = _seed_stale_job(db_session, external_id="2", days_old=10)
    stale_job.is_expired = True
    db_session.commit()

    default_results = job_service.list_jobs(db_session)
    assert len(default_results) == 1

    with_expired = job_service.list_jobs(db_session, include_expired=True)
    assert len(with_expired) == 2


def test_get_jobs_route_excludes_expired_by_default(client, db_session):
    _seed_stale_job(db_session, external_id="1", days_old=1)
    stale_job = _seed_stale_job(db_session, external_id="2", days_old=10)
    stale_job.is_expired = True
    db_session.commit()

    default_response = client.get("/jobs")
    assert len(default_response.json()) == 1

    with_expired_response = client.get("/jobs", params={"include_expired": True})
    assert len(with_expired_response.json()) == 2
