"""
WebSocket endpoint: /ws/session/{session_id}

Lifecycle:
  1. Client connects → server accepts
  2. Client sends {"type": "start_drill", "drill_type": "shooting"}
  3. Server opens camera, starts LivePipeline in ThreadPoolExecutor
  4. Pipeline pushes PipelineResult onto asyncio.Queue
  5. WS sender drains queue, serializes → sends to client
  6. Client sends {"type": "stop"} → pipeline finalized, session saved
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.backend.config import settings, model_paths_for_drill
from app.backend.database import get_db, SessionLocal
from app.backend.models.session import DrillSession
from app.backend.cv.camera_manager import camera as shared_camera
from app.backend.cv.frame_buffer import RingBuffer
from app.backend.cv.live_pipeline import LivePipeline, PipelineResult
from app.backend.cv.constants import PRE_SHOT_FRAMES, POST_SHOT_FRAMES
from app.backend.services.session_service import finalize_session
from app.backend.services.highlight_service import write_clip
from app.backend.ws.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["live-session"])

# One shared thread pool — CV work is CPU-bound and blocking
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cv-worker")

# Track active pipelines: session_id → LivePipeline
_active_pipelines: dict[int, LivePipeline] = {}

# How often to send frame_data to client (every N frames to avoid WS flood)
FRAME_DATA_INTERVAL = 6  # ~5Hz at 30fps


@router.websocket("/ws/session/{session_id}")
async def live_session_ws(
    session_id: int,
    websocket: WebSocket,
):
    await manager.connect(session_id, websocket)
    pipeline: LivePipeline | None = None
    result_queue: asyncio.Queue = asyncio.Queue(maxsize=60)
    ring_buffer = RingBuffer(capacity=PRE_SHOT_FRAMES + POST_SHOT_FRAMES + 30)
    highlight_clip_count = 0

    try:
        # ── Wait for start_drill message ──────────────────────────────────────
        drill_type = "shooting"
        try:
            msg = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            if msg.get("type") == "start_drill":
                drill_type = msg.get("drill_type", "shooting")
        except asyncio.TimeoutError:
            await websocket.send_json({"type": "error", "detail": "Timed out waiting for start_drill"})
            return

        # ── Open camera ───────────────────────────────────────────────────────
        camera_index = settings.camera_index
        if not shared_camera.is_open():
            if not shared_camera.open(camera_index):
                await websocket.send_json({"type": "error", "detail": f"Cannot open camera {camera_index}"})
                return
        fps = shared_camera.get_fps()

        # ── Build pipeline ────────────────────────────────────────────────────
        pipeline = LivePipeline(
            drill_type=drill_type,
            fps=fps,
            ring_buffer=ring_buffer,
            **model_paths_for_drill(drill_type),
        )
        _active_pipelines[session_id] = pipeline

        await websocket.send_json({"type": "session_started", "fps": fps, "drill_type": drill_type})
        logger.info("Live session %d started (drill=%s, fps=%.0f)", session_id, drill_type, fps)

        loop = asyncio.get_event_loop()
        running = True
        paused = False
        frame_idx_local = 0

        # ── Capture loop (runs in thread pool) ───────────────────────────────
        def capture_loop():
            while running:
                if paused:
                    import time; time.sleep(0.033)
                    continue
                frame = shared_camera.read_frame()
                if frame is None:
                    import time; time.sleep(0.01)
                    continue
                result = pipeline.process_frame(frame)
                loop.call_soon_threadsafe(result_queue.put_nowait, result)

        future = loop.run_in_executor(_executor, capture_loop)

        # ── Message handler coroutine ─────────────────────────────────────────
        async def handle_client_messages():
            nonlocal running, paused
            while running:
                try:
                    msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.05)
                    msg_type = msg.get("type")
                    if msg_type == "stop":
                        running = False
                    elif msg_type == "pause":
                        paused = True
                    elif msg_type == "resume":
                        paused = False
                    elif msg_type == "ping":
                        await websocket.send_json({"type": "pong"})
                except asyncio.TimeoutError:
                    pass  # no message — continue
                except WebSocketDisconnect:
                    running = False
                    break

        # ── WS sender coroutine ───────────────────────────────────────────────
        async def send_results():
            nonlocal frame_idx_local, highlight_clip_count
            while running or not result_queue.empty():
                try:
                    result: PipelineResult = await asyncio.wait_for(
                        result_queue.get(), timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue

                frame_idx_local = result.frame_idx

                # Coaching cue — send immediately
                if result.cue:
                    await websocket.send_json({
                        "type": "coaching_cue",
                        "cue": {
                            "id": result.cue.id,
                            "text": result.cue.text,
                            "detail": result.cue.detail,
                            "severity": result.cue.severity,
                            "category": result.cue.category,
                            "duration_ms": result.cue.duration_ms,
                        }
                    })

                # Shot event — send immediately + trigger highlight capture
                if result.shot_event:
                    fr = result.frame_result
                    await websocket.send_json({
                        "type": "shot_event",
                        "event": result.shot_event,
                        "frame_idx": result.frame_idx,
                        "metrics_snapshot": {
                            "elbow_angle": fr.elbow_angle,
                            "follow_through": fr.follow_through,
                            "shots_made": fr.shots_made,
                            "shots_attempted": fr.shots_attempted,
                        }
                    })

                    if result.shot_event == "MADE":
                        # Capture highlight clip asynchronously
                        frames = ring_buffer.snapshot(PRE_SHOT_FRAMES + POST_SHOT_FRAMES)
                        clip_idx = highlight_clip_count
                        highlight_clip_count += 1
                        shot_frame_idx = result.frame_idx

                        def _write_highlight(
                            _frames=frames,
                            _clip_idx=clip_idx,
                            _shot_frame=shot_frame_idx,
                        ):
                            _db = SessionLocal()
                            try:
                                row = _db.query(DrillSession).filter(
                                    DrillSession.id == session_id
                                ).first()
                                _user_id = row.user_id if row else 0
                                write_clip(_db, _frames, session_id,
                                           _user_id, _shot_frame, _clip_idx, fps)
                            except Exception as exc:
                                logger.warning("Highlight clip write failed: %s", exc)
                            finally:
                                _db.close()

                        loop.run_in_executor(_executor, _write_highlight)

                # Frame data — throttled to ~5Hz
                if result.frame_idx % FRAME_DATA_INTERVAL == 0:
                    fr = result.frame_result
                    await websocket.send_json({
                        "type": "frame_data",
                        "frame_idx": result.frame_idx,
                        "metrics": {
                            "shot_state": fr.shot_state,
                            "elbow_angle": fr.elbow_angle,
                            "arc_angle": fr.arc_angle,
                            "follow_through": fr.follow_through,
                            "speed_px_s": round(fr.speed_px_s, 1),
                            "is_release_frame": fr.is_release_frame,
                            "ball_detected": fr.ball_detected,
                            "hoop_detected": fr.hoop_detected,
                        },
                        "shot_counts": {
                            "made": fr.shots_made,
                            "attempted": fr.shots_attempted,
                        }
                    })

        # Run both coroutines concurrently
        await asyncio.gather(handle_client_messages(), send_results())

        # ── Session finalization ──────────────────────────────────────────────
        running = False
        await future  # wait for capture loop to exit

        snapshot, feedback = pipeline.finalize()

        # Collect highlight clip IDs written during session
        db_final = SessionLocal()
        try:
            from app.backend.models.highlight import HighlightClip
            clip_ids = [
                c.id for c in db_final.query(HighlightClip)
                .filter(HighlightClip.session_id == session_id)
                .all()
            ]
            finalize_session(db_final, session_id, snapshot, feedback)
        finally:
            db_final.close()

        await websocket.send_json({
            "type": "session_complete",
            "session_id": session_id,
            "summary": snapshot,
            "feedback": feedback,
            "highlight_clip_ids": clip_ids,
        })
        logger.info("Session %d complete. %d highlight clips.", session_id, len(clip_ids))

    except WebSocketDisconnect:
        logger.info("Session %d WS disconnected by client", session_id)
    except Exception as e:
        logger.error("Session %d error: %s", session_id, e, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "detail": str(e)})
        except Exception:
            pass
    finally:
        running = False
        _active_pipelines.pop(session_id, None)
        shared_camera.close()
        manager.disconnect(session_id)
