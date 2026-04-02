import json
import logging
import time
from datetime import datetime, timezone

from flight_deals_engine.adapters.search_backend.client import SearchBackendHttpClient
from flight_deals_engine.adapters.storage.factory import get_storage_writer
from flight_deals_engine.application.category_registry import get_category_configs
from flight_deals_engine.application.deal_refresh_service import DealRefreshService
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.domain.hot_deal_scorer import DealRanker
from flight_deals_engine.domain.models import CategoryMeta, CategoryPayload, ManifestCategory, ManifestPayload
from flight_deals_engine.jobs.job_result import CategoryResult, DealRefreshResult

logger = logging.getLogger(__name__)

JOB_NAME = "refresh_deal_categories"


def _validate_category_payload(payload: dict[str, object]) -> str | None:
    """Returns an error message if validation fails, None if valid."""
    try:
        json.dumps(payload)
    except (TypeError, ValueError) as e:
        return f"Not JSON-serialisable: {e}"

    category = payload.get("category")
    if not isinstance(category, dict):
        return "Missing or invalid 'category' metadata"
    for field in ("id", "title", "generated_at"):
        if not category.get(field):
            return f"Missing required category field: {field}"

    items = payload.get("items")
    if not isinstance(items, list):
        return "Missing 'items' list"

    seen_ids: set[str] = set()
    today_str = datetime.now(timezone.utc).date().isoformat()
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return f"Item {i} is not a dict"
        if not item.get("destination_code") and not item.get("destination_name"):
            return f"Item {i} missing destination_code/destination_name"
        price = item.get("price")
        if price is None or float(price) <= 0:
            return f"Item {i} has invalid price"
        if not item.get("currency"):
            return f"Item {i} missing currency"
        dep_date = item.get("departure_date") or item.get("departureDate")
        if not dep_date or str(dep_date) <= today_str:
            return f"Item {i} departure_date is not in the future"
        deal_id = str(item.get("deal_id") or item.get("dealId") or "")
        if deal_id in seen_ids:
            return f"Duplicate deal_id: {deal_id}"
        seen_ids.add(deal_id)

    return None


def run(settings: Settings) -> dict[str, object]:
    start_time = time.time()

    search_client = SearchBackendHttpClient(
        base_url=settings.SEARCH_BACKEND_BASE_URL,
        timeout_seconds=settings.SEARCH_BACKEND_TIMEOUT_SECONDS,
        max_retries=settings.SEARCH_BACKEND_MAX_RETRIES,
        retry_backoff_seconds=settings.SEARCH_BACKEND_RETRY_BACKOFF_SECONDS,
    )
    ranker = DealRanker()
    service = DealRefreshService(
        search_client,
        ranker,
        request_delay_seconds=settings.SEARCH_BACKEND_REQUEST_DELAY_SECONDS,
    )
    writer = get_storage_writer(settings.STORAGE_ADAPTER, settings.S3_BUCKET_NAME)

    configs = get_category_configs(settings)
    logger.info("Starting %s for %d categories", JOB_NAME, len(configs))

    category_results: list[CategoryResult] = []
    manifest_categories: list[ManifestCategory] = []
    manifest_written = False

    for config in configs:
        logger.info("Processing category: %s", config.id)
        try:
            items, destinations_skipped = service.generate_category(config, settings.DEFAULT_ORIGIN, settings.DEFAULT_CURRENCY)
        except Exception as e:
            logger.exception("Failed to generate category %s", config.id)
            category_results.append(CategoryResult(
                category_id=config.id,
                status="failed",
                reason=str(e),
            ))
            continue

        if not items:
            logger.info("Category %s produced no items", config.id)
            category_results.append(CategoryResult(
                category_id=config.id,
                status="empty",
                items_written=0,
            ))
            continue

        now = datetime.now(timezone.utc)
        payload = CategoryPayload(
            category=CategoryMeta(
                id=config.id,
                title=config.title,
                subtitle=config.subtitle,
                generated_at=now,
                item_count=len(items),
            ),
            items=items,
        )
        payload_dict = payload.model_dump(mode="json")

        error = _validate_category_payload(payload_dict)
        if error:
            logger.error("Validation failed for category %s: %s", config.id, error)
            category_results.append(CategoryResult(
                category_id=config.id,
                status="failed",
                reason=error,
            ))
            continue

        try:
            writer.write_category(config.id, payload_dict)
        except Exception as e:
            logger.exception("Failed to write category %s", config.id)
            category_results.append(CategoryResult(
                category_id=config.id,
                status="failed",
                reason=str(e),
            ))
            continue

        category_status = "partial" if destinations_skipped > 0 else "success"
        category_results.append(CategoryResult(
            category_id=config.id,
            status=category_status,
            items_written=len(items),
            destinations_skipped=destinations_skipped,
        ))
        manifest_categories.append(ManifestCategory(
            category_id=config.id,
            item_count=len(items),
            generated_at=now,
            status=category_status,
            destinations_skipped=destinations_skipped,
        ))
        logger.info("Category %s written with %d items", config.id, len(items))

    # Write manifest for successfully written categories
    try:
        manifest = ManifestPayload(
            generated_at=datetime.now(timezone.utc),
            categories=manifest_categories,
        )
        writer.write_manifest(manifest.model_dump(mode="json"))
        manifest_written = True
    except Exception:
        logger.exception("Failed to write manifest")

    categories_written = sum(1 for r in category_results if r.status == "success")
    categories_failed = sum(1 for r in category_results if r.status == "failed")

    result = DealRefreshResult(
        job_name=JOB_NAME,
        categories_attempted=len(configs),
        categories_written=categories_written,
        categories_failed=categories_failed,
        category_results=category_results,
        manifest_written=manifest_written,
        duration_ms=int((time.time() - start_time) * 1000),
    )

    logger.info("Job finished: %s", result)
    return result.model_dump()