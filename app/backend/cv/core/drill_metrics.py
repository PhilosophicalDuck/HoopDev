import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .pose_analyzer import PoseAnalyzer

DrillType = Literal["shooting", "ball_handling", "footwork", "general", "auto"]

IDLE_SPEED_THRESHOLD = 30.0     # px/s — below this the player is considered standing still
SPEED_SMOOTH_WINDOW  = 5        # frames for rolling mean smoothing
FOLLOW_THROUGH_WINDOW = 15      # frames post-release to check wrist stays raised
BALL_BOUNCE_MIN_GAP  = 5        # minimum frames between dribble bounces


@dataclass
class DrillMetricsSnapshot:
    """Immutable snapshot of all computed drill metrics passed to DrillReport."""

    drill_type: str
    fps: float
    total_frames: int
    duration_s: float

    # General movement
    centroid_history: list[tuple[float, float]]
    speed_history_px_per_s: list[float]
    top_speed_px_per_s: float
    avg_speed_px_per_s: float
    active_frames: int
    idle_frames: int

    # Shooting
    shot_events: list[dict]
    shot_percentage: float | None
    release_elbow_angles: list[float]
    arc_angles_deg: list[float]
    follow_through_detected: list[bool]
    release_consistency_cv: float | None

    # Ball handling
    possession_durations_s: list[float]
    hand_switches: int
    avg_possession_duration_s: float | None
    dribble_rhythm_cv: float | None

    # Footwork
    lateral_displacement_px: list[float]
    lateral_speed_px_per_s: float
    step_cadence_hz: float | None


