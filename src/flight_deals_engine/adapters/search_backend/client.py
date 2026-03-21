import logging
import httpx
from collections.abc import Sequence
from flight_deals_engine.domain.models import FlightOption, RefreshTarget
from flight_deals_engine.adapters.request_normalizer import normalize_request
from flight_deals_engine.adapters.response_normalizer import normalize_response
from flight_deals_engine.adapters.search_backend.dtos import SearchBackendResponse

logger = logging.getLogger(__name__)


class SearchBackendHttpClient:
    def __init__(self, base_url: str, timeout_seconds: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def search_flights(self, target: RefreshTarget) -> Sequence[FlightOption]:
        url = f"{self._base_url}/search/flights"
        
        request_dto = normalize_request(target)
        payload = request_dto.model_dump(mode="json", exclude_none=True)
        
        logger.debug("Calling search backend: %s payload=%s", url, payload)
        
        try:
            with httpx.Client(timeout=self._timeout_seconds) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                # Wrap list in object for response model validation if response is just a list
                if isinstance(data, list):
                    response_dto = SearchBackendResponse(results=data)
                else:
                    # If response is {"results": [...]}, parse directly
                    response_dto = SearchBackendResponse.model_validate(data)
                
                return normalize_response(response_dto)
                
        except httpx.HTTPStatusError as e:
            logger.error(
                "Search backend returned error: %s response=%s", 
                e.response.status_code, 
                e.response.text
            )
            return []
        except httpx.RequestError as e:
            logger.error("Search backend request failed: %s", str(e))
            return []
        except Exception as e:
            logger.exception("Unexpected error in search backend adapter")
            return []
