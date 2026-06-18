"""Tests for the JourneySearchService."""

from datetime import date
from typing import Any

import pytest

from src.domain.model import FlightEvent, Journey
from src.services.journey_search import JourneySearchService


class FakeFlightEventRepository:
    """A fake repository that returns predefined events."""

    def __init__(self, events: list[FlightEvent]):
        self.events = events

    async def get_all(self) -> list[FlightEvent]:
        return self.events


class FakeJourneySearchStrategy:
    """A fake strategy that returns predefined journeys and tracks arguments."""

    def __init__(self, journeys: list[Journey]):
        self.journeys = journeys
        self.last_call_args: dict[str, Any] | None = None

    def search(
        self,
        events: list[FlightEvent],
        origin: str,
        destination: str,
        search_date: date,
    ) -> list[Journey]:
        self.last_call_args = {
            "events": events,
            "origin": origin,
            "destination": destination,
            "search_date": search_date,
        }
        return self.journeys


@pytest.mark.anyio
async def test_search_delegates_to_strategy() -> None:
    """The service fetches events and delegates the search to the strategy."""
    search_date = date(2024, 9, 12)
    fake_events: list[
        FlightEvent
    ] = []  # Can be empty for the stub, bypasses the check? Wait, if it's empty, it short-circuits.
    # We must provide at least one event so the service doesn't short-circuit.
    from datetime import datetime, timezone

    dummy_event = FlightEvent(
        flight_number="UX1",
        departure_city="BUE",
        arrival_city="MAD",
        departure_datetime=datetime(2024, 9, 12, 10, 0, tzinfo=timezone.utc),
        arrival_datetime=datetime(2024, 9, 12, 22, 0, tzinfo=timezone.utc),
    )
    fake_events = [dummy_event]

    fake_journeys = [Journey(flights=[dummy_event])]

    repo = FakeFlightEventRepository(fake_events)
    strategy = FakeJourneySearchStrategy(fake_journeys)
    service = JourneySearchService(repo, strategy)

    result = await service.search(search_date, "BUE", "MAD")

    # Assert it returns what the strategy returned
    assert result == fake_journeys

    # Assert parameters were correctly passed to the strategy
    assert strategy.last_call_args is not None
    assert strategy.last_call_args["events"] == fake_events
    assert strategy.last_call_args["origin"] == "BUE"
    assert strategy.last_call_args["destination"] == "MAD"
    assert strategy.last_call_args["search_date"] == search_date


@pytest.mark.anyio
async def test_search_with_empty_events() -> None:
    """The service short-circuits and returns an empty list if repository has no events."""
    repo = FakeFlightEventRepository([])
    strategy = FakeJourneySearchStrategy([Journey(flights=[])])
    service = JourneySearchService(repo, strategy)

    result = await service.search(date(2024, 9, 12), "BUE", "MAD")

    # The service explicitly returns [] if no events exist
    assert result == []
    # Ensure strategy wasn't called
    assert strategy.last_call_args is None
