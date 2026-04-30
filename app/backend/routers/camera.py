import time

import cv2
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.backend.auth import get_current_user
from app.backend.config import settings
from app.backend.cv.camera_manager import camera as shared_camera
from app.backend.database import get_db
from app.backend.models.user import User

router = APIRouter(prefix="/api/camera", tags=["camera"])


def _get_user_flexible(
    token: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Accept JWT from either Authorization header or ?token= query param.
    Needed for MJPEG <img src> which cannot send custom headers.
    """
    raw = None
    if authorization and authorization.startswith("Bearer "):
        raw = authorization[7:]
    elif token:
        raw = token
    if not raw:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(raw, settings.secret_key, algorithms=[settings.algorithm])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _list_available_cameras(max_index: int = 5) -> list[dict]:
    import cv2
    cameras = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras.append({"index": i, "name": f"Camera {i}"})
            cap.release()
    return cameras


def _mjpeg_generator(camera_index: int):
    # Use the shared singleton so the MJPEG preview and the live session
    # never open two VideoCapture instances on the same camera index.
    opened_here = False
    if not shared_camera.is_open():
        if not shared_camera.open(camera_index):
            return  # camera unavailable — yield nothing, browser shows broken img
        opened_here = True

    try:
        while True:
            frame = shared_camera.read_frame()
            if frame is None:
                time.sleep(0.033)
                continue
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
    finally:
        # Only close if we opened it — if a live session opened the camera,
        # let the session manage the lifecycle.
        if opened_here:
            shared_camera.close()


@router.get("/stream")
def camera_stream(
    index: int = 0,
    current_user: User = Depends(_get_user_flexible),
):
    return StreamingResponse(
        _mjpeg_generator(index),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/devices")
def list_devices(current_user: User = Depends(get_current_user)):
    return {"devices": _list_available_cameras()}
