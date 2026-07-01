"""Structured logging with rotating file and console handlers."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return the root application logger.

    * Console handler writes to ``stdout``.
    * File handler writes to ``logs/server.log`` with 10 MB rotation and 5 backups.
    """
    settings = get_settings()

    logger = logging.getLogger("cloudsync")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Prevent duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "server.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "cloudsync") -> logging.Logger:
    """Retrieve a child logger under the ``cloudsync`` namespace."""
    return logging.getLogger(name)
