from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class FlightEvent:
    """A single scheduled flight between two cities (all datetimes in UTC)."""

    flight_number: str
    departure_city: str
    arrival_city: str
    departure_datetime: datetime
    arrival_datetime: datetime


@dataclass
class Journey:
    """A travel journey composed of one or two flight legs."""

    flights: list[FlightEvent]

    @property
    def connections(self) -> int:
        return len(self.flights)

    @property
    def origin(self) -> str:
        return self.flights[0].departure_city if self.flights else ""

    @property
    def destination(self) -> str:
        return self.flights[-1].arrival_city if self.flights else ""

    @property
    def total_duration(self) -> timedelta:
        if not self.flights:
            return timedelta()
        return self.flights[-1].arrival_datetime - self.flights[0].departure_datetime
