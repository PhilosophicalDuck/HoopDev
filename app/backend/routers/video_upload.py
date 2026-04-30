"""
Video upload endpoints.

POST   /api/video/upload               – upload a video file, start processing
GET    /api/video/{task_id}/status     – poll processing status
WS     /ws/video/{task_id}/progress   – real-time progress stream
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.backend.auth import get_current_user
from app.backend.config import settings, model_paths_for_drill
from app.backend.database import get_db, SessionLocal
from app.backend.models.session import DrillSession
from app.backend.models.user import User
from app.backend.schemas.video import VideoUploadResponse, VideoStatusResponse
from app.backend.services.session_service import finalize_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video", tags=["video-upload"])
# Separate router for WebSocket (no /api prefix — WS endpoints use /ws prefix)
ws_router = APIRouter(tags=["video-upload"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}

# ── In-process task state ─────────────────────────────────────────────────────
# task_id → {"status", "progress", "session_id", "summary", "feedback", "error"}
_tasks: dict[str, dict] = {}

# Shared executor for CV-bound processing
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-cv")


# ── Upload endpoint ───────────────────────────────────────────────────────────

@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    drill_type: str = Form(default="shooting"),
    drill_name: str = Form(default="Video Upload"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate file size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb} MB.",
        )

    # Save file to uploads directory
    uploads_dir = Path(settings.highlights_dir) / "uploads" / str(current_user.id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    task_id = str(uuid.uuid4())
    video_path = uploads_dir / f"{task_id}{suffix}"
    video_path.write_bytes(contents)

    # Create DrillSession record (source="upload")
    session_row = DrillSession(
        user_id=current_user.id,
        drill_type=drill_type,
        drill_name=drill_name,
        status="active",
        source="upload",
        video_path=str(video_path),
    )
    db.add(session_row)
    db.commit()
    db.refresh(session_row)
    session_id = session_row.id

    # Register task state
    _tasks[task_id] = {
        "status": "processing",
        "progress": 0,
        "session_id": session_id,
        "summary": None,
        "feedback": None,
        "error": None,
    }

    logger.info(
        "Video upload: task=%s session=%d user=%d file=%s",
        task_id, session_id, current_user.id, video_path.name,
    )

    # Launch background processing
    background_tasks.add_task(
        _run_video_pipeline,
        task_id=task_id,
        video_path=str(video_path),
        drill_type=drill_type,
        session_id=session_id,
    )

    return VideoUploadResponse(task_id=task_id, session_id=session_id)


# ── Status polling endpoint ───────────────────────────────────────────────────

@router.get("/{task_id}/status", response_model=VideoStatusResponse)
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return VideoStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        session_id=task["session_id"],
        error=task["error"],
    )


# ── WebSocket progress stream ─────────────────────────────────────────────────

@ws_router.websocket("/ws/video/{task_id}/progress")
async def video_progress_ws(
    task_id: str,
    websocket: WebSocket,
):
    await websocket.accept()

    if task_id not in _tasks:
        await websocket.send_json({"type": "error", "message": "Task not found"})
        await websocket.close()
        return

    try:
        while True:
            task = _tasks.get(task_id)
            if not task:
                await websocket.send_json({"type": "error", "message": "Task not found"})
                break

            if task["status"] == "processing":
                await websocket.send_json({
                    "type": "progress",
                    "pct": task["progress"],
                })
                await asyncio.sleep(0.5)

            elif task["status"] == "complete":
                await websocket.send_json({
                    "type": "complete",
                    "session_id": task["session_id"],
                    "summary": task["summary"],
                    "feedback": task["feedback"],
                })
                break

            elif task["status"] == "error":
                await websocket.send_json({
                    "type": "error",
                    "message": task["error"] or "Processing failed",
                })
                break

    except WebSocketDisconnect:
        logger.debug("Video progress WS disconnected: task=%s", task_id)
    except Exception as exc:
        logger.error("Video progress WS error: %s", exc, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


# ── Background processing function ───────────────────────────────────────────

def _run_video_pipeline(
    task_id: str,
    video_path: str,
    drill_type: str,
    session_id: int,
) -> None:
    """
    Runs in a FastAPI BackgroundTask (asyncio thread pool).
    Processes the video synchronously, updating task state along the way.
    """
    from app.backend.cv.video_pipeline import VideoPipeline

    def on_progress(frame_idx: int, total_frames: int) -> None:
        pct = min(99, int(frame_idx / max(total_frames, 1) * 100))
        if task_id in _tasks:
            _tasks[task_id]["progress"] = pct

    try:
        pipeline = VideoPipeline(
            video_path=video_path,
            drill_type=drill_type,
            **model_paths_for_drill(drill_type),
        )

        # Consume the generator (all CV work happens here)
        for _ in pipeline.run(on_progress=on_progress):
            pass

        snapshot, feedback = pipeline.finalize()

        # Persist to DB
        db = SessionLocal()
        try:
            finalize_session(db, session_id, snapshot, feedback)
        finally:
            db.close()

        _tasks[task_id].update({
            "status": "complete",
            "progress": 100,
            "summary": snapshot,
            "feedback": feedback,
        })
        logger.info("Video task %s complete (session %d)", task_id, session_id)

    except Exception as exc:
        logger.error("Video task %s failed: %s", task_id, exc, exc_info=True)
        _tasks[task_id].update({
            "status": "error",
            "error": str(exc),
        })
        # Mark session as abandoned on failure
        db = SessionLocal()
        try:
            row = db.query(DrillSession).filter(DrillSession.id == session_id).first()
            if row:
                row.status = "abandoned"
                db.commit()
        except Exception:
            pass
        finally:
            db.close()
