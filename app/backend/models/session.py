from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.backend.database import Base


class DrillSession(Base):
    __tablename__ = "drill_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    drill_type: Mapped[str] = mapped_column(String, nullable=False)   # shooting|ball_handling|footwork|general
    drill_name: Mapped[str] = mapped_column(String, nullable=False)   # e.g. "5-Spot Circuit"
    status: Mapped[str] = mapped_column(String, default="active")     # active|completed|abandoned
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_frames: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    source: Mapped[str] = mapped_column(String, default="live")          # "live" | "upload"
    video_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="sessions")  # type: ignore[name-defined]
    metrics: Mapped[Optional["SessionMetrics"]] = relationship(
        "SessionMetrics", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
    highlights: Mapped[list["HighlightClip"]] = relationship(  # type: ignore[name-defined]
        "HighlightClip", back_populates="session", cascade="all, delete-orphan"
    )
    benchmarks: Mapped[list["BenchmarkEntry"]] = relationship(  # type: ignore[name-defined]
        "BenchmarkEntry", back_populates="session"
    )


class SessionMetrics(Base):
    __tablename__ = "session_metrics"
    __table_args__ = (UniqueConstraint("session_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("drill_sessions.id"), nullable=False)

    # Shooting
    shots_made: Mapped[int] = mapped_column(Integer, default=0)
    shots_attempted: Mapped[int] = mapped_column(Integer, default=0)
    shot_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_release_elbow_angle: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_arc_angle_deg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    release_consistency_cv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    follow_through_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Ball handling
    hand_switches: Mapped[int] = mapped_column(Integer, default=0)
    dribble_rhythm_cv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_possession_duration_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Footwork / movement
    lateral_speed_px_per_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    step_cadence_hz: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_speed_px_per_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_speed_px_per_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Raw JSON for charts
    speed_history_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    shot_events_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    coaching_feedback_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    session: Mapped["DrillSession"] = relationship("DrillSession", back_populates="metrics")
