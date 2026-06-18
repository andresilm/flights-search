"""Application settings and strategy factory."""

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.domain.two_leg_indexed_search import TwoLegIndexedJourneySearch
from src.ports import JourneySearchStrategy


class Settings(BaseSettings):
    """Application settings loaded from environment variables or ``.env``."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    FLIGHT_EVENTS_API_URL: str
    JOURNEY_SEARCH_STRATEGY: str = "two_leg_indexed"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    @property
    def log_level_int(self) -> int:
        """Convert LOG_LEVEL string to its ``logging`` integer constant."""
        level = logging.getLevelName(self.LOG_LEVEL.upper())
        if not isinstance(level, int):
            raise ValueError(f"Invalid LOG_LEVEL: {self.LOG_LEVEL!r}")
        return level


# Registry mapping strategy names to their concrete classes.
_STRATEGY_REGISTRY: dict[str, type[JourneySearchStrategy]] = {
    "two_leg_indexed": TwoLegIndexedJourneySearch,
}


def get_search_strategy(settings: Settings) -> JourneySearchStrategy:
    """Return the search strategy configured in settings."""
    strategy_cls = _STRATEGY_REGISTRY.get(settings.JOURNEY_SEARCH_STRATEGY)
    if strategy_cls is None:
        registered = ", ".join(f'"{k}"' for k in _STRATEGY_REGISTRY)
        raise ValueError(
            f"Unknown search strategy: {settings.JOURNEY_SEARCH_STRATEGY!r}. "
            f"Registered strategies: {registered}."
        )
    return strategy_cls()
