import pytest
from unittest.mock import MagicMock, patch
from flight_deals_engine.entrypoints.lambda_handler import lambda_handler
from flight_deals_engine.jobs import refresh_calendar_prices, refresh_hot_deals
from flight_deals_engine.application.commands import RefreshCalendarPricesCommand

@patch("flight_deals_engine.entrypoints.lambda_handler.Settings")
@patch("flight_deals_engine.entrypoints.lambda_handler.configure_logging")
@patch("flight_deals_engine.jobs.refresh_calendar_prices.run")
def test_lambda_handler_calendar_prices(mock_run, mock_log, mock_settings):
    mock_settings.return_value.LOG_LEVEL = "INFO"
    mock_settings.return_value.SEARCH_BACKEND_BASE_URL = "http://mock"
    mock_run.return_value = {"status": "ok"}

    event = {
        "jobType": "refresh_calendar_prices",
        "scope": {
            "origins": ["JFK"],
            "destinations": ["LHR"],
            "monthsAhead": 3
        }
    }

    result = lambda_handler(event, {})

    assert result == {"status": "ok"}
    mock_run.assert_called_once()

    # Check if run was called with settings and command
    args, _ = mock_run.call_args
    assert args[0] == mock_settings.return_value
    command = args[1]
    assert isinstance(command, RefreshCalendarPricesCommand)
    assert command.scope.origins == ["JFK"]
    assert command.scope.destinations == ["LHR"]
    assert command.scope.months_ahead == 3

@patch("flight_deals_engine.entrypoints.lambda_handler.Settings")
@patch("flight_deals_engine.entrypoints.lambda_handler.configure_logging")
@patch("flight_deals_engine.jobs.refresh_hot_deals.run")
def test_lambda_handler_hot_deals(mock_run, mock_log, mock_settings):
    mock_settings.return_value.LOG_LEVEL = "INFO"
    mock_run.return_value = {"status": "ok"}

    event = {
        "jobType": "refresh_hot_deals"
    }

    result = lambda_handler(event, {})

    assert result == {"status": "ok"}
    mock_run.assert_called_once()

@patch("flight_deals_engine.entrypoints.lambda_handler.Settings")
@patch("flight_deals_engine.entrypoints.lambda_handler.configure_logging")
def test_lambda_handler_unknown_job(mock_log, mock_settings):
    event = {
        "jobType": "unknown_job"
    }

    with pytest.raises(ValueError, match="Unknown jobType: unknown_job"):
        lambda_handler(event, {})
