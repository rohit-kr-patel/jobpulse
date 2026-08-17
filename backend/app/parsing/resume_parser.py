"""Rule-based resume parsing.

Pipeline: PDF bytes -> text extraction (PyMuPDF) -> skills / education /
experience extraction (keyword and regex matching, no LLMs). See
docs/08_RESUME_PARSER.md.

Extraction here is deliberately simple and heuristic - resumes vary
too much in layout for perfect rule-based parsing, and the project
scope explicitly excludes LLMs for this step. Each function is a
best-effort signal, not a guarantee.
"""

import logging
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

from app.parsing.education_data import KNOWN_DEGREES
from app.parsing.skills_data import KNOWN_SKILLS
from app.text_extraction import contains_keyword, extract_years_statement

logger = logging.getLogger(__name__)

# Case-sensitive-only keywords: short language names that collide with
# common English words if matched case-insensitively (e.g. "go", "r").
_CASE_SENSITIVE_SKILL_KEYWORDS = {"Go", "R", "C"}

# Case-sensitive-only keywords: short abbreviations that collide with common
# lowercase English words (e.g. "me", "be") if matched case-insensitively.
_CASE_SENSITIVE_DEGREE_KEYWORDS = {"BE", "ME"}

_YEAR_PATTERN = re.compile(r"(19|20)\d{2}")


@dataclass
class ParsedResumeData:
    """Structured data extracted from a resume PDF."""

    skills: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    experience_years: float | None = None


def extract_text(pdf_bytes: bytes) -> str:
    """Extract all text content from a PDF's pages, in order."""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        return "\n".join(page.get_text() for page in document)


def extract_skills(text: str) -> list[str]:
    """Return the known skills that appear in the resume text.

    If one matched skill is itself a substring of another matched skill
    (e.g. "C" within "C++", "React" within "React.js"), only the
    longer, more specific skill is kept.
    """
    matched = [
        skill
        for skill in KNOWN_SKILLS
        if contains_keyword(text, skill, case_sensitive=skill in _CASE_SENSITIVE_SKILL_KEYWORDS)
    ]

    def is_shadowed(skill: str) -> bool:
        return any(other != skill and skill.lower() in other.lower() for other in matched)

    return [skill for skill in matched if not is_shadowed(skill)]


def extract_education(text: str) -> list[str]:
    """Return the known degree keywords that appear in the resume text."""
    found: list[str] = []
    for degree in KNOWN_DEGREES:
        case_sensitive = degree in _CASE_SENSITIVE_DEGREE_KEYWORDS
        if contains_keyword(text, degree, case_sensitive=case_sensitive):
            found.append(degree)
    return found


def extract_experience_years(text: str) -> float | None:
    """Estimate years of professional experience.

    Tries an explicit statement first (e.g. "3+ years of experience"),
    taking the largest such figure if several appear. Falls back to
    the span between the earliest and latest 4-digit year mentioned
    in the document (e.g. employment dates) - a rough approximation,
    only used when no explicit statement is found.
    """
    statement_result = extract_years_statement(text)
    if statement_result is not None:
        return statement_result

    years_found = [int(m.group()) for m in _YEAR_PATTERN.finditer(text)]
    if len(years_found) >= 2:
        span = max(years_found) - min(years_found)
        return float(span) if span > 0 else None

    return None


def parse_resume(pdf_bytes: bytes) -> ParsedResumeData:
    """Run the full extraction pipeline against a resume PDF's bytes.

    Never raises for parsing-quality reasons (e.g. no skills found) -
    only for a genuinely unreadable/corrupt PDF, which callers should
    catch and treat as "parsing unavailable" rather than an upload
    failure.
    """
    text = extract_text(pdf_bytes)

    if not text.strip():
        logger.warning("Resume PDF produced no extractable text")
        return ParsedResumeData()

    return ParsedResumeData(
        skills=extract_skills(text),
        education=extract_education(text),
        experience_years=extract_experience_years(text),
    )
