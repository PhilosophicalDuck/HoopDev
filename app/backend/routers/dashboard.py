"""GET /api/dashboard — aggregated data for the Dashboard page."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.backend.database import get_db
from app.backend.auth import get_current_user
from app.backend.models.user import User
from app.backend.services.progress_service import get_dashboard_data

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_dashboard_data(db, current_user.id)
