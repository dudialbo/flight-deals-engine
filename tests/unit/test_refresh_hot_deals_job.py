from unittest.mock import MagicMock, patch
from decimal import Decimal
from flight_deals_engine.jobs.refresh_hot_deals import run
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.domain.models import HotDealCandidate
import httpx

@patch("flight_deals_engine.jobs.refresh_hot_deals.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_hot_deals.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_hot_deals.HotDealsRefreshService")
def test_refresh_hot_deals_job_happy_path(mock_service_cls, mock_get_writer, mock_client_cls):
    mock_service = mock_service_cls.return_value
    mock_writer = mock_get_writer.return_value

    # Mock settings
    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.HOT_DEALS_DESTINATIONS = ["LON", "PAR"]

    # Mock best deal selection (always returns a valid flight for simplicity)
    mock_flight = MagicMock()
    mock_flight.price = Decimal("100.00")
    mock_service.fetch_and_select_best.return_value = mock_flight

    # Mock transformation
    mock_candidate = MagicMock(spec=HotDealCandidate)
    mock_service.transform_to_candidate.return_value = mock_candidate

    # Mock ranking
    mock_service.rank_deals.return_value = [mock_candidate, mock_candidate]

    result = run(settings)

    assert result["job_name"] == "refresh_hot_deals"
    assert result["total_destinations"] == 2
    assert result["destinations_succeeded"] == 2
    assert result["destinations_empty"] == 0
    assert result["destinations_failed"] == 0
    assert result["deals_persisted"] == 2

    mock_get_writer.assert_called_once_with(settings.STORAGE_ADAPTER, settings.S3_BUCKET_NAME)
    mock_writer.write_hot_deals.assert_called_once()

@patch("flight_deals_engine.jobs.refresh_hot_deals.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_hot_deals.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_hot_deals.HotDealsRefreshService")
def test_refresh_hot_deals_job_partial_failures(mock_service_cls, mock_get_writer, mock_client_cls):
    mock_service = mock_service_cls.return_value
    mock_writer = mock_get_writer.return_value

    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.HOT_DEALS_DESTINATIONS = ["LON", "PAR", "ROM"]

    # LON: Returns valid flight
    # PAR: Raises HTTP Error
    # ROM: Returns None (no results)

    mock_flight = MagicMock()
    mock_flight.price = Decimal("100.00")

    # Since we mocked the service, build_target returns a MagicMock.
    # Let's ensure it returns an object with the correct destination so our side_effect works.
    def mock_build_target(origin, destination, settings):
        target = MagicMock()
        target.destination = destination
        return target

    mock_service.build_target.side_effect = mock_build_target

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
    mock_service.rank_deals.return_value = [mock_candidate] # Only LON

    result = run(settings)

    assert result["total_destinations"] == 3
    assert result["destinations_succeeded"] == 1
    assert result["destinations_empty"] == 1
    assert result["destinations_failed"] == 1
    assert result["deals_persisted"] == 1

    mock_get_writer.assert_called_once_with(settings.STORAGE_ADAPTER, settings.S3_BUCKET_NAME)
    mock_writer.write_hot_deals.assert_called_once()
