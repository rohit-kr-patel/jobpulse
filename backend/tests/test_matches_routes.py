"""Tests for GET /matches."""


def test_get_matches_returns_404_when_no_preferences_set(client):
    response = client.get("/matches")
    assert response.status_code == 404


def test_get_matches_returns_ranked_jobs(client, monkeypatch):
    from app.fetchers.base import NormalizedJob
    from app.services import job_service

    def fake_greenhouse_fetch(_settings, _http_client):
        return [
            NormalizedJob(
                source="greenhouse",
                external_id="1",
                title="Backend Engineer",
                company="Acme",
                location="Remote",
                is_remote=True,
                description="Python, Docker, FastAPI. 3+ years of experience required.",
                apply_url="https://example.com/1",
                posted_at=None,
            ),
            NormalizedJob(
                source="greenhouse",
                external_id="2",
                title="Marketing Manager",
                company="Acme",
                location="Berlin",
                is_remote=False,
                description="Marketing role, no engineering skills needed.",
                apply_url="https://example.com/2",
                posted_at=None,
            ),
        ]

    monkeypatch.setattr(job_service.greenhouse_fetcher, "fetch", fake_greenhouse_fetch)
    monkeypatch.setattr(job_service.lever_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.remotive_fetcher, "fetch", lambda *_: [])
    monkeypatch.setattr(job_service.arbeitnow_fetcher, "fetch", lambda *_: [])
    client.post("/jobs/fetch")

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

    response = client.get("/matches")

    assert response.status_code == 200
    matches = response.json()
    assert len(matches) == 2
    assert matches[0]["job"]["title"] == "Backend Engineer"
    assert matches[0]["score"] >= matches[1]["score"]
    assert 0.0 <= matches[0]["score"] <= 1.0
    assert set(matches[0].keys()) == {
        "job",
        "score",
        "text_similarity",
        "skill_score",
        "role_score",
        "location_score",
        "experience_score",
        "remote_score",
    }
