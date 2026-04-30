"""Aggregate session metrics for the dashboard."""
from __future__ import annotations
from sqlalchemy.orm import Session
from app.backend.models.session import DrillSession, SessionMetrics
from app.backend.models.benchmark import BenchmarkEntry


def get_dashboard_data(db: Session, user_id: int) -> dict:
    """Return all data needed by the Dashboard page."""
    # Last 20 completed sessions
    sessions = (
        db.query(DrillSession)
        .filter(DrillSession.user_id == user_id, DrillSession.status == "completed")
        .order_by(DrillSession.started_at.desc())
        .limit(20)
        .all()
    )

    # Skill radar: average key metrics per category across last 5 sessions each
    radar = _build_radar(sessions)

    # Benchmark history: all entries grouped by type
    benchmarks = (
        db.query(BenchmarkEntry)
        .filter(BenchmarkEntry.user_id == user_id)
        .order_by(BenchmarkEntry.recorded_at.asc())
        .all()
    )
    benchmark_history: dict[str, list[dict]] = {}
    for b in benchmarks:
        benchmark_history.setdefault(b.benchmark_type, []).append({
            "value": b.value,
            "recorded_at": b.recorded_at.isoformat(),
            "session_id": b.session_id,
        })

    # Latest benchmark values
    latest_benchmarks: dict[str, float] = {}
    for b in benchmarks:
        latest_benchmarks[b.benchmark_type] = b.value  # last wins since ordered asc

    # Recent sessions summary
    recent = []
    for s in sessions[:10]:
        entry: dict = {
            "id": s.id,
            "drill_name": s.drill_name,
            "drill_type": s.drill_type,
            "started_at": s.started_at.isoformat(),
            "duration_s": s.duration_s,
        }
        if s.metrics:
            entry["shot_percentage"] = s.metrics.shot_percentage
            entry["shots_made"] = s.metrics.shots_made
            entry["shots_attempted"] = s.metrics.shots_attempted
        recent.append(entry)

    return {
        "radar": radar,
        "benchmark_history": benchmark_history,
        "latest_benchmarks": latest_benchmarks,
        "recent_sessions": recent,
        "total_sessions": len(sessions),
    }


def _build_radar(sessions: list[DrillSession]) -> dict[str, float | None]:
    """Compute 5-axis radar values (0–100 scale) from recent sessions."""
    def avg(values: list[float]) -> float | None:
        clean = [v for v in values if v is not None]
        return round(sum(clean) / len(clean), 1) if clean else None

    shooting_pcts, consistencies, dribble_cvs, footwork_speeds, active_ratios = [], [], [], [], []

    for s in sessions:
        if not s.metrics:
            continue
        m = s.metrics
        if m.shot_percentage is not None:
            shooting_pcts.append(m.shot_percentage * 100)
        if m.release_consistency_cv is not None:
            # Invert CV: lower CV = better consistency → map to 0–100
            consistencies.append(max(0, 100 - m.release_consistency_cv * 500))
        if m.dribble_rhythm_cv is not None:
            dribble_cvs.append(max(0, 100 - m.dribble_rhythm_cv * 400))
        if m.lateral_speed_px_per_s is not None:
            footwork_speeds.append(min(100, m.lateral_speed_px_per_s / 2))
        if m.active_ratio is not None:
            active_ratios.append(m.active_ratio * 100)

    return {
        "shooting": avg(shooting_pcts),
        "consistency": avg(consistencies),
        "ball_handling": avg(dribble_cvs),
        "footwork": avg(footwork_speeds),
        "conditioning": avg(active_ratios),
    }
