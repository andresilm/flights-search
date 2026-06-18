from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class FlightEvent:
    """Represents a single flight leg between two cities.

    Attributes:
        flight_number: The unique identifier for the flight (e.g. ``"UX123"``).
        departure_city: The IATA city code where the flight departs.
        arrival_city: The IATA city code where the flight arrives.
        departure_datetime: The scheduled departure date and time (UTC).
        arrival_datetime: The scheduled arrival date and time (UTC).
    """

    flight_number: str
    departure_city: str
    arrival_city: str
    departure_datetime: datetime
    arrival_datetime: datetime


@dataclass
class Journey:
    """Represents a complete travel journey made up of one or two flight legs.

    Attributes:
        flights: Ordered list of flight events composing the journey.
    """

    flights: list[FlightEvent]

    @property
    def connections(self) -> int:
        """Total number of flight legs in the journey."""
        return len(self.flights)

    @property
    def origin(self) -> str:
        """Departure city of the first flight leg."""
        return self.flights[0].departure_city if self.flights else ""

    @property
    def destination(self) -> str:
        """Arrival city of the last flight leg."""
        return self.flights[-1].arrival_city if self.flights else ""

    @property
    def total_duration(self) -> timedelta:
        """Elapsed time from the first departure to the last arrival."""
        if not self.flights:
            return timedelta()
        return self.flights[-1].arrival_datetime - self.flights[0].departure_datetime
