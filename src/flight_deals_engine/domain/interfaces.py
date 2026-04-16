from typing import Protocol, Sequence
from flight_deals_engine.domain.models import (
    CalendarPriceSnapshot,
    FlightOption,
    HotDealCandidate,
    RefreshTarget,
)


class SearchBackendClient(Protocol):
    def search_flights(self, target: RefreshTarget) -> Sequence[FlightOption]: ...


class PriceSnapshotWriter(Protocol):
    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None: ...


class HotDealsWriter(Protocol):
    def write_hot_deals(self, items: Sequence[HotDealCandidate]) -> None: ...


class LastMinuteDealsWriter(Protocol):
    def write_last_minute_deals(self, items: Sequence[HotDealCandidate]) -> None: ...
