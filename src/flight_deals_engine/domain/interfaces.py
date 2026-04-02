from typing import Any, Mapping, Protocol, Sequence
from flight_deals_engine.domain.models import (
    CalendarPriceSnapshot,
    FlightOption,
    RefreshTarget,
)


class SearchBackendClient(Protocol):
    def search_flights(self, target: RefreshTarget) -> Sequence[FlightOption]: ...


class PriceSnapshotWriter(Protocol):
    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None: ...


class DealCatalogWriter(Protocol):
    def write_category(self, category_id: str, payload: Mapping[str, Any]) -> None: ...
    def write_manifest(self, payload: Mapping[str, Any]) -> None: ...