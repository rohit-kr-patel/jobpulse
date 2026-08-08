"""Tests for the /health endpoint.

The real database dependency is overridden with fakes so these tests
run without a live PostgreSQL instance.
"""

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


class _FakeSessionOk:
    """Fake DB session whose queries always succeed."""

    def execute(self, *_args, **_kwargs):
        return None


class _FakeSessionDown:
    """Fake DB session that simulates a database outage."""

    def execute(self, *_args, **_kwargs):
        raise RuntimeError("simulated database outage")


def _override_db_ok():
    yield _FakeSessionOk()


def _override_db_down():
    yield _FakeSessionDown()


def test_health_reports_ok_when_database_reachable():
    app.dependency_overrides[get_db] = _override_db_ok
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert "app" in body
    assert "environment" in body

    app.dependency_overrides.clear()


def test_health_reports_unreachable_when_database_down():
    app.dependency_overrides[get_db] = _override_db_down

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "unreachable"

    app.dependency_overrides.clear()
