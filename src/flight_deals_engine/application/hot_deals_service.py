import logging
from typing import List
from datetime import date, timedelta
import uuid
from flight_deals_engine.domain.models import RefreshTarget, FlightOption, HotDealCandidate
from flight_deals_engine.adapters.search_backend.client import SearchBackendHttpClient
from flight_deals_engine.domain.hot_deal_scorer import HotDealScorer
from flight_deals_engine.domain.flight_selection import select_cheapest_flight
from flight_deals_engine.config.settings import Settings

logger = logging.getLogger(__name__)


class HotDealsRefreshService:
    def __init__(self, search_client: SearchBackendHttpClient, scorer: HotDealScorer):
        self._search_client = search_client
        self._scorer = scorer

    def build_target(self, origin: str, destination: str, settings: Settings) -> RefreshTarget:
        """
        Builds a single RefreshTarget for a destination spanning the rolling search horizon.
        """
        today = date.today()
        horizon_end = today + timedelta(days=settings.HOT_DEALS_SEARCH_HORIZON_DAYS)

        return RefreshTarget(
            origin=origin,
            destination=destination,
            date_from=today,
            date_to=horizon_end,
            nights_min=settings.HOT_DEALS_NIGHTS_MIN,
            nights_max=settings.HOT_DEALS_NIGHTS_MAX,
            direct_only=settings.HOT_DEALS_DIRECT_ONLY,
            currency=settings.DEFAULT_CURRENCY
        )

    def build_last_minute_target(self, origin: str, destination: str, settings: Settings) -> RefreshTarget:
        """
        Builds a RefreshTarget covering the next 14 days for last-minute deal searches.
        """
        today = date.today()
        window_end = today + timedelta(days=settings.LAST_MINUTE_HORIZON_DAYS)

        return RefreshTarget(
            origin=origin,
            destination=destination,
            date_from=today,
            date_to=window_end,
            nights_min=settings.LAST_MINUTE_NIGHTS_MIN,
            nights_max=settings.LAST_MINUTE_NIGHTS_MAX,
            direct_only=settings.LAST_MINUTE_DIRECT_ONLY,
            currency=settings.DEFAULT_CURRENCY
        )

    def fetch_and_select_best(self, target: RefreshTarget) -> FlightOption | None:
        """
        Fetches flights for a target, applies defensive validation, and selects the cheapest valid option.
        """
        options = self._search_client.search_flights(target)

        if not options:
            return None

        # Defensive validation: ensure it's actually direct if requested
        valid_options = []
        for opt in options:
            if target.direct_only and opt.stops > 0:
                logger.warning(
                    "Skipped non-direct flight %s->%s (%d stops) despite direct_only=True",
                    opt.origin, opt.destination, opt.stops
                )
                continue
            valid_options.append(opt)

        return select_cheapest_flight(valid_options)

    def transform_to_candidate(self, flight: FlightOption) -> HotDealCandidate:
        from datetime import datetime, timezone

        return HotDealCandidate(
            deal_id=str(uuid.uuid4()),
            origin=flight.origin,
            destination=flight.destination_code or flight.destination,
            price=flight.price,
            currency=flight.currency,
            score=0.0, # Score is handled by ranking logic implicitly via sorting in phase 1
            discovered_at=datetime.now(timezone.utc),
            deeplink=flight.deeplink,
            departure_date=flight.departure_date,
            return_date=flight.return_date,
            stops=flight.stops,
            airline=flight.airline or flight.provider_name
        )

    def rank_deals(self, candidates: List[HotDealCandidate]) -> List[HotDealCandidate]:
        return self._scorer.rank_deals(candidates)
