"""Tests for app.services.notification_service."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import Settings
from app.core.exceptions import NotificationNotFoundError
from app.models.job import Job
from app.services import matching_service, notification_service


@pytest.fixture()
def db_session(client):  # noqa: ARG001 - reuse the `client` fixture's DB setup
    from app.db import session as db_session_module

    session = db_session_module.SessionLocal()
    yield session
    session.close()


def _seed_job(db_session, *, external_id: str, title: str, fetched_at, created_at) -> Job:
    job = Job(
        source="greenhouse",
        external_id=external_id,
        title=title,
        company="Acme",
        location="Remote",
        is_remote=True,
        description=f"{title} role. Python required.",
        apply_url="https://example.com",
        posted_at=None,
        fetched_at=fetched_at,
        created_at=created_at,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def _set_preferences(client) -> None:
    client.post(
        "/preferences",
        json={
            "target_roles": ["Engineer"],
            "skills": ["Python"],
            "locations": ["Remote"],
            "experience_years": 2,
            "work_mode": "remote",
        },
    )


def test_create_notifications_only_for_newly_fetched_jobs(client, db_session):
    _set_preferences(client)
    now = datetime.now(timezone.utc)

    _seed_job(db_session, external_id="new", title="New Job", fetched_at=now, created_at=now)
    _seed_job(
        db_session,
        external_id="old",
        title="Old Job",
        fetched_at=now,
        created_at=now - timedelta(days=5),
    )

    matches = matching_service.get_top_matches(db_session, Settings())
    created = notification_service.create_notifications_for_new_top_matches(
        db_session, Settings(), matches
    )

    assert len(created) == 1
    assert "New Job" in created[0].message
    assert "Acme" in created[0].message


def test_create_notifications_is_noop_for_empty_matches(db_session):
    created = notification_service.create_notifications_for_new_top_matches(db_session, Settings(), [])
    assert created == []


def test_list_notifications_filters_unread_only(client, db_session):
    _set_preferences(client)
    now = datetime.now(timezone.utc)
    _seed_job(db_session, external_id="1", title="Job One", fetched_at=now, created_at=now)
    _seed_job(db_session, external_id="2", title="Job Two", fetched_at=now, created_at=now)

    matches = matching_service.get_top_matches(db_session, Settings())
    notification_service.create_notifications_for_new_top_matches(db_session, Settings(), matches)

    all_notifications = notification_service.list_notifications(db_session, Settings())
    assert len(all_notifications) == 2

    notification_service.mark_notification_read(db_session, Settings(), all_notifications[0].id)

    unread = notification_service.list_notifications(db_session, Settings(), unread_only=True)
    assert len(unread) == 1


def test_mark_notification_read_raises_for_missing_id(db_session):
    with pytest.raises(NotificationNotFoundError):
        notification_service.mark_notification_read(db_session, Settings(), 999999)


def test_mark_all_notifications_read_updates_every_unread_one(client, db_session):
    _set_preferences(client)
    now = datetime.now(timezone.utc)
    _seed_job(db_session, external_id="1", title="Job One", fetched_at=now, created_at=now)
    _seed_job(db_session, external_id="2", title="Job Two", fetched_at=now, created_at=now)

    matches = matching_service.get_top_matches(db_session, Settings())
    notification_service.create_notifications_for_new_top_matches(db_session, Settings(), matches)

    updated_count = notification_service.mark_all_notifications_read(db_session, Settings())
    assert updated_count == 2

    unread = notification_service.list_notifications(db_session, Settings(), unread_only=True)
    assert unread == []
