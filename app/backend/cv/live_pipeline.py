"""
LivePipeline: single-pass real-time webcam processing.

Threading model:
  - This class runs in a ThreadPoolExecutor worker (blocking CV ops).
  - Results are pushed onto an asyncio.Queue that the WebSocket handler drains.
  - CameraManager and RingBuffer are shared state; all CV work stays in this thread.
"""
import logging
import threading
from dataclasses import dataclass

import numpy as np

from app.backend.cv.core import ShotTracker, PoseAnalyzer, DrillMetricsAccumulator, DrillReport, best_detection, box_center
from app.backend.cv.feedback_engine import FeedbackEngine, FrameResult, CoachingCue
from app.backend.cv.frame_buffer import RingBuffer
from app.backend.cv.base_pipeline import BasePipeline
from app.backend.cv.constants import (
    CLS_BALL, CLS_HOOP, CLS_PLAYER,
    PRE_SHOT_FRAMES, POST_SHOT_FRAMES,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Everything the WebSocket handler needs to send a message."""
    frame_idx: int
    frame_result: FrameResult
    shot_event: str | None = None          # "MADE" | "MISS" | None
    cue: CoachingCue | None = None
    annotated_frame: np.ndarray | None = None


class LivePipeline(BasePipeline):
    """
    Processes webcam frames one at a time.

    Usage:
        pipeline = LivePipeline(...)
        # In worker thread:
        while running:
            frame = camera.read_frame()
            result = pipeline.process_frame(frame)
            loop.call_soon_threadsafe(queue.put_nowait, result)
        summary, feedback = pipeline.finalize()
    """

    def __init__(
        self,
        detection_model_path: str,
        pose_model_name: str,
        drill_type: str,
        fps: float,
        ring_buffer: RingBuffer,
        hoop_model_path: str | None = None,
    ):
        self._drill_type = drill_type
        self._fps = fps
        self._ring_buffer = ring_buffer
        self._frame_idx = 0
        self._stop_event = threading.Event()

        # ── Load models ───────────────────────────────────────────────────────
        logger.info("Loading detection model: %s", detection_model_path)
        from ultralytics import YOLO
        self._detector = YOLO(detection_model_path)
        self._detector.to("cpu")
        self._hoop_detector: YOLO | None = None
        if hoop_model_path:
            self._hoop_detector = YOLO(hoop_model_path)
            self._hoop_detector.to("cpu")
            logger.info("Hoop model loaded: %s", hoop_model_path)
        self._pose_analyzer = PoseAnalyzer(model_name=pose_model_name) if pose_model_name else None
        logger.info("Models loaded.")

        # ── CV components ─────────────────────────────────────────────────────
        self._shot_tracker = ShotTracker()
        self._metrics = DrillMetricsAccumulator(drill_type=drill_type, fps=fps)
        self._feedback = FeedbackEngine(fps=fps, drill_type=drill_type)

        # Shared pipeline state (ball history, tracker, focus ID)
        self._init_pipeline_state()

        # Post-MADE buffer: collect POST_SHOT_FRAMES after a made shot
        self._pending_highlights: list[dict] = []

    # ─────────────────────────────────────────────────────────────────────────

    def process_frame(self, frame: np.ndarray) -> PipelineResult:
        """
        Process one camera frame synchronously.
        Called from the worker thread.
        """
        self._frame_idx += 1
        idx = self._frame_idx

        # Push raw frame into ring buffer before any processing
        self._ring_buffer.push(frame.copy())

        # ── YOLO detection — ball + player from main model ────────────────────
        results = self._detector.predict(frame, verbose=False, conf=0.3)[0]
        boxes = results.boxes

        ball_bbox = best_detection(boxes, CLS_BALL)

        # Hoop: run dedicated model every 10 frames — hoop doesn't move between frames
        if self._hoop_detector is not None:
            if idx % 10 == 1:
                hoop_results = self._hoop_detector.predict(frame, verbose=False, conf=0.15)[0]
                detected = best_detection(hoop_results.boxes, CLS_HOOP)
                if detected is not None:
                    self._last_hoop_bbox = detected
            hoop_bbox = getattr(self, "_last_hoop_bbox", None)
        else:
            hoop_bbox = best_detection(boxes, CLS_HOOP)

        # Player detections → ByteTrack
        player_bboxes = [
            b.xyxy[0].tolist()
            for b in boxes
            if int(b.cls[0]) == CLS_PLAYER
        ]
        player_confs = [
            float(b.conf[0])
            for b in boxes
            if int(b.cls[0]) == CLS_PLAYER
        ]
        player_tracks = self._update_bytetrack(player_bboxes, player_confs)

        # ── Ball smoothing (5-frame median filter) ────────────────────────────
        if ball_bbox:
            cx, cy = box_center(ball_bbox)
            self._ball_history.append((cx, cy))
        else:
            self._ball_history.append(None)

        smoothed_ball = self._smooth_ball(ball_bbox)

        # ── Focus player ──────────────────────────────────────────────────────
        for tid in player_tracks:
            self._track_counts[tid] = self._track_counts.get(tid, 0) + 1
        if self._track_counts:
            self._focus_id = max(self._track_counts, key=self._track_counts.get)
        focus_bbox = player_tracks.get(self._focus_id) if self._focus_id else None

        # ── Pose ─────────────────────────────────────────────────────────────
        pose_data = None
        if focus_bbox is not None and self._pose_analyzer is not None:
            pose_data = self._pose_analyzer.extract_keypoints(frame, focus_bbox)

        # ── Shot tracker ──────────────────────────────────────────────────────
        shot_event, _ = self._shot_tracker.update(
            frame_idx=idx,
            ball_bbox=smoothed_ball,
            hoop_bbox=hoop_bbox,
            possessing_team="A",
            last_known_possessing_team="A",
        )

        # ── Metrics accumulation ──────────────────────────────────────────────
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

        # ── Elbow angle (for live feedback) ──────────────────────────────────
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

            # Follow-through: wrist above shoulder after release
            if wrist and shoulder:
                follow_through = wrist[1] < shoulder[1]  # y-axis inverted in image coords

        # ── Build FrameResult for feedback engine ─────────────────────────────
        made = self._shot_tracker.made.get("A", 0) + self._shot_tracker.made.get("B", 0)
        attempted = made + self._shot_tracker.missed.get("A", 0) + self._shot_tracker.missed.get("B", 0)

        frame_result = FrameResult(
            frame_idx=idx,
            shot_state=self._shot_tracker.state,
            shot_event=shot_event,
            elbow_angle=elbow_angle,
            arc_angle=None,  # computed post-shot in metrics; snapshot on shot_event
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

        # ── Feedback cue ──────────────────────────────────────────────────────
        cue = self._feedback.update(frame_result)

        return PipelineResult(
            frame_idx=idx,
            frame_result=frame_result,
            shot_event=shot_event,
            cue=cue,
            annotated_frame=None,  # skip annotation for now — saves ~10ms
        )

    def finalize(self) -> tuple[dict, dict]:
        """
        Call after the session ends.
        Returns (snapshot_dict, feedback_dict) for DB persistence and WS message.
        """
        snapshot = self._metrics.finalize()
        report = DrillReport(snapshot)
        feedback = report.generate()

        shots_made = self._shot_tracker.made.get("A", 0) + self._shot_tracker.made.get("B", 0)
        shots_missed = self._shot_tracker.missed.get("A", 0) + self._shot_tracker.missed.get("B", 0)
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
        }

        feedback_dict = {
            "drill_type": feedback.drill_type,
            "strengths": feedback.strengths,
            "improvements": feedback.improvements,
            "coaching_tips": feedback.coaching_tips,
        }

        logger.info(
            "Session finalized — %d frames, %.1fs, %d/%d FG",
            snapshot.total_frames, snapshot.duration_s,
            snap_dict["shots_made"], snap_dict["shots_attempted"],
        )
        return snap_dict, feedback_dict

    def stop(self) -> None:
        self._stop_event.set()
