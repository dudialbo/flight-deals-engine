from datetime import date
from flight_deals_engine.application.planner import RefreshPlanner
from flight_deals_engine.domain.models import RefreshTarget

def test_planner_build_monthly_targets():
    planner = RefreshPlanner()
    start_date = date(2023, 10, 15)
    targets = planner.build_monthly_targets(
        origin="TLV",
        destinations=["LON", "PAR"],
        start_date=start_date,
        months_ahead=2,
        currency="USD",
        nights_min=3,
        nights_max=7
    )

    assert len(targets) == 4 # 2 months * 2 destinations

    # Check first target (Oct, LON)
    t1 = targets[0]
    assert t1.origin == "TLV"
    assert t1.destination == "LON"
    assert t1.date_from == date(2023, 10, 15)
    assert t1.date_to == date(2023, 10, 31)
    assert t1.nights_min == 3
    assert t1.nights_max == 7

    # Check second target (Oct, PAR)
    t2 = targets[1]
    assert t2.destination == "PAR"

    # Check third target (Nov, LON)
    t3 = targets[2]
    assert t3.date_from == date(2023, 11, 1)
    assert t3.date_to == date(2023, 11, 30)

def test_planner_month_rollover():
    planner = RefreshPlanner()
    start_date = date(2023, 12, 1)
    targets = planner.build_monthly_targets(
        origin="TLV",
        destinations=["LON"],
        start_date=start_date,
        months_ahead=2,
        currency="USD"
    )

    assert len(targets) == 2
    assert targets[0].date_from == date(2023, 12, 1)
    assert targets[1].date_from == date(2024, 1, 1) # Rollover to next year
    assert targets[1].date_to == date(2024, 1, 31)
