import logging
import time
import httpx
from collections.abc import Sequence
from flight_deals_engine.domain.models import FlightOption, RefreshTarget
from flight_deals_engine.adapters.request_normalizer import normalize_request
from flight_deals_engine.adapters.response_normalizer import normalize_response
from flight_deals_engine.adapters.search_backend.dtos import SearchBackendResponse

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when the search backend returns HTTP 429 and retries are exhausted."""


class SearchBackendHttpClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    def search_flights(self, target: RefreshTarget) -> Sequence[FlightOption]:
        url = f"{self._base_url}/search/flights"
        request_dto = normalize_request(target)
        payload = request_dto.model_dump(mode="json", exclude_none=True)
        logger.debug("Calling search backend: %s payload=%s", url, payload)

        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    response = client.post(url, json=payload)

                    if response.status_code == 429:
                        wait = self._backoff_wait(response, attempt)
                        if attempt < self._max_retries:
                            logger.warning(
                                "Rate limited (429) for %s->%s, retrying in %.1fs "
                                "(attempt %d/%d)",
                                target.origin, target.destination,
                                wait, attempt + 1, self._max_retries,
                            )
                            time.sleep(wait)
                            continue
                        raise RateLimitError(
                            f"Rate limit exhausted after {self._max_retries} retries "
                            f"for {target.origin}->{target.destination}"
                        )

                    response.raise_for_status()

                    data = response.json()
                    if isinstance(data, list):
                        response_dto = SearchBackendResponse(results=data)
                    else:
                        response_dto = SearchBackendResponse.model_validate(data)

                    return normalize_response(response_dto)

            except RateLimitError:
                raise
            except httpx.HTTPStatusError as e:
                logger.error(
                    "Search backend returned error: %s response=%s",
                    e.response.status_code,
                    e.response.text,
                )
                return []
            except httpx.RequestError as e:
                logger.error("Search backend request failed: %s", str(e))
                return []
            except Exception:
                logger.exception("Unexpected error in search backend adapter")
                return []

        # unreachable — loop always returns or raises
        raise RateLimitError(f"Rate limit exhausted for {target.origin}->{target.destination}")

    def _backoff_wait(self, response: httpx.Response, attempt: int) -> float:
        """Return seconds to wait: use Retry-After header if present, else exponential backoff."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self._retry_backoff_seconds * float(2 ** attempt)