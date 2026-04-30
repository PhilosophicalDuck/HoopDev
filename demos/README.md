# Standalone Demo Scripts

Run these from the **Capstone project root** — no server, no login, no database needed.

---

## Setup

```bash
pip install ultralytics opencv-python supervision numpy
```

---

## Highlight Maker

Finds every made shot in a video and stitches them into a single highlight reel MP4.

```bash
# Basic usage
python demos/highlight_maker.py --video input_videos/game.mp4

# Custom clip window (default: 90 frames before, 60 after each make)
python demos/highlight_maker.py --video input_videos/game.mp4 --pre 90 --post 90

# Custom output folder
python demos/highlight_maker.py --video input_videos/game.mp4 --output my_highlights
```

**Output:** `demos/output/{video_name}_highlights.mp4`

---

## Training Feedback

Runs full drill analysis on a video and prints a coaching report.

```bash
# Auto-detect drill type
python demos/training_feedback.py --video input_videos/drill.mp4

# Specify drill type
python demos/training_feedback.py --video input_videos/drill.mp4 --drill shooting

# Also save a full JSON report
python demos/training_feedback.py --video input_videos/drill.mp4 --drill auto --json
```

**Drill types:** `shooting` | `ball_handling` | `footwork` | `general` | `auto`

**Output:**
- Formatted report printed to console (strengths, improvements, coaching tips)
- `demos/output/{video_name}_report.json` (with `--json` flag)

---

## Expected Console Output

### Highlight Maker
```
  Basketball Highlight Maker
  ────────────────────────────────────────
  Input  : input_videos/game.mp4
  Output : demos/output/game_highlights.mp4
  Clip   : 90 frames before + 60 frames after each make

  Processing video...
  [████████████████████] 100%  (1800/1800 frames)

  Found 4 made shot(s):
    Shot  1 — 00:14  (frame 420)
    Shot  2 — 00:31  (frame 930)
    Shot  3 — 00:47  (frame 1410)
    Shot  4 — 01:02  (frame 1860)

  Compiling highlight reel...
  Done. 4 clip(s) written  (~30.0s total)

  Output: C:\...\demos\output\game_highlights.mp4
```

### Training Feedback
```
  ========================================================
  DRILL ANALYSIS REPORT — SHOOTING
  ========================================================
  Duration   : 01:30  (2700 frames @ 30 fps)
  Shooting   : 8/14 FG  (57%)
  Speed      : avg 48 px/s  |  top 210 px/s
  Elbow avg  : 88.3°  (target 75–105°)
  Arc avg    : 49.1°  (target 42–58°)
  Follow-thru: 72% of shots

  ────────────────────────────────────────────────────────
  STRENGTHS (3)
    + High shooting accuracy (57% field goal percentage)
    + Consistent elbow alignment at release (88.3°)
    + Good shot arc (49.1° trajectory)

  AREAS TO IMPROVE (1)
    - Incomplete follow-through
      You are pulling your shooting hand down too quickly
      after release. Hold the 'goose-neck' follow-through
      for 2 seconds after every shot until it becomes
      automatic.

  ========================================================
```
