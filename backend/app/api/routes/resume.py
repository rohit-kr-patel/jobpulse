"""Resume upload endpoint.

Only handles storing the file and its metadata. Parsing the resume's
content is implemented in Phase 3.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import InvalidResumeFileError
from app.db.session import get_db
from app.schemas.resume import ResumeResponse
from app.services import resume_service

router = APIRouter(tags=["resume"])


@router.post(
    "/resume/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ResumeResponse:
    """Upload a resume PDF for the current user.

    Returns 400 if the file is missing, not a PDF, empty, or exceeds
    the configured size limit.
    """
    try:
        resume = await resume_service.upload_resume(
            db, user_id=settings.default_user_id, file=file, settings=settings
        )
    except InvalidResumeFileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ResumeResponse.model_validate(resume)
