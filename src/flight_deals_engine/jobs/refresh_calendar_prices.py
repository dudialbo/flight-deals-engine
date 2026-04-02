import time
import logging
from datetime import date
from typing import List

from flight_deals_engine.domain.models import CalendarPriceSnapshot
from flight_deals_engine.domain.flight_selection import select_cheapest_flight
from flight_deals_engine.domain.snapshot_transformer import transform_to_snapshot
from flight_deals_engine.application.planner import RefreshPlanner
from flight_deals_engine.application.commands import RefreshCalendarPricesCommand
from flight_deals_engine.adapters.search_backend.client import SearchBackendHttpClient
from flight_deals_engine.adapters.storage.factory import get_storage_writer
from flight_deals_engine.config.settings import Settings

logger = logging.getLogger(__name__)

JOB_NAME = "refresh_calendar_prices"


def run(settings: Settings, command: RefreshCalendarPricesCommand) -> dict[str, object]:
    start_time = time.time()
    
    # 1. Initialize components
    planner = RefreshPlanner()
    search_client = SearchBackendHttpClient(
        base_url=settings.SEARCH_BACKEND_BASE_URL,
        timeout_seconds=settings.SEARCH_BACKEND_TIMEOUT_SECONDS,
    )
    writer = get_storage_writer(settings.STORAGE_ADAPTER, settings.S3_BUCKET_NAME)
    
    logger.info("Using storage adapter: %s", settings.STORAGE_ADAPTER)

    # 2. Plan targets
    origins = command.scope.origins if command.scope and command.scope.origins else [settings.DEFAULT_ORIGIN]
    destinations = command.scope.destinations if command.scope and command.scope.destinations else ["LON", "ROM", "PAR"]
    months_ahead = command.scope.months_ahead if command.scope and command.scope.months_ahead is not None else settings.DEFAULT_MONTHS_AHEAD

    logger.info("Starting job %s for origins=%s destinations=%s months=%s", JOB_NAME, origins, destinations, months_ahead)

    targets = []
    for origin in origins:
        targets.extend(planner.build_monthly_targets(
            origin=origin,
            destinations=destinations,
            start_date=date.today(),
            months_ahead=months_ahead,
            currency=settings.DEFAULT_CURRENCY,
        ))
    
    logger.info("Generated %d search targets", len(targets))

    # 3. Process targets
    snapshots: List[CalendarPriceSnapshot] = []
    requests_attempted = 0
    results_found = 0
    failures = 0
    
    for target in targets:
        try:
            requests_attempted += 1
            options = search_client.search_flights(target)
            
            if not options:
                continue
                
            cheapest = select_cheapest_flight(list(options))
            if cheapest:
                snapshot = transform_to_snapshot(cheapest, source_job=JOB_NAME)
                snapshots.append(snapshot)
                results_found += 1
                
        except Exception as e:
            failures += 1
            logger.error("Failed to process target %s: %s", target, str(e))
            # Continue to next target
            continue

    # 4. Write results
    if snapshots:
        logger.info("Writing %d snapshots", len(snapshots))
        writer.write_calendar_snapshots(snapshots)
        # If in-memory, maybe print? (Only in debug/local context)
        if settings.STORAGE_ADAPTER == "in_memory":
            logger.debug("Snapshots stored in memory: %s", snapshots)
    else:
        logger.info("No snapshots to write")

    duration_ms = int((time.time() - start_time) * 1000)
    
    result = {
        "job_name": JOB_NAME,
        "targets_planned": len(targets),
        "requests_attempted": requests_attempted,
        "results_found": results_found,
        "snapshots_written": len(snapshots),
        "failures": failures,
        "duration_ms": duration_ms,
        "status": "success" if failures == 0 else "partial_success"
    }
    
    logger.info("Job finished: %s", result)
    return result
