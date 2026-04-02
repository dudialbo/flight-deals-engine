from collections.abc import Sequence
from typing import Any, Mapping
from flight_deals_engine.domain.models import CalendarPriceSnapshot


class NullStorageWriter:
    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None:
        _ = items

    def write_category(self, category_id: str, payload: Mapping[str, Any]) -> None:
        _ = category_id, payload

    def write_manifest(self, payload: Mapping[str, Any]) -> None:
        _ = payload