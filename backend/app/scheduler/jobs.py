"""The daily automated pipeline: fetch fresh jobs, then refresh rankings.

Runs outside request scope (triggered by APScheduler in a background
thread - see app/scheduler/scheduler.py), so it manages its own DB
session rather than using the `get_db` FastAPI dependency.
"""

import logging

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import PreferencesNotFoundError
from app.db import session as db_session
from app.schemas.job import JobFetchSummary
from app.services import job_service, matching_service, notification_service

logger = logging.getLogger(__name__)


def run_daily_pipeline(settings: Settings) -> None:
    """Fetch fresh jobs from all sources, then refresh the matching engine's rankings.

    Never raises - any failure is caught and logged so a single bad
    run doesn't crash the scheduler thread or prevent tomorrow's run.
    """
    logger.info("Scheduled daily pipeline starting")
    db = db_session.SessionLocal()
    try:
        summaries = job_service.fetch_and_store_all(db, settings)
        _log_fetch_summaries(summaries)
        _refresh_rankings(db, settings)
    except Exception:  # noqa: BLE001 - the scheduler thread must never die from this
        logger.exception("Scheduled daily pipeline failed unexpectedly")
    finally:
        db.close()
    logger.info("Scheduled daily pipeline finished")


def _log_fetch_summaries(summaries: list[JobFetchSummary]) -> None:
    total_created = sum(summary.created for summary in summaries)
    total_updated = sum(summary.updated for summary in summaries)
    failed_sources = [summary.source for summary in summaries if summary.failed]

    failure_note = f"; failed sources: {', '.join(failed_sources)}" if failed_sources else ""
    logger.info(
        "Scheduled fetch complete: %d created, %d updated across %d sources%s",
        total_created,
        total_updated,
        len(summaries),
        failure_note,
    )


def _refresh_rankings(db: Session, settings: Settings) -> None:
    """Recompute the matching engine's top matches, then notify about new ones.

    GET /matches always computes live (Phase 7 has no caching layer to
    go stale), so recomputing here serves two purposes: (1) exercising
    the full fetch -> rank pipeline end-to-end as part of the daily
    run, so a break is caught here rather than silently at the next
    API call, and (2) feeding today's top matches into notification
    creation (Phase 9) for whichever of them are newly-fetched jobs.
    Skipped (not a failure) if the user hasn't set preferences yet.
    """
    try:
        matches = matching_service.get_top_matches(db, settings)
    except PreferencesNotFoundError:
        logger.info("Skipping ranking refresh: no preferences set yet")
        return

    if not matches:
        logger.info("Ranking refresh complete: no jobs to rank yet")
        return

    top_match = matches[0]
    logger.info(
        "Ranking refresh complete: %d jobs ranked, top match '%s' at %s (score=%.3f)",
        len(matches),
        top_match.job.title,
        top_match.job.company,
        top_match.score,
    )

    created_notifications = notification_service.create_notifications_for_new_top_matches(
        db, settings, matches
    )
    logger.info("Created %d notification(s) for newly-fetched top matches", len(created_notifications))
