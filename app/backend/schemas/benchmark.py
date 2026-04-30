from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BenchmarkCreate(BaseModel):
    benchmark_type: str   # spot_shooting_pct|free_throw_streak|mikan_60s_makes|pull_up_20|sprint_17s
    value: float
    session_id: Optional[int] = None
    notes: Optional[str] = None


class BenchmarkEntry(BaseModel):
    id: int
    user_id: int
    session_id: Optional[int]
    benchmark_type: str
    value: float
    recorded_at: datetime
    notes: Optional[str]

    model_config = {"from_attributes": True}
