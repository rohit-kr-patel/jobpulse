"""Business logic for user preferences."""

from sqlalchemy.orm import Session

from app.core.exceptions import PreferencesNotFoundError
from app.models.preferences import Preferences
from app.repositories import preferences_repository
from app.schemas.preferences import PreferencesRequest


def get_preferences(db: Session, user_id: int) -> Preferences:
    """Return the user's preferences.

    Raises:
        PreferencesNotFoundError: if the user hasn't set preferences yet.
    """
    preferences = preferences_repository.get_by_user_id(db, user_id)
    if preferences is None:
        raise PreferencesNotFoundError(f"No preferences set for user {user_id}")
    return preferences


def save_preferences(db: Session, user_id: int, payload: PreferencesRequest) -> Preferences:
    """Create or update the user's preferences from a validated payload."""
    return preferences_repository.upsert(db, user_id, payload.model_dump())
