"""Tests for the FastAPI application."""

from collections.abc import Generator
from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from src.app.main import app
from src.app.routes import get_journey_service
from src.domain.model import FlightEvent, Journey
from src.services.journey_search import JourneySearchService


class DummyJourneyService(JourneySearchService):
    """A dummy service that returns a fixed response without hitting the database."""

    def __init__(self) -> None:
        pass

    async def search(
        self, search_date: date, origin: str, destination: str
    ) -> list[Journey]:
        if origin == "BUE" and destination == "MAD":
            return [
                Journey(
                    flights=[
                        FlightEvent(
                            flight_number="UX1",
                            departure_city="BUE",
                            arrival_city="MAD",
                            departure_datetime=datetime(
                                2024, 9, 12, 10, 0, tzinfo=timezone.utc
                            ),
                            arrival_datetime=datetime(
                                2024, 9, 12, 22, 0, tzinfo=timezone.utc
                            ),
                        )
                    ]
                )
            ]
        return []


def _client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_journey_service] = DummyJourneyService
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


client = _client


def test_health() -> None:
    """The /health endpoint returns 200 OK."""
    with TestClient(app) as c:
        response = c.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_journeys_success() -> None:
    """The endpoint returns a 200 OK and correctly formats the Journey models."""
    for c in _client():
        response = c.get("/journeys/search?date=2024-09-12&from=BUE&to=MAD")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        journey = data[0]
        assert journey["connections"] == 1
        assert len(journey["path"]) == 1

        flight = journey["path"][0]
        assert flight["flight_number"] == "UX1"
        assert flight["from"] == "BUE"
        assert flight["to"] == "MAD"
        assert flight["departure_time"] == "2024-09-12 10:00"
        assert flight["arrival_time"] == "2024-09-12 22:00"


def test_search_journeys_not_found() -> None:
    """The endpoint returns an empty array when no journeys exist."""
    for c in _client():
        response = c.get("/journeys/search?date=2024-09-12&from=MAD&to=BUE")
        assert response.status_code == 200
        assert response.json() == []


def test_search_journeys_missing_params() -> None:
    """The endpoint returns 422 if required query params are missing."""
    for c in _client():
        response = c.get("/journeys/search?date=2024-09-12")
        assert response.status_code == 422


def test_search_journeys_invalid_city_code() -> None:
    """The endpoint returns 422 for city codes that aren't 3 uppercase letters."""
    for c in _client():
        # Lowercase
        response = c.get("/journeys/search?date=2024-09-12&from=bue&to=MAD")
        assert response.status_code == 422

        # Too short
        response = c.get("/journeys/search?date=2024-09-12&from=BU&to=MAD")
        assert response.status_code == 422

        # Too long
        response = c.get("/journeys/search?date=2024-09-12&from=BUE&to=MADR")
        assert response.status_code == 422
