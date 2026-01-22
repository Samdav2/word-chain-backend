import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Boolean, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class GameMode(str, PyEnum):
    """Game mode enumeration."""
    STANDARD = "standard"          # Any dictionary word allowed
    EDTECH_ONLY = "edtech_only"    # Educational jargon only (Expert mode)


class WordCategory(str, PyEnum):
    """Word category for educational topics."""
    GENERAL = "general"          # Common English words
    SCIENCE = "science"          # General science vocabulary
    BIOLOGY = "biology"          # Life science terms
    PHYSICS = "physics"          # Physics and physical science
    EDUCATION = "education"      # Educational terminology
    MIXED = "mixed"              # All categories combined


class GameSession(Base):
    """Game session model tracking individual game instances."""

    __tablename__ = "game_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    mode: Mapped[GameMode] = mapped_column(
        Enum(GameMode),
        default=GameMode.STANDARD,
        nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    target_word_start: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    target_word_end: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    moves_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    hints_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    is_won: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    current_word: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    total_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    # Educational enhancements
    category: Mapped[WordCategory] = mapped_column(
        Enum(WordCategory),
        default=WordCategory.MIXED,
        nullable=False
    )
    difficulty_level: Mapped[int] = mapped_column(
        Integer,
        default=3,  # 1-5 scale, 3 is medium
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="game_sessions")
    analytics_events = relationship("AnalyticsEvent", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GameSession(id={self.id}, user_id={self.user_id}, mode={self.mode})>"
