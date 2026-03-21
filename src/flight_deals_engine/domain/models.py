from datetime import date, datetime
from decimal import Decimal
from typing import Optional
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

    # New fields for Hot Deals
    stops: int = 0
    airline: Optional[str] = None
    destination_code: Optional[str] = None


class CalendarPriceSnapshot(BaseModel):
    snapshot_key: str
    origin: str
    destination: str
    month: str
    cheapest_price: Decimal
    currency: str
    discovered_at: datetime
    source_job: str


class HotDealCandidate(BaseModel):
    deal_id: str
    origin: str
    destination: str  # e.g., 'LON' or display name
    price: Decimal
    currency: str
    score: float = Field(ge=0)
    discovered_at: datetime
    deeplink: Optional[str] = None

    # New required fields for Hot Deals frontend
    departure_date: date
    return_date: Optional[date] = None
    stops: int = 0
    airline: Optional[str] = None
