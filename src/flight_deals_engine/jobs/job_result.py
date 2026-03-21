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
