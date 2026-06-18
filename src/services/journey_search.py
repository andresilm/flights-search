"""Service layer for orchestrating journey search."""

from datetime import date

from src.domain.model import Journey
from src.logger import get_logger
from src.ports import FlightEventRepository, JourneySearchStrategy

logger = get_logger(__name__)


class JourneySearchService:
    """Coordinates fetching flight events and delegating to the search strategy."""

    def __init__(
        self,
        repository: FlightEventRepository,
        strategy: JourneySearchStrategy,
    ):
        self._repository = repository
        self._strategy = strategy

    async def search(
        self,
        search_date: date,
        origin: str,
        destination: str,
    ) -> list[Journey]:
        """Search for journeys from origin to destination on the given date."""
        logger.info(
            "Searching journeys from %s to %s on %s", origin, destination, search_date
        )

        # 1. Fetch all events from the repository.
        events = await self._repository.get_all()
        logger.debug("Fetched %d events from repository", len(events))

        if not events:
            logger.warning("No events returned by repository")
            return []

        # 2. Delegate the search logic to the injected strategy.
        journeys = self._strategy.search(events, origin, destination, search_date)
        logger.info("Search complete. Found %d journeys", len(journeys))

        return journeys
