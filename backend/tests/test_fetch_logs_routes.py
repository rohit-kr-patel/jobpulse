"""Tests for GET /fetch-logs."""

from app.services import job_service


def test_list_fetch_logs_returns_empty_list_when_none_recorded(client):
    response = client.get("/fetch-logs")
    assert response.status_code == 200
    assert response.json() == []


def test_list_fetch_logs_returns_entries_after_a_fetch_run(client, monkeypatch):
    def fake_greenhouse_fetch(_settings, _http_client):
        from app.fetchers.base import NormalizedJob

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

    client.post("/jobs/fetch")

    response = client.get("/fetch-logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 4  # one per source

    greenhouse_log = next(log for log in logs if log["source"] == "greenhouse")
    assert greenhouse_log["fetched_count"] == 1
    assert greenhouse_log["created_count"] == 1
    assert greenhouse_log["failed"] is False


def test_list_fetch_logs_respects_source_filter(client, monkeypatch):
    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])

    client.post("/jobs/fetch")

    response = client.get("/fetch-logs", params={"source": "lever"})
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["source"] == "lever"
