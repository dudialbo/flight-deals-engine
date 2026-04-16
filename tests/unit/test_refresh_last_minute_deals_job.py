from unittest.mock import MagicMock, patch
from decimal import Decimal
import httpx

from flight_deals_engine.jobs.refresh_last_minute_deals import run
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.domain.models import HotDealCandidate


@patch("flight_deals_engine.jobs.refresh_last_minute_deals.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_last_minute_deals.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_last_minute_deals.HotDealsRefreshService")
def test_refresh_last_minute_deals_happy_path(mock_service_cls, mock_get_writer, mock_client_cls):
    mock_service = mock_service_cls.return_value
    mock_writer = mock_get_writer.return_value

    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.LAST_MINUTE_DESTINATIONS = ["LON", "PAR"]

    mock_flight = MagicMock()
    mock_flight.price = Decimal("199.00")
    mock_service.fetch_and_select_best.return_value = mock_flight

    mock_candidate = MagicMock(spec=HotDealCandidate)
    mock_service.transform_to_candidate.return_value = mock_candidate
    mock_service.rank_deals.return_value = [mock_candidate, mock_candidate]

    result = run(settings)

    assert result["job_name"] == "refresh_last_minute_deals"
    assert result["total_destinations"] == 2
    assert result["destinations_succeeded"] == 2
    assert result["destinations_empty"] == 0
    assert result["destinations_failed"] == 0
    assert result["deals_persisted"] == 2

    mock_get_writer.assert_called_once_with(settings.STORAGE_ADAPTER, settings.S3_BUCKET_NAME)
    mock_writer.write_last_minute_deals.assert_called_once()


@patch("flight_deals_engine.jobs.refresh_last_minute_deals.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_last_minute_deals.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_last_minute_deals.HotDealsRefreshService")
def test_refresh_last_minute_deals_partial_failures(mock_service_cls, mock_get_writer, mock_client_cls):
    mock_service = mock_service_cls.return_value
    mock_writer = mock_get_writer.return_value

    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.LAST_MINUTE_DESTINATIONS = ["LON", "PAR", "ROM"]

    mock_flight = MagicMock()
    mock_flight.price = Decimal("99.00")

    def mock_build_target(origin, destination, settings):
        target = MagicMock()
        target.destination = destination
        return target

    mock_service.build_last_minute_target.side_effect = mock_build_target

    def side_effect(target):
        if target.destination == "LON":
            return mock_flight
        elif target.destination == "PAR":
            raise httpx.RequestError("Connection failed", request=MagicMock())
        elif target.destination == "ROM":
            return None
        return None

    mock_service.fetch_and_select_best.side_effect = side_effect

    mock_candidate = MagicMock(spec=HotDealCandidate)
    mock_service.transform_to_candidate.return_value = mock_candidate
    mock_service.rank_deals.return_value = [mock_candidate]

    result = run(settings)

    assert result["total_destinations"] == 3
    assert result["destinations_succeeded"] == 1
    assert result["destinations_empty"] == 1
    assert result["destinations_failed"] == 1
    assert result["deals_persisted"] == 1

    mock_writer.write_last_minute_deals.assert_called_once()


@patch("flight_deals_engine.jobs.refresh_last_minute_deals.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_last_minute_deals.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_last_minute_deals.HotDealsRefreshService")
def test_refresh_last_minute_deals_no_results(mock_service_cls, mock_get_writer, mock_client_cls):
    mock_service = mock_service_cls.return_value
    mock_writer = mock_get_writer.return_value

    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.LAST_MINUTE_DESTINATIONS = ["LON", "PAR"]

    mock_service.fetch_and_select_best.return_value = None
    mock_service.rank_deals.return_value = []

    result = run(settings)

    assert result["destinations_succeeded"] == 0
    assert result["destinations_empty"] == 2
    assert result["deals_persisted"] == 0
    mock_writer.write_last_minute_deals.assert_not_called()


@patch("flight_deals_engine.jobs.refresh_last_minute_deals.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_last_minute_deals.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_last_minute_deals.HotDealsRefreshService")
def test_refresh_last_minute_deals_respects_limit(mock_service_cls, mock_get_writer, mock_client_cls):
    mock_service = mock_service_cls.return_value
    mock_writer = mock_get_writer.return_value

    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.LAST_MINUTE_DESTINATIONS = ["LON", "PAR", "ROM"]
    settings.LAST_MINUTE_LIMIT = 2

    mock_flight = MagicMock()
    mock_flight.price = Decimal("150.00")
    mock_service.fetch_and_select_best.return_value = mock_flight

    mock_candidate = MagicMock(spec=HotDealCandidate)
    mock_service.transform_to_candidate.return_value = mock_candidate
    # Ranked list has 3 items but limit is 2
    mock_service.rank_deals.return_value = [mock_candidate, mock_candidate, mock_candidate]

    result = run(settings)

    assert result["deals_persisted"] == 2
    written_args = mock_writer.write_last_minute_deals.call_args[0][0]
    assert len(written_args) == 2
