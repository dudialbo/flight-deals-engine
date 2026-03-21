from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import httpx
from flight_deals_engine.jobs.refresh_calendar_prices import run
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.application.commands import RefreshCalendarPricesCommand, Scope
from flight_deals_engine.adapters.storage.in_memory_storage_writer import InMemoryStorageWriter


@patch("flight_deals_engine.adapters.search_backend.client.httpx.Client")
@patch("flight_deals_engine.jobs.refresh_calendar_prices.get_storage_writer")
def test_full_cycle_success(mock_get_writer, mock_http_client_cls):
    # 1. Setup Storage
    storage = InMemoryStorageWriter()
    mock_get_writer.return_value = storage

    # 2. Setup HTTP Client Mock
    mock_client = MagicMock()
    mock_http_client_cls.return_value.__enter__.return_value = mock_client

    # Mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "outbound": {
                    "id": "out1",
                    "airline": "TestAir",
                    "flightNumber": "TA123",
                    "originCode": "TLV",
                    "destinationCode": "LON",
                    "departureDate": "2023-11-15"
                },
                "price": 120.0,
                "currency": "USD",
                "deep_link": "http://link"
            },
            {
                "outbound": {
                    "id": "out2",
                    "airline": "TestAir",
                    "flightNumber": "TA124",
                    "originCode": "TLV",
                    "destinationCode": "LON",
                    "departureDate": "2023-11-16"
                },
                "price": 110.0, # Cheaper
                "currency": "USD",
                "deep_link": "http://link2"
            }
        ]
    }
    mock_client.post.return_value = mock_resp

    # 3. Setup Settings and Command
    # Pass required fields to constructor
    settings = Settings(
        _env_file=None,
        SEARCH_BACKEND_BASE_URL="http://test-api",
        STORAGE_ADAPTER="in_memory"
    )

    command = RefreshCalendarPricesCommand(
        jobType="refresh_calendar_prices",
        scope=Scope(
            origins=["TLV"],
            destinations=["LON"],
            monthsAhead=1
        )
    )

    # 4. Run Job
    result = run(settings, command)

    # 5. Verify Result
    assert result["status"] == "success"
    assert result["snapshots_written"] >= 1

    # 6. Verify Storage
    snapshots = storage.get_snapshots()
    assert len(snapshots) >= 1

    # Check if cheapest was selected (110.0 vs 120.0)
    # The planner generates 1 target for 1 month.
    # The mock returns 2 results for that target.
    # Cheapest is selected.

    snapshot = snapshots[0]
    assert snapshot.origin == "TLV"
    assert snapshot.destination == "LON"
    assert snapshot.cheapest_price == Decimal("110.0")
    assert snapshot.currency == "USD"