class DrillMetricsAccumulator:
    """Accumulates raw per-frame data during Pass 2, then finalizes into DrillMetricsSnapshot."""

    def __init__(self, drill_type: DrillType, fps: float) -> None:
        self._drill_type = drill_type
        self._fps = fps

        # General
        self._centroid_history: list[tuple[float, float]] = []
        self._raw_speeds: list[float] = []
        self._frame_count: int = 0

        # Shooting
        self._shot_events: list[dict] = []
        self._release_elbow_angles: list[float] = []
        self._arc_angles_deg: list[float] = []
        self._follow_through_detected: list[bool] = []
        self._ball_trajectory: list[tuple[int, float, float]] = []  # (frame, cx, cy)
        self._shot_start_frame: int = -1
        self._release_frame: int = -1
        self._post_release_frames: int = 0
        self._post_release_wrist_key: str = "right_wrist"
        self._post_release_shoulder_key: str = "right_shoulder"

        # Ball handling
        self._possession_start_frame: int = -1
        self._possession_durations_s: list[float] = []
        self._last_dribbling_hand: str = "unknown"
        self._hand_switches: int = 0
        self._ball_cy_history: list[tuple[int, float]] = []  # (frame, ball_cy)

        # Footwork
        self._lateral_displacement_px: list[float] = []
        self._ankle_cy_history: list[tuple[int, float]] = []  # (frame, avg_ankle_y)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_raw_speeds(self) -> list[float]:
        """Return a copy of the raw per-frame speed history (px/s)."""
        return list(self._raw_speeds)

    def update(
        self,
        frame_idx: int,
        player_centroid: tuple[float, float] | None,
        player_bbox: list[float] | None,
        ball_bbox: list[float] | None,
        possessing_id: int | None,
        focus_player_id: int | None,
        shot_event: str | None,
        pose_data: dict | None,
        pose_analyzer: "PoseAnalyzer",
    ) -> None:
        self._frame_count += 1
        if player_centroid is not None:
            self._update_speed(frame_idx, player_centroid)
            if len(self._centroid_history) > 0:
                prev = self._centroid_history[-1]
                dx = abs(player_centroid[0] - prev[0])
                self._lateral_displacement_px.append(dx)
            self._centroid_history.append(player_centroid)

        is_focus_possessing = (
            possessing_id is not None
            and focus_player_id is not None
            and possessing_id == focus_player_id
        )
        self._update_possession_metrics(frame_idx, is_focus_possessing)

        ball_center: tuple[float, float] | None = None
        if ball_bbox is not None:
            bx1, by1, bx2, by2 = ball_bbox
            ball_center = ((bx1 + bx2) / 2, (by1 + by2) / 2)
            self._ball_cy_history.append((frame_idx, ball_center[1]))

        if shot_event is not None:
            self._shot_events.append({"frame": frame_idx, "event": shot_event})
            self._finalize_arc_angle()
            self._ball_trajectory.clear()
            self._shot_start_frame = -1
        else:
            if ball_center is not None:
                self._ball_trajectory.append((frame_idx, ball_center[0], ball_center[1]))

        if pose_data is not None:
            self._update_shooting_metrics(frame_idx, pose_data, ball_bbox, pose_analyzer)
            self._update_footwork_metrics(frame_idx, pose_data, pose_analyzer)
            if ball_center is not None:
                self._update_hand_switch(frame_idx, pose_data, ball_center, pose_analyzer)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _update_speed(self, frame_idx: int, centroid: tuple[float, float]) -> None:
        if len(self._centroid_history) == 0:
            self._raw_speeds.append(0.0)
            return
        prev = self._centroid_history[-1]
        disp = math.sqrt((centroid[0] - prev[0]) ** 2 + (centroid[1] - prev[1]) ** 2)
        self._raw_speeds.append(disp * self._fps)

    def _update_shooting_metrics(
        self,
        frame_idx: int,
        pose_data: dict,
        ball_bbox: list[float] | None,
        pose_analyzer: "PoseAnalyzer",
    ) -> None:
        # Check follow-through in window after release
        if self._release_frame >= 0 and self._post_release_frames < FOLLOW_THROUGH_WINDOW:
            wrist = pose_analyzer.get_joint(pose_data, self._post_release_wrist_key)
            shoulder = pose_analyzer.get_joint(pose_data, self._post_release_shoulder_key)
            self._post_release_frames += 1
            if self._post_release_frames == FOLLOW_THROUGH_WINDOW:
                maintained = wrist is not None and shoulder is not None and wrist[1] < shoulder[1]
                self._follow_through_detected.append(maintained)
                self._release_frame = -1

        # Detect release candidate
        if pose_analyzer.is_release_candidate(pose_data, ball_bbox):
            arm = pose_analyzer.detect_shooting_arm(pose_data)
            shoulder_key = f"{arm}_shoulder"
            elbow_key = f"{arm}_elbow"
            wrist_key = f"{arm}_wrist"
            shoulder = pose_analyzer.get_joint(pose_data, shoulder_key)
            elbow = pose_analyzer.get_joint(pose_data, elbow_key)
            wrist = pose_analyzer.get_joint(pose_data, wrist_key)
            if shoulder is not None and elbow is not None and wrist is not None:
                angle = pose_analyzer.compute_angle(shoulder, elbow, wrist)
                self._release_elbow_angles.append(angle)
                self._release_frame = frame_idx
                self._post_release_frames = 0
                self._post_release_wrist_key = wrist_key
                self._post_release_shoulder_key = shoulder_key

    def _update_possession_metrics(self, frame_idx: int, is_focus_possessing: bool) -> None:
        if is_focus_possessing:
            if self._possession_start_frame < 0:
                self._possession_start_frame = frame_idx
        else:
            if self._possession_start_frame >= 0:
                dur = (frame_idx - self._possession_start_frame) / self._fps
                if dur > 0.1:
                    self._possession_durations_s.append(dur)
                self._possession_start_frame = -1

    def _update_hand_switch(
        self,
        frame_idx: int,
        pose_data: dict,
        ball_center: tuple[float, float],
        pose_analyzer: "PoseAnalyzer",
    ) -> None:
        lw = pose_analyzer.get_joint(pose_data, "left_wrist")
        rw = pose_analyzer.get_joint(pose_data, "right_wrist")
        if lw is None and rw is None:
            return
        def dist(p: tuple[float, float]) -> float:
            return math.sqrt((p[0] - ball_center[0]) ** 2 + (p[1] - ball_center[1]) ** 2)
        if lw is not None and rw is not None:
            current_hand = "left" if dist(lw) < dist(rw) else "right"
        elif lw is not None:
            current_hand = "left"
        else:
            current_hand = "right"
        if self._last_dribbling_hand not in ("unknown", current_hand):
            self._hand_switches += 1
        self._last_dribbling_hand = current_hand

    def _update_footwork_metrics(
        self,
        frame_idx: int,
        pose_data: dict,
        pose_analyzer: "PoseAnalyzer",
    ) -> None:
        la = pose_analyzer.get_joint(pose_data, "left_ankle")
        ra = pose_analyzer.get_joint(pose_data, "right_ankle")
        if la is not None and ra is not None:
            avg_y = (la[1] + ra[1]) / 2
            self._ankle_cy_history.append((frame_idx, avg_y))
        elif la is not None:
            self._ankle_cy_history.append((frame_idx, la[1]))
        elif ra is not None:
            self._ankle_cy_history.append((frame_idx, ra[1]))

    def _finalize_arc_angle(self) -> None:
        """Fit a parabola to ball trajectory and estimate launch angle."""
        if len(self._ball_trajectory) < 5:
            return
        xs = [p[1] for p in self._ball_trajectory]
        ys = [p[2] for p in self._ball_trajectory]
        try:
            coeffs = _fit_parabola(xs, ys)
            if coeffs is None:
                return
            a, b, _ = coeffs
            x0 = xs[0]
            dy_dx = 2 * a * x0 + b
            # In image coords y increases downward; ball going up = negative dy
            angle = abs(math.degrees(math.atan(abs(dy_dx))))
            self._arc_angles_deg.append(angle)
        except Exception:
            pass

    def _smooth_speeds(self) -> list[float]:
        if not self._raw_speeds:
            return []
        smoothed = []
        w = SPEED_SMOOTH_WINDOW
        for i in range(len(self._raw_speeds)):
            start = max(0, i - w // 2)
            end = min(len(self._raw_speeds), i + w // 2 + 1)
            smoothed.append(sum(self._raw_speeds[start:end]) / (end - start))
        return smoothed

    def _compute_dribble_rhythm_cv(self) -> float | None:
        """CV of inter-bounce intervals derived from ball_cy local minima."""
        if len(self._ball_cy_history) < 10:
            return None
        ys = [v for _, v in self._ball_cy_history]
        # Local minima: ball at bottom of bounce (max y in image = lowest on screen)
        minima_frames = []
        for i in range(1, len(ys) - 1):
            if ys[i] > ys[i - 1] and ys[i] > ys[i + 1]:
                minima_frames.append(self._ball_cy_history[i][0])
        if len(minima_frames) < 3:
            return None
        intervals = [
            (minima_frames[i + 1] - minima_frames[i]) / self._fps
            for i in range(len(minima_frames) - 1)
        ]
        return _coefficient_of_variation(intervals)

    def _compute_step_cadence(self) -> float | None:
        """Estimate step cadence Hz from ankle vertical oscillation local maxima."""
        if len(self._ankle_cy_history) < 15:
            return None
        ys = [v for _, v in self._ankle_cy_history]
        peaks = []
        for i in range(1, len(ys) - 1):
            if ys[i] < ys[i - 1] and ys[i] < ys[i + 1]:  # feet highest = smallest y
                peaks.append(self._ankle_cy_history[i][0])
        if len(peaks) < 3:
            return None
        total_frames = peaks[-1] - peaks[0]
        if total_frames < 1:
            return None
        return (len(peaks) - 1) / (total_frames / self._fps)

    def _auto_classify_drill(self) -> str:
        shots = len(self._shot_events)
        total_possession_s = sum(self._possession_durations_s)
        lateral_total = sum(self._lateral_displacement_px)
        if shots >= 3:
            return "shooting"
        if total_possession_s > (self._frame_count / self._fps) * 0.5:
            return "ball_handling"
        if lateral_total > self._frame_count * 2.0:
            return "footwork"
        return "general"

    def finalize(self) -> DrillMetricsSnapshot:
        """Compute derived statistics and return an immutable snapshot."""
        # Close any open possession bout
        if self._possession_start_frame >= 0:
            dur = (self._frame_count - self._possession_start_frame) / self._fps
            if dur > 0.1:
                self._possession_durations_s.append(dur)

        smoothed = self._smooth_speeds()
        top_speed = max(smoothed) if smoothed else 0.0
        avg_speed = sum(smoothed) / len(smoothed) if smoothed else 0.0
        active = sum(1 for s in smoothed if s > IDLE_SPEED_THRESHOLD)
        idle = len(smoothed) - active

        made = sum(1 for e in self._shot_events if e["event"] == "MADE")
        total_shots = len(self._shot_events)
        shot_pct = (made / total_shots) if total_shots > 0 else None

        release_cv = _coefficient_of_variation(self._release_elbow_angles)

        avg_poss = (
            sum(self._possession_durations_s) / len(self._possession_durations_s)
            if self._possession_durations_s
            else None
        )

        lat_speed = (
            (sum(self._lateral_displacement_px) / len(self._lateral_displacement_px)) * self._fps
            if self._lateral_displacement_px
            else 0.0
        )

        drill_type = (
            self._auto_classify_drill() if self._drill_type == "auto" else self._drill_type
        )

        return DrillMetricsSnapshot(
            drill_type=drill_type,
            fps=self._fps,
            total_frames=self._frame_count,
            duration_s=self._frame_count / self._fps if self._fps > 0 else 0.0,
            centroid_history=list(self._centroid_history),
            speed_history_px_per_s=smoothed,
            top_speed_px_per_s=top_speed,
            avg_speed_px_per_s=avg_speed,
            active_frames=active,
            idle_frames=idle,
            shot_events=list(self._shot_events),
            shot_percentage=shot_pct,
            release_elbow_angles=list(self._release_elbow_angles),
            arc_angles_deg=list(self._arc_angles_deg),
            follow_through_detected=list(self._follow_through_detected),
            release_consistency_cv=release_cv,
            possession_durations_s=list(self._possession_durations_s),
            hand_switches=self._hand_switches,
            avg_possession_duration_s=avg_poss,
            dribble_rhythm_cv=self._compute_dribble_rhythm_cv(),
            lateral_displacement_px=list(self._lateral_displacement_px),
            lateral_speed_px_per_s=lat_speed,
            step_cadence_hz=self._compute_step_cadence(),
        )


# ── Module-level helpers ──────────────────────────────────────────────────────

def _coefficient_of_variation(values: list[float]) -> float | None:
    if len(values) < 3:
        return None
    mean = sum(values) / len(values)
    if abs(mean) < 1e-6:
        return None
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance)
    return std / mean


def _fit_parabola(
    xs: list[float],
    ys: list[float],
) -> tuple[float, float, float] | None:
    """Fit y = ax^2 + bx + c to the given points. Returns (a, b, c) or None."""
    try:
        coeffs = list(map(float, __import__("numpy").polyfit(xs, ys, 2)))
        return coeffs[0], coeffs[1], coeffs[2]
    except Exception:
        return None
