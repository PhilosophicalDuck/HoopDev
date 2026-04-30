from typing import Optional, Literal
from pydantic import BaseModel


class FrameMetrics(BaseModel):
    shot_state: str                        # "IDLE" | "TRACKING"
    elbow_angle: Optional[float] = None   # degrees
    arc_angle: Optional[float] = None     # degrees
    follow_through: Optional[bool] = None
    speed_px_s: float = 0.0
    is_release_frame: bool = False
    ball_detected: bool = False
    hoop_detected: bool = False


class ShotCounts(BaseModel):
    made: int = 0
    attempted: int = 0


class CoachingCue(BaseModel):
    id: str                  # stable identifier e.g. "elbow_in"
    text: str                # short banner text e.g. "Elbow in!"
    detail: str              # full coaching sentence
    severity: Literal["info", "warning", "success"]
    category: Literal["shooting", "footwork", "ball_handling", "general"]
    duration_ms: int = 3000  # how long to show in UI


# ── Server → Client message types ──────────────────────────────────────────

class FrameDataMessage(BaseModel):
    type: Literal["frame_data"] = "frame_data"
    frame_idx: int
    metrics: FrameMetrics
    shot_counts: ShotCounts


class CoachingCueMessage(BaseModel):
    type: Literal["coaching_cue"] = "coaching_cue"
    cue: CoachingCue


class ShotEventMessage(BaseModel):
    type: Literal["shot_event"] = "shot_event"
    event: Literal["MADE", "MISS"]
    frame_idx: int
    metrics_snapshot: dict


class SessionCompleteMessage(BaseModel):
    type: Literal["session_complete"] = "session_complete"
    session_id: int
    summary: dict
    feedback: dict
    highlight_clip_ids: list[int]


# ── Client → Server message ──────────────────────────────────────────────

class ClientMessage(BaseModel):
    type: Literal["start_drill", "pause", "resume", "stop", "ping"]
    drill_type: Optional[str] = None
