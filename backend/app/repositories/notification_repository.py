"""Data access for the Notification model."""

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create(db: Session, *, user_id: int, job_id: int | None, message: str) -> Notification:
    """Insert a new notification. Does not commit - callers batch-commit."""
    notification = Notification(user_id=user_id, job_id=job_id, message=message)
    db.add(notification)
    return notification


def get_by_id(db: Session, notification_id: int) -> Notification | None:
    """Return the notification with the given id, or None if not found."""
    return db.get(Notification, notification_id)


def list_for_user(
    db: Session, user_id: int, *, unread_only: bool = False, limit: int = 50
) -> list[Notification]:
    """List a user's notifications, most recent first."""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()


def mark_read(db: Session, notification: Notification) -> Notification:
    """Mark a single notification as read and commit."""
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: int) -> int:
    """Mark every unread notification for a user as read. Returns the count updated."""
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return updated
