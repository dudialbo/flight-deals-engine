from typing import Any, List, Mapping, Sequence
from flight_deals_engine.domain.models import CalendarPriceSnapshot


class InMemoryStorageWriter:
    def __init__(self) -> None:
        self.snapshots: List[CalendarPriceSnapshot] = []
        self.deals: dict[str, Any] = {}        # keyed by category_id
        self.manifest: dict[str, Any] | None = None

    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None:
        self.snapshots.extend(items)

    def write_category(self, category_id: str, payload: Mapping[str, Any]) -> None:
        self.deals[category_id] = dict(payload)

    def write_manifest(self, payload: Mapping[str, Any]) -> None:
        self.manifest = dict(payload)

    def get_category(self, category_id: str) -> dict[str, Any] | None:
        return self.deals.get(category_id)

    def get_snapshots(self) -> List[CalendarPriceSnapshot]:
        return list(self.snapshots)

    def clear(self) -> None:
        self.snapshots.clear()
        self.deals.clear()
        self.manifest = None