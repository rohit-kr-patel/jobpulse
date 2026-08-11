"""Matches endpoint.

Not in the original API spec's endpoint list - added because ranking
jobs against the user's profile is the whole point of Phase 7
(TF-IDF + weighted scoring, see app/matching/scoring.py) and needs
somewhere to surface the result. A top-level `/matches` path (rather
than nesting under `/jobs`) avoids any ambiguity with `GET /jobs/{id}`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import PreferencesNotFoundError
from app.db.session import get_db
from app.schemas.match import JobMatchResponse
from app.services import matching_service

router = APIRouter(tags=["matches"])


@router.get("/matches", response_model=list[JobMatchResponse])
def get_matches(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[JobMatchResponse]:
    """Return the top-N jobs ranked against the user's preferences + resume.

    404s if preferences haven't been set yet - there's no profile to
    match against. Missing a resume is fine; matching still runs on
    preferences alone with reduced signal.
    """
    try:
        matches = matching_service.get_top_matches(db, settings)
    except PreferencesNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [JobMatchResponse.model_validate(match) for match in matches]
