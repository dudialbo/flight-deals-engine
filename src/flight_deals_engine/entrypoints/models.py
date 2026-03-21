from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Scope(BaseModel):
    origins: List[str] = Field(default_factory=list)
    destinations: List[str] = Field(default_factory=list)
    months_ahead: Optional[int] = Field(default=None, alias="monthsAhead")


class RefreshCalendarPricesEvent(BaseModel):
    job_type: Literal["refresh_calendar_prices"] = Field(alias="jobType")
    run_id: Optional[str] = Field(default=None, alias="runId")
    scope: Optional[Scope] = None
