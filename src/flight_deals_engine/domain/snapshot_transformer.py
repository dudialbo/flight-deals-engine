from datetime import datetime, timezone
from flight_deals_engine.domain.models import FlightOption, CalendarPriceSnapshot


def transform_to_snapshot(flight: FlightOption, source_job: str) -> CalendarPriceSnapshot:
    month_str = flight.departure_date.strftime("%Y-%m")
    snapshot_key = f"{flight.origin}#{flight.destination}#{month_str}"

    return CalendarPriceSnapshot(
        snapshot_key=snapshot_key,
        origin=flight.origin,
        destination=flight.destination,
        month=month_str,
        cheapest_price=flight.price,
        currency=flight.currency,
        discovered_at=datetime.now(timezone.utc),
        source_job=source_job
    )
