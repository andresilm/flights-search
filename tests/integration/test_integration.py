"""Integration tests for the complete application flow."""

import json
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src.app.main import app

EVENTS_FILE = Path(__file__).parent / "events.json"
with EVENTS_FILE.open() as f:
    MOCK_API_DATA = json.load(f)


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
    with patch("src.app.main.httpx.AsyncClient", side_effect=factory):
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
    """Tests finding direct flights (BUE -> MAD has 2 options)."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=MAD"
    )
    assert response.status_code == 200
    data = response.json()

    # BUE -> MAD has multiple valid routes:
    # 1. XX1000 direct
    # 2. XX1001 direct
    # 3. XX1007 -> XX1008 (BUE -> GRU -> MAD)
    # 4. XX1011 -> XX1012 (BUE -> JFK -> MAD) exact 24h
    assert len(data) == 4
    direct_flights = [j for j in data if j["connections"] == 1]
    assert len(direct_flights) == 2


def test_integration_valid_connection(integration_client: TestClient) -> None:
    """Tests finding valid 2-leg journeys (BUE -> PMI)."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=PMI"
    )
    assert response.status_code == 200
    data = response.json()

    # Should find 2 journeys:
    # 1. XX1000 -> XX1002
    # 2. XX1001 -> XX1003
    # XX1000 -> XX1003 is discarded (7h layover > 4h)
    assert len(data) == 2
    for journey in data:
        assert journey["connections"] == 2
        assert len(journey["path"]) == 2

    paths = [[f["flight_number"] for f in j["path"]] for j in data]
    assert ["XX1000", "XX1002"] in paths
    assert ["XX1001", "XX1003"] in paths
    assert ["XX1000", "XX1003"] not in paths


def test_integration_invalid_layover_rejected(integration_client: TestClient) -> None:
    """Tests that a layover > 4 hours is rejected implicitly in the previous test."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=PMI"
    )
    data = response.json()
    paths = [[f["flight_number"] for f in j["path"]] for j in data]
    assert ["XX1000", "XX1003"] not in paths


def test_integration_invalid_total_duration(integration_client: TestClient) -> None:
    """Tests that a journey exceeding 24 hours total duration is rejected."""
    # BUE -> LHR via GRU: XX1007 -> XX1009 is a valid 2-leg journey under 24h.
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=BUE&to=LHR"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["path"][0]["flight_number"] == "XX1007"
    assert data[0]["path"][1]["flight_number"] == "XX1009"


def test_integration_wrong_start_date(integration_client: TestClient) -> None:
    """Tests that flights starting on a different date are ignored."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-13&from=BUE&to=MAD"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_integration_no_solution(integration_client: TestClient) -> None:
    """Tests a search between cities with no possible connection."""
    response = integration_client.get(
        "/journeys/search?date=2024-09-12&from=MAD&to=JFK"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_integration_empty_api(empty_api_client: TestClient) -> None:
    """Tests the system resilience when the external API returns no events."""
    response = empty_api_client.get("/journeys/search?date=2024-09-12&from=BUE&to=MAD")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
