"""Tests for the /applications endpoints."""

from app.fetchers.base import NormalizedJob
from app.services import job_service


def _fetch_one_job(client, monkeypatch) -> int:
    def fake_greenhouse_fetch(_settings, _http_client):
        return [
            NormalizedJob(
                source="greenhouse",
                external_id="1",
                title="Backend Engineer",
                company="Acme",
                location="Remote",
                is_remote=True,
                description="Python required.",
                apply_url="https://example.com/1",
                posted_at=None,
            )
        ]

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", fake_greenhouse_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])
    client.post("/jobs/fetch")

    return client.get("/jobs").json()[0]["id"]


def test_save_job_returns_404_for_missing_job(client):
    response = client.post("/applications", json={"job_id": 999999})
    assert response.status_code == 404


def test_save_job_creates_application(client, monkeypatch):
    job_id = _fetch_one_job(client, monkeypatch)

    response = client.post("/applications", json={"job_id": job_id})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "saved"
    assert body["job"]["id"] == job_id
    assert body["job"]["title"] == "Backend Engineer"


def test_save_job_twice_returns_409(client, monkeypatch):
    job_id = _fetch_one_job(client, monkeypatch)
    client.post("/applications", json={"job_id": job_id})

    response = client.post("/applications", json={"job_id": job_id})

    assert response.status_code == 409


def test_patch_application_updates_status(client, monkeypatch):
    job_id = _fetch_one_job(client, monkeypatch)
    create_response = client.post("/applications", json={"job_id": job_id})
    application_id = create_response.json()["id"]

    response = client.patch(f"/applications/{application_id}", json={"status": "applied"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "applied"
    assert body["applied_at"] is not None


def test_patch_application_can_set_notes_without_touching_status(client, monkeypatch):
    job_id = _fetch_one_job(client, monkeypatch)
    create_response = client.post("/applications", json={"job_id": job_id})
    application_id = create_response.json()["id"]

    response = client.patch(f"/applications/{application_id}", json={"notes": "Great culture fit"})

    assert response.status_code == 200
    body = response.json()
    assert body["notes"] == "Great culture fit"
    assert body["status"] == "saved"


def test_patch_application_returns_404_for_missing_id(client):
    response = client.patch("/applications/999999", json={"status": "applied"})
    assert response.status_code == 404


def test_list_applications_returns_history(client, monkeypatch):
    job_id = _fetch_one_job(client, monkeypatch)
    client.post("/applications", json={"job_id": job_id, "status": "applied"})

    response = client.get("/applications")

    assert response.status_code == 200
    applications = response.json()
    assert len(applications) == 1
    assert applications[0]["status"] == "applied"


def test_list_applications_filters_by_status_query_param(client, monkeypatch):
    job_id = _fetch_one_job(client, monkeypatch)
    client.post("/applications", json={"job_id": job_id, "status": "rejected"})

    matching = client.get("/applications", params={"status": "rejected"})
    assert len(matching.json()) == 1

    non_matching = client.get("/applications", params={"status": "applied"})
    assert len(non_matching.json()) == 0
