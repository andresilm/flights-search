from datetime import date
from typing import Protocol

from src.domain.model import FlightEvent, Journey


class FlightEventRepository(Protocol):
    """Port for fetching flight events from a data source."""

    async def get_all(self) -> list[FlightEvent]: ...


class JourneySearchStrategy(Protocol):
    """Port for the journey search algorithm."""

    def search(
        self,
        events: list[FlightEvent],
        origin: str,
        destination: str,
        search_date: date,
    ) -> list[Journey]: ...
