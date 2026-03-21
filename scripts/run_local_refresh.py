import logging
from flight_deals_engine.config.settings import Settings
from flight_deals_engine.jobs.refresh_calendar_prices import run
from flight_deals_engine.application.commands import RefreshCalendarPricesCommand
from flight_deals_engine.observability.logging import configure_logging


if __name__ == "__main__":
    # Force DEBUG logging for local run
    configure_logging("DEBUG")
    
    settings = Settings()
    # Ensure settings also use DEBUG if loaded from env, but configure_logging above overrides it for the root logger

    command = RefreshCalendarPricesCommand(jobType="refresh_calendar_prices")
    print(run(settings, command))
