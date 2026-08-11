"""Tests for app.services.matching_service."""

import pytest

from app.core.config import Settings
from app.core.exceptions import PreferencesNotFoundError
from app.models.job import Job
from app.services import matching_service


@pytest.fixture()
def db_session(client):  # noqa: ARG001 - reuse the `client` fixture's DB setup
    from app.db import session as db_session_module

    session = db_session_module.SessionLocal()
    yield session
    session.close()


def _seed_job(db_session, job_id_suffix: str, title: str) -> None:
    job = Job(
        source="greenhouse",
        external_id=job_id_suffix,
        title=title,
        company="Acme",
        location="Remote",
        is_remote=True,
        description=f"{title} role. Python and Docker required.",
        apply_url="https://example.com",
        posted_at=None,
    )
    db_session.add(job)
    db_session.commit()


def test_get_top_matches_raises_when_no_preferences_set(db_session):
    with pytest.raises(PreferencesNotFoundError):
        matching_service.get_top_matches(db_session, Settings())


def test_get_top_matches_returns_ranked_jobs_once_preferences_exist(client, db_session):
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
    _seed_job(db_session, "1", "Backend Engineer")
    _seed_job(db_session, "2", "Marketing Manager")

    results = matching_service.get_top_matches(db_session, Settings())

    assert len(results) == 2
    assert results[0].job.title == "Backend Engineer"
    assert results[0].score >= results[1].score


def test_get_top_matches_respects_match_top_n(client, db_session):
    client.post(
        "/preferences",
        json={
            "target_roles": ["Engineer"],
            "skills": ["Python"],
            "locations": ["Remote"],
            "experience_years": 2,
            "work_mode": "any",
        },
    )
    for i in range(5):
        _seed_job(db_session, str(i), f"Engineer {i}")

    results = matching_service.get_top_matches(db_session, Settings(match_top_n=3))

    assert len(results) == 3
