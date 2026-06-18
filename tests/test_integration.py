"""Integration tests for the complete application flow."""

from collections.abc import Callable, Generator
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src.app.main import app

# A predefined set of flight events that the mock external API will return.
# We include cases for direct flights, valid connections, and invalid connections.
MOCK_API_DATA = [
    # Flight 1: BUE -> MAD (12h duration) - valid for direct and as 1st leg
    {
        "flight_number": "XX1234",
        "departure_city": "BUE",
        "arrival_city": "MAD",
        "departure_datetime": "2024-09-12T12:00:00Z",
        "arrival_datetime": "2024-09-13T00:00:00Z",
    },
    # Flight 2: MAD -> PMI (1h duration, 2h layover) - Valid connection for Flight 1
    {
        "flight_number": "XX2345",
        "departure_city": "MAD",
        "arrival_city": "PMI",
        "departure_datetime": "2024-09-13T02:00:00Z",
        "arrival_datetime": "2024-09-13T03:00:00Z",
    },
    # Flight 3: MAD -> BCN (1h duration, 5h layover) - Invalid connection (layover > 4h)
    {
        "flight_number": "XX3456",
        "departure_city": "MAD",
        "arrival_city": "BCN",
        "departure_datetime": "2024-09-13T05:00:00Z",
        "arrival_datetime": "2024-09-13T06:00:00Z",
    },
    # Flight 4: BUE -> JFK (10h duration)
    {
        "flight_number": "XX4567",
        "departure_city": "BUE",
        "arrival_city": "JFK",
        "departure_datetime": "2024-09-12T08:00:00Z",
        "arrival_datetime": "2024-09-12T18:00:00Z",
    },
    # Flight 5: JFK -> LHR (10h duration, 3h layover) - Total duration = 10 + 3 + 10 = 23h. Valid.
    {
        "flight_number": "XX5678",
        "departure_city": "JFK",
        "arrival_city": "LHR",
        "departure_datetime": "2024-09-12T21:00:00Z",
        "arrival_datetime": "2024-09-13T07:00:00Z",
    },
    # Flight 6: LHR -> DXB - Just some other flight
    {
        "flight_number": "XX6789",
        "departure_city": "LHR",
        "arrival_city": "DXB",
        "departure_datetime": "2024-09-13T10:00:00Z",
        "arrival_datetime": "2024-09-13T16:00:00Z",
    },
    # Flight 7: BUE -> MIA (Very long flight, pushes total duration > 24h)
    {
        "flight_number": "XX9991",
        "departure_city": "BUE",
        "arrival_city": "MIA",
        "departure_datetime": "2024-09-12T00:00:00Z",
        "arrival_datetime": "2024-09-12T21:00:00Z",
    },
    # Flight 8: MIA -> ORL (2h layover) - Total duration = 21 + 2 + 2 = 25h. Invalid duration.
    {
        "flight_number": "XX9992",
        "departure_city": "MIA",
        "arrival_city": "ORL",
        "departure_datetime": "2024-09-12T23:00:00Z",
        "arrival_datetime": "2024-09-13T01:00:00Z",
    },
]


OriginalAsyncClient = httpx.AsyncClient

def make_mock_client_factory(
    data: list[dict[str, Any]],
) -> Callable[..., httpx.AsyncClient]:
    """Returns a factory that creates httpx.AsyncClient with a mock transport."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=data)

    def factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = httpx.MockTransport(handler)
        return OriginalAsyncClient(*args, **kwargs)

    return factory


@pytest.fixture
def integration_client() -> Generator[TestClient, None, None]:
    """Yields a TestClient that uses a mocked httpx.AsyncClient for the external API."""
    factory = make_mock_client_factory(MOCK_API_DATA)
    # Patch the AsyncClient specifically inside src.app.main where it is used.
    with patch("src.app.main.httpx.AsyncClient", side_effect=factory):
        # We must instantiate TestClient within the patch so the lifespan picks it up.
        with TestClient(app) as client:
            yield client


@pytest.fixture
def empty_api_client() -> Generator[TestClient, None, None]:
    """Yields a TestClient where the external API returns an empty list."""
    factory = make_mock_client_factory([])
    with patch("src.app.main.httpx.AsyncClient", side_effect=factory):
        with TestClient(app) as client:
            yield client


def test_integration_direct_flight(integration_client: TestClient) -> None:
    """Tests finding a direct flight."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=MAD"
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    journey = data[0]
    assert journey["connections"] == 1
    assert len(journey["path"]) == 1
    assert journey["path"][0]["flight_number"] == "XX1234"


def test_integration_valid_connection(integration_client: TestClient) -> None:
    """Tests finding a valid 2-leg journey (the example from the challenge)."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=PMI"
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    journey = data[0]
    assert journey["connections"] == 2
    assert len(journey["path"]) == 2

    assert journey["path"][0]["flight_number"] == "XX1234"
    assert journey["path"][1]["flight_number"] == "XX2345"
    assert journey["path"][0]["departure_time"] == "2024-09-12 12:00"
    assert journey["path"][1]["arrival_time"] == "2024-09-13 03:00"


def test_integration_invalid_layover(integration_client: TestClient) -> None:
    """Tests that a layover > 4 hours is rejected (BUE -> MAD -> BCN)."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=BCN"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_integration_invalid_total_duration(integration_client: TestClient) -> None:
    """Tests that a journey exceeding 24 hours total duration is rejected."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=ORL"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_integration_wrong_start_date(integration_client: TestClient) -> None:
    """Tests that flights starting on a different date are ignored."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-13&from=BUE&to=MAD"
    )
    assert response.status_code == 200
    data = response.json()
    # Flight XX1234 starts on 2024-09-12, so a search for 09-13 yields nothing.
    assert len(data) == 0


def test_integration_no_solution(integration_client: TestClient) -> None:
    """Tests a search between cities with no possible connection."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=JFK&to=DXB"
    )
    assert response.status_code == 200
    data = response.json()
    # JFK -> LHR starts on 09-12, LHR -> DXB starts on 09-13, but layover is 3h.
    # Wait, JFK -> LHR arrives 09-13 07:00, LHR -> DXB departs 09-13 10:00 (3h layover).
    # That is valid! Let's search for a truly disconnected route: MAD to LHR.
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=MAD&to=LHR"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_integration_empty_api(empty_api_client: TestClient) -> None:
    """Tests the system resilience when the external API returns no events."""
    response = empty_api_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=MAD"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
