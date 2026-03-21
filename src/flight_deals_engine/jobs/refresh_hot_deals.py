import time
import logging
import httpx
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.application.hot_deals_service import HotDealsRefreshService
from flight_deals_engine.domain.hot_deal_scorer import HotDealScorer
from flight_deals_engine.adapters.search_backend.client import SearchBackendHttpClient
from flight_deals_engine.adapters.storage.factory import get_storage_writer

logger = logging.getLogger(__name__)

JOB_NAME = "refresh_hot_deals"


def run(settings: Settings) -> dict:
    start_time = time.time()
    
    # 1. Initialize components
    search_client = SearchBackendHttpClient(
        base_url=settings.SEARCH_BACKEND_BASE_URL,
        timeout_seconds=settings.SEARCH_BACKEND_TIMEOUT_SECONDS,
    )
    scorer = HotDealScorer()
    service = HotDealsRefreshService(search_client, scorer)
    writer = get_storage_writer(settings.STORAGE_ADAPTER, settings.S3_BUCKET_NAME)
    
    logger.info(
        "Starting job %s for origin=%s destinations=%s",
        JOB_NAME, settings.DEFAULT_ORIGIN, settings.HOT_DEALS_DESTINATIONS
    )

    # 2. Process destinations
    all_deals = []
    destinations_succeeded = 0
    destinations_failed = 0
    destinations_empty = 0

    for destination in settings.HOT_DEALS_DESTINATIONS:
        try:
            logger.debug("Processing destination: %s", destination)
            target = service.build_target(settings.DEFAULT_ORIGIN, destination, settings)

            best_deal = service.fetch_and_select_best(target)

            if best_deal:
                candidate = service.transform_to_candidate(best_deal)
                all_deals.append(candidate)
                destinations_succeeded += 1
                logger.info("Found best deal for %s: %s", destination, best_deal.price)
            else:
                destinations_empty += 1
                logger.info("No deals found for %s", destination)

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            destinations_failed += 1
            logger.error("Failed to fetch deals for destination %s: %s", destination, str(e))
            continue
        except Exception:
            destinations_failed += 1
            logger.exception("An unexpected error occurred for destination %s", destination)
            continue

    # 3. Rank and persist
    ranked_deals = service.rank_deals(all_deals)

    if ranked_deals:
        logger.info("Writing %d ranked hot deals", len(ranked_deals))
        writer.write_hot_deals(ranked_deals)
    else:
        logger.info("No deals to write.")

    duration_ms = int((time.time() - start_time) * 1000)

    result = {
        "job_name": JOB_NAME,
        "total_destinations": len(settings.HOT_DEALS_DESTINATIONS),
        "destinations_succeeded": destinations_succeeded,
        "destinations_empty": destinations_empty,
        "destinations_failed": destinations_failed,
        "deals_persisted": len(ranked_deals),
        "duration_ms": duration_ms,
    }
    
    logger.info("Job finished: %s", result)
    return result
