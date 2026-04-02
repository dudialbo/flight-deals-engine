from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from flight_deals_engine.config.settings import Settings
from flight_deals_engine.domain.models import DealItem
from flight_deals_engine.jobs.refresh_deal_categories import run


def _make_deal_item(destination: str, price: str) -> DealItem:
    from datetime import datetime, timezone
    return DealItem(
        deal_id=f"id-{destination}",
        origin="TLV",
        destination_code=destination,
        destination_name=destination,
        price=Decimal(price),
        currency="USD",
        score=0.0,
        discovered_at=datetime.now(timezone.utc),
        departure_date=date.today() + timedelta(days=10),
        category_id="hot_deals",
    )


@patch("flight_deals_engine.jobs.refresh_deal_categories.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_deal_categories.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_deal_categories.DealRefreshService")
def test_refresh_deals_job_happy_path(
    mock_service_cls: MagicMock,
    mock_get_writer: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    mock_service = mock_service_cls.return_value
    mock_writer = mock_get_writer.return_value

    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
    settings.HOT_DEALS_DESTINATIONS = ["LON", "PAR"]

    mock_service.generate_category.return_value = (
        [_make_deal_item("LON", "250"), _make_deal_item("PAR", "180")],
        0,  # destinations_skipped
    )

    result = run(settings)

    assert result["job_name"] == "refresh_deal_categories"
    categories_attempted = result["categories_attempted"]
    assert result["categories_written"] == categories_attempted
    assert result["categories_failed"] == 0
    assert result["manifest_written"] is True
    assert mock_writer.write_category.call_count == categories_attempted
    mock_writer.write_manifest.assert_called_once()


@patch("flight_deals_engine.jobs.refresh_deal_categories.SearchBackendHttpClient")
@patch("flight_deals_engine.jobs.refresh_deal_categories.get_storage_writer")
@patch("flight_deals_engine.jobs.refresh_deal_categories.DealRefreshService")
def test_refresh_deals_job_category_failure(
    mock_service_cls: MagicMock,
    mock_get_writer: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    mock_service = mock_service_cls.return_value

    settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")

    mock_service.generate_category.side_effect = RuntimeError("search backend down")

    result = run(settings)

    assert result["categories_failed"] == result["categories_attempted"]
    assert result["categories_written"] == 0
    # Manifest is still written (with empty categories list)
    assert result["manifest_written"] is True