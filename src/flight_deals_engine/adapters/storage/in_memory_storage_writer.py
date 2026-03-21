from typing import List, Sequence
from flight_deals_engine.domain.models import CalendarPriceSnapshot, HotDealCandidate


class InMemoryStorageWriter:
    def __init__(self) -> None:
        self.snapshots: List[CalendarPriceSnapshot] = []
        self.deals: List[HotDealCandidate] = []

    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None:
        self.snapshots.extend(items)

    def write_hot_deals(self, items: Sequence[HotDealCandidate]) -> None:
        self.deals.extend(items)

    def get_snapshots(self) -> List[CalendarPriceSnapshot]:
        return list(self.snapshots)

    def get_deals(self) -> List[HotDealCandidate]:
        return list(self.deals)

    def clear(self) -> None:
        self.snapshots.clear()
        self.deals.clear()
