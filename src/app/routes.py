"""HTTP endpoints for the application."""

from datetime import date, datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_serializer

from src.domain.model import Journey
from src.services.journey_search import JourneySearchService

router = APIRouter(tags=["journeys"])


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
        # Consigna: "campo con la cantidad de eventos de vuelo del viaje"
        return cls(connections=len(path), path=path)


def get_journey_service(request: Request) -> JourneySearchService:
    """Dependency to retrieve the JourneySearchService from app state."""
    return cast(JourneySearchService, request.app.state.journey_service)


@router.get("/journeys/search", response_model=list[JourneyResponse])
async def search_journeys(
    search_date: Annotated[date, Query(alias="date")],
    origin: Annotated[str, Query(alias="from")],
    destination: Annotated[str, Query(alias="to")],
    service: Annotated[JourneySearchService, Depends(get_journey_service)],
) -> list[JourneyResponse]:
    """Searches for valid flight journeys."""
    journeys = await service.search(search_date, origin, destination)
    return [JourneyResponse.from_domain(j) for j in journeys]
