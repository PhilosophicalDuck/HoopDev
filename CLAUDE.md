# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Basketball computer vision project using YOLOv11 (Ultralytics) to detect players, ball, refs, hoops, clocks, scoreboards, and overlays in basketball game videos.

## Setup

```bash
pip install ultralytics roboflow
```

GPU (CUDA) is recommended for training but inference runs on CPU.

## Key Commands

**Run inference on a video:**
```bash
python main.py
```
Loads `models/best_yolox_player_detection.pt`, runs on `input_videos/video_1.mp4`, saves results to `runs/detect/`.

**Train a new model:**
```bash
python train_model.py
```
Downloads dataset v17 from Roboflow, trains YOLOv11x for 100 epochs at 640×640. Requires internet access and the Roboflow API key.

**Jupyter training notebooks** (run in Jupyter or Google Colab):
- `training_notebooks/ball_detection.ipynb` — trains YOLOv11s for 250 epochs
- `training_notebooks/player_detection.ipynb` — trains YOLOv11x for 100 epochs

## Architecture

### Detection Pipeline

Two independent models work together:
- **Player/object detection**: `best_yolox_player_detection.pt` (YOLOv11 Extra-Large, higher accuracy) or `best_yolos_player_detection.pt` (YOLOv11 Small, faster)
- **Ball detection**: `best_ball_detection.pt` (YOLOv11s, trained separately for 250 epochs)

Inference results are returned as YOLO `Results` objects; bounding boxes are extracted via `results[0].boxes` in XYXY format.

### Dataset

Located in `Basketball-Players-17/` (Roboflow export, YOLOv11 format):
- 320 images, pre-processed to 640×640
- 7 classes: `Ball`, `Clock`, `Hoop`, `Overlay`, `Player`, `Ref`, `Scoreboard`
- Split: `train/`, `valid/`, `test/` subdirectories
- Config: `Basketball-Players-17/data.yaml`

Training outputs (weights, metrics, confusion matrices) are saved under `runs/detect/train*/`.

## Roboflow Credentials

The Roboflow API key, workspace, and project are required to download the dataset. Set `ROBOFLOW_API_KEY` in your `.env` file (see `.env.example`). The workspace and project slugs are found in your Roboflow dashboard URL. Dataset version is 17.
