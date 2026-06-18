"""Centralized logging configuration for the flights-search service.

Usage::

    from src.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Something happened", extra={"key": "value"})
"""

import logging
import sys

# Log format: timestamp · level · logger name · message
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

# Root logger name for the entire service.
_ROOT_LOGGER = "flights_search"


def configure_logging(level: int = logging.INFO) -> None:
    """Configures the root logger for the service.

    Should be called once at application startup (e.g. in the FastAPI lifespan).
    Subsequent calls are safe but have no effect if the root logger is already
    configured.

    Args:
        level: The minimum log level to emit. Defaults to ``logging.INFO``.
    """
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
    """Returns a child logger scoped under the service root logger.

    Conventionally called with ``__name__`` so log records carry the full
    module path (e.g. ``flights_search.adapters.flight_events_api``).

    Args:
        name: The module name, typically ``__name__``.

    Returns:
        A ``logging.Logger`` instance parented to the service root logger.
    """
    # Strip the "src." prefix so logger names read as "flights_search.<module>".
    relative = name.removeprefix("src.")
    return logging.getLogger(f"{_ROOT_LOGGER}.{relative}")
