import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.backend.database import get_db
from app.backend.models.user import User
from app.backend.models.highlight import HighlightClip
from app.backend.schemas.highlight import HighlightClipMeta
from app.backend.auth import get_current_user
from app.backend.config import settings, CAPSTONE_ROOT

router = APIRouter(prefix="/api/highlights", tags=["highlights"])


@router.get("", response_model=list[HighlightClipMeta])
def list_highlights(
    session_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(HighlightClip).filter(HighlightClip.user_id == current_user.id)
    if session_id:
        query = query.filter(HighlightClip.session_id == session_id)
    return query.order_by(HighlightClip.created_at.desc()).all()


@router.get("/{clip_id}/stream")
def stream_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clip = db.query(HighlightClip).filter(
        HighlightClip.id == clip_id, HighlightClip.user_id == current_user.id
    ).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    file_path = CAPSTONE_ROOT / clip.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Clip file not found on disk")

    return FileResponse(str(file_path), media_type="video/mp4")


@router.get("/{clip_id}/thumbnail")
def get_thumbnail(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clip = db.query(HighlightClip).filter(
        HighlightClip.id == clip_id, HighlightClip.user_id == current_user.id
    ).first()
    if not clip or not clip.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    file_path = CAPSTONE_ROOT / clip.thumbnail_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found on disk")

    return FileResponse(str(file_path), media_type="image/jpeg")


@router.delete("/{clip_id}", status_code=204)
def delete_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clip = db.query(HighlightClip).filter(
        HighlightClip.id == clip_id, HighlightClip.user_id == current_user.id
    ).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Remove files from disk
    for path_attr in (clip.file_path, clip.thumbnail_path):
        if path_attr:
            disk_path = CAPSTONE_ROOT / path_attr
            if disk_path.exists():
                disk_path.unlink()

    db.delete(clip)
    db.commit()
