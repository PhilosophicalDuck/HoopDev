from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.backend.database import get_db
from app.backend.models.user import User
from app.backend.models.benchmark import BenchmarkEntry as BenchmarkModel
from app.backend.schemas.benchmark import BenchmarkCreate, BenchmarkEntry
from app.backend.auth import get_current_user

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.get("", response_model=list[BenchmarkEntry])
def list_benchmarks(
    benchmark_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(BenchmarkModel).filter(BenchmarkModel.user_id == current_user.id)
    if benchmark_type:
        query = query.filter(BenchmarkModel.benchmark_type == benchmark_type)
    return query.order_by(BenchmarkModel.recorded_at.desc()).all()


@router.post("", response_model=BenchmarkEntry, status_code=201)
def create_benchmark(
    body: BenchmarkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = BenchmarkModel(
        user_id=current_user.id,
        session_id=body.session_id,
        benchmark_type=body.benchmark_type,
        value=body.value,
        notes=body.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
