"""Tests for the /notifications endpoints."""

from app.fetchers.base import NormalizedJob
from app.services import job_service


def _fetch_one_job(client, monkeypatch, *, title: str = "Backend Engineer") -> None:
    def fake_greenhouse_fetch(_settings, _http_client):
        return [
            NormalizedJob(
                source="greenhouse",
                external_id="1",
                title=title,
                company="Acme",
                location="Remote",
                is_remote=True,
                description="Python, Docker required.",
                apply_url="https://example.com/1",
                posted_at=None,
            )
        ]

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", fake_greenhouse_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])
    client.post("/jobs/fetch")


def _set_preferences(client) -> None:
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


def test_list_notifications_returns_empty_list_when_none_exist(client):
    response = client.get("/notifications")
    assert response.status_code == 200
    assert response.json() == []


def test_mark_notification_read_returns_404_for_missing_id(client):
    response = client.patch("/notifications/999999/read")
    assert response.status_code == 404


def test_full_notification_lifecycle_via_scheduler_pipeline(client, monkeypatch):
    from app.core.config import Settings
    from app.scheduler import jobs as scheduler_jobs

    _set_preferences(client)
    _fetch_one_job(client, monkeypatch)

    scheduler_jobs.run_daily_pipeline(Settings())

    list_response = client.get("/notifications")
    assert list_response.status_code == 200
    notifications = list_response.json()
    assert len(notifications) == 1
    assert "Backend Engineer" in notifications[0]["message"]
    assert notifications[0]["is_read"] is False

    notification_id = notifications[0]["id"]
    mark_read_response = client.patch(f"/notifications/{notification_id}/read")
    assert mark_read_response.status_code == 200
    assert mark_read_response.json()["is_read"] is True

    unread_response = client.get("/notifications", params={"unread_only": True})
    assert unread_response.json() == []


def test_mark_all_read_endpoint(client, monkeypatch):
    from app.core.config import Settings
    from app.scheduler import jobs as scheduler_jobs

    _set_preferences(client)
    _fetch_one_job(client, monkeypatch)
    scheduler_jobs.run_daily_pipeline(Settings())

    response = client.post("/notifications/mark-all-read")
    assert response.status_code == 200
    assert response.json() == {"updated": 1}

    unread_response = client.get("/notifications", params={"unread_only": True})
    assert unread_response.json() == []
