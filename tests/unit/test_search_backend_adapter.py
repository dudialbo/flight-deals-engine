from datetime import date
from unittest.mock import MagicMock, patch
from decimal import Decimal
import httpx
from flight_deals_engine.domain.models import RefreshTarget
from flight_deals_engine.adapters.search_backend.client import RateLimitError, SearchBackendHttpClient
from flight_deals_engine.adapters.search_backend.dtos import SearchBackendResponse, BackendFlightResult, FlightLeg, Layover, Segment
from flight_deals_engine.adapters.request_normalizer import normalize_request
from flight_deals_engine.adapters.response_normalizer import normalize_response


def test_normalize_request():
    target = RefreshTarget(
        origin="TLV",
        destination="LON",
        date_from=date(2023, 10, 1),
        date_to=date(2023, 10, 31),
        nights_min=3,
        nights_max=7,
        currency="USD",
        direct_only=True
    )
    
    req = normalize_request(target)
    
    assert req.origin == "TLV"
    assert req.destination == "LON"
    assert req.date_from == date(2023, 10, 1)
    assert req.date_to == date(2023, 10, 31)
    assert req.nights_in_dst_from == 3
    assert req.nights_in_dst_to == 7
    assert req.direct_only is True
    # verify return window is calculated
    assert req.return_from == date(2023, 10, 4) # 1 + 3
    assert req.return_to == date(2023, 11, 7) # 31 + 7


def test_normalize_response():
    resp_dto = SearchBackendResponse(results=[
        BackendFlightResult(
            outbound=FlightLeg(
                id="out1",
                airline="TestAir",
                flightNumber="TA123",
                originCode="TLV",
                destinationCode="LON",
                destinationCityCode="LON_CITY",
                departureDate=date(2023, 10, 15),
                stops=0
            ),
            return_leg=FlightLeg(
                id="ret1",
                airline="TestAir",
                flightNumber="TA456",
                originCode="LON",
                destinationCode="TLV",
                departureDate=date(2023, 10, 20),
                stops=1
            ),
            price=Decimal("150.00"),
            currency="USD",
            deep_link="http://link"
        )
    ])
    
    options = normalize_response(resp_dto)
    
    assert len(options) == 1
    opt = options[0]
    assert opt.origin == "TLV"
    assert opt.destination == "LON"
    assert opt.destination_code == "LON"  # airport code takes priority over city code
    assert opt.departure_date == date(2023, 10, 15)
    assert opt.return_date == date(2023, 10, 20)
    assert opt.price == Decimal("150.00")
    assert opt.currency == "USD"
    assert opt.provider_name == "TestAir"
    assert opt.airline == "TestAir"
    assert opt.stops == 1  # max(0, 1)


def test_normalize_response_computes_layover_from_segments() -> None:
    """Layover quality fields are derived from segments/layovers, not backend-provided totals."""
    resp_dto = SearchBackendResponse(results=[
        BackendFlightResult(
            outbound=FlightLeg(
                id="out1",
                airline="TestAir",
                flightNumber="TA123",
                originCode="TLV",
                destinationCode="BKK",
                departureDate=date(2026, 5, 23),
                stops=1,
                segments=[Segment(duration_seconds=11400), Segment(duration_seconds=23700)],  # 9h45m
                layovers=[Layover(duration="3h 0m")],  # 180 min
            ),
            return_leg=FlightLeg(
                id="ret1",
                airline="TestAir",
                flightNumber="TA456",
                originCode="BKK",
                destinationCode="TLV",
                departureDate=date(2026, 5, 28),
                stops=1,
                segments=[Segment(duration_seconds=23400), Segment(duration_seconds=12300)],  # 9h55m
                layovers=[Layover(duration="2h 0m")],  # 120 min
            ),
            price=Decimal("793.00"),
            currency="USD",
            deep_link="http://link",
        )
    ])

    options = normalize_response(resp_dto)
    opt = options[0]

    # Worst leg is outbound: 585 min flight, 180 min layover (30.7%)
    assert opt.total_duration_minutes == 585
    assert opt.layover_duration_minutes == 180
    # stops = max(1, 1) = 1
    assert opt.stops == 1


def test_normalize_response_bad_layover_detected() -> None:
    """A flight with layover exceeding 50% of flight time is correctly flagged."""
    resp_dto = SearchBackendResponse(results=[
        BackendFlightResult(
            outbound=FlightLeg(
                id="out1",
                airline="BadAir",
                flightNumber="BA1",
                originCode="TLV",
                destinationCode="MIA",
                departureDate=date(2026, 9, 2),
                stops=2,
                # 14h35m total flight
                segments=[Segment(duration_seconds=26100), Segment(duration_seconds=26400)],
                layovers=[Layover(duration="19h 5m")],  # 1145 min — way over 50%
            ),
            return_leg=None,
            price=Decimal("785.00"),
            currency="USD",
            deep_link="http://link",
        )
    ])

    options = normalize_response(resp_dto)
    opt = options[0]

    # 875 min flight, 1145 min layover → 130% — should fail passes_layover_quality
    assert opt.total_duration_minutes == 875
    assert opt.layover_duration_minutes == 1145

    from flight_deals_engine.domain.deal_filters import passes_layover_quality
    assert passes_layover_quality(opt) is False


