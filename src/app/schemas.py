"""Pydantic schemas for API request/response serialization."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from src.domain.model import Journey


class FlightResponse(BaseModel):
    """API representation of a single flight event."""

    model_config = ConfigDict(populate_by_name=True)

    flight_number: str
    from_city: str = Field(alias="from")
    to_city: str = Field(alias="to")
    departure_time: datetime
    arrival_time: datetime

    @field_serializer("departure_time", "arrival_time")
    def serialize_datetime(self, dt: datetime, _info: Any) -> str:
        """Formats datetime as YYYY-MM-DD HH:MM (without seconds or timezone)."""
        return dt.strftime("%Y-%m-%d %H:%M")


class JourneyResponse(BaseModel):
    """API representation of a journey."""

    connections: int
    path: list[FlightResponse]

    @classmethod
    def from_domain(cls, journey: Journey) -> "JourneyResponse":
        path = [
            FlightResponse(
                flight_number=f.flight_number,
                **{"from": f.departure_city, "to": f.arrival_city},
                departure_time=f.departure_datetime,
                arrival_time=f.arrival_datetime,
            )
            for f in journey.flights
        ]
        return cls(connections=len(path), path=path)
