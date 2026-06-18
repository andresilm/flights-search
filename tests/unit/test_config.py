"""Tests for application settings and the search strategy factory."""

import pytest

from src.app.config import Settings, get_search_strategy
from src.domain.two_leg_indexed_search import TwoLegIndexedJourneySearch


def test_default_settings() -> None:
    """Settings defaults are correct when only the required field is provided.

    LOG_LEVEL and PORT are passed explicitly to prevent the ``.env`` file
    from overriding the class-level defaults during testing.
    """
    settings = Settings(
        FLIGHT_EVENTS_API_URL="http://test.example.com",
        LOG_LEVEL="INFO",
        PORT=8000,
    )
    assert settings.JOURNEY_SEARCH_STRATEGY == "two_leg_indexed"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.PORT == 8000


def test_log_level_int_valid() -> None:
    """log_level_int converts a valid LOG_LEVEL string to its integer constant."""
    import logging

    settings = Settings(
        FLIGHT_EVENTS_API_URL="http://test.example.com", LOG_LEVEL="DEBUG"
    )
    assert settings.log_level_int == logging.DEBUG


def test_log_level_int_invalid() -> None:
    """log_level_int raises ValueError for an unrecognized level string."""
    settings = Settings(
        FLIGHT_EVENTS_API_URL="http://test.example.com", LOG_LEVEL="NOPE"
    )
    with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
        _ = settings.log_level_int


def test_get_search_strategy_indexed() -> None:
    """Factory returns an TwoLegIndexedJourneySearch instance for strategy 'two_leg_indexed'."""
    settings = Settings(
        FLIGHT_EVENTS_API_URL="http://test.example.com",
        JOURNEY_SEARCH_STRATEGY="two_leg_indexed",
    )
    strategy = get_search_strategy(settings)
    assert isinstance(strategy, TwoLegIndexedJourneySearch)


def test_get_search_strategy_unknown() -> None:
    """Factory raises ValueError for an unregistered strategy name."""
    settings = Settings(
        FLIGHT_EVENTS_API_URL="http://test.example.com",
        JOURNEY_SEARCH_STRATEGY="unknown_algo",
    )
    with pytest.raises(ValueError, match="Unknown search strategy"):
        get_search_strategy(settings)
