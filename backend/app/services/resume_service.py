"""Business logic for resume uploads.

Validates, stores, and records metadata for the uploaded PDF, then
runs it through the rule-based parser (app/parsing/resume_parser.py)
to extract skills, education, and experience. Parsing never blocks a
successful upload - if it fails or finds nothing, the parsed fields
are simply left empty/null.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import InvalidResumeFileError
from app.models.resume import Resume
from app.parsing.resume_parser import ParsedResumeData, parse_resume
from app.repositories import resume_repository

logger = logging.getLogger(__name__)

_PDF_CONTENT_TYPE = "application/pdf"
_PDF_MAGIC_BYTES = b"%PDF-"


def _validate_file(filename: str | None, content_type: str | None, contents: bytes, settings: Settings) -> None:
    """Validate the uploaded file is a non-empty, correctly-sized PDF.

    Raises:
        InvalidResumeFileError: if any validation rule fails.
    """
    if not filename or not filename.lower().endswith(".pdf"):
        raise InvalidResumeFileError("Resume must be a .pdf file")

    if content_type != _PDF_CONTENT_TYPE:
        raise InvalidResumeFileError(f"Unsupported content type: {content_type}")

    if not contents:
        raise InvalidResumeFileError("Uploaded file is empty")

    if not contents.startswith(_PDF_MAGIC_BYTES):
        raise InvalidResumeFileError("File does not appear to be a valid PDF")

    max_bytes = settings.resume_max_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise InvalidResumeFileError(
            f"File exceeds the {settings.resume_max_size_mb}MB size limit"
        )


def _safe_parse(contents: bytes) -> ParsedResumeData:
    """Run the resume parser, downgrading any failure to "nothing extracted".

    A resume that passed our PDF validation but still can't be parsed
    (e.g. a corrupt or unusually-encoded PDF) should not block the
    upload - it should just end up with empty parsed fields.
    """
    try:
        return parse_resume(contents)
    except Exception:  # noqa: BLE001 - parsing quality issues must never fail the upload
        logger.exception("Resume parsing failed; continuing with empty parsed fields")
        return ParsedResumeData()


async def upload_resume(
    db: Session, *, user_id: int, file: UploadFile, settings: Settings
) -> Resume:
    """Validate, store, parse, and record a resume upload for the given user.

    Raises:
        InvalidResumeFileError: if the file fails validation.
    """
    contents = await file.read()
    _validate_file(file.filename, file.content_type, contents, settings)

    upload_dir = Path(settings.resume_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}.pdf"
    stored_path = upload_dir / stored_filename
    stored_path.write_bytes(contents)

    logger.info(
        "Resume uploaded for user_id=%s size_bytes=%d stored_path=%s",
        user_id,
        len(contents),
        stored_path,
    )

    parsed = _safe_parse(contents)
    logger.info(
        "Resume parsed for user_id=%s skills=%d education=%d experience_years=%s",
        user_id,
        len(parsed.skills),
        len(parsed.education),
        parsed.experience_years,
    )

    return resume_repository.create(
        db,
        user_id=user_id,
        original_filename=file.filename,
        stored_path=str(stored_path),
        content_type=file.content_type,
        size_bytes=len(contents),
        parsed_skills=parsed.skills,
        parsed_education=parsed.education,
        parsed_experience_years=parsed.experience_years,
        parsed_at=datetime.now(timezone.utc),
    )
