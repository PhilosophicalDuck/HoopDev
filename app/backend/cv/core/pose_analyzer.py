import math
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

JOINT_NAMES: dict[str, int] = {
    "nose": 0,
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_hip": 11,
    "right_hip": 12,
    "left_knee": 13,
    "right_knee": 14,
    "left_ankle": 15,
    "right_ankle": 16,
}

SKELETON_EDGES = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
]


class PoseAnalyzer:
    """Wraps a YOLOv11-pose model to extract 17 COCO keypoints per player."""

    def __init__(
        self,
        model_name: str = "yolo11n-pose.pt",
        conf_threshold: float = 0.5,
    ) -> None:
        self._model = YOLO(model_name)
        self._conf = conf_threshold

    def extract_keypoints(
        self,
        frame: np.ndarray,
        player_bbox: list[float],
        padding: float = 0.15,
    ) -> dict[str, Any] | None:
        """
        Crop frame to player_bbox with padding, run pose inference.
        Returns keypoints remapped to original frame pixel coordinates, or None.

        Return dict shape:
            {
                "keypoints": np.ndarray (17, 3),  # x, y, confidence
                "bbox_offset": (x_offset, y_offset),
            }
        """
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = [float(v) for v in player_bbox]
        bw = x2 - x1
        bh = y2 - y1
        px = bw * padding
        py = bh * padding
        cx1 = max(0, int(x1 - px))
        cy1 = max(0, int(y1 - py))
        cx2 = min(w, int(x2 + px))
        cy2 = min(h, int(y2 + py))
        if (cx2 - cx1) < 32 or (cy2 - cy1) < 32:
            return None
        crop = frame[cy1:cy2, cx1:cx2]
        results = self._model.predict(crop, conf=self._conf, verbose=False)
        if not results or results[0].keypoints is None:
            return None
        kp_data = results[0].keypoints
        if kp_data.xy is None or len(kp_data.xy) == 0:
            return None
        xy = kp_data.xy[0].cpu().numpy()       # (17, 2)
        conf = kp_data.conf[0].cpu().numpy()   # (17,)
        kp_full = np.zeros((17, 3), dtype=np.float32)
        kp_full[:, 0] = xy[:, 0] + cx1        # remap x to original frame
        kp_full[:, 1] = xy[:, 1] + cy1        # remap y to original frame
        kp_full[:, 2] = conf
        return {
            "keypoints": kp_full,
            "bbox_offset": (cx1, cy1),
        }

    def get_joint(
        self,
        kp_data: dict[str, Any],
        joint_name: str,
        min_conf: float = 0.3,
    ) -> tuple[float, float] | None:
        """Return (x, y) in original frame coords for a named joint, or None if low confidence."""
        idx = JOINT_NAMES.get(joint_name)
        if idx is None:
            return None
        kp = kp_data["keypoints"]
        if kp[idx, 2] < min_conf:
            return None
        return float(kp[idx, 0]), float(kp[idx, 1])

    def compute_angle(
        self,
        a: tuple[float, float],
        b: tuple[float, float],
        c: tuple[float, float],
    ) -> float:
        """Interior angle at vertex b in degrees [0, 180]."""
        v1 = (a[0] - b[0], a[1] - b[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        n1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        n2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
        if n1 < 1e-9 or n2 < 1e-9:
            return 0.0
        cos_val = max(-1.0, min(1.0, dot / (n1 * n2)))
        return math.degrees(math.acos(cos_val))

    def detect_shooting_arm(self, kp_data: dict[str, Any]) -> str:
        """Infer shooting arm by finding which wrist is higher (smaller y = higher on screen)."""
        lw = self.get_joint(kp_data, "left_wrist")
        rw = self.get_joint(kp_data, "right_wrist")
        if lw is None and rw is None:
            return "unknown"
        if lw is None:
            return "right"
        if rw is None:
            return "left"
        return "left" if lw[1] < rw[1] else "right"

    def is_release_candidate(
        self,
        kp_data: dict[str, Any],
        ball_bbox: list[float] | None,
    ) -> bool:
        """
        True if frame looks like a shooting release:
        - At least one wrist is above (smaller y than) its ipsilateral shoulder
        - Ball bbox overlaps wrist region within 40px (if ball is visible)
        """
        arm = self.detect_shooting_arm(kp_data)
        if arm == "unknown":
            return False
        wrist_key = f"{arm}_wrist"
        shoulder_key = f"{arm}_shoulder"
        wrist = self.get_joint(kp_data, wrist_key)
        shoulder = self.get_joint(kp_data, shoulder_key)
        if wrist is None or shoulder is None:
            return False
        wrist_above_shoulder = wrist[1] < shoulder[1]
        if not wrist_above_shoulder:
            return False
        if ball_bbox is None:
            return True
        bx1, by1, bx2, by2 = ball_bbox
        ball_cx = (bx1 + bx2) / 2
        ball_cy = (by1 + by2) / 2
        dist = math.sqrt((ball_cx - wrist[0]) ** 2 + (ball_cy - wrist[1]) ** 2)
        return dist < 80.0

    def draw_skeleton(
        self,
        frame: np.ndarray,
        kp_data: dict[str, Any],
        color: tuple[int, int, int] = (0, 255, 0),
    ) -> None:
        """Draw 17-point skeleton lines on frame in-place."""
        for joint_a, joint_b in SKELETON_EDGES:
            pa = self.get_joint(kp_data, joint_a)
            pb = self.get_joint(kp_data, joint_b)
            if pa is None or pb is None:
                continue
            cv2.line(frame, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), color, 2)
        for name, idx in JOINT_NAMES.items():
            pt = self.get_joint(kp_data, name)
            if pt is not None:
                cv2.circle(frame, (int(pt[0]), int(pt[1])), 4, color, -1)
