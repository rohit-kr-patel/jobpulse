"""Shared test fixtures.

Endpoint tests run against an in-memory SQLite database whose schema is
built directly from the SQLAlchemy models (Base.metadata), rather than
a live PostgreSQL instance. This keeps unit tests fast and dependency-free.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import session as db_session
from app.db.session import Base, get_db
from app.main import app


@pytest.fixture()
def db_engine():
    """A fresh in-memory SQLite engine with all tables created.

    Uses StaticPool so every session shares the same underlying
    connection - a plain in-memory SQLite DB is otherwise recreated
    empty for each new connection.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_engine, monkeypatch) -> TestClient:
    """A TestClient wired to the in-memory SQLite database.

    Patches both the `get_db` request dependency and the module-level
    `SessionLocal` (used by the app's startup lifespan to seed the
    default user) so no real PostgreSQL connection is required.
    """
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    monkeypatch.setattr(db_session, "SessionLocal", testing_session_local)

    def _override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
