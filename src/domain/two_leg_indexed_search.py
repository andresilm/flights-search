from collections import defaultdict
from datetime import date, timedelta

from src.domain.model import FlightEvent, Journey

# Maximum allowed connection time between two flights.
_MAX_CONNECTION_TIME = timedelta(hours=4)

# Maximum allowed total journey duration.
_MAX_JOURNEY_DURATION = timedelta(hours=24)

# Type alias for the departure index key: (city, date).
_DepartureDateKey = tuple[str, date]


class TwoLegIndexedJourneySearch:
    """Searches for journeys using hash map indexes for O(n) performance."""

    def search(
        self,
        events: list[FlightEvent],
        origin: str,
        destination: str,
        search_date: date,
    ) -> list[Journey]:
        """Find direct and one-stop journeys from origin to destination on the given date."""
        by_departure, by_departure_city = self._build_indexes(events)

        journeys: list[Journey] = []

        # Candidate first flights: events departing from origin on the search date.
        first_flights = by_departure.get((origin, search_date), [])

        for first in first_flights:
            if first.arrival_city == destination:
                # Direct flight.
                journeys.append(Journey(flights=[first]))
                continue

            # Look for a valid connecting second flight departing from the intermediate city.
            intermediate = first.arrival_city
            for second in by_departure_city.get(intermediate, []):
                if self._is_valid_connection(first, second, destination):
                    journeys.append(Journey(flights=[first, second]))

        return journeys

    def _build_indexes(
        self, events: list[FlightEvent]
    ) -> tuple[
        dict[_DepartureDateKey, list[FlightEvent]],
        dict[str, list[FlightEvent]],
    ]:
        """Build departure indexes from the event list in O(n)."""
        by_departure: dict[_DepartureDateKey, list[FlightEvent]] = defaultdict(list)
        by_departure_city: dict[str, list[FlightEvent]] = defaultdict(list)

        for event in events:
            key: _DepartureDateKey = (
                event.departure_city,
                event.departure_datetime.date(),
            )
            by_departure[key].append(event)
            by_departure_city[event.departure_city].append(event)

        return by_departure, by_departure_city

    def _is_valid_connection(
        self,
        first: FlightEvent,
        second: FlightEvent,
        destination: str,
    ) -> bool:
        """Check if two flights form a valid connection to the destination."""
        if second.arrival_city != destination:
            return False

        # Second flight must depart strictly after the first one arrives.
        if second.departure_datetime <= first.arrival_datetime:
            return False

        # Connection time must not exceed 4 hours.
        if second.departure_datetime - first.arrival_datetime > _MAX_CONNECTION_TIME:
            return False

        # Total journey duration must not exceed 24 hours.
        if second.arrival_datetime - first.departure_datetime > _MAX_JOURNEY_DURATION:
            return False

        return True
