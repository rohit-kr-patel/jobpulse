"""Data access for the Preferences model."""

from sqlalchemy.orm import Session

from app.models.preferences import Preferences


def get_by_user_id(db: Session, user_id: int) -> Preferences | None:
    """Return the preferences row for a user, or None if not set yet."""
    return db.query(Preferences).filter(Preferences.user_id == user_id).one_or_none()


def upsert(db: Session, user_id: int, values: dict) -> Preferences:
    """Create or update the single preferences row for a user.

    Commits the transaction and returns the refreshed row.
    """
    existing = get_by_user_id(db, user_id)
    if existing is None:
        preferences = Preferences(user_id=user_id, **values)
        db.add(preferences)
    else:
        for field_name, value in values.items():
            setattr(existing, field_name, value)
        preferences = existing

    db.commit()
    db.refresh(preferences)
    return preferences
