from typing import List
from flight_deals_engine.domain.models import FlightOption
from flight_deals_engine.adapters.search_backend.dtos import SearchBackendResponse


def normalize_response(response: SearchBackendResponse) -> List[FlightOption]:
    normalized_options = []

    for result in response.results:
        # Determine total stops
        outbound_stops = result.outbound.stops
        return_stops = result.return_leg.stops if result.return_leg else 0
        total_stops = outbound_stops + return_stops

        # Use destinationCityCode if available, fallback to destinationCode
        dest_code = result.outbound.destinationCityCode or result.outbound.destinationCode

        normalized_options.append(
            FlightOption(
                origin=result.outbound.originCode or "UNKNOWN",
                destination=result.outbound.destinationCode or "UNKNOWN",
                destination_code=dest_code,
                departure_date=result.outbound.departureDate,
                return_date=result.return_leg.departureDate if result.return_leg else None,
                price=result.price,
                currency=result.currency,
                deeplink=result.deep_link,
                provider_name=result.outbound.airline,
                airline=result.outbound.airline,
                stops=total_stops
            )
        )

    return normalized_options
