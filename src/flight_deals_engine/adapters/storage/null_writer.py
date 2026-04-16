from collections.abc import Sequence
from flight_deals_engine.domain.models import CalendarPriceSnapshot, HotDealCandidate


class NullStorageWriter:
    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None:
        _ = items

    def write_hot_deals(self, items: Sequence[HotDealCandidate]) -> None:
        _ = items

    def write_last_minute_deals(self, items: Sequence[HotDealCandidate]) -> None:
        _ = items
