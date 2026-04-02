from flight_deals_engine.config.settings import Settings
from flight_deals_engine.jobs import refresh_deal_categories

JOB_NAME = "refresh_hot_deals"


def run(settings: Settings) -> dict[str, object]:
    # Delegate entirely to the generic job — hot-deals is now just one category
    return refresh_deal_categories.run(settings)