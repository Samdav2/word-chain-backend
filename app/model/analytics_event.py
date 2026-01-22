import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Boolean, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class EventType(str, PyEnum):
    """Analytics event type enumeration."""
    MOVE_VALID = "move_valid"        # Valid word move
    MOVE_INVALID = "move_invalid"    # Invalid word attempt
    HINT_USED = "hint_used"          # User requested a hint
    GAME_START = "game_start"        # Game session started
    GAME_COMPLETE = "game_complete"  # Game successfully completed
    GAME_FORFEIT = "game_forfeit"    # User gave up
    TIMEOUT = "timeout"              # Time limit reached (if applicable)


class ErrorReason(str, PyEnum):
    """Specific error reasons for invalid moves."""
    NOT_IN_DICTIONARY = "not_in_dictionary"    # Word doesn't exist
    NOT_ONE_LETTER = "not_one_letter"          # More than 1 letter changed
    SAME_WORD = "same_word"                     # Entered the same word
    WRONG_LENGTH = "wrong_length"              # Word length mismatch
    NOT_EDTECH_WORD = "not_edtech_word"        # Not in educational vocabulary (Expert mode)
    ALREADY_USED = "already_used"              # Word already used in this session


class AnalyticsEvent(Base):
    """Analytics event model for tracking user actions and metacognitive data."""

    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType),
        nullable=False,
        index=True
    )
    input_word: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    error_reason: Mapped[ErrorReason | None] = mapped_column(
        Enum(ErrorReason),
        nullable=True
    )
    # Time-on-task tracking (milliseconds)
    thinking_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # SAM Phase tracking data
    sam_phase: Mapped[str | None] = mapped_column(
        String(20),  # "evaluate", "design", "develop"
        nullable=True
    )

    # Relationships
    session = relationship("GameSession", back_populates="analytics_events")

    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, word={self.input_word})>"
