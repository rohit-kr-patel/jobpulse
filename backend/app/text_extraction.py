"""Generic text-extraction helpers shared across domains.

Used by both app/parsing/resume_parser.py (resume text) and
app/matching/scoring.py (job description text) - factored out here so
the two don't duplicate the same regex/matching logic.
"""

import re

_EXPERIENCE_STATEMENT_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp\b)",
    re.IGNORECASE,
)


def contains_keyword(text: str, keyword: str, *, case_sensitive: bool = False) -> bool:
    """Whole-token match: `keyword` must not be flanked by alphanumeric chars.

    Works for keywords containing punctuation (e.g. "Node.js", "C++")
    since the boundary check only excludes alphanumeric neighbours.
    """
    pattern = r"(?<![A-Za-z0-9])" + re.escape(keyword) + r"(?![A-Za-z0-9])"
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.search(pattern, text, flags) is not None


def extract_years_statement(text: str) -> float | None:
    """Find explicit "X years of experience" style statements in text.

    Returns the largest such figure if several appear, or None if no
    statement is found.
    """
    matches = _EXPERIENCE_STATEMENT_PATTERN.findall(text)
    if not matches:
        return None
    return max(float(value) for value in matches)
