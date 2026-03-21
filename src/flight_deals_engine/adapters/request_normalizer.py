from datetime import timedelta
from flight_deals_engine.domain.models import RefreshTarget
from flight_deals_engine.adapters.search_backend.dtos import SearchBackendRequest


def normalize_request(target: RefreshTarget, limit: int = 100) -> SearchBackendRequest:
    # Calculate return window based on stay duration if provided
    return_from = None
    return_to = None

    if target.nights_min is not None and target.nights_max is not None:
        # Earliest possible return: Earliest departure + min stay
        return_from = target.date_from + timedelta(days=target.nights_min)
        # Latest possible return: Latest departure + max stay
        return_to = target.date_to + timedelta(days=target.nights_max)

    return SearchBackendRequest(
        origin=target.origin,
        destination=target.destination,
        date_from=target.date_from,
        date_to=target.date_to,
        return_from=return_from,
        return_to=return_to,
        nights_in_dst_from=target.nights_min,
        nights_in_dst_to=target.nights_max,
        direct_only=target.direct_only,
        limit=limit
    )
