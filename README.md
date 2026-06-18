# Flights Search

A REST API that searches for flight journeys (direct and with one connection) based on flight events fetched from an external API. Built with **FastAPI**, managed with **uv**, and designed following the **Ports & Adapters** (Hexagonal Architecture) pattern.

## Architecture

```
src/
├── domain/
│   ├── model.py              # Pure domain models: FlightEvent, Journey
│   └── indexed_search.py     # IndexedJourneySearch (concrete strategy)
├── ports.py                  # Protocols: FlightEventRepository, JourneySearchStrategy
├── adapters/
│   └── flight_events_api.py  # HTTP adapter for the external flight events API
├── services/
│   └── journey_search.py     # Orchestration service
└── app/
    ├── config.py             # Settings (pydantic-settings)
    ├── main.py               # FastAPI app + lifespan
    └── routes.py             # GET /journeys/search
```

The search algorithm is a **replaceable strategy** (`JourneySearchStrategy` protocol). The current implementation, `IndexedJourneySearch`, pre-indexes all events into hash maps in O(n) and performs lookups in O(k × m) — effectively O(n) overall. A new algorithm can be plugged in by implementing the protocol and configuring `JOURNEY_SEARCH_STRATEGY` in `.env`.

## Business Rules

1. A **journey** is a sequence of 1 or 2 flight events connecting an origin to a destination.
2. The first flight must depart on the **search date** (UTC date comparison).
3. The **total duration** of the journey (first departure → last arrival) must not exceed **24 hours**.
4. The **connection time** between two flights (first arrival → second departure) must not exceed **4 hours**.
5. The intermediate city must match between the two connecting flights.
6. The second flight must depart **strictly after** the first one lands.

## API

### `GET /journeys/search`

| Query param | Type | Description |
|---|---|---|
| `date` | `YYYY-MM-DD` | Departure date |
| `from` | `string` | Origin city code (3 letters) |
| `to` | `string` | Destination city code (3 letters) |

**Example response:**

```json
[
  {
    "connections": 2,
    "path": [
      {
        "flight_number": "UX100",
        "from": "BUE",
        "to": "MAD",
        "departure_time": "2024-09-12 10:00",
        "arrival_time": "2024-09-12 22:00"
      },
      {
        "flight_number": "UX200",
        "from": "MAD",
        "to": "PMI",
        "departure_time": "2024-09-13 00:00",
        "arrival_time": "2024-09-13 01:00"
      }
    ]
  }
]
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) to be installed.

```bash
# Install dependencies
uv sync

# Run in development mode
uv run uvicorn src.app.main:app --reload --port 8000

# Run tests with coverage
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .
```

## Environment Variables

Copy `.env` and adjust as needed:

| Variable | Default | Description |
|---|---|---|
| `FLIGHT_EVENTS_API_URL` | — | Base URL of the external flight events API |
| `JOURNEY_SEARCH_STRATEGY` | `indexed` | Search algorithm to use (`indexed`) |
