# HoopDev — AI Basketball Training Assistant

HoopDev is a full-stack basketball training system that uses computer vision to give players real-time coaching feedback. Point a webcam at a drill, pick a drill type, and the app watches you play — tracking your shots, reading your body mechanics, and calling out coaching cues live on screen. Upload a recorded video and it produces a full drill report with strengths, areas to improve, and actionable tips.

---

## How It Works

### The Big Picture

```
Camera / Video File
        ↓
  YOLO Detection  ──────────────────────────────────────────┐
  (ball, players, hoop)                                     │
        ↓                                                   │
  ByteTrack (player IDs)    YOLOv11 Pose (keypoints)        │
        ↓                          ↓                        │
  Shot Tracker ←──── ball + hoop positions                  │
  Team Classifier ←─ jersey colors (K-Means)                │
  Touch Tracker ←─── possession changes                     │
        ↓                                                   │
  Drill Metrics Accumulator                                 │
  (speed, elbow angles, arc, rhythm, footwork, …)           │
        ↓                                                   │
  Feedback Engine ──→ real-time coaching cues               │
        ↓                                                   │
  Drill Report ──────→ post-session summary                 │
        ↓                                                   │
  Ring Buffer ───────────────────────────────────────────── ┘
  (auto-clips highlights on every made shot)
```

Everything runs locally. No cloud inference, no subscription — just your machine.

---

## Models

### Detection Model — `best_yolos_player_detection.pt`

**What it is:** YOLOv11 Small, custom-trained on a Roboflow basketball dataset (320 images, 7 classes). Handles real-time detection at camera speed.

**What it detects:**
| Class ID | Label |
|----------|-------|
| 0 | Ball |
| 2 | Hoop |
| 4 | Player |

**Why this model:** YOLOv11s gives the best trade-off between accuracy and speed for CPU inference. We need the model to run in real time alongside ByteTrack and pose estimation — a larger model would drop too many frames.

**Ball smoothing:** A 5-frame median filter is applied to the detected ball center to remove jitter. When the ball briefly disappears (occlusion, out-of-frame), the last cached size is used to reconstruct the bounding box so the shot tracker doesn't lose continuity.

---

### Hoop Model — `best_yolo26s_player_detection.pt`

**What it is:** A second YOLOv11 variant trained specifically for hoop detection with a lower confidence threshold (0.15 vs 0.30) to catch partial or angled views of the rim.

**Why separate:** The main model is optimized for the whole scene. A dedicated hoop model at a very low threshold catches the rim even when it's partly occluded or seen from a sharp angle — both common in real shooting drills. Since the hoop doesn't move, we only run it every 10 frames and cache the result, keeping the overhead low.

---

### Pose Model — `yolo11n-pose.pt`

**What it is:** YOLOv11 Nano Pose, the smallest YOLO pose model. Extracts the standard 17 COCO keypoints (nose, shoulders, elbows, wrists, hips, knees, ankles).

**Why this model:** Pose estimation is only needed on a single cropped player region (the focus player), not the full frame. The Nano model is fast enough to run per-frame on a CPU crop. We use it for:
- **Shooting analysis:** Elbow angle at release, wrist position, follow-through detection
- **Footwork analysis:** Lateral displacement, step cadence from ankle movement
- **Ball handling:** Detecting hand switches and dribble rhythm

**Thresholds that matter:**
| Metric | Range | Coaching signal |
|--------|-------|-----------------|
| Elbow angle at release | 75–105° | Optimal; <65° = arm collapse, >115° = elbow flare |
| Shot arc | 42–58° | Optimal; <42° = flat shot, >58° = too high |
| Follow-through | ≥75% of shots | Wrist stays above shoulder for 15 frames post-release |
| Release consistency | CV < 0.08 | Low variance across shots = repeatable mechanics |

---

## Shot Detection

The shot tracker is a state machine: **IDLE → TRACKING → IDLE**.

