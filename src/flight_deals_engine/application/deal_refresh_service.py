import logging
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List

from flight_deals_engine.adapters.search_backend.client import RateLimitError, SearchBackendHttpClient
from flight_deals_engine.domain.deal_filters import passes_filters
from flight_deals_engine.domain.flight_selection import select_cheapest_flight
from flight_deals_engine.domain.hot_deal_scorer import DealRanker
from flight_deals_engine.domain.models import DealCategoryConfig, DealItem, FlightOption, RefreshTarget

logger = logging.getLogger(__name__)

DESTINATION_NAMES = {
    "LON": "London", "PAR": "Paris", "ATH": "Athens", "ROM": "Rome",
    "MAD": "Madrid", "BCN": "Barcelona", "RHO": "Rhodes", "HER": "Crete",
    "AMS": "Amsterdam", "BUD": "Budapest", "VIE": "Vienna", "LIS": "Lisbon",
    "BER": "Berlin", "PRG": "Prague", "WAW": "Warsaw", "BRU": "Brussels",
    "CPH": "Copenhagen", "ARN": "Stockholm", "DUB": "Dublin",
    "EDI": "Edinburgh", "MXP": "Milan", "MIL": "Milan",
    "STO": "Stockholm",
    # Greece & Cyprus
    "JMK": "Mykonos", "LCA": "Larnaca", "PFO": "Paphos",
    # Caucasus
    "TBS": "Tbilisi", "BUS": "Batumi",
    # Southeast Asia & Indian Ocean
    "BKK": "Bangkok", "HKT": "Phuket", "MLE": "Maldives", "SEZ": "Seychelles",
    # USA
    "JFK": "New York", "EWR": "New York", "LGA": "New York", "NYC": "New York",
    "MIA": "Miami", "FLL": "Fort Lauderdale",
    "LAX": "Los Angeles", "LAS": "Las Vegas",
}


class DealRefreshService:
    def __init__(
        self,
        search_client: SearchBackendHttpClient,
        ranker: DealRanker,
        request_delay_seconds: float = 0.0,
    ) -> None:
        self._search_client = search_client
        self._ranker = ranker
        self._request_delay_seconds = request_delay_seconds

    def build_target(self, origin: str, destination: str, config: DealCategoryConfig) -> RefreshTarget:
        today = date.today()
        date_from = config.date_from or today
        date_to = config.date_to or (today + timedelta(days=config.date_horizon_days))
        return RefreshTarget(
            origin=origin,
            destination=destination,
            date_from=date_from,
            date_to=date_to,
            nights_min=config.nights_min,
            nights_max=config.nights_max,
            direct_only=config.direct_only,
        )

    def fetch_candidates_for_destination(
        self, target: RefreshTarget, config: DealCategoryConfig
    ) -> List[FlightOption]:
        """Fetch flights and apply filters. Returns valid options only."""
        options = self._search_client.search_flights(target)
        today = date.today()
        valid = []
        for opt in options:
            if target.direct_only and opt.stops > 0:
                logger.warning(
                    "Skipped non-direct flight %s->%s (%d stops) despite direct_only=True",
                    opt.origin, opt.destination, opt.stops,
                )
                continue
            if passes_filters(opt, config, today):
                valid.append(opt)
        return valid

    def select_cheapest_per_destination(
        self, options: List[FlightOption]
    ) -> FlightOption | None:
        """Delegates to domain/flight_selection.py select_cheapest_flight."""
        return select_cheapest_flight(options)

    def select_best_overall(
        self, all_options: List[FlightOption], config: DealCategoryConfig
    ) -> List[FlightOption]:
        """Sort globally by price, dedupe by destination, return top N."""
        seen: set[str] = set()
        unique: List[FlightOption] = []
        for opt in sorted(all_options, key=lambda o: o.price):
            key = opt.destination_code or opt.destination
            if key not in seen:
                seen.add(key)
                unique.append(opt)
        return unique[: config.max_items]

    def transform_to_deal_item(self, flight: FlightOption, category_id: str) -> DealItem:
        code = flight.destination_code or flight.destination
        nights = (
            (flight.return_date - flight.departure_date).days
            if flight.return_date else None
        )
        return DealItem(
            deal_id=str(uuid.uuid4()),
            origin=flight.origin,
            destination_code=code,
            destination_name=DESTINATION_NAMES.get(code) or flight.destination_name,
            price=flight.price,
            currency=flight.currency,
            score=0.0,
            discovered_at=datetime.now(timezone.utc),
            deeplink=flight.deeplink,
            departure_date=flight.departure_date,
            return_date=flight.return_date,
            nights=nights,
            direct=flight.stops == 0,
            stops=flight.stops,
            airline=flight.airline or flight.provider_name,
            category_id=category_id,
        )

    def generate_category(
        self, config: DealCategoryConfig, origin: str, currency: str
    ) -> tuple[List[DealItem], int]:
        """
        Top-level method: given a category config, returns (ranked_items, destinations_skipped).
        Destinations that hit a rate limit are skipped; other destinations are still processed.
        """
        destinations = config.destinations or []
        deal_items: List[DealItem] = []
        destinations_skipped = 0

        if config.selection_mode == "cheapest_per_destination":
            for i, destination in enumerate(destinations):
                if i > 0 and self._request_delay_seconds > 0:
                    time.sleep(self._request_delay_seconds)
                try:
                    target = self.build_target(origin, destination, config)
                    options = self.fetch_candidates_for_destination(target, config)
                    best = self.select_cheapest_per_destination(options)
                    if best:
                        deal_items.append(self.transform_to_deal_item(best, config.id))
                    else:
                        logger.info("No valid options for %s -> %s", origin, destination)
                except RateLimitError:
                    logger.warning("Rate limit exhausted for %s -> %s, skipping destination", origin, destination)
                    destinations_skipped += 1
                except Exception:
                    logger.exception("Error fetching %s -> %s", origin, destination)

        elif config.selection_mode == "best_overall":
            all_options: List[FlightOption] = []
            for i, destination in enumerate(destinations):
                if i > 0 and self._request_delay_seconds > 0:
                    time.sleep(self._request_delay_seconds)
                try:
                    target = self.build_target(origin, destination, config)
                    options = self.fetch_candidates_for_destination(target, config)
                    all_options.extend(options)
                except RateLimitError:
                    logger.warning("Rate limit exhausted for %s -> %s, skipping destination", origin, destination)
                    destinations_skipped += 1
                except Exception:
                    logger.exception("Error fetching %s -> %s", origin, destination)
            for flight in self.select_best_overall(all_options, config):
                deal_items.append(self.transform_to_deal_item(flight, config.id))

        ranked = self._ranker.rank(deal_items, config.ranking_mode)
        return ranked[: config.max_items], destinations_skipped