"""Startup data seeding.

V1 has no authentication: a single user row is guaranteed to exist so
every other table can hang off a real `user_id`.
"""

import logging

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User

logger = logging.getLogger(__name__)


def seed_default_user(db: Session, settings: Settings) -> None:
    """Ensure the single hardcoded V1 user exists.

    Safe to call on every startup - a no-op if the user already exists.
    """
    existing = db.get(User, settings.default_user_id)
    if existing is not None:
        return

    default_user = User(
        id=settings.default_user_id,
        full_name=settings.default_user_full_name,
        email=settings.default_user_email,
    )
    db.add(default_user)
    db.commit()
    logger.info("Seeded default user with id=%s", settings.default_user_id)