1. When the ball enters a zone around the hoop (3.5× the hoop width, extending above and below the rim), tracking starts and a 4-second deadline begins.
2. If the ball stays inside the basket region for at least 1 frame after being above the rim → **MADE**.
3. If the deadline expires and the ball was above the rim but never in the basket → **MISS**.
4. A 45-frame cooldown prevents the same shot from being counted twice.

On every MADE event, the last 90 frames (3 s) plus the next 60 frames (2 s) are pulled from a ring buffer and written to a highlight clip automatically.

---

## Team & Possession Detection

- **Team classification:** HSV color features are extracted from each player's torso crop and K-Means (k=2) groups them into Team A and Team B automatically — no manual labeling needed.
- **Possession:** The ball is considered possessed when it overlaps a player's bounding box by more than 80% for 11 consecutive frames. Possession changes drive the touch counter.

---

## Real-Time Feedback

The Feedback Engine watches every frame and fires coaching cues with a cooldown so they don't spam. Examples:

| Cue | Trigger |
|-----|---------|
| "Elbow is flaring out" | Elbow angle > 115° at release |
| "Extend your arm fully" | Elbow angle < 65° at release |
| "Good mechanics!" | Elbow 75–105° |
| "No follow-through" | Wrist drops below shoulder post-release |
| "Flat shot — aim higher" | Arc < 42° |
| "Dribble rhythm is improving" | Ball bounce timing CV < 0.15 |
| "You've been idle" | 90 consecutive low-movement frames |

---

## Post-Session Drill Report

After a session (live or uploaded video), the system computes a full report:

- **Shot percentage and volume**
- **Average elbow angle and arc** with consistency scores
- **Possession time** and touch count
- **Lateral speed and step cadence** (footwork drills)
- **Strengths** — what the player is doing well
- **Improvements** — specific mechanics to work on
- **Coaching tips** — one actionable instruction per issue

---

## Project Structure

```
Capstone/
├── app/
│   ├── backend/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── auth.py               # JWT authentication
│   │   ├── config.py             # Settings (model paths, DB, etc.)
│   │   ├── database.py           # SQLite setup
│   │   ├── cv/
│   │   │   ├── base_pipeline.py      # Shared ByteTrack + ball smoothing
│   │   │   ├── live_pipeline.py      # Real-time camera processing
│   │   │   ├── video_pipeline.py     # Uploaded video processing
│   │   │   ├── feedback_engine.py    # Per-frame coaching cues
│   │   │   ├── thresholds.py         # All coaching decision thresholds
│   │   │   ├── constants.py          # Class IDs, frame window sizes
│   │   │   ├── camera_manager.py     # Shared camera singleton
│   │   │   ├── frame_buffer.py       # Ring buffer for highlight capture
│   │   │   └── core/
│   │   │       ├── shot_tracker.py         # IDLE→TRACKING state machine
│   │   │       ├── player_tracker.py       # Team colors + possession
│   │   │       ├── pose_analyzer.py        # Keypoint extraction + angles
│   │   │       ├── touch_tracker.py        # Ball touch counter
│   │   │       ├── player_focus_tracker.py # Focus player re-ID
│   │   │       ├── enrollment.py           # Jersey feature calibration
│   │   │       ├── drill_metrics.py        # Metric accumulator
│   │   │       ├── drill_report.py         # Coaching report generator
│   │   │       └── highlight_writer.py     # Highlight clip compiler
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── routers/              # API route handlers
│   │   └── services/
│   │       ├── session_service.py      # Session lifecycle
│   │       ├── progress_service.py     # Upload progress tracking
│   │       └── workout_recommender.py  # Drill recommendation engine
│   └── frontend/                 # React + Vite + Tailwind UI
├── models/                       # YOLO .pt weight files (not committed)
├── demos/
│   ├── training_feedback.py      # CLI drill analysis
│   ├── highlight_maker.py        # CLI highlight reel generator
│   └── debug_detections.py       # Visualize raw YOLO detections
├── .env.example                  # Environment variable template
└── .gitignore
```

---

## Setup

### Requirements

- Python 3.10+
- Node.js 18+
- A webcam (for live sessions) or a basketball drill video file
- GPU optional — all models run on CPU

