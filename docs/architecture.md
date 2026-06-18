# Architecture & Design Decisions

This project follows the **Ports & Adapters** (Hexagonal) architecture. The main goal is to separate the core business logic (finding flight journeys) from external concerns (the web framework, the external flight data API).

## High-Level Architecture

```mermaid
flowchart TD
    subgraph API Layer
        Router["FastAPI Router\n(src/app/routes.py)"]
    end
    
    subgraph Service Layer
        Service["JourneySearchService\n(src/services/journey_search.py)"]
    end
    
    subgraph Domain & Ports
        StrategyPort["JourneySearchStrategy (Port)"]
        RepoPort["FlightEventRepository (Port)"]
        Domain["Domain Models\nFlightEvent, Journey"]
        IndexedStrategy["IndexedJourneySearch\n(src/domain/indexed_search.py)"]
    end
    
    subgraph Adapters
        HttpAdapter["HttpFlightEventRepository\n(src/adapters/flight_events_api.py)"]
    end

    Router -->|Uses| Service
    Service -->|Depends on| StrategyPort
    Service -->|Depends on| RepoPort
    Service -->|Uses| Domain
    
    IndexedStrategy -.-|> StrategyPort
    HttpAdapter -.-|> RepoPort
    
    StrategyPort -.-> Domain
    RepoPort -.-> Domain
```

## Key Decisions

### 1. Hexagonal Architecture (Ports & Adapters)
By defining `FlightEventRepository` as a port, the business logic does not know *how* flights are fetched. The `HttpFlightEventRepository` is just one implementation. If the external API changes to gRPC, or if a database is introduced, the core logic remains untouched.

### 2. Strategy Pattern
The `JourneySearchStrategy` port enables swapping out the search algorithm. We currently use `IndexedJourneySearch` (an O(n) optimized algorithm), but a new algorithm (like BFS or Dijkstra for N-connections) could be introduced by implementing the protocol and updating the `.env` configuration, without touching existing services.

### 3. FastAPI and Pydantic
FastAPI provides native asynchronous support, which is critical since fetching flights from an external API is an I/O bound operation. Pydantic is used for rigorous request/response validation, ensuring the exact expected date formats (`YYYY-MM-DD HH:MM`) are outputted to the clients.
