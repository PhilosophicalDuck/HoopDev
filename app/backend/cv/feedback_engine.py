"""
FeedbackEngine: translates per-frame numeric data into debounced coaching cues.

All thresholds mirror drill_report.py constants to keep live and post-session
feedback consistent. Each cue has a cooldown_frames to prevent spam.
"""
import logging
from dataclasses import dataclass, field
from typing import Literal

logger = logging.getLogger(__name__)

from app.backend.cv.thresholds import (
    ELBOW_MIN, ELBOW_MAX, ELBOW_FLAIR, ELBOW_COLLAPSE,
    ARC_MIN, ARC_MAX,
    IDLE_SPEED, IDLE_FRAMES_WARN,
    SLOW_CADENCE_HZ, GOOD_RHYTHM_CV,
)


@dataclass(frozen=True)
class CoachingCue:
    id: str
    text: str
    detail: str
    severity: Literal["info", "warning", "success"]
    category: Literal["shooting", "footwork", "ball_handling", "general"]
    duration_ms: int = 3000


@dataclass
class FrameResult:
    """Minimal per-frame data needed by FeedbackEngine. Set by LivePipeline."""
    frame_idx: int = 0
    shot_state: str = "IDLE"          # "IDLE" | "TRACKING"
    shot_event: str | None = None     # "MADE" | "MISS" | None
    elbow_angle: float | None = None
    arc_angle: float | None = None    # only available on shot completion
    follow_through: bool | None = None
    speed_px_s: float = 0.0
    is_release_frame: bool = False
    ball_detected: bool = False
    hoop_detected: bool = False
    step_cadence_hz: float | None = None
    dribble_rhythm_cv: float | None = None
    shots_made: int = 0
    shots_attempted: int = 0
    drill_type: str = "shooting"
    session_elapsed_frames: int = 0


