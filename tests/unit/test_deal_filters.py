from datetime import date, timedelta
from decimal import Decimal


from flight_deals_engine.domain.deal_filters import (
    is_within_summer_window,
    passes_filters,
    passes_layover_quality,
)
from flight_deals_engine.domain.models import DealCategoryConfig, FlightOption


def _flight(**kwargs) -> FlightOption:  # type: ignore[no-untyped-def]
    defaults = dict(
        origin="TLV",
        destination="ATH",
        departure_date=date.today() + timedelta(days=10),
        price=Decimal("150"),
        currency="USD",
        stops=0,
    )
    defaults.update(kwargs)
    return FlightOption(**defaults)


# --- passes_layover_quality ---

def test_layover_quality_passes_when_layover_40_percent() -> None:
    flight = _flight(total_duration_minutes=200, layover_duration_minutes=80)  # 40%
    assert passes_layover_quality(flight) is True


def test_layover_quality_fails_when_layover_60_percent() -> None:
    flight = _flight(total_duration_minutes=200, layover_duration_minutes=120)  # 60%
    assert passes_layover_quality(flight) is False


def test_layover_quality_passes_exactly_at_50_percent() -> None:
    flight = _flight(total_duration_minutes=200, layover_duration_minutes=100)  # 50%
    assert passes_layover_quality(flight) is True


def test_layover_quality_passes_when_duration_data_missing() -> None:
    flight = _flight(total_duration_minutes=None, layover_duration_minutes=None)
    assert passes_layover_quality(flight) is True


def test_layover_quality_passes_when_only_one_field_missing() -> None:
    assert passes_layover_quality(_flight(total_duration_minutes=200, layover_duration_minutes=None)) is True
    assert passes_layover_quality(_flight(total_duration_minutes=None, layover_duration_minutes=80)) is True


# --- is_within_summer_window ---

def test_summer_window_june_in_range() -> None:
    assert is_within_summer_window(date(2026, 6, 1)) is True


def test_summer_window_august_in_range() -> None:
    assert is_within_summer_window(date(2026, 8, 31)) is True


def test_summer_window_september_out_of_range() -> None:
    assert is_within_summer_window(date(2026, 9, 1)) is False


def test_summer_window_may_out_of_range() -> None:
    assert is_within_summer_window(date(2026, 5, 31)) is False


# --- passes_filters: layover_filter wiring ---

def _config(**kwargs) -> DealCategoryConfig:  # type: ignore[no-untyped-def]
    defaults = dict(
        id="test",
        title="Test",
        selection_mode="best_overall",
        direct_only=False,
        layover_filter=True,
        max_stops=1,
    )
    defaults.update(kwargs)
    return DealCategoryConfig(**defaults)


def test_passes_filters_layover_filter_applied_for_non_direct() -> None:
    today = date.today()
    flight = _flight(
        departure_date=today + timedelta(days=5),
        stops=1,
        total_duration_minutes=200,
        layover_duration_minutes=120,  # 60% — should fail
    )
    assert passes_filters(flight, _config(direct_only=False, layover_filter=True), today) is False


def test_passes_filters_layover_filter_skipped_for_direct() -> None:
    today = date.today()
    # Even with bad layover data, direct categories skip the layover check
    flight = _flight(
        departure_date=today + timedelta(days=5),
        stops=0,
        total_duration_minutes=200,
        layover_duration_minutes=120,  # 60% — but direct_only=True so ignored
    )
    assert passes_filters(flight, _config(direct_only=True, layover_filter=True), today) is True


def test_passes_filters_max_stops_enforced() -> None:
    today = date.today()
    flight = _flight(departure_date=today + timedelta(days=5), stops=2)
    assert passes_filters(flight, _config(max_stops=1), today) is False


def test_passes_filters_max_stops_allows_exact() -> None:
    today = date.today()
    flight = _flight(departure_date=today + timedelta(days=5), stops=1)
    assert passes_filters(flight, _config(max_stops=1), today) is True