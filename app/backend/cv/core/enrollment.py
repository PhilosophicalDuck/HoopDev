import cv2
import numpy as np
from ultralytics import YOLO

from .player_tracker import get_jersey_features, PLAYER_CLASS
from .shot_tracker import best_detection


def run_enrollment(
    video_path: str,
    model: YOLO,
    sample_interval: int = 5,
    duration_s: float | None = None,
) -> list[np.ndarray]:
    """
    Run YOLO on video_path and collect jersey HSV feature vectors for the focus person.

    Assumes the enrollment video contains primarily the focus person (e.g., doing a 360°
    rotation in front of the camera). Takes the highest-confidence PLAYER_CLASS detection
    per sampled frame.

    Args:
        video_path:       Path to the enrollment video file.
        model:            Loaded YOLO model instance (reused from main pipeline).
        sample_interval:  Extract features every N frames.
        duration_s:       Stop after this many seconds of video. None = process all.

    Returns:
        List of 6-element numpy arrays [H_mean, H_std, S_mean, S_std, V_mean, V_std].
        Empty list if no valid detections found.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [enrollment] Could not open video: {video_path}")
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.release()

    max_frames = int(duration_s * fps) if duration_s is not None else None

    gallery = []
    frame_idx = 0

    for result in model.predict(video_path, stream=True, verbose=False):
        if max_frames is not None and frame_idx >= max_frames:
            break

        if frame_idx % sample_interval == 0:
            box = best_detection(result.boxes, PLAYER_CLASS)
            if box is not None:
                feats = get_jersey_features(result.orig_img, box.xyxy[0].tolist())
                if feats is not None:
                    gallery.append(feats)

        frame_idx += 1

    print(f"  [enrollment] {frame_idx} frames scanned, {len(gallery)} feature samples collected.")
    return gallery
