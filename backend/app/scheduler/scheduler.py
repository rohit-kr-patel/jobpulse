"""APScheduler setup and lifecycle.

Runs `app.scheduler.jobs.run_daily_pipeline` on a daily cron schedule
in a background thread (BackgroundScheduler), so it never blocks the
main FastAPI asyncio event loop - important since the pipeline itself
uses synchronous SQLAlchemy sessions and httpx clients.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import Settings
from app.scheduler.jobs import run_daily_pipeline

logger = logging.getLogger(__name__)

_JOB_ID = "daily_job_fetch_and_rank"


def build_scheduler(settings: Settings) -> BackgroundScheduler:
    """Construct a scheduler configured to run the daily pipeline, without starting it."""
    scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)
    trigger = CronTrigger(
        hour=settings.scheduler_fetch_hour,
        minute=settings.scheduler_fetch_minute,
        timezone=settings.scheduler_timezone,
    )
    scheduler.add_job(
        run_daily_pipeline,
        trigger=trigger,
        args=[settings],
        id=_JOB_ID,
        replace_existing=True,
    )
    return scheduler


def start_scheduler(settings: Settings) -> BackgroundScheduler | None:
    """Start the daily scheduler if enabled, returning None (no-op) otherwise."""
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled (SCHEDULER_ENABLED=false); skipping daily automated fetch")
        return None

    scheduler = build_scheduler(settings)
    scheduler.start()
    logger.info(
        "Scheduler started: daily fetch at %02d:%02d %s",
        settings.scheduler_fetch_hour,
        settings.scheduler_fetch_minute,
        settings.scheduler_timezone,
    )
    return scheduler


def stop_scheduler(scheduler: BackgroundScheduler | None) -> None:
    """Shut down the scheduler if one is running. Safe to call with None."""
    if scheduler is None:
        return
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
