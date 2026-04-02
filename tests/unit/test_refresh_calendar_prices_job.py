from datetime import date
from unittest.mock import patch
from decimal import Decimal
from flight_deals_engine.jobs.refresh_calendar_prices import run
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.application.commands import RefreshCalendarPricesCommand, Scope
from flight_deals_engine.domain.models import RefreshTarget, FlightOption, CalendarPriceSnapshot


@patch("flight_deals_engine.jobs.refresh_calendar_prices.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_calendar_prices.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_calendar_prices.RefreshPlanner")
@patch("flight_deals_engine.jobs.refresh_calendar_prices.transform_to_snapshot")
@patch("flight_deals_engine.jobs.refresh_calendar_prices.select_cheapest_flight")
def test_refresh_calendar_prices_job(
    mock_select_cheapest,
    mock_transform,
    mock_planner_cls,
    mock_get_writer,
    mock_client_cls
):
    # Setup mocks
    mock_planner = mock_planner_cls.return_value
    mock_client = mock_client_cls.return_value
    mock_writer = mock_get_writer.return_value

    # Mock planner targets
    target = RefreshTarget(
        origin="TLV", destination="LON",
        date_from=date(2023, 10, 1), date_to=date(2023, 10, 31),
        currency="USD"
    )
    mock_planner.build_monthly_targets.return_value = [target]

    # Mock backend response
    flight_opt = FlightOption(
        origin="TLV", destination="LON",
        departure_date=date(2023, 10, 15),
        price=Decimal("100.00"), currency="USD"
    )
    mock_client.search_flights.return_value = [flight_opt]

    # Mock selection
    mock_select_cheapest.return_value = flight_opt

    # Mock transformation
    snapshot = CalendarPriceSnapshot(
        snapshot_key="key", origin="TLV", destination="LON",
        month="2023-10", cheapest_price=Decimal("100.00"),
        currency="USD", discovered_at=date(2023, 10, 1), source_job="test"
    )
    mock_transform.return_value = snapshot

    # Run job
    settings = Settings(
        _env_file=None,
        SEARCH_BACKEND_BASE_URL="http://test",
        STORAGE_ADAPTER="null"
    )
    command = RefreshCalendarPricesCommand(
        jobType="refresh_calendar_prices",
        scope=Scope(origins=["TLV"], destinations=["LON"], monthsAhead=1)
    )

    result = run(settings, command)

    # Verify
    assert result["status"] == "success"
    assert result["targets_planned"] == 1
    assert result["results_found"] == 1
    assert result["snapshots_written"] == 1

    mock_planner.build_monthly_targets.assert_called_once()
    mock_client.search_flights.assert_called_once_with(target)
    mock_select_cheapest.assert_called_once()
    mock_transform.assert_called_once()
    mock_get_writer.assert_called_once_with("null", None)
    mock_writer.write_calendar_snapshots.assert_called_once()
    args, _ = mock_writer.write_calendar_snapshots.call_args
    assert args[0] == [snapshot]
