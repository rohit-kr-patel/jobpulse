"""Health check endpoint.

Used for container orchestration liveness/readiness checks and for
verifying the API and database are both reachable.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Return API status and database connectivity.

    Never raises on a database failure — instead reports
    `"database": "unreachable"` so the endpoint stays useful for
    debugging even when Postgres is down.
    """
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - deliberately broad for a health probe
        logger.exception("Health check database probe failed")
        db_status = "unreachable"

    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": db_status,
    }
