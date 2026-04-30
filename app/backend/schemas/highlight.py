from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HighlightClipMeta(BaseModel):
    id: int
    session_id: int
    user_id: int
    file_path: str
    duration_s: Optional[float]
    shot_frame: Optional[int]
    thumbnail_path: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
