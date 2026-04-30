from pydantic import BaseModel
from typing import Optional


class VideoUploadResponse(BaseModel):
    task_id: str
    session_id: int
    message: str = "Video uploaded. Processing started."


class VideoStatusResponse(BaseModel):
    task_id: str
    status: str          # "processing" | "complete" | "error"
    progress: int        # 0–100
    session_id: Optional[int] = None
    error: Optional[str] = None
