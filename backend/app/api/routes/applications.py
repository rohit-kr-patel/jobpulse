"""Application tracker endpoints.

POST /applications and PATCH /applications/{id} are in the original
API spec. GET /applications is not - added since "application history"
is an explicit Phase 10 task and needs somewhere to view it.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
    JobNotFoundError,
)
from app.db.session import get_db
from app.models.application import ApplicationStatus
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationUpdateRequest,
)
from app.services import application_service

router = APIRouter(tags=["applications"])


@router.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_job(
    payload: ApplicationCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ApplicationResponse:
    """Start tracking a job (default status: saved).

    404s if the job doesn't exist; 409s if it's already tracked - use
    PATCH to change an existing tracked application's status instead.
    """
    try:
        application = application_service.save_job(db, settings, payload)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateApplicationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ApplicationResponse.model_validate(application)


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ApplicationResponse:
    """Partially update a tracked application's status and/or notes.

    Reads the raw JSON body (rather than a plain Pydantic-model
    parameter) so we can tell "notes omitted" apart from "notes
    explicitly set to null" - see ApplicationUpdateRequest's docstring.
    """
    raw_body = await request.json()
    payload = ApplicationUpdateRequest.model_validate(raw_body)
    notes_provided = "notes" in raw_body

    try:
        application = application_service.update_application(
            db, settings, application_id, payload, notes_provided=notes_provided
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApplicationResponse.model_validate(application)


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[ApplicationResponse]:
    """List the current user's tracked applications - the application history view."""
    applications = application_service.list_applications(db, settings, status=status_filter)
    return [ApplicationResponse.model_validate(a) for a in applications]
