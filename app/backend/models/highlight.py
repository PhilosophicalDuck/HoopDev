from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.backend.database import Base


class HighlightClip(Base):
    __tablename__ = "highlight_clips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("drill_sessions.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)          # highlights/{session_id}_{n}.mp4
    duration_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shot_frame: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["DrillSession"] = relationship("DrillSession", back_populates="highlights")  # type: ignore[name-defined]
    user: Mapped["User"] = relationship("User", back_populates="highlights")  # type: ignore[name-defined]
