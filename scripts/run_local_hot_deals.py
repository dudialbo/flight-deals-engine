import logging
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.jobs.refresh_hot_deals import run
from flight_deals_engine.observability.logging import configure_logging


if __name__ == "__main__":
    # Force DEBUG logging for local run to see requests and decisions
    configure_logging("DEBUG")

    settings = Settings()
    # Explicitly use in-memory adapter so we don't accidentally write to prod if env is misconfigured
    settings.STORAGE_ADAPTER = "json"

    print("Running Hot Deals Refresh locally...")
    result = run(settings)
    print("\n--- Job Result ---")
    print(result)
