from datetime import date

from flight_deals_engine.config.settings import Settings
from flight_deals_engine.domain.models import DealCategoryConfig

# Shared destination pools
HOT_DEALS_DESTINATIONS = [
    "LON", "PAR", "ATH", "ROM", "MAD", "BCN",
    "RHO", "HER", "AMS", "BUD", "VIE", "LIS", "BER",
]

SUMMER_DESTINATIONS = [
    "RHO",   # Rhodes
    "HER",   # Crete (Heraklion)
    "JMK",   # Mykonos
    "LCA",   # Larnaca
    "PFO",   # Paphos
    "BUS",   # Batumi
]

CHEAP_FLIGHTS_DESTINATIONS = [
    "LON", "PAR", "ATH", "ROM", "MAD", "BCN", "RHO", "HER",
    "AMS", "BUD", "VIE", "LIS", "BER", "PRG", "WAW", "BRU",
    "CPH", "ARN", "DUB", "EDI", "MXP",
]

USA_DESTINATIONS = [
    "JFK",   # New York JFK
    "EWR",   # New York Newark
    "LGA",   # New York LaGuardia
    "MIA",   # Miami
    "FLL",   # Fort Lauderdale (Miami area)
    "LAX",   # Los Angeles
    "LAS",   # Las Vegas
]

TROPICAL_DESTINATIONS = [
    "BKK",   # Bangkok
    "HKT",   # Phuket
    "MLE",   # Maldives
    "SEZ",   # Seychelles
]


def get_category_configs(settings: Settings) -> list[DealCategoryConfig]:
    today = date.today()
    current_year = today.year

    summer_start = date(current_year, 6, 1)
    summer_end = date(current_year, 8, 31)
    summer_active = today <= summer_end

    configs: list[DealCategoryConfig] = []

    # 1. Hot Deals
    configs.append(DealCategoryConfig(
        id="hot_deals",
        title="Hot Deals",
        subtitle="Cheapest direct flights in the next 3 months",
        destinations=settings.HOT_DEALS_DESTINATIONS or HOT_DEALS_DESTINATIONS,
        date_horizon_days=90,
        nights_min=4,
        nights_max=5,
        direct_only=True,
        layover_filter=False,
        max_items=20,
        selection_mode="cheapest_per_destination",
        ranking_mode="price",
    ))

    # 2. Summer Deals — only active while today <= Aug 31
    if summer_active:
        configs.append(DealCategoryConfig(
            id="summer_deals",
            title="Summer Deals",
            subtitle="Best direct flights for summer 2026",
            destinations=SUMMER_DESTINATIONS,
            date_from=summer_start if today < summer_start else today,
            date_to=summer_end,
            nights_min=4,
            nights_max=6,
            direct_only=True,
            layover_filter=False,
            max_items=20,
            selection_mode="cheapest_per_destination",
            ranking_mode="price",
        ))

    # 3. Cheap Flights — up to 1 stop, layover quality enforced
    configs.append(DealCategoryConfig(
        id="cheap_flights",
        title="Cheap Flights",
        subtitle="Best value flights including one-stop options",
        destinations=CHEAP_FLIGHTS_DESTINATIONS,
        date_horizon_days=120,
        nights_min=3,
        nights_max=5,
        direct_only=False,
        layover_filter=True,
        max_stops=1,
        max_items=20,
        selection_mode="best_overall",
        ranking_mode="price",
    ))

    # 4. USA
    configs.append(DealCategoryConfig(
        id="usa",
        title="USA",
        subtitle="Flights to the United States",
        destinations=USA_DESTINATIONS,
        date_horizon_days=180,
        nights_min=8,
        nights_max=14,
        direct_only=False,
        layover_filter=True,
        max_stops=1,
        max_items=20,
        selection_mode="best_overall",
        ranking_mode="price",
    ))

    # 5. Tropical Escapes
    configs.append(DealCategoryConfig(
        id="tropical_escapes",
        title="Tropical Escapes",
        subtitle="Long-haul flights to tropical destinations",
        destinations=TROPICAL_DESTINATIONS,
        date_horizon_days=180,
        nights_min=8,
        nights_max=14,
        direct_only=False,
        layover_filter=True,
        max_stops=1,
        max_items=20,
        selection_mode="best_overall",
        ranking_mode="price",
    ))

    return configs