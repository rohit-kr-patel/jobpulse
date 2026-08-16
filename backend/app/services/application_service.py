"""Business logic for the application tracker.

One application row per (user, job) - saving an already-tracked job is
rejected (DuplicateApplicationError); use update_application to change
its status instead. This keeps POST=create/PATCH=update semantics
unambiguous rather than making POST silently upsert.
"""

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import ApplicationNotFoundError, DuplicateApplicationError, JobNotFoundError
from app.models.application import Application, ApplicationStatus
from app.repositories import application_repository, job_repository
from app.repositories.application_repository import _UNSET
from app.schemas.application import ApplicationCreateRequest, ApplicationUpdateRequest


def save_job(db: Session, settings: Settings, payload: ApplicationCreateRequest) -> Application:
    """Start tracking a job for the current user.

    Raises:
        JobNotFoundError: if `payload.job_id` doesn't exist.
        DuplicateApplicationError: if this job is already tracked.
    """
    user_id = settings.default_user_id

    if job_repository.get_by_id(db, payload.job_id) is None:
        raise JobNotFoundError(f"No job found with id {payload.job_id}")

    if application_repository.get_by_user_and_job(db, user_id, payload.job_id) is not None:
        raise DuplicateApplicationError(
            f"Job {payload.job_id} is already tracked - use PATCH to update its status"
        )

    return application_repository.create(
        db, user_id=user_id, job_id=payload.job_id, status=payload.status, notes=payload.notes
    )


def update_application(
    db: Session,
    settings: Settings,
    application_id: int,
    payload: ApplicationUpdateRequest,
    *,
    notes_provided: bool,
) -> Application:
    """Apply a partial update to a tracked application.

    `notes_provided` distinguishes "notes omitted from the request"
    (leave unchanged) from "notes explicitly set, possibly to null"
    (update it) - see ApplicationUpdateRequest's docstring.

    Raises:
        ApplicationNotFoundError: if it doesn't exist, or belongs to a different user.
    """
    application = application_repository.get_by_id(db, application_id)
    if application is None or application.user_id != settings.default_user_id:
        raise ApplicationNotFoundError(f"No application found with id {application_id}")

    return application_repository.update(
        db,
        application,
        status=payload.status,
        notes=payload.notes if notes_provided else _UNSET,
    )


def list_applications(
    db: Session, settings: Settings, *, status: ApplicationStatus | None = None
) -> list[Application]:
    """List the current user's tracked applications, most recently updated first."""
    return application_repository.list_for_user(db, settings.default_user_id, status=status)
