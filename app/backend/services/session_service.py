"""Session finalization — called after a live drill session ends."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.backend.models.session import DrillSession, SessionMetrics

logger = logging.getLogger(__name__)


def finalize_session(
    db: Session,
    session_id: int,
    snapshot: dict,
    feedback: dict,
) -> DrillSession:
    """
    Persist the DrillMetricsSnapshot and CoachingFeedback after a live session ends.
    Called by the WebSocket handler when the pipeline fires session_complete.
    """
    session = db.query(DrillSession).filter(DrillSession.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    now = datetime.now(timezone.utc)
    session.status = "completed"
    session.ended_at = now
    if session.started_at:
        delta = now - session.started_at.replace(tzinfo=timezone.utc)
        session.duration_s = delta.total_seconds()
    session.total_frames = snapshot.get("total_frames")
    session.fps = snapshot.get("fps")

    # Upsert session_metrics row
    metrics = db.query(SessionMetrics).filter(SessionMetrics.session_id == session_id).first()
    if not metrics:
        metrics = SessionMetrics(session_id=session_id)
        db.add(metrics)

    metrics.shots_made = snapshot.get("shots_made", 0)
    metrics.shots_attempted = snapshot.get("shots_attempted", 0)
    metrics.shot_percentage = snapshot.get("shot_percentage")
    metrics.avg_release_elbow_angle = _safe_mean(snapshot.get("release_elbow_angles"))
    metrics.avg_arc_angle_deg = _safe_mean(snapshot.get("arc_angles_deg"))
    metrics.release_consistency_cv = snapshot.get("release_consistency_cv")
    metrics.follow_through_ratio = _safe_ratio(snapshot.get("follow_through_detected"))
    metrics.hand_switches = snapshot.get("hand_switches", 0)
    metrics.dribble_rhythm_cv = snapshot.get("dribble_rhythm_cv")
    metrics.avg_possession_duration_s = snapshot.get("avg_possession_duration_s")
    metrics.lateral_speed_px_per_s = snapshot.get("lateral_speed_px_per_s")
    metrics.step_cadence_hz = snapshot.get("step_cadence_hz")
    metrics.avg_speed_px_per_s = snapshot.get("avg_speed_px_per_s")
    metrics.top_speed_px_per_s = snapshot.get("top_speed_px_per_s")
    metrics.active_ratio = _safe_active_ratio(snapshot)
    metrics.speed_history_json = snapshot.get("speed_history_px_per_s", [])
    metrics.shot_events_json = snapshot.get("shot_events", [])
    metrics.coaching_feedback_json = feedback

    db.commit()
    db.refresh(session)
    logger.info("Session %d finalized — %d frames, %.1fs", session_id,
                session.total_frames or 0, session.duration_s or 0)
    return session


def _safe_mean(values: list | None) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _safe_ratio(bools: list | None) -> float | None:
    if not bools:
        return None
    return sum(1 for b in bools if b) / len(bools)


def _safe_active_ratio(snapshot: dict) -> float | None:
    active = snapshot.get("active_frames")
    total = snapshot.get("total_frames")
    if active is None or not total:
        return None
    return active / total
