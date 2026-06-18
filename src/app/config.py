"""Application settings and strategy factory.

Reads configuration from environment variables and the ``.env`` file.
Provides a factory function to instantiate the active search strategy.
"""

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.domain.two_leg_indexed_search import TwoLegIndexedJourneySearch
from src.ports import JourneySearchStrategy


class Settings(BaseSettings):
    """Application-level configuration loaded from environment variables.

    All fields can be overridden via environment variables or a ``.env`` file
    in the project root.

    Attributes:
        FLIGHT_EVENTS_API_URL: Base URL of the external flight events API.
            The adapter calls ``GET <FLIGHT_EVENTS_API_URL>/flight-events``.
        JOURNEY_SEARCH_STRATEGY: Name of the search algorithm to use.
            Supported values: ``"indexed"``.
        LOG_LEVEL: Minimum log level for the service logger.
            Accepts standard Python logging level names (e.g. ``"DEBUG"``, ``"INFO"``).
        PORT: TCP port that Uvicorn will listen on.

    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    FLIGHT_EVENTS_API_URL: str
    JOURNEY_SEARCH_STRATEGY: str = "two_leg_indexed"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    @property
    def log_level_int(self) -> int:
        """Converts the ``LOG_LEVEL`` string to a ``logging`` integer constant.

        Returns:
            The integer log level (e.g. ``logging.DEBUG``, ``logging.INFO``).

        Raises:
            ValueError: If the ``LOG_LEVEL`` string is not a valid logging level.

        """
        level = logging.getLevelName(self.LOG_LEVEL.upper())
        if not isinstance(level, int):
            raise ValueError(f"Invalid LOG_LEVEL: {self.LOG_LEVEL!r}")
        return level


# Registry mapping strategy names to their concrete classes.
_STRATEGY_REGISTRY: dict[str, type[JourneySearchStrategy]] = {
    "two_leg_indexed": TwoLegIndexedJourneySearch,
}


def get_search_strategy(settings: Settings) -> JourneySearchStrategy:
    """Instantiates and returns the active journey search strategy.

    The strategy is selected based on ``settings.JOURNEY_SEARCH_STRATEGY``.
    To add a new algorithm: implement ``JourneySearchStrategy``, register it
    in ``_STRATEGY_REGISTRY``, and set the corresponding name in ``.env``.

    Args:
        settings: The application settings instance.

    Returns:
        A concrete ``JourneySearchStrategy`` instance.

    Raises:
        ValueError: If ``settings.JOURNEY_SEARCH_STRATEGY`` does not match
            any registered strategy name.

    """
    strategy_cls = _STRATEGY_REGISTRY.get(settings.JOURNEY_SEARCH_STRATEGY)
    if strategy_cls is None:
        registered = ", ".join(f'"{k}"' for k in _STRATEGY_REGISTRY)
        raise ValueError(
            f"Unknown search strategy: {settings.JOURNEY_SEARCH_STRATEGY!r}. "
            f"Registered strategies: {registered}."
        )
    return strategy_cls()
