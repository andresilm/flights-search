from collections import defaultdict
from datetime import date, timedelta

from src.domain.model import FlightEvent, Journey

# Maximum allowed connection time between two flights.
_MAX_CONNECTION_TIME = timedelta(hours=4)

# Maximum allowed total journey duration.
_MAX_JOURNEY_DURATION = timedelta(hours=24)

# Type alias for the departure index key: (city, date).
_DepartureDateKey = tuple[str, date]


class IndexedJourneySearch:
    """Optimized journey search strategy using pre-built hash map indexes.

    Replaces the O(n²) brute-force double loop with O(n) index construction
    and O(k × m) lookups, where k and m are small subsets of the full event list.

    Indexes built on each call to ``search``:
        - ``_by_departure``: maps ``(city, date)`` → flights departing from that city on that date.
        - ``_by_departure_city``: maps ``city`` → all flights departing from that city (any date).

    This class implements the ``JourneySearchStrategy`` protocol and can be
    swapped for any other strategy implementation without changing the service layer.
    """

    def search(
        self,
        events: list[FlightEvent],
        origin: str,
        destination: str,
        search_date: date,
    ) -> list[Journey]:
        """Searches for valid journeys connecting origin and destination on the given date.

        Applies the following business rules:
        - The first flight must depart on ``search_date`` (UTC date comparison).
        - Connection time between two flights must not exceed 4 hours.
        - Total journey duration must not exceed 24 hours.
        - The second flight must depart strictly after the first flight arrives.
        - The intermediate city must match between the two flights.

        Args:
            events: The full list of available flight events.
            origin: The departure city code for the journey.
            destination: The arrival city code for the journey.
            search_date: The desired departure date for the first flight.

        Returns:
            A list of valid Journey objects (direct and with one connection).
        """
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
        """Builds two hash map indexes from the event list in O(n).

        Args:
            events: The full list of available flight events to index.

        Returns:
            A tuple of:
                - ``by_departure``: maps ``(departure_city, departure_date)`` to a list of events.
                - ``by_departure_city``: maps ``departure_city`` to all events from that city.
        """
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
        """Validates whether two flights form a valid connecting journey leg.

        Args:
            first: The first flight of the potential connection.
            second: The candidate second flight.
            destination: The required final arrival city for the journey.

        Returns:
            True if all business rules are satisfied, False otherwise.
        """
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
