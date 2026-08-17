"""Shared helpers for job fetchers - HTML cleanup and defensive parsing.

External APIs are outside our control and occasionally return
malformed or unexpected values, so every parser here fails soft
(returns None / a safe default) rather than raising.
"""

from datetime import UTC, datetime

from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    """Strip HTML tags, returning clean plain text with collapsed whitespace.

    Job descriptions from Greenhouse/Lever/Remotive/Arbeitnow are HTML;
    storing plain text keeps the database readable and ready for the
    Phase 7 matching engine (TF-IDF works on plain text).
    """
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text(separator=" ")
    return " ".join(text.split())


def parse_csv_list(raw_value: str) -> list[str]:
    """Split a comma-separated settings value into a clean list of tokens."""
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def looks_remote(location: str | None) -> bool:
    """Heuristic: does the location text itself indicate a remote role?"""
    if not location:
        return False
    return "remote" in location.lower()


def display_company_name(slug: str) -> str:
    """Turn a company slug (e.g. 'acme-corp') into a display name ('Acme Corp').

    Best-effort only - the real display name isn't always available
    from per-company board APIs without an extra request.
    """
    return slug.replace("-", " ").replace("_", " ").title()


def parse_iso_datetime(raw_value: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string, defaulting to UTC if no offset is given."""
    if not raw_value:
        return None
    try:
        normalized = raw_value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def parse_epoch_seconds(raw_value: int | float | None) -> datetime | None:
    """Parse a Unix timestamp in seconds into a UTC datetime."""
    if raw_value is None:
        return None
    try:
        return datetime.fromtimestamp(raw_value, tz=UTC)
    except (ValueError, OSError, OverflowError):
        return None


def parse_epoch_millis(raw_value: int | float | None) -> datetime | None:
    """Parse a Unix timestamp in milliseconds into a UTC datetime."""
    if raw_value is None:
        return None
    return parse_epoch_seconds(raw_value / 1000)
