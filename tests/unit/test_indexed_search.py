from datetime import datetime, timedelta


from src.domain.indexed_search import IndexedJourneySearch
from src.domain.model import FlightEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_event(
    flight_number: str,
    departure_city: str,
    arrival_city: str,
    departure_dt: datetime,
    arrival_dt: datetime,
) -> FlightEvent:
    """Creates a FlightEvent with the given parameters.

    Args:
        flight_number: The unique identifier for the flight.
        departure_city: The city code where the flight departs.
        arrival_city: The city code where the flight arrives.
        departure_dt: The departure datetime.
        arrival_dt: The arrival datetime.

    Returns:
        A FlightEvent instance.

    """
    return FlightEvent(
        flight_number=flight_number,
        departure_city=departure_city,
        arrival_city=arrival_city,
        departure_datetime=departure_dt,
        arrival_datetime=arrival_dt,
    )


SEARCH_DATE = datetime(2024, 9, 12).date()

strategy = IndexedJourneySearch()


# ---------------------------------------------------------------------------
# Direct flight
# ---------------------------------------------------------------------------


def test_direct_flight_found() -> None:
    """A direct flight from origin to destination on the search date is returned."""
    events = [
        make_event(
            "UX100",
            "BUE",
            "MAD",
            datetime(2024, 9, 12, 10, 0),
            datetime(2024, 9, 12, 22, 0),
        )
    ]
    result = strategy.search(events, "BUE", "MAD", SEARCH_DATE)
    assert len(result) == 1
    assert result[0].connections == 1
    assert result[0].origin == "BUE"
    assert result[0].destination == "MAD"


def test_no_flights_for_date() -> None:
    """No events on the search date returns an empty list."""
    events = [
        make_event(
            "UX100",
            "BUE",
            "MAD",
            datetime(2024, 9, 13, 10, 0),
            datetime(2024, 9, 13, 22, 0),
        )
    ]
    result = strategy.search(events, "BUE", "MAD", SEARCH_DATE)
    assert result == []


def test_no_matching_route() -> None:
    """Events exist on the date but none connect origin to destination."""
    events = [
        make_event(
            "UX100",
            "BUE",
            "SCL",
            datetime(2024, 9, 12, 10, 0),
            datetime(2024, 9, 12, 14, 0),
        )
    ]
    result = strategy.search(events, "BUE", "MAD", SEARCH_DATE)
    assert result == []


# ---------------------------------------------------------------------------
# Connecting flight
# ---------------------------------------------------------------------------


def test_connecting_flight_found() -> None:
    """Two flights forming a valid connection are returned as one journey."""
    events = [
        make_event(
            "UX100",
            "BUE",
            "MAD",
            datetime(2024, 9, 12, 10, 0),
            datetime(2024, 9, 12, 22, 0),
        ),
        make_event(
            "UX200",
            "MAD",
            "PMI",
            datetime(2024, 9, 13, 0, 0),
            datetime(2024, 9, 13, 1, 0),
        ),
    ]
    result = strategy.search(events, "BUE", "PMI", SEARCH_DATE)
    assert len(result) == 1
    assert result[0].connections == 2
    assert result[0].origin == "BUE"
    assert result[0].destination == "PMI"


def test_connection_exceeds_4h() -> None:
    """A connection with layover > 4 hours is excluded."""
    events = [
        make_event(
            "UX100",
            "BUE",
            "MAD",
            datetime(2024, 9, 12, 10, 0),
            datetime(2024, 9, 12, 22, 0),
        ),
        # Layover = 5 hours (22:00 → 03:00 next day)
        make_event(
            "UX200",
            "MAD",
            "PMI",
            datetime(2024, 9, 13, 3, 0),
            datetime(2024, 9, 13, 4, 0),
        ),
    ]
    result = strategy.search(events, "BUE", "PMI", SEARCH_DATE)
    assert result == []


def test_journey_exceeds_24h() -> None:
    """A journey whose total duration exceeds 24 hours is excluded."""
    events = [
        make_event(
            "UX100",
            "BUE",
            "MAD",
            datetime(2024, 9, 12, 10, 0),
            datetime(2024, 9, 12, 22, 0),
        ),
        # Arrival at 10:01 next day → total = 24h01m
        make_event(
            "UX200",
            "MAD",
            "PMI",
            datetime(2024, 9, 13, 0, 0),
            datetime(2024, 9, 13, 10, 1),
        ),
    ]
    result = strategy.search(events, "BUE", "PMI", SEARCH_DATE)
    assert result == []


def test_second_flight_departs_before_first_arrives() -> None:
    """A second flight departing before the first lands is excluded."""
    events = [
        make_event(
            "UX100",
            "BUE",
            "MAD",
            datetime(2024, 9, 12, 10, 0),
            datetime(2024, 9, 12, 22, 0),
        ),
        # Departs at 21:00, before UX100 arrives at 22:00.
        make_event(
            "UX200",
            "MAD",
            "PMI",
            datetime(2024, 9, 12, 21, 0),
            datetime(2024, 9, 12, 23, 0),
        ),
    ]
    result = strategy.search(events, "BUE", "PMI", SEARCH_DATE)
    assert result == []


# ---------------------------------------------------------------------------
# Mixed scenario
# ---------------------------------------------------------------------------


def test_mixed_results() -> None:
    """Valid direct and connecting flights are returned; invalid ones are excluded."""
    events = [
        # Valid direct flight BUE→MAD
        make_event(
            "UX100",
            "BUE",
            "MAD",
            datetime(2024, 9, 12, 10, 0),
            datetime(2024, 9, 12, 22, 0),
        ),
        # Valid connecting: BUE→SCL + SCL→PMI
        make_event(
            "UX101",
            "BUE",
            "SCL",
            datetime(2024, 9, 12, 8, 0),
            datetime(2024, 9, 12, 12, 0),
        ),
        make_event(
            "UX201",
            "SCL",
            "PMI",
            datetime(2024, 9, 12, 14, 0),
            datetime(2024, 9, 12, 20, 0),
        ),
        # Invalid: connection > 4h
        make_event(
            "UX300",
            "SCL",
            "PMI",
            datetime(2024, 9, 12, 20, 0),
            datetime(2024, 9, 12, 23, 0),
        ),
    ]

    # Search BUE→MAD: only the direct flight.
    mad_result = strategy.search(events, "BUE", "MAD", SEARCH_DATE)
    assert len(mad_result) == 1
    assert mad_result[0].connections == 1

    # Search BUE→PMI: only the valid connection (layover 2h).
    pmi_result = strategy.search(events, "BUE", "PMI", SEARCH_DATE)
    assert len(pmi_result) == 1
    assert pmi_result[0].connections == 2


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


def test_performance_large_dataset() -> None:
    """Indexed search completes in under 100ms with 10,000 synthetic events."""
    import time

    base = datetime(2024, 9, 12, 0, 0)
    large_events = [
        make_event(
            f"XX{i:04d}",
            f"C{i % 50:03d}",
            f"C{(i + 1) % 50:03d}",
            base + timedelta(hours=i % 24),
            base + timedelta(hours=i % 24, minutes=90),
        )
        for i in range(10_000)
    ]

    start = time.perf_counter()
    strategy.search(large_events, "C000", "C001", SEARCH_DATE)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 100, f"Search took {elapsed_ms:.1f}ms, expected < 100ms"
