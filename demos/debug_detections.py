"""
debug_detections.py — Prints every detection the model makes on a sample frame.

Usage:
    python demos/debug_detections.py --video input_videos/first_form_shot.mp4
    python demos/debug_detections.py --video input_videos/first_form_shot.mp4 --frame 60

Shows all classes detected, their confidence scores, and saves an annotated
image so you can see exactly what the model sees.
"""
import argparse
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backend.config import settings
from ultralytics import YOLO

# Class names from the Roboflow Basketball-Players-17 dataset (alphabetical)
CLASS_NAMES = {
    0: "Ball",
    1: "Clock",
    2: "Hoop",
    3: "Overlay",
    4: "Player",
    5: "Ref",
    6: "Scoreboard",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--frame", type=int, default=30,
                        help="Frame index to sample (default: 30)")
    parser.add_argument("--conf", type=float, default=0.01,
                        help="Minimum confidence to show (default: 0.01 — shows everything)")
    parser.add_argument("--model", default=None,
                        help="Override model path (default: uses config)")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: {video_path} not found")
        sys.exit(1)

    # Grab the frame
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_idx = min(args.frame, total - 1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ok, frame = cap.read()
    cap.release()

    if not ok:
        print(f"Could not read frame {frame_idx}")
        sys.exit(1)

    model_path = args.model or settings.detection_model_path
    print(f"\n  Model  : {Path(model_path).name}")
    print(f"  Video  : {video_path.name}  ({total} frames)")
    print(f"  Frame  : {frame_idx}")
    print(f"  Size   : {frame.shape[1]}x{frame.shape[0]}")
    print()

    # Run model at very low confidence to see everything
    model = YOLO(model_path)
    results = model.predict(frame, conf=args.conf, verbose=False)[0]
    boxes = results.boxes

    if boxes is None or len(boxes) == 0:
        print("  No detections at all — model may not suit this video.")
        sys.exit(0)

    # Sort by confidence descending
    detections = []
    for b in boxes:
        cls_id = int(b.cls[0])
        conf   = float(b.conf[0])
        xyxy   = b.xyxy[0].tolist()
        name   = CLASS_NAMES.get(cls_id, f"cls_{cls_id}")
        detections.append((conf, cls_id, name, xyxy))
    detections.sort(reverse=True)

    print(f"  {'Class':<14} {'Cls ID':>6}  {'Conf':>6}  {'BBox (x1,y1,x2,y2)'}")
    print(f"  {'─'*14} {'─'*6}  {'─'*6}  {'─'*32}")
    for conf, cls_id, name, xyxy in detections:
        x1, y1, x2, y2 = [int(v) for v in xyxy]
        print(f"  {name:<14} {cls_id:>6}  {conf:>6.3f}  ({x1}, {y1}, {x2}, {y2})")

    # Check specifically for hoops
    hoop_detections = [(c, co, x) for c, co, n, x in detections if n == "Hoop"]
    print()
    if hoop_detections:
        print(f"  Hoop detections found: {len(hoop_detections)}")
        best_conf = hoop_detections[0][1]
        print(f"  Best hoop confidence : {best_conf:.3f}")
        if best_conf < 0.3:
            print(f"  !! Pipeline threshold is 0.3 — hoop is detected but filtered out!")
            print(f"     Fix: lower conf threshold in video_pipeline.py to 0.15")
    else:
        print(f"  No Hoop class detected at any confidence.")
        print(f"  Check: is the basket clearly visible in frame {frame_idx}?")
        print(f"  Try a different frame with --frame N")

    # Save annotated debug image
    out_path = Path("demos/output/debug_frame.jpg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    annotated = frame.copy()
    for conf, cls_id, name, xyxy in detections:
        x1, y1, x2, y2 = [int(v) for v in xyxy]
        color = (0, 255, 0) if name == "Hoop" else \
                (0, 165, 255) if name == "Ball" else \
                (200, 200, 200)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"{name} {conf:.2f}"
        cv2.putText(annotated, label, (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    cv2.imwrite(str(out_path), annotated)
    print(f"\n  Saved annotated frame → {out_path.resolve()}\n")


if __name__ == "__main__":
    main()
