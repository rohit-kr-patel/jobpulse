"""Unit tests for app.parsing.resume_parser.

Text-level extraction is tested directly against strings (fast, no PDF
needed). PDF text extraction itself is covered separately with a real
PyMuPDF-generated PDF.
"""

import fitz

from app.parsing.resume_parser import (
    extract_education,
    extract_experience_years,
    extract_skills,
    extract_text,
    parse_resume,
)


def _build_pdf_bytes(text: str) -> bytes:
    """Generate a real, parseable single-page PDF containing the given text."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def test_extract_skills_finds_known_skills():
    text = "Experienced with Python, FastAPI, PostgreSQL, Docker, and React.js."
    assert set(extract_skills(text)) == {"Python", "FastAPI", "PostgreSQL", "Docker", "React.js"}


def test_extract_skills_does_not_match_substrings_of_longer_skills():
    text = "Built services with PostgreSQL and C++."
    skills = extract_skills(text)
    assert "SQL" not in skills
    assert "C" not in skills
    assert "PostgreSQL" in skills
    assert "C++" in skills


def test_extract_skills_ignores_common_words_that_look_like_language_names():
    text = "I want to go further and be the best version of me."
    assert extract_skills(text) == []


def test_extract_skills_matches_capitalized_short_language_names():
    text = "Comfortable with Go, R, and C for systems work."
    skills = extract_skills(text)
    assert set(skills) == {"Go", "R", "C"}


def test_extract_education_finds_known_degrees():
    text = "B.Tech in Computer Science, followed by an MBA."
    assert extract_education(text) == ["B.Tech", "MBA"]


def test_extract_education_ignores_pronoun_collisions():
    text = "Let me be clear about my goals."
    assert extract_education(text) == []


def test_extract_education_returns_empty_list_when_nothing_found():
    text = "This resume has no degree keywords in it at all."
    assert extract_education(text) == []


def test_extract_experience_years_from_explicit_statement():
    text = "Backend engineer with 4 years of experience in distributed systems."
    assert extract_experience_years(text) == 4.0


def test_extract_experience_years_takes_the_largest_explicit_statement():
    text = "Worked as an intern (1 year of experience) then full-time (5+ years of experience)."
    assert extract_experience_years(text) == 5.0


def test_extract_experience_years_falls_back_to_year_span():
    text = "Employed at Acme Corp from 2018 to 2022 as a software engineer."
    assert extract_experience_years(text) == 4.0


def test_extract_experience_years_returns_none_when_no_signal_present():
    text = "A resume with no dates or explicit experience statements."
    assert extract_experience_years(text) is None


def test_extract_text_reads_a_real_pdf():
    pdf_bytes = _build_pdf_bytes("Hello from a real PDF.")
    assert "Hello from a real PDF." in extract_text(pdf_bytes)


def test_parse_resume_runs_the_full_pipeline_against_a_real_pdf():
    text = (
        "Jane Doe\n"
        "Backend engineer with 3 years of experience.\n"
        "Skills: Python, Docker, PostgreSQL\n"
        "Education: B.Tech in Computer Science\n"
    )
    pdf_bytes = _build_pdf_bytes(text)

    result = parse_resume(pdf_bytes)

    assert set(result.skills) == {"Python", "Docker", "PostgreSQL"}
    assert result.education == ["B.Tech"]
    assert result.experience_years == 3.0


def test_parse_resume_handles_a_pdf_with_no_extractable_text():
    document = fitz.open()
    document.new_page()  # blank page, no text
    pdf_bytes = document.tobytes()
    document.close()

    result = parse_resume(pdf_bytes)

    assert result.skills == []
    assert result.education == []
    assert result.experience_years is None
