"""Preferences endpoints.

V1 is single-user: every request operates on `settings.default_user_id`.
There is no auth/session mechanism yet - see docs/15_PROJECT_SCOPE.md.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import PreferencesNotFoundError
from app.db.session import get_db
from app.schemas.preferences import PreferencesRequest, PreferencesResponse
from app.services import preferences_service

router = APIRouter(tags=["preferences"])


@router.get("/preferences", response_model=PreferencesResponse)
def read_preferences(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PreferencesResponse:
    """Return the current user's preferences.

    Returns 404 if preferences haven't been set yet.
    """
    try:
        preferences = preferences_service.get_preferences(db, settings.default_user_id)
    except PreferencesNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PreferencesResponse.model_validate(preferences)


@router.post(
    "/preferences",
    response_model=PreferencesResponse,
    status_code=status.HTTP_200_OK,
)
def write_preferences(
    payload: PreferencesRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PreferencesResponse:
    """Create or update the current user's preferences."""
    preferences = preferences_service.save_preferences(db, settings.default_user_id, payload)
    return PreferencesResponse.model_validate(preferences)
