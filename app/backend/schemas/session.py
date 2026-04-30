from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SessionMetricsSchema(BaseModel):
    shots_made: int = 0
    shots_attempted: int = 0
    shot_percentage: Optional[float] = None
    avg_release_elbow_angle: Optional[float] = None
    avg_arc_angle_deg: Optional[float] = None
    release_consistency_cv: Optional[float] = None
    follow_through_ratio: Optional[float] = None
    hand_switches: int = 0
    dribble_rhythm_cv: Optional[float] = None
    avg_possession_duration_s: Optional[float] = None
    lateral_speed_px_per_s: Optional[float] = None
    step_cadence_hz: Optional[float] = None
    avg_speed_px_per_s: Optional[float] = None
    top_speed_px_per_s: Optional[float] = None
    active_ratio: Optional[float] = None
    speed_history_json: Optional[list] = None
    shot_events_json: Optional[list] = None
    coaching_feedback_json: Optional[dict] = None

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    drill_type: str   # shooting|ball_handling|footwork|general
    drill_name: str   # e.g. "5-Spot Circuit"


class SessionUpdate(BaseModel):
    status: str       # completed|abandoned


class SessionSummary(BaseModel):
    id: int
    drill_type: str
    drill_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_s: Optional[float]
    shots_made: Optional[int] = None
    shot_percentage: Optional[float] = None

    model_config = {"from_attributes": True}


class HighlightMini(BaseModel):
    id: int
    file_path: str
    duration_s: Optional[float]
    thumbnail_path: Optional[str]

    model_config = {"from_attributes": True}


class SessionDetail(BaseModel):
    id: int
    drill_type: str
    drill_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_s: Optional[float]
    total_frames: Optional[int]
    fps: Optional[float]
    metrics: Optional[SessionMetricsSchema]
    highlights: list[HighlightMini] = []

    model_config = {"from_attributes": True}
