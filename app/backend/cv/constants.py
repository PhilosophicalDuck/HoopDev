"""
YOLO class IDs and shared pipeline frame constants.

Class IDs come from Basketball-Players-17/data.yaml.
Frame constants are shared between live_pipeline and video_pipeline.
"""

# ── YOLO detection class IDs ──────────────────────────────────────────────────
CLS_BALL: int = 0
CLS_HOOP: int = 2
CLS_PLAYER: int = 4

# ── Ball median filter ────────────────────────────────────────────────────────
BALL_FILTER_WINDOW: int = 5        # frames in rolling median smoother

# ── Highlight capture ─────────────────────────────────────────────────────────
PRE_SHOT_FRAMES: int = 90          # frames before made shot to keep (3s @ 30fps)
POST_SHOT_FRAMES: int = 60         # frames after made shot to keep (2s @ 30fps)

# ── Focus player selection ────────────────────────────────────────────────────
MIN_FOCUS_DETECTIONS: int = 10     # consecutive detections before locking focus ID

# ── Video pipeline ────────────────────────────────────────────────────────────
PROGRESS_INTERVAL: int = 30        # report progress every N frames
