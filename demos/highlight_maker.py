"""
highlight_maker.py — Standalone highlight reel generator.

Processes a basketball video, detects every made shot, and writes a single
MP4 highlight reel containing all makes stitched together.

Usage:
    python demos/highlight_maker.py --video input_videos/game.mp4
    python demos/highlight_maker.py --video input_videos/game.mp4 --output demos/output --pre 90 --post 60

Requirements:
    pip install ultralytics opencv-python supervision numpy
"""

import argparse
import sys
from pathlib import Path

# Make the Capstone root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backend.cv.video_pipeline import VideoPipeline
from app.backend.cv.core.highlight_writer import HighlightWriter
from app.backend.cv.constants import PRE_SHOT_FRAMES, POST_SHOT_FRAMES
from app.backend.config import settings


# ── Progress bar ──────────────────────────────────────────────────────────────

def _progress(frame_idx: int, total: int) -> None:
    pct = int(frame_idx / total * 100) if total > 0 else 0
    filled = pct // 5
    bar = "█" * filled + "░" * (20 - filled)
    print(f"\r  [{bar}] {pct}%  ({frame_idx}/{total} frames)", end="", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a highlight reel of made shots from a basketball video."
    )
    parser.add_argument("--video",  required=True,         help="Path to input video file")
    parser.add_argument("--output", default="demos/output", help="Output directory (default: demos/output)")
    parser.add_argument("--pre",    type=int, default=PRE_SHOT_FRAMES,  help=f"Frames before each made shot (default: {PRE_SHOT_FRAMES})")
    parser.add_argument("--post",   type=int, default=POST_SHOT_FRAMES, help=f"Frames after each made shot (default: {POST_SHOT_FRAMES})")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: video file not found: {video_path}")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video_path.stem}_highlights.mp4"

    print(f"\n  Basketball Highlight Maker")
    print(f"  {'─' * 40}")
    print(f"  Input  : {video_path}")
    print(f"  Output : {output_path}")
    print(f"  Clip   : {args.pre} frames before + {args.post} frames after each make")
    print(f"  Models : {Path(settings.detection_model_path).name}  +  {Path(settings.pose_model_name).name}")
    print()

    # ── Pass 1: detect all made shots ─────────────────────────────────────────
    print("  Processing video...")
    pipeline = VideoPipeline(
        video_path=str(video_path),
        detection_model_path=settings.detection_model_path,
        pose_model_name=settings.pose_model_name,
        hoop_model_path=settings.hoop_model_path,
        drill_type="auto",
    )

    shot_frames: list[int] = []
    shot_times: list[float] = []

    for result in pipeline.run(on_progress=_progress):
        if result.shot_event == "MADE":
            shot_frames.append(result.frame_idx)
            shot_times.append(result.frame_idx / pipeline._fps)

    print()  # newline after progress bar

    if not shot_frames:
        print("\n  No made shots detected. Try a different video or check model paths.")
        sys.exit(0)

    print(f"\n  Found {len(shot_frames)} made shot(s):")
    for i, t in enumerate(shot_times, 1):
        mins, secs = divmod(int(t), 60)
        print(f"    Shot {i:2d} — {mins:02d}:{secs:02d}  (frame {shot_frames[i - 1]})")

    # ── Pass 2: compile highlight reel ────────────────────────────────────────
    print(f"\n  Compiling highlight reel...")
    writer = HighlightWriter(
        output_path=str(output_path),
        fps=pipeline._fps,
        pre_frames=args.pre,
        post_frames=args.post,
    )
    writer._shot_frames = shot_frames
    clips_written = writer.compile(str(video_path), pipeline._total_frames)

    clip_duration = clips_written * (args.pre + args.post + 1) / pipeline._fps
    print(f"  Done. {clips_written} clip(s) written  (~{clip_duration:.1f}s total)")
    print(f"\n  Output: {output_path.resolve()}\n")


if __name__ == "__main__":
    main()
