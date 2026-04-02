from datetime import date
from flight_deals_engine.domain.models import DealCategoryConfig, FlightOption


def passes_layover_quality(option: FlightOption) -> bool:
    """
    Returns True if this flight passes the layover quality rule.
    Rule: total layover duration <= 50% of total flight duration.
    If duration data is missing, return True (fail open — don't discard the deal).
    """
    if option.total_duration_minutes is None or option.layover_duration_minutes is None:
        return True
    if option.total_duration_minutes <= 0:
        return True
    return option.layover_duration_minutes <= (option.total_duration_minutes * 0.5)


def is_within_summer_window(departure_date: date, year: int | None = None) -> bool:
    """
    Returns True if departure_date falls between June 1 and August 31.
    Uses the departure date's own year if year is not specified.
    """
    y = year or departure_date.year
    return date(y, 6, 1) <= departure_date <= date(y, 8, 31)


def passes_filters(option: FlightOption, config: DealCategoryConfig, today: date) -> bool:
    if option.price <= 0:
        return False
    if option.departure_date <= today:
        return False
    if config.direct_only and option.stops > 0:
        return False
    if config.max_stops is not None and option.stops > config.max_stops:
        return False
    if config.price_max is not None and option.price > config.price_max:
        return False
    if config.departure_days and option.departure_date.weekday() not in config.departure_days:
        return False
    if config.return_days and option.return_date and option.return_date.weekday() not in config.return_days:
        return False
    if config.departure_months and option.departure_date.month not in config.departure_months:
        return False
    if config.layover_filter and not config.direct_only:
        if not passes_layover_quality(option):
            return False
    return True