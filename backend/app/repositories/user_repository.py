"""Data access for the User model."""

from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    """Return the user with the given id, or None if not found."""
    return db.get(User, user_id)
