"""
VideoPipeline: single-pass processing of an uploaded video file.

Mirrors LivePipeline but reads frames from a file instead of the webcam.
Progress is reported via a callback so the router can push updates to
waiting WebSocket clients.
"""
import logging
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from app.backend.cv.core import ShotTracker, PoseAnalyzer, DrillMetricsAccumulator, DrillReport, best_detection, box_center
from app.backend.cv.feedback_engine import FeedbackEngine, FrameResult, CoachingCue
from app.backend.cv.live_pipeline import PipelineResult
from app.backend.cv.base_pipeline import BasePipeline
from app.backend.cv.constants import (
    CLS_BALL, CLS_HOOP, CLS_PLAYER,
    PROGRESS_INTERVAL,
)

logger = logging.getLogger(__name__)


class VideoPipeline(BasePipeline):
    """
    Processes every frame of an uploaded video file synchronously.

    Usage (in a background thread / executor):
        pipeline = VideoPipeline(...)
        for result in pipeline.run(on_progress=callback):
            # result is a PipelineResult (same shape as LivePipeline)
            pass
        snapshot, feedback = pipeline.finalize()
    """

    def __init__(
        self,
        video_path: str,
        detection_model_path: str,
        pose_model_name: str,
        drill_type: str,
        annotate: bool = False,
        hoop_model_path: str | None = None,
    ) -> None:
        self._video_path = video_path
        self._drill_type = drill_type
        self._frame_idx = 0

        # ── Probe video for FPS / frame count ────────────────────────────────
        cap = cv2.VideoCapture(video_path)
        self._fps: float = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._total_frames: int = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        self._frame_w: int = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._frame_h: int = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        logger.info(
            "VideoPipeline init: %s  fps=%.1f  frames=%d  drill=%s",
            Path(video_path).name, self._fps, self._total_frames, drill_type,
        )

        # ── Load models ───────────────────────────────────────────────────────
        from ultralytics import YOLO
        self._detector = YOLO(detection_model_path)
        self._detector.to("cpu")
        # Optional dedicated hoop model (better hoop detection, no ball detection)
        self._hoop_detector: YOLO | None = None
        if hoop_model_path:
            self._hoop_detector = YOLO(hoop_model_path)
            self._hoop_detector.to("cpu")
            logger.info("Hoop model loaded: %s", hoop_model_path)
        self._pose_analyzer = PoseAnalyzer(model_name=pose_model_name) if pose_model_name else None

        # ── CV components ─────────────────────────────────────────────────────
        self._shot_tracker = ShotTracker()
        self._metrics = DrillMetricsAccumulator(drill_type=drill_type, fps=self._fps)
        self._feedback = FeedbackEngine(fps=self._fps, drill_type=drill_type)

        # Shared pipeline state (ball history, tracker, focus ID)
        self._init_pipeline_state()

        # Collected coaching cues for summary
        self._all_cues: list[CoachingCue] = []

        # Annotation overlay state (only active when annotate=True)
        self._annotate = annotate
        self._ann_flash_frame: int = -9999
        self._ann_flash_text: str = ""
        self._ann_flash_color: tuple = (255, 255, 255)
        self._ann_last_cue: CoachingCue | None = None
        self._ann_last_cue_frame: int = -9999

        # Detection diagnostics
        self._diag_ball_frames: int = 0
        self._diag_hoop_frames: int = 0
        self._diag_both_frames: int = 0

    # ─────────────────────────────────────────────────────────────────────────

    def run(
        self,
        on_progress: Callable[[int, int], None] | None = None,
    ):
        """
        Generator — yields a PipelineResult per frame.
        on_progress(frame_idx, total_frames) called every PROGRESS_INTERVAL frames.
        """
        cap = cv2.VideoCapture(self._video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {self._video_path}")

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                result = self._process_frame(frame)
                yield result

                if on_progress and result.frame_idx % PROGRESS_INTERVAL == 0:
                    on_progress(result.frame_idx, self._total_frames)
        finally:
            cap.release()

        # Final progress update
        if on_progress:
            on_progress(self._total_frames, self._total_frames)

    def finalize(self) -> tuple[dict, dict]:
        """
        Returns (snapshot_dict, feedback_dict) — identical shape to LivePipeline.finalize().
        """
        snapshot = self._metrics.finalize()
        report = DrillReport(snapshot)
        feedback = report.generate()

        shots_made = (
            self._shot_tracker.made.get("A", 0) + self._shot_tracker.made.get("B", 0)
        )
        shots_missed = (
            self._shot_tracker.missed.get("A", 0) + self._shot_tracker.missed.get("B", 0)
        )
        shots_attempted = shots_made + shots_missed

        snap_dict = {
            "drill_type": snapshot.drill_type,
            "fps": snapshot.fps,
            "total_frames": snapshot.total_frames,
            "duration_s": snapshot.duration_s,
            "shots_made": shots_made,
            "shots_attempted": shots_attempted,
            "shot_percentage": snapshot.shot_percentage,
            "release_elbow_angles": snapshot.release_elbow_angles,
            "arc_angles_deg": snapshot.arc_angles_deg,
            "release_consistency_cv": snapshot.release_consistency_cv,
            "follow_through_detected": snapshot.follow_through_detected,
            "hand_switches": snapshot.hand_switches,
            "dribble_rhythm_cv": snapshot.dribble_rhythm_cv,
            "avg_possession_duration_s": snapshot.avg_possession_duration_s,
            "lateral_speed_px_per_s": snapshot.lateral_speed_px_per_s,
            "step_cadence_hz": snapshot.step_cadence_hz,
            "avg_speed_px_per_s": snapshot.avg_speed_px_per_s,
            "top_speed_px_per_s": snapshot.top_speed_px_per_s,
            "active_frames": snapshot.active_frames,
            "speed_history_px_per_s": snapshot.speed_history_px_per_s,
            "shot_events": snapshot.shot_events,
            "cue_log": [
                {"text": c.text, "severity": c.severity, "category": c.category}
                for c in self._all_cues
            ],
        }

        feedback_dict = {
            "drill_type": feedback.drill_type,
            "strengths": feedback.strengths,
            "improvements": feedback.improvements,
            "coaching_tips": feedback.coaching_tips,
        }

        total = snapshot.total_frames or 1
        diag_dict = {
            "total_frames": total,
            "ball_detected_frames": self._diag_ball_frames,
            "hoop_detected_frames": self._diag_hoop_frames,
            "both_detected_frames": self._diag_both_frames,
            "ball_detection_rate": self._diag_ball_frames / total,
            "hoop_detection_rate": self._diag_hoop_frames / total,
        }

        logger.info(
            "VideoPipeline finalized — %d frames, %.1fs, %d/%d FG | "
            "ball %.0f%% hoop %.0f%% both %.0f%%",
            snapshot.total_frames, snapshot.duration_s,
            shots_made, shots_attempted,
            diag_dict["ball_detection_rate"] * 100,
            diag_dict["hoop_detection_rate"] * 100,
            self._diag_both_frames / total * 100,
        )
        return snap_dict, feedback_dict, diag_dict

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _process_frame(self, frame: np.ndarray) -> PipelineResult:
        self._frame_idx += 1
        idx = self._frame_idx

        # YOLO detection — ball + player from main model
        results = self._detector.predict(frame, verbose=False, conf=0.3)[0]
        boxes = results.boxes

        ball_bbox = best_detection(boxes, CLS_BALL)

        # Hoop: run dedicated model every 10 frames only — hoop doesn't move,
        # so reusing the last detection costs nothing in accuracy.
        if self._hoop_detector is not None:
            if idx % 10 == 1:
                hoop_results = self._hoop_detector.predict(frame, verbose=False, conf=0.15)[0]
                detected = best_detection(hoop_results.boxes, CLS_HOOP)
                if detected is not None:
                    self._last_hoop_bbox = detected
            hoop_bbox = getattr(self, "_last_hoop_bbox", None)
        else:
            hoop_bbox = best_detection(boxes, CLS_HOOP)

        player_bboxes = [b.xyxy[0].tolist() for b in boxes if int(b.cls[0]) == CLS_PLAYER]
        player_confs = [float(b.conf[0]) for b in boxes if int(b.cls[0]) == CLS_PLAYER]
        player_tracks = self._update_bytetrack(player_bboxes, player_confs)

        # Detection diagnostics
        if ball_bbox:
            self._diag_ball_frames += 1
        if hoop_bbox:
            self._diag_hoop_frames += 1
        if ball_bbox and hoop_bbox:
            self._diag_both_frames += 1

        # Ball smoothing
        if ball_bbox:
            cx, cy = box_center(ball_bbox)
            self._ball_history.append((cx, cy))
        else:
            self._ball_history.append(None)
        smoothed_ball = self._smooth_ball(ball_bbox)

        # Focus player
        for tid in player_tracks:
            self._track_counts[tid] = self._track_counts.get(tid, 0) + 1
        if self._track_counts:
            self._focus_id = max(self._track_counts, key=self._track_counts.get)
        focus_bbox = player_tracks.get(self._focus_id) if self._focus_id else None

        # Pose
        pose_data = None
        if focus_bbox is not None and self._pose_analyzer is not None:
            pose_data = self._pose_analyzer.extract_keypoints(frame, focus_bbox)

        # Shot tracker
        shot_event, _ = self._shot_tracker.update(
            frame_idx=idx,
            ball_bbox=smoothed_ball,
            hoop_bbox=hoop_bbox,
            possessing_team="A",
            last_known_possessing_team="A",
        )

        # Metrics accumulation
        player_centroid = box_center(focus_bbox) if focus_bbox else None
        self._metrics.update(
            frame_idx=idx,
            player_centroid=player_centroid,
            player_bbox=focus_bbox,
            ball_bbox=smoothed_ball,
            possessing_id=self._focus_id,
            focus_player_id=self._focus_id,
            shot_event=shot_event,
            pose_data=pose_data,
            pose_analyzer=self._pose_analyzer,
        )

        # Elbow angle / follow-through at release
        elbow_angle = None
        is_release = False
        follow_through = None
        if pose_data and self._pose_analyzer is not None and self._pose_analyzer.is_release_candidate(pose_data, smoothed_ball):
            is_release = True
            arm = self._pose_analyzer.detect_shooting_arm(pose_data)
            if arm == "right":
                shoulder = self._pose_analyzer.get_joint(pose_data, "right_shoulder")
                elbow = self._pose_analyzer.get_joint(pose_data, "right_elbow")
                wrist = self._pose_analyzer.get_joint(pose_data, "right_wrist")
            else:
                shoulder = self._pose_analyzer.get_joint(pose_data, "left_shoulder")
                elbow = self._pose_analyzer.get_joint(pose_data, "left_elbow")
                wrist = self._pose_analyzer.get_joint(pose_data, "left_wrist")

            if shoulder and elbow and wrist:
                elbow_angle = self._pose_analyzer.compute_angle(shoulder, elbow, wrist)
            if wrist and shoulder:
                follow_through = wrist[1] < shoulder[1]

        made = (
            self._shot_tracker.made.get("A", 0) + self._shot_tracker.made.get("B", 0)
        )
        attempted = made + self._shot_tracker.missed.get("A", 0) + self._shot_tracker.missed.get("B", 0)

        frame_result = FrameResult(
            frame_idx=idx,
            shot_state=self._shot_tracker.state,
            shot_event=shot_event,
            elbow_angle=elbow_angle,
            arc_angle=None,
            follow_through=follow_through,
            speed_px_s=self.get_current_speed(),
            is_release_frame=is_release,
            ball_detected=ball_bbox is not None,
            hoop_detected=hoop_bbox is not None,
            shots_made=made,
            shots_attempted=attempted,
            drill_type=self._drill_type,
            session_elapsed_frames=idx,
        )

        cue = self._feedback.update(frame_result)
        if cue:
            self._all_cues.append(cue)

        ann_frame = (
            self._draw_annotations(
                frame, player_tracks, smoothed_ball, hoop_bbox,
                pose_data, elbow_angle, is_release, shot_event,
                cue, made, attempted,
            )
            if self._annotate else None
        )

        return PipelineResult(
            frame_idx=idx,
            frame_result=frame_result,
            shot_event=shot_event,
            cue=cue,
            annotated_frame=ann_frame,
        )

    def _draw_annotations(
        self,
        frame: np.ndarray,
        player_tracks: dict[int, list],
        ball_bbox: list | None,
        hoop_bbox: list | None,
        pose_data: dict | None,
        elbow_angle: float | None,
        is_release: bool,
        shot_event: str | None,
        cue: CoachingCue | None,
        made: int,
        attempted: int,
    ) -> np.ndarray:
        """Render bboxes, skeleton, HUD, shot flash, and cue text onto a copy of frame."""
        out = frame.copy()
        h, w = out.shape[:2]

        # ── Other players (subtle gray) ───────────────────────────────────────
        for tid, bbox in player_tracks.items():
            if tid == self._focus_id:
                continue
            x1, y1, x2, y2 = (int(v) for v in bbox)
            cv2.rectangle(out, (x1, y1), (x2, y2), (120, 120, 120), 1)

        # ── Focus player (orange box + ID badge) ─────────────────────────────
        focus_bbox = player_tracks.get(self._focus_id) if self._focus_id else None
        if focus_bbox:
            x1, y1, x2, y2 = (int(v) for v in focus_bbox)
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 165, 255), 2)
            label = f"#{self._focus_id}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(out, (x1, y1 - th - 8), (x1 + tw + 6, y1), (0, 165, 255), -1)
            cv2.putText(out, label, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        # ── Pose skeleton ─────────────────────────────────────────────────────
        if pose_data:
            self._pose_analyzer.draw_skeleton(out, pose_data, color=(0, 255, 120))
            if is_release and elbow_angle is not None:
                arm = self._pose_analyzer.detect_shooting_arm(pose_data)
                elbow_pt = self._pose_analyzer.get_joint(pose_data, f"{arm}_elbow")
                if elbow_pt:
                    ex, ey = int(elbow_pt[0]), int(elbow_pt[1])
                    in_range = 75 <= elbow_angle <= 105
                    dot_color = (0, 220, 80) if in_range else (30, 30, 230)
                    cv2.circle(out, (ex, ey), 10, dot_color, -1)
                    cv2.putText(out, f"{elbow_angle:.0f}\u00b0", (ex + 13, ey - 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, dot_color, 2)

        # ── Ball (orange circle) ──────────────────────────────────────────────
        if ball_bbox:
            bx1, by1, bx2, by2 = (int(v) for v in ball_bbox)
            cx = (bx1 + bx2) // 2
            cy = (by1 + by2) // 2
            r = max(10, (bx2 - bx1) // 2)
            cv2.circle(out, (cx, cy), r, (0, 140, 255), 2)
            cv2.circle(out, (cx, cy), 3, (0, 140, 255), -1)

        # ── Hoop (blue box) ───────────────────────────────────────────────────
        if hoop_bbox:
            hx1, hy1, hx2, hy2 = (int(v) for v in hoop_bbox)
            cv2.rectangle(out, (hx1, hy1), (hx2, hy2), (255, 80, 0), 2)

        # ── Shot zone debug overlay (draws zone rect + rim line when hoop seen) ─
        self._shot_tracker.draw_debug(out)

        # ── HUD panel (top-left, semi-transparent) ────────────────────────────
        pct_str = f"{made / attempted:.0%}" if attempted > 0 else "\u2014"
        ball_dot = "\u25cf" if ball_bbox else "\u25cb"
        hoop_dot = "\u25cf" if hoop_bbox else "\u25cb"
        hud_lines = [
            f"FG  {made} / {attempted}  ({pct_str})",
            f"t   {self._frame_idx / self._fps:.1f}s",
            f"BALL {ball_dot}   HOOP {hoop_dot}",
        ]
        line_h, pad, panel_w = 22, 10, 200
        panel_h = pad + len(hud_lines) * line_h + pad // 2
        overlay = out.copy()
        cv2.rectangle(overlay, (6, 6), (6 + panel_w, 6 + panel_h), (15, 15, 15), -1)
        cv2.addWeighted(overlay, 0.70, out, 0.30, 0, out)
        for i, line in enumerate(hud_lines):
            cv2.putText(out, line, (14, pad + 14 + i * line_h),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (210, 210, 210), 1)

        # ── Shot event flash (centre, fades over 1.5 s) ───────────────────────
        if shot_event == "MADE":
            self._ann_flash_frame = self._frame_idx
            self._ann_flash_text = "MADE!"
            self._ann_flash_color = (40, 210, 40)
        elif shot_event == "MISS":
            self._ann_flash_frame = self._frame_idx
            self._ann_flash_text = "MISS"
            self._ann_flash_color = (40, 40, 220)

        frames_since = self._frame_idx - self._ann_flash_frame
        if frames_since < int(self._fps * 1.5) and self._ann_flash_text:
            alpha = max(0.0, 1.0 - frames_since / (self._fps * 1.5))
            text = self._ann_flash_text
            raw = self._ann_flash_color
            color = (int(raw[0] * alpha), int(raw[1] * alpha), int(raw[2] * alpha))
            fs, thick = 2.0, 4
            (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, fs, thick)
            tx, ty = (w - tw) // 2, h // 3
            cv2.putText(out, text, (tx + 2, ty + 2),
                        cv2.FONT_HERSHEY_DUPLEX, fs, (0, 0, 0), thick + 2)
            cv2.putText(out, text, (tx, ty),
                        cv2.FONT_HERSHEY_DUPLEX, fs, color, thick)

        # ── Coaching cue (bottom-centre, shown for 3 s) ───────────────────────
        if cue is not None:
            self._ann_last_cue = cue
            self._ann_last_cue_frame = self._frame_idx

        if (
            self._ann_last_cue is not None
            and self._frame_idx - self._ann_last_cue_frame < int(self._fps * 3)
        ):
            cue_color = {
                "success": (60, 220, 80),
                "warning": (30, 150, 255),
                "info":    (200, 180, 40),
            }.get(self._ann_last_cue.severity, (200, 200, 200))
            cue_text = self._ann_last_cue.text
            fs, thick = 0.9, 2
            (tw, _), _ = cv2.getTextSize(cue_text, cv2.FONT_HERSHEY_SIMPLEX, fs, thick)
            tx, ty = (w - tw) // 2, h - 30
            cv2.putText(out, cue_text, (tx + 1, ty + 1),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 0, 0), thick + 2)
            cv2.putText(out, cue_text, (tx, ty),
                        cv2.FONT_HERSHEY_SIMPLEX, fs, cue_color, thick)

        return out
