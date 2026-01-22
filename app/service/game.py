"""Game service for managing word chain game sessions."""

import uuid
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.service.word_graph import get_word_graph, WordCategory as WGCategory
from app.repo import game_session as session_repo
from app.repo import analytics as analytics_repo
from app.repo import user as user_repo
from app.model.game_session import GameMode, GameSession, WordCategory
from app.model.analytics_event import EventType, ErrorReason
from app.core.config import settings


class GameError(Exception):
    """Custom exception for game errors."""
    pass


async def start_game(
    db: AsyncSession,
    user_id: uuid.UUID,
    mode: GameMode = GameMode.STANDARD,
    category: WordCategory = WordCategory.MIXED,
    difficulty: Optional[int] = None
) -> GameSession:
    """
    Start a new game session with category and difficulty options.

    Args:
        db: Database session
        user_id: User ID
        mode: Game mode (standard or edtech_only)
        category: Word category (general, science, biology, physics, education, mixed)
        difficulty: Optional difficulty level (1-5)

    Returns:
        New game session.
    """
    # Check if user has an active game
    active = await session_repo.get_user_active_session(db, user_id)
    if active:
        raise GameError("You have an active game. Complete or forfeit it first.")

    # Get a random word pair from the graph, filtered by category
    graph = get_word_graph()

    # Map model category to word graph category
    category_map = {
        WordCategory.GENERAL: WGCategory.GENERAL,
        WordCategory.SCIENCE: WGCategory.SCIENCE,
        WordCategory.BIOLOGY: WGCategory.BIOLOGY,
        WordCategory.PHYSICS: WGCategory.PHYSICS,
        WordCategory.EDUCATION: WGCategory.EDUCATION,
        WordCategory.MIXED: WGCategory.MIXED,
    }
    wg_category = category_map.get(category, WGCategory.MIXED)

    pair = graph.get_random_word_pair_by_category(
        category=wg_category,
        min_distance=3,
        max_distance=6,
        difficulty=difficulty
    )

    if not pair:
        # Fallback to any word pair
        pair = graph.get_random_word_pair(min_distance=3, max_distance=6)

    if not pair:
        # Ultimate fallback
        pair = ("FAIL", "PASS")

    start_word, target_word = pair

    # Calculate difficulty level based on word difficulty
    difficulty_level = difficulty or graph.get_word_difficulty_level(start_word)

    # Create the session
    session = await session_repo.create_game_session(
        db=db,
        user_id=user_id,
        start_word=start_word,
        target_word=target_word,
        mode=mode,
        category=category,
        difficulty_level=difficulty_level
    )

    # Log the game start event
    await analytics_repo.log_event(
        db=db,
        session_id=session.id,
        event_type=EventType.GAME_START,
        input_word=start_word,
        is_valid=True,
        sam_phase="evaluate"
    )

    return session


async def get_active_game(db: AsyncSession, user_id: uuid.UUID) -> Optional[GameSession]:
    """Get the user's current active game session."""
    return await session_repo.get_user_active_session(db, user_id)


async def validate_move(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    current_word: str,
    next_word: str,
    thinking_time_ms: Optional[int] = None
) -> Tuple[bool, int, Optional[str], dict]:
    """
    Validate a word move in the game.

    Returns:
        Tuple of (is_valid, score_delta, error_reason, session_info)
    """
    # Get the session
    session = await session_repo.get_game_session(db, session_id)
    if not session:
        raise GameError("Game session not found")

    if session.user_id != user_id:
        raise GameError("This is not your game session")

    if session.is_completed:
        raise GameError("This game is already completed")

    current_word = current_word.upper()
    next_word = next_word.upper()

    # Verify current word matches session state
    if session.current_word.upper() != current_word:
        raise GameError(f"Current word mismatch. Expected: {session.current_word}")

    # Check for duplicate words
    used_words = await analytics_repo.get_session_words_used(db, session_id)
    if next_word in used_words:
        # Log invalid move
        await analytics_repo.log_event(
            db=db,
            session_id=session_id,
            event_type=EventType.MOVE_INVALID,
            input_word=next_word,
            is_valid=False,
            error_reason=ErrorReason.ALREADY_USED,
            thinking_time_ms=thinking_time_ms,
            sam_phase="design"
        )
        return False, 0, "already_used", _get_session_info(session)

    # Validate the move using the word graph
    graph = get_word_graph()
    is_valid, error_reason = graph.is_valid_move(current_word, next_word)

    if not is_valid:
        # Map error reason to enum
        error_enum = _map_error_reason(error_reason)

        # Log invalid move
        await analytics_repo.log_event(
            db=db,
            session_id=session_id,
            event_type=EventType.MOVE_INVALID,
            input_word=next_word,
            is_valid=False,
            error_reason=error_enum,
            thinking_time_ms=thinking_time_ms,
            sam_phase="design"
        )
        return False, 0, error_reason, _get_session_info(session)

    # Valid move - update session
    new_moves = session.moves_count + 1
    score_delta = settings.xp_per_valid_move
    new_score = session.total_score + score_delta

    await session_repo.update_game_session(
        db=db,
        session_id=session_id,
        current_word=next_word,
        moves_count=new_moves,
        total_score=new_score
    )

    # Log valid move
    await analytics_repo.log_event(
        db=db,
        session_id=session_id,
        event_type=EventType.MOVE_VALID,
        input_word=next_word,
        is_valid=True,
        thinking_time_ms=thinking_time_ms,
        sam_phase="develop"
    )

    # Check if game is complete
    is_complete = next_word == session.target_word_end.upper()

    if is_complete:
        await _complete_game(db, session_id, user_id, True, new_score)

    # Update session info with latest data
    session = await session_repo.get_game_session(db, session_id)
    return True, score_delta, None, _get_session_info(session, is_complete)


