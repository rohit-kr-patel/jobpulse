"""Notifications endpoints.

GET /notifications is in the original API spec's endpoint list.
PATCH /notifications/{id}/read and POST /notifications/mark-all-read
are not - added since "mark notifications as read" is an explicit
Phase 9 task and needs an endpoint to do it through.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import NotificationNotFoundError
from app.db.session import get_db
from app.schemas.notification import NotificationResponse
from app.services import notification_service

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[NotificationResponse]:
    """List the current user's notifications, most recent first."""
    notifications = notification_service.list_notifications(
        db, settings, unread_only=unread_only, limit=limit
    )
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> NotificationResponse:
    """Mark a single notification as read."""
    try:
        notification = notification_service.mark_notification_read(db, settings, notification_id)
    except NotificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return NotificationResponse.model_validate(notification)


@router.post("/notifications/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Mark every unread notification for the current user as read."""
    updated_count = notification_service.mark_all_notifications_read(db, settings)
    return {"updated": updated_count}
