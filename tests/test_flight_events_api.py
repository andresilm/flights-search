"""Tests for the HTTP flight events adapter."""

from datetime import datetime, timezone
from typing import Callable

import httpx
import pytest

from src.adapters.flight_events_api import HttpFlightEventRepository
from src.domain.model import FlightEvent


def make_mock_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.AsyncClient:
    """Creates an httpx.AsyncClient that routes requests to a mock handler."""
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


@pytest.mark.anyio
async def test_get_all_parses_response() -> None:
    """The repository correctly parses a valid JSON response into FlightEvent objects."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://api.test/flight-events"
        return httpx.Response(
            200,
            json=[
                {
                    "flight_number": "IB1234",
                    "departure_city": "MAD",
                    "arrival_city": "BUE",
                    "departure_datetime": "2021-12-31T23:59:59Z",
                    "arrival_datetime": "2022-01-01T00:00:00Z",
                }
            ],
        )

    client = make_mock_client(handler)
    repo = HttpFlightEventRepository(client, "http://api.test")

    events = await repo.get_all()

    assert len(events) == 1
    event = events[0]
    assert isinstance(event, FlightEvent)
    assert event.flight_number == "IB1234"
    assert event.departure_city == "MAD"
    assert event.arrival_city == "BUE"
    assert event.departure_datetime == datetime(
        2021, 12, 31, 23, 59, 59, tzinfo=timezone.utc
    )
    assert event.arrival_datetime == datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.mark.anyio
async def test_get_all_empty_response() -> None:
    """The repository returns an empty list when the API returns an empty array."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = make_mock_client(handler)
    repo = HttpFlightEventRepository(client, "http://api.test")

    events = await repo.get_all()
    assert events == []


@pytest.mark.anyio
async def test_get_all_api_error() -> None:
    """The repository propagates httpx HTTP errors."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = make_mock_client(handler)
    repo = HttpFlightEventRepository(client, "http://api.test")

    with pytest.raises(httpx.HTTPStatusError):
        await repo.get_all()
