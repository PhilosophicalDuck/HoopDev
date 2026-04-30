from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.backend.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sessions: Mapped[list["DrillSession"]] = relationship(  # type: ignore[name-defined]
        "DrillSession", back_populates="user", cascade="all, delete-orphan"
    )
    benchmarks: Mapped[list["BenchmarkEntry"]] = relationship(  # type: ignore[name-defined]
        "BenchmarkEntry", back_populates="user", cascade="all, delete-orphan"
    )
    highlights: Mapped[list["HighlightClip"]] = relationship(  # type: ignore[name-defined]
        "HighlightClip", back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String)   # PG|SG|SF|PF|C
    skill_level: Mapped[Optional[str]] = mapped_column(String) # beginner|intermediate|advanced|elite
    height_cm: Mapped[Optional[float]] = mapped_column(Float)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    dominant_hand: Mapped[Optional[str]] = mapped_column(String)  # left|right
    goals: Mapped[Optional[list]] = mapped_column(JSON)  # list[str]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
