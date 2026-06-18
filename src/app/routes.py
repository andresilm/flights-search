"""HTTP endpoints for the application."""

from datetime import date
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Query, Request

from src.app.schemas import JourneyResponse
from src.services.journey_search import JourneySearchService

router = APIRouter()

_CITY_CODE = Query(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")


def get_journey_service(request: Request) -> JourneySearchService:
    """Dependency to retrieve the JourneySearchService from app state."""
    return cast(JourneySearchService, request.app.state.journey_service)


@router.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/journeys/search", response_model=list[JourneyResponse], tags=["journeys"])
async def search_journeys(
    search_date: Annotated[date, Query(alias="date")],
    origin: Annotated[
        str, Query(alias="from", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    ],
    destination: Annotated[
        str, Query(alias="to", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    ],
    service: Annotated[JourneySearchService, Depends(get_journey_service)],
) -> list[JourneyResponse]:
    """Searches for valid flight journeys."""
    journeys = await service.search(search_date, origin, destination)
    return [JourneyResponse.from_domain(j) for j in journeys]