### 1. Clone and install Python dependencies

```bash
git clone <your-repo-url>
cd Capstone
pip install ultralytics supervision fastapi uvicorn sqlalchemy passlib python-jose pydantic-settings python-multipart opencv-python numpy pandas
```

### 2. Copy environment config

```bash
cp .env.example .env
```

Open `.env` and set a real `SECRET_KEY` (any long random string). The other defaults work out of the box.

### 3. Download model weights

The model weights are not stored in the repository (too large for git). There are two custom-trained models and one standard Ultralytics model.

**Custom-trained models** — download from the [Releases page](https://github.com/PhilosophicalDuck/HoopDev/releases) and place them in the `models/` folder:

| File | Size | Description |
|------|------|-------------|
| `best_yolos_player_detection.pt` | ~23 MB | Main detection model (ball, players, hoop) |
| `best_yolo26s_player_detection.pt` | ~23 MB | Dedicated hoop detection model |

**Pose model** — downloaded automatically by Ultralytics the first time the app runs:

| File | Size | Description |
|------|------|-------------|
| `yolo11n-pose.pt` | ~7 MB | Body keypoint estimation (17 joints) |

Your `models/` folder should look like this before running:

```
models/
├── best_yolos_player_detection.pt
├── best_yolo26s_player_detection.pt
└── yolo11n-pose.pt          ← auto-downloaded on first run if missing
```

### 4. Download demo videos (optional)

Only needed if you want to use the in-app demo mode (`/session/demo`). Download the following files from the [Releases page](https://github.com/PhilosophicalDuck/HoopDev/releases/tag/v1.0) and place them in `app/frontend/public/demo/`:

- `shooting_h264.mp4`
- `dribbling_h264.mp4`

The rest of the app works fine without them — the demo page is just a preview that plays pre-recorded footage.

### 5. Install and run the frontend

```bash
cd app/frontend
npm install
npm run dev
```

### 6. Run the backend

```bash
# From the repo root
uvicorn app.backend.main:app --reload
```

The app is now running at `http://localhost:5173`.

---

## Running the Demos (No Frontend Needed)

These scripts run from the command line against a video file. They're the fastest way to test the CV pipeline without setting up the full web app.

### Drill Analysis Report

Analyze a shooting or ball-handling drill and print a coaching report:

```bash
python demos/training_feedback.py --video input_videos/drill.mp4 --drill shooting
```

Options:
- `--drill` — `shooting`, `ball_handling`, or `footwork`
- `--json` — also export metrics as JSON

Example output:
```
=== Drill Report (shooting) ===
Shots: 12 made / 18 attempted (66.7%)
Avg elbow angle: 91.3°  |  Avg arc: 48.2°

Strengths:
  ✓ Consistent release angle (CV = 0.06)
  ✓ Good follow-through on 80% of shots

Improvements:
  ✗ Elbow flared on 4 shots — keep it tucked under the ball

Coaching Tips:
  elbow_in: Focus on keeping your shooting elbow directly under the ball at release.
```

### Highlight Reel

Clip every made shot (with 3 s before and 2 s after) into a single video:

```bash
python demos/highlight_maker.py --video input_videos/game.mp4 --output demos/output
```

Output: `demos/output/game_highlights.mp4`

### Debug Detections

Inspect what the model is actually seeing on a specific frame:

```bash
python demos/debug_detections.py --video input_videos/drill.mp4 --frame 60 --conf 0.01
```

Prints a table of every detection and saves an annotated frame to `demos/output/debug_frame.jpg`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Object detection | YOLOv11 (Ultralytics) |
| Pose estimation | YOLOv11-Pose |
| Multi-object tracking | ByteTrack (via Supervision) |
| Backend API | FastAPI + WebSockets |
| Database | SQLite (via SQLAlchemy) |
| Auth | JWT (python-jose + passlib) |
| Frontend | React + Vite + Tailwind CSS |
| AI Coach chat | Ollama (local LLM, Gemma 3 1B) |
