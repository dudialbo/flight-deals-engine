import re
from typing import List, Optional, Tuple

from flight_deals_engine.adapters.search_backend.dtos import FlightLeg, SearchBackendResponse
from flight_deals_engine.domain.models import FlightOption


def _parse_layover_duration_minutes(duration_str: str) -> int:
    """Parse a duration string like '3h 0m' or '19h 5m' into minutes."""
    match = re.match(r"(\d+)h\s*(\d+)m", duration_str.strip())
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))
    return 0


def _leg_minutes(leg: FlightLeg) -> Tuple[int, int]:
    """Return (flight_minutes, layover_minutes) for a leg, computed from segments/layovers."""
    flight_min = sum(s.duration_seconds or 0 for s in leg.segments) // 60
    layover_min = sum(
        _parse_layover_duration_minutes(lv.duration)
        for lv in leg.layovers
        if lv.duration
    )
    return flight_min, layover_min


def _worst_leg_durations(
    outbound: FlightLeg, return_leg: Optional[FlightLeg]
) -> Tuple[Optional[int], Optional[int]]:
    """
    Return (total_duration_minutes, layover_duration_minutes) for the leg with the
    highest layover/flight ratio. Returns (None, None) when no segment data is available.
    """
    legs = [outbound]
    if return_leg is not None:
        legs.append(return_leg)

    worst_flight: Optional[int] = None
    worst_layover: Optional[int] = None
    worst_ratio = -1.0

    for leg in legs:
        flight_min, layover_min = _leg_minutes(leg)
        if flight_min <= 0:
            continue
        ratio = layover_min / flight_min
        if ratio > worst_ratio:
            worst_ratio = ratio
            worst_flight = flight_min
            worst_layover = layover_min

    return worst_flight, worst_layover


def normalize_response(response: SearchBackendResponse) -> List[FlightOption]:
    normalized_options = []

    for result in response.results:
        # Use max stops across both directions — so max_stops=1 means ≤1 stop per leg,
        # and direct_only rejects if either leg has any stop.
        return_stops = result.return_leg.stops if result.return_leg else 0
        total_stops = max(result.outbound.stops, return_stops)

        # Use airport code (destinationCode); city code used only as fallback
        dest_code = result.outbound.destinationCode or result.outbound.destinationCityCode

        total_duration, layover_duration = _worst_leg_durations(result.outbound, result.return_leg)

        normalized_options.append(
            FlightOption(
                origin=result.outbound.originCode or "UNKNOWN",
                destination=result.outbound.destinationCode or "UNKNOWN",
                destination_code=dest_code,
                destination_name=result.outbound.destination,
                departure_date=result.outbound.departureDate,
                return_date=result.return_leg.departureDate if result.return_leg else None,
                price=result.price,
                currency=result.currency,
                deeplink=result.deep_link,
                provider_name=result.outbound.airline,
                airline=result.outbound.airline,
                stops=total_stops,
                total_duration_minutes=total_duration,
                layover_duration_minutes=layover_duration,
            )
        )

    return normalized_options