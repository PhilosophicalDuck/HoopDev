import json
from dataclasses import dataclass, asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .drill_metrics import DrillMetricsSnapshot

from app.backend.cv.thresholds import (
    SHOT_PCT_GOOD, SHOT_PCT_POOR,
    ELBOW_MIN as ELBOW_ANGLE_MIN,
    ELBOW_MAX as ELBOW_ANGLE_MAX,
    ELBOW_FLAIR as ELBOW_ANGLE_FLAIR,
    ELBOW_COLLAPSE as ELBOW_ANGLE_COLLAPSE,
    ARC_MIN as ARC_ANGLE_MIN,
    ARC_MAX as ARC_ANGLE_MAX,
    RELEASE_CV_GOOD, RELEASE_CV_POOR,
    FOLLOW_THROUGH_GOOD, FOLLOW_THROUGH_POOR,
    DRIBBLE_CV_GOOD, DRIBBLE_CV_POOR,
    HAND_SWITCH_GOOD_PER_MIN, HAND_SWITCH_POOR_PER_MIN,
    POSSESSION_RATIO_GOOD, POSSESSION_RATIO_POOR,
    LATERAL_SPEED_GOOD, LATERAL_SPEED_POOR,
    STEP_CADENCE_MIN, STEP_CADENCE_MAX, STEP_CADENCE_LOW,
    REST_RATIO_GOOD, REST_RATIO_POOR,
)


@dataclass
class CoachingFeedback:
    drill_type: str
    strengths: list[str]
    improvements: list[str]
    coaching_tips: dict[str, str]
    llm_summary: str | None = None


