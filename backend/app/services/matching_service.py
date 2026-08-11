"""Business logic for job matching.

Combines the user's preferences and latest resume into a profile
(app/matching/scoring.build_profile), scores every stored job against
it (app/matching/scoring.rank_jobs), and returns the top N.
"""

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import PreferencesNotFoundError
from app.matching import scoring
from app.matching.scoring import JobMatchResult
from app.repositories import job_repository, preferences_repository, resume_repository


def get_top_matches(db: Session, settings: Settings) -> list[JobMatchResult]:
    """Return the top-N ranked jobs for the current (single V1) user.

    Raises:
        PreferencesNotFoundError: if the user hasn't set preferences yet -
            there's no meaningful profile to match against without them.
    """
    user_id = settings.default_user_id

    preferences = preferences_repository.get_by_user_id(db, user_id)
    if preferences is None:
        raise PreferencesNotFoundError(f"No preferences set for user {user_id}")

    resume = resume_repository.get_latest_for_user(db, user_id)
    profile = scoring.build_profile(preferences, resume)

    candidate_jobs = job_repository.list_jobs(db, limit=settings.match_candidate_pool_size)
    ranked = scoring.rank_jobs(profile, candidate_jobs, settings)

    return ranked[: settings.match_top_n]