@patch("flight_deals_engine.adapters.search_backend.client.httpx.Client")
def test_search_backend_client_success(mock_client_cls):
    mock_client = MagicMock()
    # Mock context manager
    mock_client_cls.return_value.__enter__.return_value = mock_client
    
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
                    "departureDate": "2023-10-15",
                    "stops": 0
                },
                "return": {
                    "id": "ret1",
                    "airline": "TestAir",
                    "flightNumber": "TA456",
                    "originCode": "LON",
                    "destinationCode": "TLV",
                    "departureDate": "2023-10-20",
                    "stops": 0
                },
                "price": 150.0,
                "currency": "USD",
                "deep_link": "http://link"
            }
        ]
    }
    mock_client.post.return_value = mock_resp
    
    client = SearchBackendHttpClient("http://api", 5)
    target = RefreshTarget(
        origin="TLV",
        destination="LON",
        date_from=date(2023, 10, 1),
        date_to=date(2023, 10, 31),
        nights_min=3,
        nights_max=7,
        direct_only=True
    )
    
    results = client.search_flights(target)
    
    assert len(results) == 1
    assert results[0].price == Decimal("150.0")
    assert results[0].stops == 0
    
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert args[0] == "http://api/search/flights"
    payload = kwargs["json"]
    assert payload["origin"] == "TLV"
    assert payload["destination"] == "LON"
    assert payload["direct_only"] is True


@patch("flight_deals_engine.adapters.search_backend.client.httpx.Client")
def test_search_backend_client_request_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    
    mock_client.post.side_effect = httpx.RequestError("Connection failed")
    
    client = SearchBackendHttpClient("http://api", 5)
    target = RefreshTarget(
        origin="TLV",
        destination="LON",
        date_from=date(2023, 10, 1),
        date_to=date(2023, 10, 31)
    )
    
    results = client.search_flights(target)
    
    assert results == []

@patch("flight_deals_engine.adapters.search_backend.client.httpx.Client")
def test_search_backend_client_http_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    # Raise HTTPStatusError when raise_for_status is called
    error = httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_resp)
    mock_resp.raise_for_status.side_effect = error
    
    mock_client.post.return_value = mock_resp
    
    client = SearchBackendHttpClient("http://api", 5)
    target = RefreshTarget(
        origin="TLV",
        destination="LON",
        date_from=date(2023, 10, 1),
        date_to=date(2023, 10, 31)
    )
    
    results = client.search_flights(target)

    assert results == []


@patch("flight_deals_engine.adapters.search_backend.client.time.sleep")
@patch("flight_deals_engine.adapters.search_backend.client.httpx.Client")
def test_search_backend_rate_limit_retries_then_raises(
    mock_client_cls: MagicMock, mock_sleep: MagicMock
) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {}
    mock_client.post.return_value = mock_resp

    client = SearchBackendHttpClient("http://api", 5, max_retries=2, retry_backoff_seconds=1.0)
    target = RefreshTarget(
        origin="TLV", destination="LON",
        date_from=date(2023, 10, 1), date_to=date(2023, 10, 31),
    )

    import pytest
    with pytest.raises(RateLimitError):
        client.search_flights(target)

    # 2 retries → 2 sleeps (1s, 2s)
    assert mock_sleep.call_count == 2
    assert mock_client.post.call_count == 3   # initial + 2 retries


@patch("flight_deals_engine.adapters.search_backend.client.time.sleep")
@patch("flight_deals_engine.adapters.search_backend.client.httpx.Client")
def test_search_backend_rate_limit_respects_retry_after_header(
    mock_client_cls: MagicMock, mock_sleep: MagicMock
) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client

    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.headers = {"Retry-After": "5"}

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"results": []}

    mock_client.post.side_effect = [mock_429, mock_200]

    client = SearchBackendHttpClient("http://api", 5, max_retries=2, retry_backoff_seconds=1.0)
    target = RefreshTarget(
        origin="TLV", destination="LON",
        date_from=date(2023, 10, 1), date_to=date(2023, 10, 31),
    )

    result = client.search_flights(target)

    assert result == []
    mock_sleep.assert_called_once_with(5.0)   # used Retry-After, not backoff
