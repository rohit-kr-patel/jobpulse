"""Business logic for notifications.

V1's only notification-creation path is
`create_notifications_for_new_top_matches`, called by
app/scheduler/jobs.py right after the daily ranking refresh (Phase 8).
A job is considered "new" (worth notifying about) if its `created_at`
and `fetched_at` are within a few seconds of each other - meaning this
fetch run is the first time we've ever seen it, not a re-fetch of an
already-known job. Since `fetched_at` is bumped on every re-fetch but
`created_at` never changes, this naturally stops re-notifying about
the same job on subsequent days without needing any extra bookkeeping.
"""

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import NotificationNotFoundError
from app.matching.scoring import JobMatchResult
from app.models.notification import Notification
from app.repositories import notification_repository

_NEW_JOB_THRESHOLD_SECONDS = 60


def _is_newly_fetched(match: JobMatchResult) -> bool:
    job = match.job
    return abs((job.fetched_at - job.created_at).total_seconds()) < _NEW_JOB_THRESHOLD_SECONDS


def create_notifications_for_new_top_matches(
    db: Session, settings: Settings, matches: list[JobMatchResult]
) -> list[Notification]:
    """Create a notification for each newly-fetched job among today's top matches.

    Commits once at the end. Safe to call with an empty match list
    (returns an empty list, no-op).
    """
    created = []
    for match in matches:
        if not _is_newly_fetched(match):
            continue
        message = (
            f"New match: {match.job.title} at {match.job.company} "
            f"({match.score * 100:.0f}% fit)"
        )
        notification = notification_repository.create(
            db, user_id=settings.default_user_id, job_id=match.job.id, message=message
        )
        created.append(notification)

    if created:
        db.commit()
    return created


def list_notifications(
    db: Session, settings: Settings, *, unread_only: bool = False, limit: int = 50
) -> list[Notification]:
    """List the current user's notifications, most recent first."""
    return notification_repository.list_for_user(
        db, settings.default_user_id, unread_only=unread_only, limit=limit
    )


def mark_notification_read(db: Session, settings: Settings, notification_id: int) -> Notification:
    """Mark a single notification as read.

    Raises:
        NotificationNotFoundError: if it doesn't exist, or belongs to
            a different user.
    """
    notification = notification_repository.get_by_id(db, notification_id)
    if notification is None or notification.user_id != settings.default_user_id:
        raise NotificationNotFoundError(f"No notification found with id {notification_id}")
    return notification_repository.mark_read(db, notification)


def mark_all_notifications_read(db: Session, settings: Settings) -> int:
    """Mark every unread notification for the current user as read. Returns the count updated."""
    return notification_repository.mark_all_read(db, settings.default_user_id)
