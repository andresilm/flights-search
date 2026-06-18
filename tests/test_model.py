from datetime import datetime, timedelta
from src.domain.model import FlightEvent, Journey


def test_flight_event_creation():
    event = FlightEvent(
        flight_number="UX123",
        departure_city="BUE",
        arrival_city="MAD",
        departure_datetime=datetime(2024, 9, 12, 10, 0),
        arrival_datetime=datetime(2024, 9, 12, 22, 0),
    )
    assert event.flight_number == "UX123"
    assert event.departure_city == "BUE"
    assert event.arrival_city == "MAD"
    assert event.departure_datetime == datetime(2024, 9, 12, 10, 0)
    assert event.arrival_datetime == datetime(2024, 9, 12, 22, 0)


def test_journey_single_flight():
    event = FlightEvent(
        flight_number="UX123",
        departure_city="BUE",
        arrival_city="MAD",
        departure_datetime=datetime(2024, 9, 12, 10, 0),
        arrival_datetime=datetime(2024, 9, 12, 22, 0),
    )
    journey = Journey(flights=[event])
    assert journey.connections == 1
    assert journey.origin == "BUE"
    assert journey.destination == "MAD"
    assert journey.total_duration == timedelta(hours=12)


def test_journey_two_flights():
    event1 = FlightEvent(
        flight_number="UX123",
        departure_city="BUE",
        arrival_city="MAD",
        departure_datetime=datetime(2024, 9, 12, 10, 0),
        arrival_datetime=datetime(2024, 9, 12, 22, 0),
    )
    event2 = FlightEvent(
        flight_number="UX456",
        departure_city="MAD",
        arrival_city="BCN",
        departure_datetime=datetime(2024, 9, 13, 0, 0),
        arrival_datetime=datetime(2024, 9, 13, 1, 30),
    )
    journey = Journey(flights=[event1, event2])
    assert journey.connections == 2
    assert journey.origin == "BUE"
    assert journey.destination == "BCN"
    assert journey.total_duration == timedelta(hours=15, minutes=30)
