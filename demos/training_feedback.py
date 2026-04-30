"""
training_feedback.py — Standalone drill analysis and coaching feedback.

Processes a basketball drill video and produces a detailed coaching report:
shot percentage, elbow angles, arc, follow-through, dribble rhythm, footwork,
and actionable improvement tips.

Usage:
    python demos/training_feedback.py --video input_videos/drill.mp4
    python demos/training_feedback.py --video input_videos/drill.mp4 --drill shooting
    python demos/training_feedback.py --video input_videos/drill.mp4 --drill auto --json

Drill types: shooting | ball_handling | footwork | general | auto (default)

Requirements:
    pip install ultralytics opencv-python supervision numpy
"""

import argparse
import json
import sys
from pathlib import Path

# Make the Capstone root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backend.cv.video_pipeline import VideoPipeline
from app.backend.config import settings, model_paths_for_drill


# ── Progress bar ──────────────────────────────────────────────────────────────

def _progress(frame_idx: int, total: int) -> None:
    pct = int(frame_idx / total * 100) if total > 0 else 0
    filled = pct // 5
    bar = "█" * filled + "░" * (20 - filled)
    print(f"\r  [{bar}] {pct}%  ({frame_idx}/{total} frames)", end="", flush=True)


# ── Report formatting ─────────────────────────────────────────────────────────

def _print_report(snapshot: dict, feedback: dict) -> None:
    sep = "=" * 56
    thin = "─" * 56

    print(f"\n  {sep}")
    print(f"  DRILL ANALYSIS REPORT — {feedback['drill_type'].upper()}")
    print(f"  {sep}")

    # Stats
    dur = snapshot.get("duration_s", 0)
    fps = snapshot.get("fps", 30)
    frames = snapshot.get("total_frames", 0)
    mins, secs = divmod(int(dur), 60)
    print(f"  Duration   : {mins:02d}:{secs:02d}  ({frames} frames @ {fps:.0f} fps)")

    shots_made = snapshot.get("shots_made", 0)
    shots_att  = snapshot.get("shots_attempted", 0)
    shot_pct   = snapshot.get("shot_percentage")
    if shots_att > 0:
        pct_str = f"{shot_pct:.0%}" if shot_pct is not None else "n/a"
        print(f"  Shooting   : {shots_made}/{shots_att} FG  ({pct_str})")

    avg_spd = snapshot.get("avg_speed_px_per_s", 0)
    top_spd = snapshot.get("top_speed_px_per_s", 0)
    print(f"  Speed      : avg {avg_spd:.0f} px/s  |  top {top_spd:.0f} px/s")

    elbows = snapshot.get("release_elbow_angles", [])
    if elbows:
        mean_elbow = sum(elbows) / len(elbows)
        print(f"  Elbow avg  : {mean_elbow:.1f}°  (target 75–105°)")

    arcs = snapshot.get("arc_angles_deg", [])
    if arcs:
        mean_arc = sum(arcs) / len(arcs)
        print(f"  Arc avg    : {mean_arc:.1f}°  (target 42–58°)")

    ft = snapshot.get("follow_through_detected", [])
    if ft:
        ft_ratio = sum(ft) / len(ft)
        print(f"  Follow-thru: {ft_ratio:.0%} of shots")

    # Strengths
    strengths = feedback.get("strengths", [])
    print(f"\n  {thin}")
    print(f"  STRENGTHS ({len(strengths)})")
    if strengths:
        for s in strengths:
            print(f"    + {s}")
    else:
        print("    (none identified yet — keep working!)")

    # Improvements
    improvements = feedback.get("improvements", [])
    tips = feedback.get("coaching_tips", {})
    print(f"\n  AREAS TO IMPROVE ({len(improvements)})")
    if improvements:
        for label in improvements:
            print(f"    - {label}")
            tip = tips.get(label, "")
            if tip:
                # Wrap tip text at 60 chars
                words = tip.split()
                line, lines = "      ", []
                for word in words:
                    if len(line) + len(word) + 1 > 64:
                        lines.append(line)
                        line = "      " + word
                    else:
                        line += ("" if line.strip() == "" else " ") + word
                if line.strip():
                    lines.append(line)
                print("\n".join(lines))
    else:
        print("    (no specific improvements flagged)")

    print(f"\n  {sep}\n")


