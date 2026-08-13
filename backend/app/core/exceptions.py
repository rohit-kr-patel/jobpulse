"""Domain-level exceptions.

Services raise these; routes catch them and translate to the
appropriate HTTP status code. This keeps HTTP concerns out of the
service layer.
"""


class PreferencesNotFoundError(Exception):
    """Raised when preferences are requested but none exist yet."""


class InvalidResumeFileError(Exception):
    """Raised when an uploaded file fails resume validation rules."""


class JobNotFoundError(Exception):
    """Raised when a requested job id does not exist."""


class NotificationNotFoundError(Exception):
    """Raised when a requested notification id does not exist (for this user)."""
