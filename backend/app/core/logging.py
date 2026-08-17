"""Structured logging setup for the application.

CLAUDE.md requires structured logging and forbids logging sensitive data.
This module configures a single, consistent logging format used across
the whole backend.
"""

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure root logging handlers and formatting.

    Should be called once, on application startup.
    """
    settings = get_settings()

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt=("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"),
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    # Avoid duplicate handlers if configure_logging() is called more than once
    # (e.g. during tests that re-import the app).
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
