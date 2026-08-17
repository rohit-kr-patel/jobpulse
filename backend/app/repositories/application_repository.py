"""Data access for the Application model."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus

# Sentinel distinguishing "leave notes unchanged" from "set notes to None"
# in update() below - see application_service.py, the only caller.
_UNSET = object()


def get_by_id(db: Session, application_id: int) -> Application | None:
    """Return the application with the given id, or None if not found."""
    return db.get(Application, application_id)


def get_by_user_and_job(db: Session, user_id: int, job_id: int) -> Application | None:
    """Return the user's tracked application for a job, if any."""
    return (
        db.query(Application)
        .filter(Application.user_id == user_id, Application.job_id == job_id)
        .one_or_none()
    )


def list_for_user(
    db: Session,
    user_id: int,
    *,
    status: ApplicationStatus | None = None,
    limit: int = 100,
) -> list[Application]:
    """List a user's tracked applications, most recently updated first."""
    query = db.query(Application).filter(Application.user_id == user_id)
    if status is not None:
        query = query.filter(Application.status == status)
    return query.order_by(Application.updated_at.desc(), Application.id.desc()).limit(limit).all()


def create(
    db: Session,
    *,
    user_id: int,
    job_id: int,
    status: ApplicationStatus,
    notes: str | None,
) -> Application:
    """Insert a new application row and commit."""
    now = datetime.now(UTC)
    application = Application(
        user_id=user_id,
        job_id=job_id,
        status=status,
        notes=notes,
        applied_at=now if status == ApplicationStatus.APPLIED else None,
        rejected_at=now if status == ApplicationStatus.REJECTED else None,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def update(
    db: Session,
    application: Application,
    *,
    status: ApplicationStatus | None,
    notes: str | None | object,
) -> Application:
    """Apply a partial update to an application and commit.

    `notes=None` explicitly means "clear the notes"; pass the module's
    `_UNSET` sentinel to mean "leave notes unchanged".
    """
    if status is not None and status != application.status:
        application.status = status
        now = datetime.now(UTC)
        if status == ApplicationStatus.APPLIED:
            application.applied_at = now
        elif status == ApplicationStatus.REJECTED:
            application.rejected_at = now

    if notes is not _UNSET:
        application.notes = notes

    db.commit()
    db.refresh(application)
    return application
