"""Centralized logging configuration for the flights-search service."""

import logging
import sys

# Log format: timestamp · level · logger name · message
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

# Root logger name for the entire service.
_ROOT_LOGGER = "flights_search"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the service root logger. Safe to call multiple times."""
    root = logging.getLogger(_ROOT_LOGGER)

    # Avoid adding duplicate handlers on repeated calls.
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root.setLevel(level)
    root.addHandler(handler)

    # Suppress noisy third-party loggers.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the service root. Call with ``__name__``."""
    # Strip the "src." prefix so logger names read as "flights_search.<module>".
    relative = name.removeprefix("src.")
    return logging.getLogger(f"{_ROOT_LOGGER}.{relative}")