class DrillReport:
    """Generates a structured coaching feedback report from a DrillMetricsSnapshot."""

    def __init__(self, metrics: "DrillMetricsSnapshot") -> None:
        self._m = metrics

    def generate(self) -> CoachingFeedback:
        fb = CoachingFeedback(
            drill_type=self._m.drill_type,
            strengths=[],
            improvements=[],
            coaching_tips={},
        )
        self._evaluate_general(fb)
        if self._m.drill_type == "shooting":
            self._evaluate_shooting(fb)
        elif self._m.drill_type == "ball_handling":
            self._evaluate_ball_handling(fb)
        elif self._m.drill_type == "footwork":
            self._evaluate_footwork(fb)
        else:
            self._evaluate_shooting(fb)
            self._evaluate_ball_handling(fb)
            self._evaluate_footwork(fb)
        return fb

    # ── Drill-type evaluations ────────────────────────────────────────────────

    def _evaluate_shooting(self, fb: CoachingFeedback) -> None:
        m = self._m

        # Shot percentage
        if m.shot_percentage is not None:
            if m.shot_percentage >= SHOT_PCT_GOOD:
                fb.strengths.append(
                    f"High shooting accuracy ({m.shot_percentage:.0%} field goal percentage)"
                )
            elif m.shot_percentage < SHOT_PCT_POOR:
                label = "Low shooting accuracy"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Focus on aligning your shooting elbow directly under the ball. "
                    "Use the BEEF cue: Balance, Eyes, Elbow, Follow-through."
                )

        # Elbow angle at release
        if m.release_elbow_angles:
            mean_elbow = sum(m.release_elbow_angles) / len(m.release_elbow_angles)
            if ELBOW_ANGLE_MIN <= mean_elbow <= ELBOW_ANGLE_MAX:
                fb.strengths.append(
                    f"Consistent elbow alignment at release ({mean_elbow:.1f}°)"
                )
            elif mean_elbow > ELBOW_ANGLE_FLAIR:
                label = "Elbow flaring out at release"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Keep your elbow tucked directly under the ball. "
                    "Practice 'wall shots' — stand 3 feet from a wall and shoot against it "
                    "to force proper elbow alignment."
                )
            elif mean_elbow < ELBOW_ANGLE_COLLAPSE:
                label = "Arm not fully extending at release"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Extend your arm fully through the release. Your elbow angle should be "
                    "75-100° at the point of release. Practice form shooting at 3 feet to "
                    "build the correct muscle memory."
                )

        # Ball arc angle
        if m.arc_angles_deg:
            mean_arc = sum(m.arc_angles_deg) / len(m.arc_angles_deg)
            if ARC_ANGLE_MIN <= mean_arc <= ARC_ANGLE_MAX:
                fb.strengths.append(f"Good shot arc ({mean_arc:.1f}° trajectory)")
            elif mean_arc < ARC_ANGLE_MIN:
                label = "Flat shot trajectory"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Your shot is too flat — aim for a 45-55° arc. "
                    "Imagine shooting over a 10-foot wall just past the rim. "
                    "A higher arc gives the ball a larger target and more margin on the way down."
                )
            elif mean_arc > ARC_ANGLE_MAX:
                label = "Excessively high arc"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Your arc is too high, reducing distance control. "
                    "Extend your wrist slightly earlier in the shooting motion "
                    "to bring the trajectory down to 45-55°."
                )

        # Release consistency
        if m.release_consistency_cv is not None:
            if m.release_consistency_cv < RELEASE_CV_GOOD:
                fb.strengths.append("Very consistent release mechanics")
            elif m.release_consistency_cv >= RELEASE_CV_POOR:
                label = "Inconsistent release point"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Your release angle varies significantly shot-to-shot. "
                    "Pick a consistent spot on the backboard to aim and take 50 form shots "
                    "per session focusing on the exact same release every time."
                )

        # Follow-through
        if m.follow_through_detected:
            ratio = sum(m.follow_through_detected) / len(m.follow_through_detected)
            if ratio >= FOLLOW_THROUGH_GOOD:
                fb.strengths.append(f"Solid follow-through ({ratio:.0%} of shots)")
            elif ratio < FOLLOW_THROUGH_POOR:
                label = "Incomplete follow-through"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "You are pulling your shooting hand down too quickly after release. "
                    "Hold the 'goose-neck' follow-through for 2 seconds after every shot "
                    "until it becomes automatic."
                )

    def _evaluate_ball_handling(self, fb: CoachingFeedback) -> None:
        m = self._m
        duration_min = m.duration_s / 60.0 if m.duration_s > 0 else 1.0

        # Dribble rhythm
        if m.dribble_rhythm_cv is not None:
            if m.dribble_rhythm_cv < DRIBBLE_CV_GOOD:
                fb.strengths.append("Rhythmic, consistent dribble cadence")
            elif m.dribble_rhythm_cv >= DRIBBLE_CV_POOR:
                label = "Inconsistent dribble rhythm"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Use a metronome app at 120 BPM during practice — each beat equals one "
                    "dribble. Consistent rhythm builds ball security under defensive pressure."
                )

        # Hand switching
        switches_per_min = m.hand_switches / duration_min if duration_min > 0 else 0.0
        if switches_per_min >= HAND_SWITCH_GOOD_PER_MIN:
            fb.strengths.append(
                f"Good hand switching ({switches_per_min:.1f} switches/min)"
            )
        elif switches_per_min < HAND_SWITCH_POOR_PER_MIN and m.duration_s > 15:
            label = "Over-reliance on dominant hand"
            fb.improvements.append(label)
            fb.coaching_tips[label] = (
                "Dedicate 5 minutes of each practice session to your weak hand only. "
                "The first 500 reps will feel awkward — push through and the muscle memory "
                "will form."
            )

        # Possession ratio
        if m.duration_s > 10:
            total_possession = sum(m.possession_durations_s)
            possession_ratio = total_possession / m.duration_s
            if possession_ratio >= POSSESSION_RATIO_GOOD:
                fb.strengths.append(
                    f"Strong ball security ({possession_ratio:.0%} possession time)"
                )
            elif possession_ratio < POSSESSION_RATIO_POOR:
                label = "Frequent ball loss during drill"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Work on low dribbles (knee height) to protect the ball. "
                    "Keep your body between the ball and the imaginary defender."
                )

    def _evaluate_footwork(self, fb: CoachingFeedback) -> None:
        m = self._m

        # Lateral speed
        if m.lateral_speed_px_per_s >= LATERAL_SPEED_GOOD:
            fb.strengths.append("Strong lateral quickness")
        elif m.lateral_speed_px_per_s < LATERAL_SPEED_POOR and m.lateral_speed_px_per_s > 0:
            label = "Slow lateral movement"
            fb.improvements.append(label)
            fb.coaching_tips[label] = (
                "Explode off your inside foot in each direction. Stay in an athletic stance "
                "(knees bent, weight on balls of feet) throughout the drill."
            )

        # Step cadence
        if m.step_cadence_hz is not None:
            if STEP_CADENCE_MIN <= m.step_cadence_hz <= STEP_CADENCE_MAX:
                fb.strengths.append(
                    f"Good step frequency ({m.step_cadence_hz:.1f} Hz)"
                )
            elif m.step_cadence_hz < STEP_CADENCE_LOW:
                label = "Low step frequency"
                fb.improvements.append(label)
                fb.coaching_tips[label] = (
                    "Increase the pace of your footwork — each step should be quick and "
                    "purposeful. Use a ladder drill at a higher tempo to train your feet "
                    "to move faster."
                )

    def _evaluate_general(self, fb: CoachingFeedback) -> None:
        m = self._m
        total = m.active_frames + m.idle_frames
        if total == 0:
            return
        rest_ratio = m.idle_frames / total
        if rest_ratio <= REST_RATIO_GOOD:
            fb.strengths.append(
                f"High drill intensity ({(1 - rest_ratio):.0%} of time actively moving)"
            )
        elif rest_ratio > REST_RATIO_POOR:
            label = "Too much standing still during drill"
            fb.improvements.append(label)
            fb.coaching_tips[label] = (
                "Minimize rest within the drill — transition immediately into each next "
                "movement. Reduce standing rest periods to under 5 seconds between reps."
            )

    # ── LLM enhancement ───────────────────────────────────────────────────────

    def add_llm_summary(
        self,
        feedback: CoachingFeedback,
        model: str = "llama3.2",
    ) -> None:
        """Generate a natural-language coaching paragraph via Ollama (optional)."""
        strengths_text = "; ".join(feedback.strengths) or "none identified"
        improvements_text = "; ".join(feedback.improvements) or "none identified"
        tips_text = "\n".join(
            f"- {k}: {v}" for k, v in feedback.coaching_tips.items()
        )
        prompt = (
            f"You are a professional basketball coach. A player just completed a "
            f"{feedback.drill_type} drill. Here is the analysis:\n\n"
            f"Strengths: {strengths_text}\n"
            f"Areas to improve: {improvements_text}\n"
            f"Coaching tips:\n{tips_text}\n\n"
            f"Write a concise, encouraging 3-4 sentence coaching summary for the player. "
            f"Be specific and actionable."
        )
        try:
            import ollama
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            feedback.llm_summary = response["message"]["content"]
        except ImportError:
            feedback.llm_summary = None
        except Exception:
            feedback.llm_summary = None

    # ── Output ────────────────────────────────────────────────────────────────

    def print_summary(self, feedback: CoachingFeedback) -> None:
        m = self._m
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"  DRILL ANALYSIS REPORT — {feedback.drill_type.upper()}")
        print(sep)
        print(f"  Duration  : {m.duration_s:.1f}s  ({m.total_frames} frames @ {m.fps:.1f} fps)")
        print(f"  Top Speed : {m.top_speed_px_per_s:.0f} px/s")
        print(f"  Avg Speed : {m.avg_speed_px_per_s:.0f} px/s")
        if m.shot_percentage is not None:
            made = sum(1 for e in m.shot_events if e["event"] == "MADE")
            total = len(m.shot_events)
            print(f"  Shooting  : {made}/{total} ({m.shot_percentage:.0%} FG%)")
        print(f"\n  STRENGTHS ({len(feedback.strengths)})")
        for s in feedback.strengths:
            print(f"    + {s}")
        print(f"\n  AREAS TO IMPROVE ({len(feedback.improvements)})")
        for imp in feedback.improvements:
            tip = feedback.coaching_tips.get(imp, "")
            print(f"    - {imp}")
            if tip:
                wrapped = _wrap(tip, 70, prefix="        ")
                print(wrapped)
        if feedback.llm_summary:
            print(f"\n  COACH'S NOTE")
            print(_wrap(feedback.llm_summary, 70, prefix="    "))
        print(sep + "\n")

    def save_json(
        self,
        feedback: CoachingFeedback,
        path: str,
    ) -> None:
        m = self._m
        data = {
            "drill_type": feedback.drill_type,
            "duration_s": m.duration_s,
            "fps": m.fps,
            "total_frames": m.total_frames,
            "strengths": feedback.strengths,
            "improvements": feedback.improvements,
            "coaching_tips": feedback.coaching_tips,
            "llm_summary": feedback.llm_summary,
            "metrics": {
                "shot_percentage": m.shot_percentage,
                "shot_events": m.shot_events,
                "top_speed_px_per_s": m.top_speed_px_per_s,
                "avg_speed_px_per_s": m.avg_speed_px_per_s,
                "active_frames": m.active_frames,
                "idle_frames": m.idle_frames,
                "release_elbow_angles": m.release_elbow_angles,
                "arc_angles_deg": m.arc_angles_deg,
                "release_consistency_cv": m.release_consistency_cv,
                "follow_through_ratio": (
                    sum(m.follow_through_detected) / len(m.follow_through_detected)
                    if m.follow_through_detected else None
                ),
                "hand_switches": m.hand_switches,
                "avg_possession_duration_s": m.avg_possession_duration_s,
                "dribble_rhythm_cv": m.dribble_rhythm_cv,
                "lateral_speed_px_per_s": m.lateral_speed_px_per_s,
                "step_cadence_hz": m.step_cadence_hz,
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wrap(text: str, width: int, prefix: str = "") -> str:
    words = text.split()
    lines = []
    current = prefix
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = prefix + word
        else:
            current = current + (" " if current.strip() else "") + word
    if current.strip():
        lines.append(current)
    return "\n".join(lines)
