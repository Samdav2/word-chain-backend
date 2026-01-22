"""Game API endpoints."""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import CurrentUser
from app.service.game import (
    start_game,
    get_active_game,
    validate_move,
    get_hint,
    complete_game,
    GameError
)
from app.service.word_graph import get_word_graph
from app.repo import game_session as session_repo
from app.schema.game import (
    GameStartRequest,
    GameStartResponse,
    MoveValidateRequest,
    MoveValidateResponse,
    HintRequest,
    HintResponse,
    GameCompleteRequest,
    GameCompleteResponse,
    GameSessionResponse,
    CategoriesResponse,
    CategoryInfo,
    WordInfo
)


router = APIRouter(prefix="/game", tags=["Game"])


@router.get(
    "/active",
    response_model=Optional[GameSessionResponse],
    summary="Get active game",
    description="Get the current user's active game session, if any."
)
async def get_my_active_game(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Check if the user has an active game session.

    Returns the active session details if one exists, or null if not.
    Use this to decide whether to show "Continue Game" or "Start New Game".
    """
    session = await get_active_game(db, current_user.id)

    if not session:
        return None

    # Calculate XP earned (current score)
    # Note: XP is only finalized on completion, but we show current score
    xp_earned = session.total_score

    return GameSessionResponse(
        id=session.id,
        mode=session.mode,
        category=session.category,
        difficulty_level=session.difficulty_level,
        start_time=session.start_time,
        end_time=session.end_time,
        target_word_start=session.target_word_start,
        target_word_end=session.target_word_end,
        moves_count=session.moves_count,
        hints_used=session.hints_used,
        is_completed=session.is_completed,
        is_won=session.is_won,
        total_score=session.total_score,
        xp_earned=xp_earned
    )


@router.post(
    "/start",
    response_model=GameStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new game",
    description="Initialize a new word chain game session with optional category and difficulty."
)
async def start_new_game(
    game_request: GameStartRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Start a new word chain game.

    - **mode**: STANDARD (any dictionary word) or EDTECH_ONLY (educational terms)
    - **category**: Word category (general, science, biology, physics, education, mixed)
    - **difficulty**: Optional difficulty level (1-5)

    Returns the start word, target word, and session ID.
    Transform the start word into the target word by changing one letter at a time!
    """
    try:
        session = await start_game(
            db=db,
            user_id=current_user.id,
            mode=game_request.mode,
            category=game_request.category,
            difficulty=game_request.difficulty
        )

        category_desc = {
            "general": "common English words",
            "science": "science vocabulary",
            "biology": "biology terms",
            "physics": "physics terms",
            "education": "educational vocabulary",
            "mixed": "all categories"
        }
        cat_name = session.category.value if session.category else "mixed"

        return GameStartResponse(
            session_id=session.id,
            start_word=session.target_word_start,
            target_word=session.target_word_end,
            mode=session.mode,
            category=session.category,
            difficulty_level=session.difficulty_level,
            message=f"🎮 Game started! Transform '{session.target_word_start}' into '{session.target_word_end}' using {category_desc.get(cat_name, 'words')}."
        )
    except GameError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/validate",
    response_model=MoveValidateResponse,
    summary="Validate a word move",
    description="Check if a word move is valid and update the game state."
)
async def validate_word_move(
    move_request: MoveValidateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Validate a word move in the game.

    - **session_id**: Current game session ID
    - **current_word**: Your current word
    - **next_word**: The word you want to move to
    - **thinking_time_ms**: (Optional) Time spent thinking before this move

    A valid move changes exactly one letter and results in a valid dictionary word.
    """
    try:
        is_valid, score_delta, reason, session_info = await validate_move(
            db=db,
            user_id=current_user.id,
            session_id=move_request.session_id,
            current_word=move_request.current_word,
            next_word=move_request.next_word,
            thinking_time_ms=move_request.thinking_time_ms
        )

        if is_valid:
            message = f"Valid move! +{score_delta} points."
            if session_info.get("is_complete"):
                message = f"🎉 Congratulations! You've completed the chain! +{score_delta} points."
            elif session_info.get("distance_remaining", 0) > 0:
                message += f" You are {session_info['distance_remaining']} steps away from the goal."
        else:
            error_messages = {
                "not_in_dictionary": "That word is not in the dictionary.",
                "not_one_letter": "You must change exactly one letter.",
                "same_word": "You entered the same word.",
                "wrong_length": "Word length must match.",
                "already_used": "You've already used that word in this game."
            }
            message = error_messages.get(reason, "Invalid move.")

        return MoveValidateResponse(
            valid=is_valid,
            score_delta=score_delta,
            reason=reason,
            distance_remaining=session_info.get("distance_remaining"),
            current_word=session_info.get("current_word", move_request.current_word),
            target_word=session_info.get("target_word", ""),
            total_score=session_info.get("total_score", 0),
            moves_count=session_info.get("moves_count", 0),
            is_complete=session_info.get("is_complete", False),
            message=message
        )
    except GameError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/hint",
    response_model=HintResponse,
    summary="Get a hint",
    description="Get the next word suggestion using BFS algorithm."
)
async def get_game_hint(
    hint_request: HintRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get a hint for the current game.

    Uses Breadth-First Search to find the optimal next word.
    Using hints will cost XP points!

    - **session_id**: Current game session ID
    """
    try:
        hint_word, hint_cost, hints_used, hints_remaining, max_hints_allowed = await get_hint(
            db=db,
            user_id=current_user.id,
            session_id=hint_request.session_id
        )

        return HintResponse(
            hint_word=hint_word,
            hint_cost=hint_cost,
            hints_used=hints_used,
            hints_remaining=hints_remaining,
            max_hints_allowed=max_hints_allowed,
            message=f"💡 Try the word: '{hint_word}'. This hint costs {hint_cost} XP. ({hints_remaining} hints remaining)"
        )
    except GameError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/complete",
    response_model=GameCompleteResponse,
    summary="Complete or forfeit a game",
    description="End the current game session (win, lose, or forfeit)."
)
async def complete_current_game(
    complete_request: GameCompleteRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Complete or forfeit the current game.

    - **session_id**: Current game session ID
    - **forfeit**: Set to true to give up (lose the game)
    """
    try:
        result = await complete_game(
            db=db,
            user_id=current_user.id,
            session_id=complete_request.session_id,
            forfeit=complete_request.forfeit
        )

        if complete_request.forfeit:
            message = "You forfeited the game. Better luck next time!"
        elif result["is_won"]:
            message = f"🏆 Victory! You completed the chain in {result['moves_count']} moves and earned {result['xp_earned']} XP!"
        else:
            message = f"Game over. You earned {result['xp_earned']} XP. Keep practicing!"

        return GameCompleteResponse(
            session_id=result["session_id"],
            is_won=result["is_won"],
            total_score=result["total_score"],
            moves_count=result["moves_count"],
            hints_used=result["hints_used"],
            xp_earned=result["xp_earned"],
            path_taken=result["path_taken"],
            optimal_path_length=result["optimal_path_length"],
            message=message
        )
    except GameError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/history",
    response_model=List[GameSessionResponse],
    summary="Get game history",
    description="Get the current user's game history."
)
async def get_game_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 20
):
    """
    Get the user's past game sessions.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    sessions = await session_repo.get_user_sessions(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    # Calculate XP earned for each session
    # XP = total_score + bonus if won
    from app.core.config import settings

    result = []
    for s in sessions:
        xp_earned = s.total_score
        if s.is_won:
            xp_earned += settings.xp_bonus_completion

        result.append(GameSessionResponse(
            id=s.id,
            mode=s.mode,
            category=s.category,
            difficulty_level=s.difficulty_level,
            start_time=s.start_time,
            end_time=s.end_time,
            target_word_start=s.target_word_start,
            target_word_end=s.target_word_end,
            moves_count=s.moves_count,
            hints_used=s.hints_used,
            is_completed=s.is_completed,
            is_won=s.is_won,
            total_score=s.total_score,
            xp_earned=xp_earned
        ))

    return result


# Categories endpoints

@router.get(
    "/categories",
    response_model=CategoriesResponse,
    summary="List word categories",
    description="Get all available word categories with statistics."
)
async def list_categories():
    """
    Get all available word categories.

    Returns category names, descriptions, word counts, and sample words.
    """
    graph = get_word_graph()
    stats = graph.get_stats()

    category_descriptions = {
        "general": "Common English vocabulary suitable for all players",
        "science": "General science terminology including lab terms",
        "biology": "Life science vocabulary: anatomy, organisms, cells",
        "physics": "Physical science terms: forces, energy, motion",
        "education": "Academic and educational terminology",
        "mixed": "All categories combined for varied gameplay"
    }

    categories = []
    for cat_name in ["general", "science", "biology", "physics", "education", "mixed"]:
        cat_stats = graph.get_category_stats(cat_name)
        categories.append(CategoryInfo(
            name=cat_name,
            description=category_descriptions.get(cat_name, ""),
            word_count=cat_stats["word_count"],
            sample_words=cat_stats["sample_words"][:10]
        ))

    return CategoriesResponse(
        categories=categories,
        total_words=stats["total_words"]
    )


@router.get(
    "/categories/{category_name}",
    response_model=CategoryInfo,
    summary="Get category details",
    description="Get detailed information about a specific word category."
)
async def get_category_details(category_name: str):
    """
    Get detailed information about a word category.

    - **category_name**: One of: general, science, biology, physics, education, mixed
    """
    valid_categories = ["general", "science", "biology", "physics", "education", "mixed"]
    if category_name.lower() not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{category_name}' not found. Valid categories: {valid_categories}"
        )

    graph = get_word_graph()
    cat_stats = graph.get_category_stats(category_name.lower())

    category_descriptions = {
        "general": "Common English vocabulary suitable for all players",
        "science": "General science terminology including lab terms",
        "biology": "Life science vocabulary: anatomy, organisms, cells",
        "physics": "Physical science terms: forces, energy, motion",
        "education": "Academic and educational terminology",
        "mixed": "All categories combined for varied gameplay"
    }

    return CategoryInfo(
        name=category_name.lower(),
        description=category_descriptions.get(category_name.lower(), ""),
        word_count=cat_stats["word_count"],
        sample_words=cat_stats["sample_words"][:20]
    )


@router.get(
    "/word/{word}",
    response_model=WordInfo,
    summary="Get word information",
    description="Get educational information about a specific word."
)
async def get_word_info(word: str):
    """
    Get detailed information about a word.

    Returns category, difficulty, definition, learning tips, and valid next moves.
    """
    graph = get_word_graph()
    word = word.upper()

    if not graph.is_valid_word(word):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Word '{word}' not found in dictionary"
        )

    # Find which category the word belongs to
    category = None
    for cat_name, words in graph.words_by_category.items():
        if word in words:
            category = cat_name
            break

    # Get rich definition data
    definition_data = graph.get_word_definition(word) or {}

    return WordInfo(
        word=word,
        category=category,
        difficulty=graph.get_word_difficulty_level(word),
        definition=definition_data.get("definition"),
        pronunciation=definition_data.get("pronunciation"),
        part_of_speech=definition_data.get("part_of_speech"),
        examples=definition_data.get("examples", []),
        etymology=definition_data.get("etymology"),
        learning_tip=graph.get_learning_tip(word),
        neighbors=graph.get_neighbors(word)[:10]
    )
