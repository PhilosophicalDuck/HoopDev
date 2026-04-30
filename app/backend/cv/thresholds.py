"""
Coaching thresholds — single source of truth.

Consumed by:
  - app/backend/cv/feedback_engine.py  (live per-frame cues)
  - app/backend/cv/core/drill_report.py  (post-session report)

Do NOT duplicate these values. Import from here.
"""

# ── Shooting: elbow angle at release (degrees) ────────────────────────────────
ELBOW_MIN: float = 75.0
ELBOW_MAX: float = 105.0
ELBOW_FLAIR: float = 115.0
ELBOW_COLLAPSE: float = 65.0

# ── Shooting: ball arc angle (degrees) ───────────────────────────────────────
ARC_MIN: float = 42.0
ARC_MAX: float = 58.0

# ── Shooting: field goal percentage ──────────────────────────────────────────
SHOT_PCT_GOOD: float = 0.50
SHOT_PCT_POOR: float = 0.30

# ── Shooting: release angle consistency (coefficient of variation) ────────────
RELEASE_CV_GOOD: float = 0.08
RELEASE_CV_POOR: float = 0.12

# ── Shooting: follow-through rate ────────────────────────────────────────────
FOLLOW_THROUGH_GOOD: float = 0.75
FOLLOW_THROUGH_POOR: float = 0.50

# ── Ball handling ─────────────────────────────────────────────────────────────
DRIBBLE_CV_GOOD: float = 0.15
DRIBBLE_CV_POOR: float = 0.25
HAND_SWITCH_GOOD_PER_MIN: float = 5.0
HAND_SWITCH_POOR_PER_MIN: float = 2.0
POSSESSION_RATIO_GOOD: float = 0.70
POSSESSION_RATIO_POOR: float = 0.50

# ── Footwork ──────────────────────────────────────────────────────────────────
LATERAL_SPEED_GOOD: float = 120.0
LATERAL_SPEED_POOR: float = 72.0
STEP_CADENCE_MIN: float = 2.5
STEP_CADENCE_MAX: float = 4.5
STEP_CADENCE_LOW: float = 2.0

# ── General activity ──────────────────────────────────────────────────────────
IDLE_SPEED: float = 30.0           # px/s — below this the player is considered still
IDLE_FRAMES_WARN: int = 90         # consecutive idle frames before warning cue fires
SLOW_CADENCE_HZ: float = 2.0
GOOD_RHYTHM_CV: float = 0.15
REST_RATIO_GOOD: float = 0.20
REST_RATIO_POOR: float = 0.40
