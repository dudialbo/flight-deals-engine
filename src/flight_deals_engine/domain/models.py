from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, Field


class RefreshTarget(BaseModel):
    origin: str
    destination: str | None = None
    destination_country: str | None = None
    date_from: date
    date_to: date
    nights_min: int | None = None
    nights_max: int | None = None
    direct_only: bool = False
    currency: str = "USD"


class FlightOption(BaseModel):
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    price: Decimal
    currency: str
    deeplink: Optional[str] = None
    provider_name: Optional[str] = None

    stops: int = 0
    airline: Optional[str] = None
    destination_code: Optional[str] = None
    destination_name: Optional[str] = None   # text name from backend e.g. "Bangkok"
    total_duration_minutes: int | None = None
    layover_duration_minutes: int | None = None


class CalendarPriceSnapshot(BaseModel):
    snapshot_key: str
    origin: str
    destination: str
    month: str
    cheapest_price: Decimal
    currency: str
    discovered_at: datetime
    source_job: str


class DealCategoryConfig(BaseModel):
    id: str
    title: str
    subtitle: str | None = None
    destinations: list[str] | None = None
    date_horizon_days: int = 180
    nights_min: int | None = None
    nights_max: int | None = None
    direct_only: bool = False
    price_max: Decimal | None = None
    departure_days: list[int] | None = None    # weekday() integers, 0=Mon
    return_days: list[int] | None = None        # weekday() integers, 0=Mon
    departure_months: list[int] | None = None   # month integers, 1=Jan … 12=Dec
    date_from: date | None = None              # fixed window start (overrides today)
    date_to: date | None = None                # fixed window end (overrides horizon)
    max_stops: int | None = None               # None = no limit; 1 = up to 1 stop
    layover_filter: bool = False               # apply passes_layover_quality() when True
    max_items: int = 20
    selection_mode: Literal["cheapest_per_destination", "best_overall"]
    ranking_mode: Literal["price", "weekend", "value"] = "price"


class DealItem(BaseModel):
    deal_id: str
    origin: str
    destination_code: str | None = None
    destination_name: str | None = None
    price: Decimal
    currency: str
    score: float = Field(ge=0)
    discovered_at: datetime
    deeplink: str | None = None
    departure_date: date
    return_date: date | None = None
    nights: int | None = None        # (return_date - departure_date).days
    direct: bool = False             # derived from stops == 0
    stops: int = 0
    airline: str | None = None
    category_id: str | None = None


class CategoryMeta(BaseModel):
    id: str
    title: str
    subtitle: str | None = None
    generated_at: datetime
    item_count: int


class CategoryPayload(BaseModel):
    category: CategoryMeta
    items: list[DealItem]


class ManifestCategory(BaseModel):
    category_id: str
    item_count: int
    generated_at: datetime
    status: Literal["success", "partial", "failed", "empty"]
    destinations_skipped: int = 0


class ManifestPayload(BaseModel):
    generated_at: datetime
    categories: list[ManifestCategory]