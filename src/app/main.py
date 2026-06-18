"""FastAPI application initialization."""

import contextlib
from collections.abc import AsyncGenerator

import httpx
from fastapi import FastAPI

from src.adapters.flight_events_api import HttpFlightEventRepository
from src.app.config import Settings, get_search_strategy
from src.app.routes import router
from src.logger import configure_logging, get_logger
from src.services.journey_search import JourneySearchService

logger = get_logger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle and dependencies."""
    settings: Settings = app.state.settings
    configure_logging(settings.log_level_int)

    logger.info("Starting up FastAPI application")

    strategy = get_search_strategy(settings)

    # We use a single shared httpx.AsyncClient for connection pooling
    async with httpx.AsyncClient() as client:
        repository = HttpFlightEventRepository(client, settings.FLIGHT_EVENTS_API_URL)
        app.state.journey_service = JourneySearchService(repository, strategy)
        yield

    logger.info("Shutting down FastAPI application")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Creates and configures the FastAPI application."""
    if settings is None:
        settings = Settings(**{})

    app = FastAPI(
        title="Flights Search API",
        description="Searches for flight journeys based on external events API.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.include_router(router)

    return app


app = create_app()
