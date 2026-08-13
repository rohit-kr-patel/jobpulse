"""JobPulse FastAPI application entrypoint.

Phase 1 wired up the application factory, logging, CORS, and health
check. Phase 2 added user preferences, resume upload, startup seeding
of the single V1 user, and a generic exception handler. Phase 3 added
resume parsing (no new routes). Phase 4 added job fetching/listing.
Phase 5 added fetch-log history (applications remain Phase 10 scope -
see docs/TODO.md). Phase 6 added the frontend dashboard (no new
backend routes). Phase 7 added job matching. Phase 8 added the daily
scheduler (disabled by default - see docs/TODO.md). Phase 9 adds
notifications.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.fetch_logs import router as fetch_logs_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.matches import router as matches_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.preferences import router as preferences_router
from app.api.routes.resume import router as resume_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import session as db_session
from app.db.seed import seed_default_user
from app.scheduler.scheduler import start_scheduler, stop_scheduler

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup/shutdown hooks."""
    logger.info("JobPulse backend starting up (environment=%s)", settings.environment)

    db = db_session.SessionLocal()
    try:
        seed_default_user(db, settings)
    finally:
        db.close()

    app.state.scheduler = start_scheduler(settings)

    yield

    stop_scheduler(app.state.scheduler)
    logger.info("JobPulse backend shutting down")


def create_app() -> FastAPI:
    """Application factory.

    Keeping app creation in a factory function makes the app easy to
    import in tests without triggering side effects at import time.
    """
    app = FastAPI(
        title=settings.app_name,
        description="Personal job assistant: fetch, rank, and track jobs daily.",
        version="0.10.0",
        lifespan=lifespan,
    )

    allow_origins = (
        ["*"]
        if settings.cors_allow_origins == "*"
        else [origin.strip() for origin in settings.cors_allow_origins.split(",")]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        """Log the full exception server-side, but never leak internals to the client."""
        logger.exception("Unhandled exception while processing request", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    app.include_router(health_router)
    app.include_router(preferences_router)
    app.include_router(resume_router)
    app.include_router(jobs_router)
    app.include_router(fetch_logs_router)
    app.include_router(matches_router)
    app.include_router(notifications_router)

    return app


app = create_app()