def _save_json(snapshot: dict, feedback: dict, output_path: Path) -> None:
    data = {
        "drill_type": feedback.get("drill_type"),
        "duration_s": snapshot.get("duration_s"),
        "fps": snapshot.get("fps"),
        "total_frames": snapshot.get("total_frames"),
        "shooting": {
            "shots_made": snapshot.get("shots_made"),
            "shots_attempted": snapshot.get("shots_attempted"),
            "shot_percentage": snapshot.get("shot_percentage"),
            "release_elbow_angles": snapshot.get("release_elbow_angles"),
            "arc_angles_deg": snapshot.get("arc_angles_deg"),
            "follow_through_detected": snapshot.get("follow_through_detected"),
            "release_consistency_cv": snapshot.get("release_consistency_cv"),
        },
        "movement": {
            "avg_speed_px_per_s": snapshot.get("avg_speed_px_per_s"),
            "top_speed_px_per_s": snapshot.get("top_speed_px_per_s"),
            "active_frames": snapshot.get("active_frames"),
            "lateral_speed_px_per_s": snapshot.get("lateral_speed_px_per_s"),
            "step_cadence_hz": snapshot.get("step_cadence_hz"),
        },
        "ball_handling": {
            "hand_switches": snapshot.get("hand_switches"),
            "dribble_rhythm_cv": snapshot.get("dribble_rhythm_cv"),
            "avg_possession_duration_s": snapshot.get("avg_possession_duration_s"),
        },
        "coaching_report": {
            "strengths": feedback.get("strengths"),
            "improvements": feedback.get("improvements"),
            "coaching_tips": feedback.get("coaching_tips"),
        },
        "cue_log": snapshot.get("cue_log", []),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  Report saved: {output_path.resolve()}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse a basketball drill video and generate a coaching report."
    )
    parser.add_argument("--video", required=True,        help="Path to input video file")
    parser.add_argument("--drill", default="auto",
                        choices=["shooting", "ball_handling", "footwork", "general", "auto"],
                        help="Drill type (default: auto-detect)")
    parser.add_argument("--output",   default="demos/output", help="Output directory (default: demos/output)")
    parser.add_argument("--json",     action="store_true",   help="Save full metrics report as JSON")
    parser.add_argument("--annotate", action="store_true",   help="Write annotated MP4 with boxes, skeleton, and HUD")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: video file not found: {video_path}")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Basketball Training Feedback")
    print(f"  {'─' * 40}")
    print(f"  Input  : {video_path}")
    print(f"  Drill  : {args.drill}")
    model_cfg = model_paths_for_drill(args.drill)
    hoop_name = Path(model_cfg["hoop_model_path"]).name if model_cfg["hoop_model_path"] else "n/a"
    pose_name = Path(model_cfg["pose_model_name"]).name if model_cfg["pose_model_name"] else "n/a"
    print(f"  Models : {Path(model_cfg['detection_model_path']).name} (ball+player)")
    print(f"           {hoop_name} (hoop)")
    print(f"           {pose_name} (pose)")
    if args.annotate:
        annotated_path = output_dir / f"{video_path.stem}_annotated.mp4"
        print(f"  Output : {annotated_path}")
    print()

    # ── Run pipeline ──────────────────────────────────────────────────────────
    print("  Processing video...")
    pipeline = VideoPipeline(
        video_path=str(video_path),
        drill_type=args.drill,
        annotate=args.annotate,
        **model_cfg,
    )

    video_writer = None
    if args.annotate:
        import cv2 as _cv2
        fourcc = _cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = _cv2.VideoWriter(
            str(annotated_path),
            fourcc,
            pipeline._fps,
            (pipeline._frame_w, pipeline._frame_h),
        )

    for result in pipeline.run(on_progress=_progress):
        if video_writer is not None and result.annotated_frame is not None:
            video_writer.write(result.annotated_frame)

    if video_writer is not None:
        video_writer.release()
        print(f"\n  Annotated video: {annotated_path.resolve()}")

    print()  # newline after progress bar

    snapshot_dict, feedback_dict, diag_dict = pipeline.finalize()

    # ── Detection diagnostics ─────────────────────────────────────────────────
    total = diag_dict["total_frames"]
    print(f"  Detection rates ({total} frames):")
    print(f"    Ball : {diag_dict['ball_detected_frames']:5d} frames  ({diag_dict['ball_detection_rate']:.0%})")
    print(f"    Hoop : {diag_dict['hoop_detected_frames']:5d} frames  ({diag_dict['hoop_detection_rate']:.0%})")
    print(f"    Both : {diag_dict['both_detected_frames']:5d} frames  ({diag_dict['both_detected_frames']/total:.0%})  ← shots can only be counted here")
    if diag_dict["hoop_detection_rate"] < 0.1:
        print(f"\n  !! Hoop barely visible — ensure the basket is in frame for accurate shot counting")
    if diag_dict["ball_detection_rate"] < 0.2:
        print(f"\n  !! Ball rarely detected — check lighting and that ball is visible to camera")
    print()

    # ── Print report ──────────────────────────────────────────────────────────
    _print_report(snapshot_dict, feedback_dict)

    # ── Save JSON ─────────────────────────────────────────────────────────────
    if args.json:
        json_path = output_dir / f"{video_path.stem}_report.json"
        _save_json(snapshot_dict, feedback_dict, json_path)


if __name__ == "__main__":
    main()
