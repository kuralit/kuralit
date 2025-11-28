"""Standalone logging utilities for KuralIt."""

import logging
from typing import Any, Optional

# Create a simple logger
logger = logging.getLogger("kuralit")
logger.setLevel(logging.INFO)

# Create console handler if not exists
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_debug(message: str, center: bool = False, symbol: str = "-", log_level: int = 1) -> None:
    """Log a debug message."""
    if center:
        logger.debug(f"{symbol * 20} {message} {symbol * 20}")
    else:
        logger.debug(message)


def log_info(message: str) -> None:
    """Log an info message."""
    logger.info(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    logger.warning(message)


def log_error(message: str) -> None:
    """Log an error message."""
    logger.error(message)


def log_exception(message: str, exc: Exception) -> None:
    """Log an exception."""
    logger.exception(f"{message}: {exc}")

