"""Tests for the /preferences endpoints."""


def test_get_preferences_returns_404_when_not_set(client):
    response = client.get("/preferences")
    assert response.status_code == 404


def test_post_preferences_creates_and_returns_them(client):
    payload = {
        "target_roles": ["Backend Engineer", "Platform Engineer"],
        "skills": ["Python", "SQL", "Docker"],
        "locations": ["Bangalore", "Remote"],
        "experience_years": 2,
        "min_ctc": 800000,
        "max_ctc": 1500000,
        "work_mode": "remote",
    }

    response = client.post("/preferences", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["target_roles"] == payload["target_roles"]
    assert body["skills"] == payload["skills"]
    assert body["locations"] == payload["locations"]
    assert body["experience_years"] == 2
    assert body["min_ctc"] == 800000
    assert body["max_ctc"] == 1500000
    assert body["work_mode"] == "remote"
    assert body["user_id"] == 1


def test_get_preferences_returns_previously_saved_values(client):
    payload = {
        "target_roles": ["Data Engineer"],
        "skills": ["Python"],
        "locations": ["Remote"],
        "experience_years": 1,
        "min_ctc": None,
        "max_ctc": None,
        "work_mode": "any",
    }
    client.post("/preferences", json=payload)

    response = client.get("/preferences")

    assert response.status_code == 200
    assert response.json()["target_roles"] == ["Data Engineer"]


def test_post_preferences_upserts_rather_than_duplicating(client):
    first = {
        "target_roles": ["Backend Engineer"],
        "skills": ["Python"],
        "locations": ["Remote"],
        "experience_years": 1,
        "work_mode": "remote",
    }
    second = {**first, "experience_years": 3, "target_roles": ["Senior Backend Engineer"]}

    client.post("/preferences", json=first)
    response = client.post("/preferences", json=second)

    assert response.status_code == 200
    assert response.json()["experience_years"] == 3
    assert response.json()["target_roles"] == ["Senior Backend Engineer"]

    # Confirm there's still only one row by fetching once more.
    get_response = client.get("/preferences")
    assert get_response.json()["experience_years"] == 3


def test_post_preferences_rejects_empty_target_roles(client):
    payload = {
        "target_roles": [],
        "skills": ["Python"],
        "locations": ["Remote"],
        "experience_years": 1,
        "work_mode": "remote",
    }

    response = client.post("/preferences", json=payload)

    assert response.status_code == 422


def test_post_preferences_rejects_max_ctc_below_min_ctc(client):
    payload = {
        "target_roles": ["Backend Engineer"],
        "skills": ["Python"],
        "locations": ["Remote"],
        "experience_years": 1,
        "min_ctc": 2000000,
        "max_ctc": 1000000,
        "work_mode": "remote",
    }

    response = client.post("/preferences", json=payload)

    assert response.status_code == 422


def test_post_preferences_rejects_invalid_work_mode(client):
    payload = {
        "target_roles": ["Backend Engineer"],
        "skills": ["Python"],
        "locations": ["Remote"],
        "experience_years": 1,
        "work_mode": "on-the-moon",
    }

    response = client.post("/preferences", json=payload)

    assert response.status_code == 422


def test_post_preferences_rejects_negative_experience(client):
    payload = {
        "target_roles": ["Backend Engineer"],
        "skills": ["Python"],
        "locations": ["Remote"],
        "experience_years": -1,
        "work_mode": "remote",
    }

    response = client.post("/preferences", json=payload)

    assert response.status_code == 422
