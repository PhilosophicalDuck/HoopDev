from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.backend.database import get_db
from app.backend.models.user import User
from app.backend.models.session import DrillSession, SessionMetrics
from app.backend.schemas.session import SessionCreate, SessionUpdate, SessionSummary, SessionDetail
from app.backend.auth import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionDetail, status_code=201)
def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = DrillSession(
        user_id=current_user.id,
        drill_type=body.drill_type,
        drill_name=body.drill_name,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=list[SessionSummary])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(DrillSession)
        .options(joinedload(DrillSession.metrics))
        .filter(DrillSession.user_id == current_user.id)
        .order_by(DrillSession.started_at.desc())
        .all()
    )
    result = []
    for s in sessions:
        summary = SessionSummary.model_validate(s)
        if s.metrics:
            summary.shots_made = s.metrics.shots_made
            summary.shot_percentage = s.metrics.shot_percentage
        result.append(summary)
    return result


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(DrillSession)
        .options(joinedload(DrillSession.metrics), joinedload(DrillSession.highlights))
        .filter(DrillSession.id == session_id, DrillSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=SessionDetail)
def update_session(
    session_id: int,
    body: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(DrillSession)
        .filter(DrillSession.id == session_id, DrillSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = body.status
    if body.status in ("completed", "abandoned") and not session.ended_at:
        session.ended_at = datetime.now(timezone.utc)
        if session.started_at:
            delta = session.ended_at - session.started_at.replace(tzinfo=timezone.utc)
            session.duration_s = delta.total_seconds()

    db.commit()
    db.refresh(session)
    return session
