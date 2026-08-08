"""Tests for the global unhandled-exception handler (app/main.py).

By default FastAPI's TestClient re-raises server exceptions instead of
converting them to HTTP responses, so these tests need
raise_server_exceptions=False to actually exercise our handler instead
of just re-raising through the test itself.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.services import job_service


def test_unhandled_exception_returns_generic_500_without_leaking_details(monkeypatch, client):
    def broken_list_jobs(*_args, **_kwargs):
        raise RuntimeError("a secret internal detail that must not leak")

    monkeypatch.setattr(job_service, "list_jobs", broken_list_jobs)

    # Reuse the DB override already set up by the `client` fixture, but
    # disable exception re-raising so our handler actually runs.
    non_raising_client = TestClient(app, raise_server_exceptions=False)
    non_raising_client.dependency_overrides = app.dependency_overrides

    response = non_raising_client.get("/jobs")

    assert response.status_code == 500
    body = response.json()
    assert body == {"detail": "Internal server error"}
    assert "secret internal detail" not in response.text


def test_domain_not_found_errors_still_return_clean_404_not_generic_500(client):
    """Sanity check that our handled domain exceptions aren't swallowed
    by the catch-all handler - they should still produce their specific
    404, not a generic 500."""
    response = client.get("/jobs/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "No job found with id 999999"}
