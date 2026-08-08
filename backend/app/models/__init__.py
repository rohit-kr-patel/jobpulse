"""SQLAlchemy ORM models.

All models are imported here so `Base.metadata` is fully populated
when Alembic (or anything else) imports this package.
"""

from app.models.job import Job
from app.models.preferences import Preferences, WorkMode
from app.models.resume import Resume
from app.models.user import User

__all__ = ["User", "Resume", "Preferences", "WorkMode", "Job"]
