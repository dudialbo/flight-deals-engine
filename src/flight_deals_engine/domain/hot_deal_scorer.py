from decimal import Decimal
from typing import List
from flight_deals_engine.domain.models import FlightOption, HotDealCandidate


class HotDealScorer:
    """
    Evaluates and ranks flight options to determine hot deals.
    """

    def rank_deals(self, candidates: List[HotDealCandidate]) -> List[HotDealCandidate]:
        """
        Ranks a list of HotDealCandidate objects.
        
        Ranking rules for Phase 1:
        1. Lowest price
        2. Earliest outbound departure date
        3. Destination code (stable tie-breaker)
        """
        return sorted(
            candidates,
            key=lambda deal: (
                deal.price,
                deal.departure_date,
                deal.destination
            )
        )
