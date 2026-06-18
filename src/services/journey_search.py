"""Service layer for orchestrating journey search."""

from datetime import date

from src.domain.model import Journey
from src.logger import get_logger
from src.ports import FlightEventRepository, JourneySearchStrategy

logger = get_logger(__name__)


class JourneySearchService:
    """Orchestration service for searching flight journeys.

    Coordinates fetching data from the repository and applying the
    search strategy.
    """

    def __init__(
        self,
        repository: FlightEventRepository,
        strategy: JourneySearchStrategy,
    ):
        """Initialize the service with required dependencies.

        Args:
            repository: Port implementation to fetch flight events.
            strategy: Port implementation representing the search algorithm.

        """
        self._repository = repository
        self._strategy = strategy

    async def search(
        self,
        search_date: date,
        origin: str,
        destination: str,
    ) -> list[Journey]:
        """Orchestrates the search for valid journeys.

        Args:
            search_date: The departure date for the first flight.
            origin: The departure city code.
            destination: The arrival city code.

        Returns:
            A list of valid journeys connecting the origin and destination.

        """
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