class FeedbackEngine:
    """
    Called every frame with a FrameResult.
    Returns a CoachingCue when a new cue should fire, or None.
    Each cue type has a cooldown to prevent repeated firing.
    """

    # cue_id → cooldown in frames
    CUE_COOLDOWNS: dict[str, int] = {
        "elbow_in":            90,
        "extend_arm":          90,
        "good_mechanics":      150,
        "flat_shot":           90,
        "high_arc":            90,
        "good_arc":            150,
        "no_follow_through":   120,
        "shot_made":           30,
        "shot_miss":           60,
        "slow_cadence":        150,
        "good_rhythm":         300,
        "idle_warning":        180,
    }

    def __init__(self, fps: float = 30.0, drill_type: str = "shooting"):
        self._fps = fps
        self._drill_type = drill_type
        self._cooldowns: dict[str, int] = {}  # cue_id → frames_remaining
        self._consecutive_idle: int = 0
        self._session_frames: int = 0

    def update(self, result: FrameResult) -> CoachingCue | None:
        self._session_frames += 1

        # Decrement all active cooldowns
        for key in list(self._cooldowns):
            self._cooldowns[key] -= 1
            if self._cooldowns[key] <= 0:
                del self._cooldowns[key]

        # Track consecutive idle frames
        if result.speed_px_s < IDLE_SPEED:
            self._consecutive_idle += 1
        else:
            self._consecutive_idle = 0

        cue = self._evaluate(result)
        if cue:
            self._cooldowns[cue.id] = self.CUE_COOLDOWNS.get(cue.id, 90)
            logger.debug("Cue fired: %s (frame %d)", cue.id, result.frame_idx)
        return cue

    def _ready(self, cue_id: str) -> bool:
        """True if this cue is not on cooldown."""
        return cue_id not in self._cooldowns

    def _evaluate(self, r: FrameResult) -> CoachingCue | None:
        # ── Shot events (highest priority) ───────────────────────────────────
        if r.shot_event == "MADE" and self._ready("shot_made"):
            pct = int(r.shots_made / r.shots_attempted * 100) if r.shots_attempted else 0
            return CoachingCue(
                id="shot_made",
                text="Buckets!",
                detail=f"{r.shots_made}/{r.shots_attempted} ({pct}% FG) — keep that form.",
                severity="success",
                category="shooting",
                duration_ms=2500,
            )

        if r.shot_event == "MISS" and self._ready("shot_miss"):
            return CoachingCue(
                id="shot_miss",
                text="Keep going!",
                detail="Stay with it — focus on your release point and follow through.",
                severity="info",
                category="shooting",
                duration_ms=2000,
            )

        # ── Shooting form at release ──────────────────────────────────────────
        if r.is_release_frame and r.elbow_angle is not None:
            angle = r.elbow_angle

            if angle > ELBOW_FLAIR and self._ready("elbow_in"):
                return CoachingCue(
                    id="elbow_in",
                    text="Elbow in!",
                    detail=f"Your elbow is at {angle:.0f}°. Tuck it under the ball (target: {ELBOW_MIN:.0f}–{ELBOW_MAX:.0f}°).",
                    severity="warning",
                    category="shooting",
                )

            if angle < ELBOW_COLLAPSE and self._ready("extend_arm"):
                return CoachingCue(
                    id="extend_arm",
                    text="Extend!",
                    detail=f"Arm not fully extended ({angle:.0f}°). Drive through the shot toward the basket.",
                    severity="warning",
                    category="shooting",
                )

            if ELBOW_MIN <= angle <= ELBOW_MAX and self._ready("good_mechanics"):
                return CoachingCue(
                    id="good_mechanics",
                    text="Nice release!",
                    detail=f"Elbow at {angle:.0f}° — perfect position. Repeat that form every rep.",
                    severity="success",
                    category="shooting",
                )

        # ── Follow-through ────────────────────────────────────────────────────
        if (r.follow_through is False
                and r.is_release_frame
                and self._ready("no_follow_through")):
            return CoachingCue(
                id="no_follow_through",
                text="Hold finish!",
                detail="Wrist dropped too early. Hold the goose-neck for 2 full seconds after release.",
                severity="warning",
                category="shooting",
                duration_ms=3500,
            )

        # ── Shot arc (available after shot resolves) ──────────────────────────
        if r.arc_angle is not None and r.shot_event in ("MADE", "MISS"):
            arc = r.arc_angle

            if arc < ARC_MIN and self._ready("flat_shot"):
                return CoachingCue(
                    id="flat_shot",
                    text="Arc it up!",
                    detail=f"Shot arc {arc:.0f}° — too flat. Aim for {ARC_MIN:.0f}–{ARC_MAX:.0f}°. Aim higher on the backboard.",
                    severity="warning",
                    category="shooting",
                )

            if arc > ARC_MAX and self._ready("high_arc"):
                return CoachingCue(
                    id="high_arc",
                    text="Lower the arc",
                    detail=f"Arc at {arc:.0f}° — too rainbow. Slightly earlier wrist snap on release.",
                    severity="warning",
                    category="shooting",
                )

            if ARC_MIN <= arc <= ARC_MAX and self._ready("good_arc"):
                return CoachingCue(
                    id="good_arc",
                    text=f"Great arc {arc:.0f}°!",
                    detail=f"Ideal trajectory at {arc:.0f}°. That's the sweet spot — lock it in.",
                    severity="success",
                    category="shooting",
                )

        # ── Footwork cadence ──────────────────────────────────────────────────
        if (r.drill_type in ("footwork", "general")
                and r.step_cadence_hz is not None
                and r.step_cadence_hz < SLOW_CADENCE_HZ
                and self._ready("slow_cadence")):
            return CoachingCue(
                id="slow_cadence",
                text="Faster feet!",
                detail=f"Step cadence {r.step_cadence_hz:.1f} Hz. Target 2.5–4.5 Hz — stay on your toes.",
                severity="warning",
                category="footwork",
            )

        # ── Dribble rhythm ────────────────────────────────────────────────────
        if (r.drill_type in ("ball_handling", "general")
                and r.dribble_rhythm_cv is not None
                and r.dribble_rhythm_cv < GOOD_RHYTHM_CV
                and self._session_frames > int(self._fps * 5)  # 5s warmup
                and self._ready("good_rhythm")):
            return CoachingCue(
                id="good_rhythm",
                text="Nice rhythm!",
                detail=f"Consistent dribble cadence (CV {r.dribble_rhythm_cv:.2f}). Keep that beat going.",
                severity="success",
                category="ball_handling",
                duration_ms=2000,
            )

        # ── Idle warning ──────────────────────────────────────────────────────
        if (self._consecutive_idle >= IDLE_FRAMES_WARN
                and r.drill_type != "footwork"
                and self._ready("idle_warning")):
            return CoachingCue(
                id="idle_warning",
                text="Stay active!",
                detail="Keep moving between reps — don't let your feet go cold.",
                severity="info",
                category="general",
                duration_ms=2000,
            )

        return None
