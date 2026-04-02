from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from flight_deals_engine.application.deal_refresh_service import DealRefreshService
from flight_deals_engine.domain.hot_deal_scorer import DealRanker
from flight_deals_engine.domain.models import DealCategoryConfig, FlightOption


def _make_config(**kwargs) -> DealCategoryConfig:  # type: ignore[no-untyped-def]
    defaults = dict(
        id="hot_deals",
        title="Hot Deals",
        destinations=["LON"],
        date_horizon_days=30,
        nights_min=4,
        nights_max=5,
        direct_only=True,
        max_items=20,
        selection_mode="cheapest_per_destination",
        ranking_mode="price",
    )
    defaults.update(kwargs)
    return DealCategoryConfig(**defaults)


def test_build_target() -> None:
    service = DealRefreshService(MagicMock(), DealRanker())
    config = _make_config(date_horizon_days=30, nights_min=4, nights_max=5, direct_only=True)

    target = service.build_target("TLV", "LON", config)

    assert target.origin == "TLV"
    assert target.destination == "LON"
    assert target.date_from == date.today()
    assert target.date_to == date.today() + timedelta(days=30)
    assert target.nights_min == 4
    assert target.nights_max == 5
    assert target.direct_only is True


def test_fetch_candidates_defensive_validation() -> None:
    mock_client = MagicMock()
    tomorrow = date.today() + timedelta(days=1)

    f_direct = FlightOption(
        origin="TLV", destination="LON", departure_date=tomorrow,
        price=Decimal("200"), currency="USD", stops=0
    )
    f_indirect = FlightOption(
        origin="TLV", destination="LON", departure_date=tomorrow,
        price=Decimal("150"), currency="USD", stops=1
    )
    mock_client.search_flights.return_value = [f_direct, f_indirect]

    service = DealRefreshService(mock_client, DealRanker())
    config = _make_config(direct_only=True)
    target = service.build_target("TLV", "LON", config)

    results = service.fetch_candidates_for_destination(target, config)

    assert len(results) == 1
    assert results[0].stops == 0
    assert results[0].price == Decimal("200")


def test_select_cheapest_per_destination() -> None:
    service = DealRefreshService(MagicMock(), DealRanker())
    tomorrow = date.today() + timedelta(days=1)
    options = [
        FlightOption(origin="TLV", destination="LON", departure_date=tomorrow,
                     price=Decimal("300"), currency="USD"),
        FlightOption(origin="TLV", destination="LON", departure_date=tomorrow,
                     price=Decimal("200"), currency="USD"),
    ]
    best = service.select_cheapest_per_destination(options)
    assert best is not None
    assert best.price == Decimal("200")


def test_generate_category_cheapest_per_destination() -> None:
    mock_client = MagicMock()
    tomorrow = date.today() + timedelta(days=1)

    mock_client.search_flights.return_value = [
        FlightOption(origin="TLV", destination="LON", departure_date=tomorrow,
                     price=Decimal("150"), currency="USD", stops=0)
    ]

    service = DealRefreshService(mock_client, DealRanker())
    config = _make_config(destinations=["LON", "PAR"], selection_mode="cheapest_per_destination")

    items, skipped = service.generate_category(config, "TLV", "USD")

    assert len(items) == 2
    assert skipped == 0
    assert all(i.category_id == "hot_deals" for i in items)