from datetime import date
from typing import Protocol

from src.domain.model import FlightEvent, Journey


class FlightEventRepository(Protocol):
    """Protocol defining the repository for flight events.

    This interface outlines the required methods for any data source
    that provides flight events.
    """

    async def get_all(self) -> list[FlightEvent]:
        """Retrieves all available flight events.

        Returns:
            list[FlightEvent]: A list containing all flight events from the repository.
        """
        ...


class JourneySearchStrategy(Protocol):
    """Protocol defining the strategy for searching journeys.

    This interface outlines the required methods for any algorithm
    that constructs flight journeys from a list of flight events.
    """

    def search(
        self,
        events: list[FlightEvent],
        origin: str,
        destination: str,
        search_date: date,
    ) -> list[Journey]:
        """Searches for valid journeys connecting the origin and destination.

        Args:
            events (list[FlightEvent]): The available flight events to use for the search.
            origin (str): The departure city code.
            destination (str): The arrival city code.
            search_date (date): The desired departure date for the first flight.

        Returns:
            list[Journey]: A list of valid journeys that meet the criteria.
        """
        ...
