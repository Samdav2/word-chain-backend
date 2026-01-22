import uuid
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.analytics_event import AnalyticsEvent, EventType, ErrorReason


async def log_event(
    db: AsyncSession,
    session_id: uuid.UUID,
    event_type: EventType,
    input_word: Optional[str] = None,
    is_valid: bool = True,
    error_reason: Optional[ErrorReason] = None,
    thinking_time_ms: Optional[int] = None,
    sam_phase: Optional[str] = None
) -> AnalyticsEvent:
    """Log a game analytics event."""
    event = AnalyticsEvent(
        session_id=session_id,
        event_type=event_type,
        input_word=input_word.upper() if input_word else None,
        is_valid=is_valid,
        error_reason=error_reason,
        thinking_time_ms=thinking_time_ms,
        sam_phase=sam_phase
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_session_events(
    db: AsyncSession,
    session_id: uuid.UUID
) -> List[AnalyticsEvent]:
    """Get all events for a game session."""
    result = await db.execute(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.session_id == session_id)
        .order_by(AnalyticsEvent.timestamp.asc())
    )
    return list(result.scalars().all())


async def get_session_words_used(
    db: AsyncSession,
    session_id: uuid.UUID
) -> List[str]:
    """Get list of words used in a session (for duplicate detection)."""
    result = await db.execute(
        select(AnalyticsEvent.input_word)
        .where(AnalyticsEvent.session_id == session_id)
        .where(AnalyticsEvent.event_type == EventType.MOVE_VALID)
        .where(AnalyticsEvent.input_word.isnot(None))
    )
    return [row[0] for row in result.all() if row[0]]


async def get_user_error_breakdown(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Get error type breakdown for a user across all sessions."""
    from app.model.game_session import GameSession

    # Join analytics events with game sessions to filter by user
    subquery = select(AnalyticsEvent.error_reason, func.count(AnalyticsEvent.id).label('count')).join(
        GameSession,
        AnalyticsEvent.session_id == GameSession.id
    ).where(
        GameSession.user_id == user_id
    ).where(
        AnalyticsEvent.event_type == EventType.MOVE_INVALID
    ).where(
        AnalyticsEvent.error_reason.isnot(None)
    ).group_by(
        AnalyticsEvent.error_reason
    )

    result = await db.execute(subquery)

    breakdown = {
        "not_in_dictionary": 0,
        "not_one_letter": 0,
        "same_word": 0,
        "wrong_length": 0,
        "already_used": 0
    }

    for row in result.all():
        if row[0]:
            breakdown[row[0].value] = row[1]

    return breakdown


async def get_average_thinking_time(db: AsyncSession, user_id: uuid.UUID) -> float:
    """Get average thinking time for a user."""
    from app.model.game_session import GameSession

    result = await db.execute(
        select(func.avg(AnalyticsEvent.thinking_time_ms))
        .join(GameSession, AnalyticsEvent.session_id == GameSession.id)
        .where(GameSession.user_id == user_id)
        .where(AnalyticsEvent.thinking_time_ms.isnot(None))
    )

    avg = result.scalar()
    return float(avg) if avg else 0.0


async def get_leaderboard_data(db: AsyncSession, limit: int = 10) -> List[dict]:
    """Get leaderboard data with user rankings."""
    from app.model.user import User
    from app.model.game_session import GameSession

    # Aggregate user stats
    result = await db.execute(
        select(
            User.id,
            User.email,
            User.first_name,
            User.last_name,
            User.matric_no,
            User.current_xp,
            func.count(GameSession.id).filter(GameSession.is_won == True).label('games_won'),
            func.count(GameSession.id).filter(GameSession.is_completed == True).label('total_games'),
            func.avg(GameSession.moves_count).filter(GameSession.is_completed == True).label('avg_moves')
        )
        .outerjoin(GameSession, User.id == GameSession.user_id)
        .group_by(User.id)
        .order_by(User.current_xp.desc())
        .limit(limit)
    )

    leaderboard = []
    for idx, row in enumerate(result.all(), 1):
        total_games = row[7] or 0
        games_won = row[6] or 0
        first_name = row[2] or ""
        last_name = row[3] or ""
        display_name = f"{first_name} {last_name}".strip() if first_name or last_name else row[1].split("@")[0]

        leaderboard.append({
            "rank": idx,
            "user_id": row[0],
            "email": row[1],
            "first_name": first_name,
            "last_name": last_name,
            "display_name": display_name,
            "matric_no": row[4],
            "total_xp": row[5],
            "games_won": games_won,
            "total_games": total_games,
            "win_rate": games_won / total_games if total_games > 0 else 0,
            "average_moves": float(row[8]) if row[8] else 0
        })

    return leaderboard
