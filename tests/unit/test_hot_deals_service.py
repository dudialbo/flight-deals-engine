from datetime import date, timedelta
from unittest.mock import MagicMock
from decimal import Decimal
from flight_deals_engine.application.hot_deals_service import HotDealsRefreshService
from flight_deals_engine.domain.hot_deal_scorer import HotDealScorer
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.domain.models import FlightOption, HotDealCandidate

def test_build_target():
    service = HotDealsRefreshService(MagicMock(), HotDealScorer())
    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.HOT_DEALS_SEARCH_HORIZON_DAYS = 30
    settings.HOT_DEALS_NIGHTS_MIN = 4
    settings.HOT_DEALS_NIGHTS_MAX = 5
    settings.HOT_DEALS_DIRECT_ONLY = True

    target = service.build_target("TLV", "LON", settings)

    assert target.origin == "TLV"
    assert target.destination == "LON"
    assert target.date_from == date.today()
    assert target.date_to == date.today() + timedelta(days=30)
    assert target.nights_min == 4
    assert target.nights_max == 5
    assert target.direct_only is True

def test_fetch_and_select_best_defensive_validation():
    mock_client = MagicMock()

    # 1 direct flight, 1 non-direct flight (cheaper)
    f1 = FlightOption(
        origin="TLV", destination="LON", departure_date=date(2023, 1, 1),
        price=Decimal("200"), currency="USD", stops=0
    )
    f2 = FlightOption(
        origin="TLV", destination="LON", departure_date=date(2023, 1, 1),
        price=Decimal("150"), currency="USD", stops=1 # Cheaper but not direct
    )

    mock_client.search_flights.return_value = [f1, f2]
    service = HotDealsRefreshService(mock_client, HotDealScorer())

    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.HOT_DEALS_DIRECT_ONLY = True
    target = service.build_target("TLV", "LON", settings)

    best = service.fetch_and_select_best(target)

    # Should select the direct flight even though it's more expensive
    assert best is not None
    assert best.price == Decimal("200")
    assert best.stops == 0

def test_rank_deals():
    service = HotDealsRefreshService(MagicMock(), HotDealScorer())

    c1 = HotDealCandidate(
        deal_id="1", origin="TLV", destination="LON",
        price=Decimal("200"), currency="USD", score=0,
        discovered_at=date(2023, 1, 1), departure_date=date(2023, 1, 10)
    )
    c2 = HotDealCandidate(
        deal_id="2", origin="TLV", destination="PAR",
        price=Decimal("150"), currency="USD", score=0,
        discovered_at=date(2023, 1, 1), departure_date=date(2023, 1, 15)
    )
    c3 = HotDealCandidate(
        deal_id="3", origin="TLV", destination="ROM",
        price=Decimal("150"), currency="USD", score=0,
        discovered_at=date(2023, 1, 1), departure_date=date(2023, 1, 12) # Same price, earlier date
    )

    ranked = service.rank_deals([c1, c2, c3])

    assert len(ranked) == 3
    assert ranked[0].destination == "ROM" # 150, earlier date
    assert ranked[1].destination == "PAR" # 150, later date
    assert ranked[2].destination == "LON" # 200
