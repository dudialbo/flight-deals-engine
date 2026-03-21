from flight_deals_engine.config.settings import Settings
from flight_deals_engine.jobs import refresh_calendar_prices, refresh_hot_deals
from flight_deals_engine.observability.logging import configure_logging
from flight_deals_engine.application.commands import RefreshCalendarPricesCommand


def lambda_handler(event: dict, context: object) -> dict:
    _ = context
    settings = Settings()
    configure_logging(settings.LOG_LEVEL)

    job_type = event.get("jobType", refresh_calendar_prices.JOB_NAME)

    if job_type == refresh_calendar_prices.JOB_NAME:
        # Pydantic will validate the event structure
        command = RefreshCalendarPricesCommand.model_validate(event)
        return refresh_calendar_prices.run(settings, command)

    if job_type == refresh_hot_deals.JOB_NAME:
        return refresh_hot_deals.run(settings)

    raise ValueError(f"Unknown jobType: {job_type}")
