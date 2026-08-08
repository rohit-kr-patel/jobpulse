"""SQLAlchemy engine and session configuration.

Establishes DB connectivity, the declarative Base, and the session
factory used throughout the app. ORM models live in app/models and are
imported at the bottom of this module (after `Base` is defined) so
they register with `Base.metadata` - required for Alembic autogenerate
and for SQLAlchemy to resolve relationship() string references.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine: Engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request.

    The session is always closed after the request completes, even if
    an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from app import models  # noqa: E402,F401  (must follow Base definition)
