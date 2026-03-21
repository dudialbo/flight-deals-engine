from datetime import datetime, timezone
from flight_deals_engine.domain.models import CalendarPriceSnapshot, FlightOption


class FlightNormalizer:
    def to_calendar_snapshot(
        self,
        source_job: str,
        month: str,
        flight: FlightOption,
    ) -> CalendarPriceSnapshot:
        return CalendarPriceSnapshot(
            snapshot_key=f"{flight.origin}:{flight.destination}:{month}",
            origin=flight.origin,
            destination=flight.destination,
            month=month,
            cheapest_price=flight.price,
            currency=flight.currency,
            discovered_at=datetime.now(timezone.utc),
            source_job=source_job,
        )
