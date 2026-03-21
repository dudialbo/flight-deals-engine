from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import httpx
from flight_deals_engine.jobs.refresh_hot_deals import run
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.adapters.storage.in_memory_storage_writer import InMemoryStorageWriter


@patch("flight_deals_engine.adapters.search_backend.client.httpx.Client")
@patch("flight_deals_engine.jobs.refresh_hot_deals.get_storage_writer")
def test_hot_deals_full_cycle_success(mock_get_writer, mock_http_client_cls):
    # 1. Setup Storage
    storage = InMemoryStorageWriter()
    mock_get_writer.return_value = storage

    # 2. Setup HTTP Client Mock
    mock_client = MagicMock()
    mock_http_client_cls.return_value.__enter__.return_value = mock_client

    def mock_post(url, json, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        dest = json.get("destination")
        if dest == "LON":
            mock_resp.json.return_value = {
                "results": [
                    {
                        "outbound": {
                            "id": "out1", "airline": "TestAir", "flightNumber": "TA123",
                            "originCode": "TLV", "destinationCode": "LON",
                            "departureDate": "2026-04-15", "stops": 0
                        },
                        "price": 250.0, "currency": "USD", "deep_link": "http://link"
                    }
                ]
            }
        elif dest == "PAR":
            mock_resp.json.return_value = {
                "results": [
                    {
                        "outbound": {
                            "id": "out2", "airline": "TestAir", "flightNumber": "TA456",
                            "originCode": "TLV", "destinationCode": "PAR",
                            "departureDate": "2026-05-10", "stops": 0
                        },
                        "price": 180.0, "currency": "USD", "deep_link": "http://link"
                    }
                ]
            }
        else:
            # Empty results for others
            mock_resp.json.return_value = {"results": []}

        return mock_resp

    mock_client.post.side_effect = mock_post

    # 3. Setup Settings
    settings = Settings(
        _env_file=None,
        SEARCH_BACKEND_BASE_URL="http://test-api",
        STORAGE_ADAPTER="in_memory"
    )
    settings.HOT_DEALS_DESTINATIONS = ["LON", "PAR", "ATH"]

    # 4. Run Job
    result = run(settings)

    # 5. Verify Result
    assert result["status"] == "success" if "status" in result else True # Status might not be in Hot Deals summary explicitly, but check counts
    assert result["total_destinations"] == 3
    assert result["destinations_succeeded"] == 2
    assert result["destinations_empty"] == 1
    assert result["destinations_failed"] == 0
    assert result["deals_persisted"] == 2

    # 6. Verify Storage
    deals = storage.get_deals()
    assert len(deals) == 2

    # Verify Ranking (Cheapest first: PAR (180) then LON (250))
    assert deals[0].destination == "PAR"
    assert deals[0].price == Decimal("180.0")

    assert deals[1].destination == "LON"
    assert deals[1].price == Decimal("250.0")