async def get_hint(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID
) -> Tuple[str, int, int, int, int]:
    """
    Get a hint for the current game.

    Returns:
        Tuple of (hint_word, hint_cost, hints_used, hints_remaining, max_hints_allowed)
    """
    session = await session_repo.get_game_session(db, session_id)
    if not session:
        raise GameError("Game session not found")

    if session.user_id != user_id:
        raise GameError("This is not your game session")

    if session.is_completed:
        raise GameError("This game is already completed")

    # Calculate max hints based on difficulty level
    # Difficulty 1=5, 2=4, 3=3, 4=2, 5=1
    difficulty = session.difficulty_level or 3
    max_hints_allowed = max(1, 6 - difficulty)

    # Check if user has exhausted hints
    if session.hints_used >= max_hints_allowed:
        raise GameError(f"No hints remaining. Maximum {max_hints_allowed} hints allowed for difficulty {difficulty}.")

    # Get hint from graph
    graph = get_word_graph()
    hint = graph.get_hint(session.current_word, session.target_word_end)

    if not hint:
        raise GameError("No path available to target. Consider forfeiting.")

    # Update hint count and deduct XP
    new_hints = session.hints_used + 1
    hint_cost = settings.xp_penalty_hint
    hints_remaining = max_hints_allowed - new_hints

    await session_repo.update_game_session(
        db=db,
        session_id=session_id,
        hints_used=new_hints
    )

    # Log hint usage
    await analytics_repo.log_event(
        db=db,
        session_id=session_id,
        event_type=EventType.HINT_USED,
        input_word=hint,
        is_valid=True,
        sam_phase="evaluate"
    )

    return hint, hint_cost, new_hints, hints_remaining, max_hints_allowed


async def complete_game(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    forfeit: bool = False
) -> dict:
    """
    Complete or forfeit a game session.

    Returns:
        Game completion summary.
    """
    session = await session_repo.get_game_session(db, session_id)
    if not session:
        raise GameError("Game session not found")

    if session.user_id != user_id:
        raise GameError("This is not your game session")

    # Idempotent: If already completed, return the existing result
    if session.is_completed:
        # Fetch data for the response without modifying state
        words_used = await analytics_repo.get_session_words_used(db, session_id)
        path = [session.target_word_start] + words_used

        graph = get_word_graph()
        optimal_path = graph.get_shortest_path(session.target_word_start, session.target_word_end)
        optimal_length = len(optimal_path) - 1 if optimal_path else 0

        return {
            "session_id": session_id,
            "is_won": session.is_won,
            "total_score": session.total_score,
            "moves_count": session.moves_count,
            "hints_used": session.hints_used,
            "xp_earned": session.total_score,  # Already awarded
            "path_taken": path,
            "optimal_path_length": optimal_length
        }

    is_won = not forfeit and session.current_word.upper() == session.target_word_end.upper()

    return await _complete_game(db, session_id, user_id, is_won, session.total_score, forfeit)


async def _complete_game(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    is_won: bool,
    final_score: int,
    forfeit: bool = False
) -> dict:
    """Internal method to finalize a game."""
    session = await session_repo.get_game_session(db, session_id)

    # Calculate XP earned
    xp_earned = final_score
    if is_won:
        xp_earned += settings.xp_bonus_completion

    # Complete the session
    await session_repo.complete_game_session(
        db=db,
        session_id=session_id,
        is_won=is_won,
        total_score=final_score
    )

    # Award XP to user
    await user_repo.update_user_xp(db, user_id, xp_earned)

    # Log completion/forfeit event
    event_type = EventType.GAME_FORFEIT if forfeit else EventType.GAME_COMPLETE
    await analytics_repo.log_event(
        db=db,
        session_id=session_id,
        event_type=event_type,
        input_word=session.current_word,
        is_valid=True,
        sam_phase="evaluate"
    )

    # Get the words used in the game
    words_used = await analytics_repo.get_session_words_used(db, session_id)
    path = [session.target_word_start] + words_used

    # Get optimal path length
    graph = get_word_graph()
    optimal_path = graph.get_shortest_path(session.target_word_start, session.target_word_end)
    optimal_length = len(optimal_path) - 1 if optimal_path else 0

    return {
        "session_id": session_id,
        "is_won": is_won,
        "total_score": final_score,
        "moves_count": session.moves_count,
        "hints_used": session.hints_used,
        "xp_earned": xp_earned,
        "path_taken": path,
        "optimal_path_length": optimal_length
    }


def _get_session_info(session: GameSession, is_complete: bool = False) -> dict:
    """Get current session info for response."""
    graph = get_word_graph()
    distance = graph.get_distance(session.current_word, session.target_word_end)

    return {
        "session_id": session.id,
        "current_word": session.current_word,
        "target_word": session.target_word_end,
        "distance_remaining": distance if distance > 0 else 0,
        "moves_count": session.moves_count,
        "total_score": session.total_score,
        "is_complete": is_complete
    }


def _map_error_reason(reason: Optional[str]) -> Optional[ErrorReason]:
    """Map string error reason to enum."""
    if not reason:
        return None

    mapping = {
        "not_in_dictionary": ErrorReason.NOT_IN_DICTIONARY,
        "not_one_letter": ErrorReason.NOT_ONE_LETTER,
        "same_word": ErrorReason.SAME_WORD,
        "wrong_length": ErrorReason.WRONG_LENGTH,
        "already_used": ErrorReason.ALREADY_USED,
        "not_edtech_word": ErrorReason.NOT_EDTECH_WORD
    }

    return mapping.get(reason)
