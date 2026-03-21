from datetime import date
from decimal import Decimal
from flight_deals_engine.application.normalizer import FlightNormalizer
from flight_deals_engine.domain.models import FlightOption


def test_to_calendar_snapshot() -> None:
    normalizer = FlightNormalizer()
    flight = FlightOption(
        origin="TLV",
        destination="LON",
        departure_date=date(2026, 6, 1),
        price=Decimal("199.99"),
        currency="USD",
    )
    snapshot = normalizer.to_calendar_snapshot(
        source_job="refresh_calendar_prices",
        month="2026-06",
        flight=flight,
    )
    assert snapshot.origin == "TLV"
    assert snapshot.destination == "LON"
    assert snapshot.cheapest_price == Decimal("199.99")
