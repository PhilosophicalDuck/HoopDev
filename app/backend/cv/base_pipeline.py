"""
BasePipeline: shared frame-processing helpers for LivePipeline and VideoPipeline.

Subclasses must call _init_pipeline_state() in their __init__ before using
any helper method. The _metrics attribute must be set by the subclass before
calling get_current_speed().
"""
from __future__ import annotations

import logging
from collections import deque

import numpy as np

from app.backend.cv.constants import BALL_FILTER_WINDOW

logger = logging.getLogger(__name__)


class BasePipeline:
    """
    Base class providing shared stateful helpers for CV pipelines.

    Does NOT own model or metrics objects — subclasses do.
    Call _init_pipeline_state() from subclass __init__.
    """

    def _init_pipeline_state(self) -> None:
        """Initialize shared state. Must be called from subclass __init__."""
        self._ball_history: deque = deque(maxlen=BALL_FILTER_WINDOW)
        self._last_ball_wh: tuple[float, float] | None = None   # (w, h) of last good detection
        self._track_counts: dict[int, int] = {}
        self._focus_id: int | None = None

        import supervision as sv
        self._tracker = sv.ByteTrack()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _update_bytetrack(
        self,
        bboxes: list,
        confs: list,
    ) -> dict[int, list]:
        """Run ByteTrack on current player detections; return {track_id: bbox}."""
        import supervision as sv
        if not bboxes:
            return {}
        det = sv.Detections(
            xyxy=np.array(bboxes, dtype=float),
            confidence=np.array(confs, dtype=float),
        )
        tracked = self._tracker.update_with_detections(det)
        tracker_ids = tracked.tracker_id
        if tracker_ids is None or len(tracker_ids) == 0:
            return {}
        return {
            int(tid): tracked.xyxy[i].tolist()
            for i, tid in enumerate(tracker_ids)
        }

    def _smooth_ball(self, raw_bbox: list | None) -> list | None:
        """
        Return a smoothed ball bbox using recent detection history.

        When the ball IS detected: smooth its position using a median of recent
        centres (reduces jitter) and cache its size for later.

        When the ball is NOT detected: return an estimated position from recent
        history using the cached size.  This keeps the ball "alive" for up to
        BALL_FILTER_WINDOW frames after the last good detection so that the shot
        tracker can still see it during brief occlusions or detection drops.

        Returns None only when there is no recent history at all.
        """
        recent = [p for p in self._ball_history if p is not None]

        if raw_bbox:
            # Cache the ball size whenever we have a live detection
            w = raw_bbox[2] - raw_bbox[0]
            h = raw_bbox[3] - raw_bbox[1]
            self._last_ball_wh = (w, h)

        if not recent:
            return raw_bbox  # no history — pass through whatever we have

        xs = [p[0] for p in recent]
        ys = [p[1] for p in recent]
        smooth_cx = sorted(xs)[len(xs) // 2]
        smooth_cy = sorted(ys)[len(ys) // 2]

        # Prefer live detection size; fall back to last cached size
        if raw_bbox:
            w = raw_bbox[2] - raw_bbox[0]
            h = raw_bbox[3] - raw_bbox[1]
        elif self._last_ball_wh:
            w, h = self._last_ball_wh
        else:
            return raw_bbox  # no size info — can't reconstruct bbox

        return [
            smooth_cx - w / 2,
            smooth_cy - h / 2,
            smooth_cx + w / 2,
            smooth_cy + h / 2,
        ]

    def get_current_speed(self) -> float:
        """
        Return a smoothed speed reading from the metrics accumulator.
        Subclasses must set self._metrics before calling this.
        """
        hist = self._metrics.get_raw_speeds()
        if len(hist) < 2:
            return 0.0
        window = hist[-5:]
        return sum(window) / len(window)
