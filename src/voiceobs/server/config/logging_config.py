"""Logging configuration for voiceobs server."""

import logging
import os


def configure_logging() -> None:
    """Configure logging for voiceobs modules."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure root logger format
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Ensure voiceobs modules log at the configured level
    voiceobs_logger = logging.getLogger("voiceobs")
    voiceobs_logger.setLevel(getattr(logging, log_level, logging.INFO))
