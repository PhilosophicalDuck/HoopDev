"""Write highlight MP4 clips and thumbnails from a RingBuffer snapshot."""
from __future__ import annotations
import logging
from pathlib import Path
import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.backend.models.highlight import HighlightClip
from app.backend.config import settings, CAPSTONE_ROOT

logger = logging.getLogger(__name__)


def write_clip(
    db: Session,
    frames: list[np.ndarray],
    session_id: int,
    user_id: int,
    shot_frame: int,
    clip_index: int,
    fps: float = 30.0,
) -> HighlightClip | None:
    """
    Write a list of BGR frames to disk as an MP4 and save a DB row.
    Returns the created HighlightClip or None on failure.
    """
    if not frames:
        return None

    highlights_dir = CAPSTONE_ROOT / "highlights"
    highlights_dir.mkdir(exist_ok=True)

    clip_filename = f"{session_id}_{clip_index}.mp4"
    thumb_filename = f"{session_id}_{clip_index}_thumb.jpg"
    clip_path = highlights_dir / clip_filename
    thumb_path = highlights_dir / thumb_filename

    # Write video
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    writer = cv2.VideoWriter(str(clip_path), fourcc, fps, (w, h))
    for frame in frames:
        writer.write(frame)
    writer.release()

    # Write thumbnail — middle frame
    mid = frames[len(frames) // 2]
    cv2.imwrite(str(thumb_path), mid)

    duration_s = len(frames) / fps

    clip = HighlightClip(
        session_id=session_id,
        user_id=user_id,
        file_path=f"highlights/{clip_filename}",
        duration_s=duration_s,
        shot_frame=shot_frame,
        thumbnail_path=f"highlights/{thumb_filename}",
    )
    db.add(clip)
    db.commit()
    db.refresh(clip)
    logger.info("Highlight clip saved: %s (%.1fs)", clip_filename, duration_s)
    return clip
