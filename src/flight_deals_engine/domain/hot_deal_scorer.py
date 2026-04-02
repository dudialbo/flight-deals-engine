from typing import List, Literal
from flight_deals_engine.domain.models import DealItem


class DealRanker:
    def rank(
        self,
        candidates: List[DealItem],
        mode: Literal["price", "weekend", "value"] = "price",
    ) -> List[DealItem]:
        if mode == "price":
            return self._rank_by_price(candidates)
        if mode == "weekend":
            return self._rank_by_weekend(candidates)
        return self._rank_by_price(candidates)  # value not yet implemented

    def _rank_by_price(self, candidates: List[DealItem]) -> List[DealItem]:
        return sorted(candidates, key=lambda d: (d.price, d.departure_date, d.destination_code or ""))

    def _rank_by_weekend(self, candidates: List[DealItem]) -> List[DealItem]:
        return sorted(candidates, key=lambda d: (d.stops, d.price, d.departure_date))