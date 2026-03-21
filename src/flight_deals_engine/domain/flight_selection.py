from typing import List, Optional
from flight_deals_engine.domain.models import FlightOption


def select_cheapest_flight(options: List[FlightOption]) -> Optional[FlightOption]:
    if not options:
        return None

    valid_options = [o for o in options if o.price > 0]
    if not valid_options:
        return None

    return min(valid_options, key=lambda o: o.price)
