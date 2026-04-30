from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.backend.database import Base

BENCHMARK_TYPES = [
    "spot_shooting_pct",
    "free_throw_streak",
    "mikan_60s_makes",
    "pull_up_20",
    "sprint_17s",
]


class BenchmarkEntry(Base):
    __tablename__ = "benchmark_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    session_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("drill_sessions.id"), nullable=True
    )
    benchmark_type: Mapped[str] = mapped_column(String, nullable=False)  # see BENCHMARK_TYPES
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="benchmarks")  # type: ignore[name-defined]
    session: Mapped[Optional["DrillSession"]] = relationship(  # type: ignore[name-defined]
        "DrillSession", back_populates="benchmarks"
    )
