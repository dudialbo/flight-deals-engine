from decimal import Decimal
from unittest.mock import MagicMock, patch

from flight_deals_engine.adapters.storage.in_memory_storage_writer import InMemoryStorageWriter
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.jobs.refresh_deal_categories import run


@patch("flight_deals_engine.adapters.search_backend.client.httpx.Client")
@patch("flight_deals_engine.jobs.refresh_deal_categories.get_storage_writer")
def test_hot_deals_full_cycle_success(
    mock_get_writer: MagicMock,
    mock_http_client_cls: MagicMock,
) -> None:
    # 1. Setup Storage
    storage = InMemoryStorageWriter()
    mock_get_writer.return_value = storage

    # 2. Setup HTTP Client Mock
    mock_client = MagicMock()
    mock_http_client_cls.return_value.__enter__.return_value = mock_client

    def mock_post(url: str, json: dict, **kwargs: object) -> MagicMock:  # type: ignore[type-arg]
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
            mock_resp.json.return_value = {"results": []}

        return mock_resp  # type: ignore[return-value]

    mock_client.post.side_effect = mock_post

    # 3. Setup Settings
    settings = Settings(
        _env_file=None,
        SEARCH_BACKEND_BASE_URL="http://test-api",
        STORAGE_ADAPTER="in_memory",
    )
    settings.HOT_DEALS_DESTINATIONS = ["LON", "PAR", "ATH"]

    # 4. Run Job
    result = run(settings)

    # 5. Verify result shape
    assert result["job_name"] == "refresh_deal_categories"
    assert result["categories_written"] >= 1
    assert result["manifest_written"] is True

    # 6. Verify storage — category payload written
    payload = storage.get_category("hot_deals")
    assert payload is not None
    items = payload["items"]
    assert len(items) == 2

    # Verify ranking (cheapest first: PAR=180, LON=250)
    assert items[0]["destination_code"] == "PAR"
    assert Decimal(str(items[0]["price"])) == Decimal("180.0")

    assert items[1]["destination_code"] == "LON"
    assert Decimal(str(items[1]["price"])) == Decimal("250.0")

    # Manifest lists hot-deals
    assert storage.manifest is not None
    assert any(c["category_id"] == "hot_deals" for c in storage.manifest["categories"])

    mock_get_writer.assert_called_once_with("in_memory", None)