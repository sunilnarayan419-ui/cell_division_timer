"""Application logging configuration."""

import logging
import sys
from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return root logger for the application."""
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("cell_division_timer")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
