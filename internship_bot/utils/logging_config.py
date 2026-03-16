"""Centralized logging setup."""

import logging


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging for the app."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
