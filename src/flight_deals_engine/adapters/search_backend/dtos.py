from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SearchBackendRequest(BaseModel):
    origin: str
    destination: str
    date_from: date
    date_to: date
    # Optional return window
    return_from: Optional[date] = None
    return_to: Optional[date] = None
    
    nights_in_dst_from: Optional[int] = None
    nights_in_dst_to: Optional[int] = None
    
    passengers: int = 1
    limit: int = 100
    
    direct_only: Optional[bool] = None


class FlightLeg(BaseModel):
    id: Optional[str] = None
    airline: Optional[str] = None
    airlineCode: Optional[str] = None
    airlineLogo: Optional[str] = None
    flightNumber: Optional[str] = None
    originCode: Optional[str] = None
    destinationCode: Optional[str] = None
    destinationCityCode: Optional[str] = None
    departureDate: date
    stops: int = 0


class BackendFlightResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    outbound: FlightLeg
    return_leg: Optional[FlightLeg] = Field(alias="return", default=None)
    price: Decimal
    currency: str
    deep_link: str


class SearchBackendResponse(BaseModel):
    results: List[BackendFlightResult]
