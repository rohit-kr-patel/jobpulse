"""Tests for the POST /resume/upload endpoint."""

from pathlib import Path

import fitz

from app.core.config import Settings, get_settings
from app.main import app

_MINIMAL_PDF_BYTES = b"%PDF-1.4\n%mock pdf content for testing\n%%EOF"


def _build_pdf_bytes(text: str) -> bytes:
    """Generate a real, parseable single-page PDF containing the given text."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def _override_settings_with_upload_dir(tmp_path: Path):
    def _override() -> Settings:
        return Settings(resume_upload_dir=str(tmp_path / "resumes"))

    return _override


def test_upload_resume_succeeds_for_valid_pdf(client, tmp_path):
    app.dependency_overrides[get_settings] = _override_settings_with_upload_dir(tmp_path)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", _MINIMAL_PDF_BYTES, "application/pdf")},
        )
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "resume.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["size_bytes"] == len(_MINIMAL_PDF_BYTES)
    assert body["user_id"] == 1

    stored_files = list((tmp_path / "resumes").glob("*.pdf"))
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == _MINIMAL_PDF_BYTES


def test_upload_resume_gracefully_handles_unparseable_pdf_content(client, tmp_path):
    """The minimal fake PDF above has valid magic bytes but no real PDF structure.

    Parsing should fail internally and downgrade to empty/null parsed
    fields rather than failing the upload.
    """
    app.dependency_overrides[get_settings] = _override_settings_with_upload_dir(tmp_path)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", _MINIMAL_PDF_BYTES, "application/pdf")},
        )
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 201
    body = response.json()
    assert body["parsed_skills"] == []
    assert body["parsed_education"] == []
    assert body["parsed_experience_years"] is None
    assert body["parsed_at"] is not None


def test_upload_resume_persists_and_returns_parsed_fields_for_real_pdf(client, tmp_path):
    app.dependency_overrides[get_settings] = _override_settings_with_upload_dir(tmp_path)
    resume_text = (
        "Jane Doe\n"
        "Backend engineer with 3 years of experience.\n"
        "Skills: Python, Docker, PostgreSQL\n"
        "Education: B.Tech in Computer Science\n"
    )
    pdf_bytes = _build_pdf_bytes(resume_text)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        )
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 201
    body = response.json()
    assert set(body["parsed_skills"]) == {"Python", "Docker", "PostgreSQL"}
    assert body["parsed_education"] == ["B.Tech"]
    assert body["parsed_experience_years"] == 3.0
    assert body["parsed_at"] is not None


def test_upload_resume_rejects_non_pdf_extension(client, tmp_path):
    app.dependency_overrides[get_settings] = _override_settings_with_upload_dir(tmp_path)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.docx", b"not a pdf", "application/pdf")},
        )
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 400


def test_upload_resume_rejects_wrong_content_type(client, tmp_path):
    app.dependency_overrides[get_settings] = _override_settings_with_upload_dir(tmp_path)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", _MINIMAL_PDF_BYTES, "text/plain")},
        )
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 400


def test_upload_resume_rejects_empty_file(client, tmp_path):
    app.dependency_overrides[get_settings] = _override_settings_with_upload_dir(tmp_path)
    try:
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", b"", "application/pdf")},
        )
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 400


def test_upload_resume_rejects_file_without_pdf_magic_bytes(client, tmp_path):
    app.dependency_overrides[get_settings] = _override_settings_with_upload_dir(tmp_path)
    try:
        response = client.post(
            "/resume/upload",
            files={
                "file": (
                    "resume.pdf",
                    b"just some text, not a real pdf",
                    "application/pdf",
                )
            },
        )
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 400


def test_upload_resume_rejects_oversized_file(client, tmp_path):
    def _override() -> Settings:
        return Settings(resume_upload_dir=str(tmp_path / "resumes"), resume_max_size_mb=1)

    app.dependency_overrides[get_settings] = _override
    try:
        oversized_content = _MINIMAL_PDF_BYTES + b"0" * (2 * 1024 * 1024)
        response = client.post(
            "/resume/upload",
            files={"file": ("resume.pdf", oversized_content, "application/pdf")},
        )
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 400
