"""HTTP adapter for the external flight events API."""

from datetime import datetime

import httpx

from src.domain.model import FlightEvent
from src.logger import get_logger
from src.ports import FlightEventRepository

logger = get_logger(__name__)


class HttpFlightEventRepository(FlightEventRepository):
    """Adapter that fetches flight events from an external REST API via HTTP."""

    def __init__(self, client: httpx.AsyncClient, base_url: str):
        """Initializes the HTTP repository.

        Args:
            client: The shared httpx.AsyncClient instance.
            base_url: The base URL of the external API (e.g., https://api.example.com).
        """
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def get_all(self) -> list[FlightEvent]:
        """Retrieves all available flight events from the external API.

        Makes a GET request to `<base_url>/flight-events` and parses the JSON
        response into domain ``FlightEvent`` objects.

        Returns:
            A list of FlightEvent instances.

        Raises:
            httpx.HTTPError: If the HTTP request fails.
        """
        url = f"{self._base_url}/flight-events"
        logger.debug("Fetching flight events from %s", url)

        response = await self._client.get(url)
        response.raise_for_status()

        data = response.json()
        logger.debug("Fetched %d flight events", len(data))

        events: list[FlightEvent] = []
        for item in data:
            # The API returns ISO 8601 strings with 'Z' for UTC.
            # Python's fromisoformat handles 'Z' in Python 3.11+,
            # but replacing it with '+00:00' is universally safe.
            departure_dt = datetime.fromisoformat(
                item["departure_datetime"].replace("Z", "+00:00")
            )
            arrival_dt = datetime.fromisoformat(
                item["arrival_datetime"].replace("Z", "+00:00")
            )

            events.append(
                FlightEvent(
                    flight_number=item["flight_number"],
                    departure_city=item["departure_city"],
                    arrival_city=item["arrival_city"],
                    departure_datetime=departure_dt,
                    arrival_datetime=arrival_dt,
                )
            )

        return events
