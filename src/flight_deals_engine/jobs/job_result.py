from typing import Literal
from pydantic import BaseModel


class JobResult(BaseModel):
    job_name: str
    targets_planned: int
    requests_attempted: int
    results_found: int
    snapshots_written: int
    failures: int
    duration_ms: int
    status: str = "success"


class CategoryResult(BaseModel):
    category_id: str
    status: Literal["success", "partial", "failed", "empty"]
    items_written: int = 0
    destinations_skipped: int = 0
    reason: str | None = None


class DealRefreshResult(BaseModel):
    job_name: str
    categories_attempted: int
    categories_written: int
    categories_failed: int
    category_results: list[CategoryResult]
    manifest_written: bool
    duration_ms: int