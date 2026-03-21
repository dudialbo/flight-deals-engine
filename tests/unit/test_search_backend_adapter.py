from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from decimal import Decimal
import httpx
from flight_deals_engine.domain.models import RefreshTarget, FlightOption
from flight_deals_engine.adapters.search_backend.client import SearchBackendHttpClient
from flight_deals_engine.adapters.search_backend.dtos import SearchBackendRequest, SearchBackendResponse, BackendFlightResult, FlightLeg
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
    assert opt.destination_code == "LON_CITY"
    assert opt.departure_date == date(2023, 10, 15)
    assert opt.return_date == date(2023, 10, 20)
    assert opt.price == Decimal("150.00")
    assert opt.currency == "USD"
    assert opt.provider_name == "TestAir"
    assert opt.airline == "TestAir"
    assert opt.stops == 1 # 0 + 1


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
