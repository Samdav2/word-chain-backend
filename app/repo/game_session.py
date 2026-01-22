import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.game_session import GameSession, GameMode, WordCategory


async def create_game_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    start_word: str,
    target_word: str,
    mode: GameMode = GameMode.STANDARD,
    category: WordCategory = WordCategory.MIXED,
    difficulty_level: int = 3
) -> GameSession:
    """Create a new game session with category and difficulty."""
    session = GameSession(
        user_id=user_id,
        mode=mode,
        category=category,
        difficulty_level=difficulty_level,
        target_word_start=start_word.upper(),
        target_word_end=target_word.upper(),
        current_word=start_word.upper()
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_game_session(db: AsyncSession, session_id: uuid.UUID) -> Optional[GameSession]:
    """Get a game session by ID."""
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_user_active_session(db: AsyncSession, user_id: uuid.UUID) -> Optional[GameSession]:
    """Get user's current active (not completed) game session."""
    result = await db.execute(
        select(GameSession)
        .where(GameSession.user_id == user_id)
        .where(GameSession.is_completed == False)
        .order_by(GameSession.start_time.desc())
    )
    return result.scalar_one_or_none()


async def update_game_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    current_word: Optional[str] = None,
    moves_count: Optional[int] = None,
    hints_used: Optional[int] = None,
    total_score: Optional[int] = None
) -> Optional[GameSession]:
    """Update game session progress."""
    session = await get_game_session(db, session_id)
    if session:
        if current_word is not None:
            session.current_word = current_word.upper()
        if moves_count is not None:
            session.moves_count = moves_count
        if hints_used is not None:
            session.hints_used = hints_used
        if total_score is not None:
            session.total_score = total_score
        await db.commit()
        await db.refresh(session)
    return session


async def complete_game_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    is_won: bool,
    total_score: int
) -> Optional[GameSession]:
    """Mark a game session as completed."""
    session = await get_game_session(db, session_id)
    if session:
        session.is_completed = True
        session.is_won = is_won
        session.total_score = total_score
        session.end_time = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
    return session


async def get_user_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20
) -> List[GameSession]:
    """Get user's game history."""
    result = await db.execute(
        select(GameSession)
        .where(GameSession.user_id == user_id)
        .order_by(GameSession.start_time.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_user_game_stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Get aggregated game statistics for a user."""
    # Total games
    total_result = await db.execute(
        select(func.count(GameSession.id))
        .where(GameSession.user_id == user_id)
        .where(GameSession.is_completed == True)
    )
    total_games = total_result.scalar() or 0

    # Games won
    won_result = await db.execute(
        select(func.count(GameSession.id))
        .where(GameSession.user_id == user_id)
        .where(GameSession.is_won == True)
    )
    games_won = won_result.scalar() or 0

    # Total moves
    moves_result = await db.execute(
        select(func.sum(GameSession.moves_count))
        .where(GameSession.user_id == user_id)
        .where(GameSession.is_completed == True)
    )
    total_moves = moves_result.scalar() or 0

    # Total hints used
    hints_result = await db.execute(
        select(func.sum(GameSession.hints_used))
        .where(GameSession.user_id == user_id)
    )
    total_hints = hints_result.scalar() or 0

    return {
        "total_games": total_games,
        "games_won": games_won,
        "games_lost": total_games - games_won,
        "total_moves": total_moves,
        "total_hints_used": total_hints,
        "average_moves": total_moves / total_games if total_games > 0 else 0,
        "win_rate": games_won / total_games if total_games > 0 else 0
    }
