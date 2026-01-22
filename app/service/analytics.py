"""Analytics service for user statistics and leaderboards."""

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repo import analytics as analytics_repo
from app.repo import game_session as session_repo
from app.repo import user as user_repo
from app.service.word_graph import get_word_graph
from app.schema.analytics import (
    PersonalStats,
    ErrorBreakdown,
    SAMScores,
    TimeMetrics,
    GameSummary,
    LeaderboardEntry,
    LeaderboardResponse
)


async def get_personal_stats(db: AsyncSession, user_id: uuid.UUID) -> PersonalStats:
    """
    Get comprehensive personal statistics for a user.

    Includes game stats, SAM phase scores, error breakdowns, and recent games.
    """
    # Get basic user info
    user = await user_repo.get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    # Get game statistics
    game_stats = await session_repo.get_user_game_stats(db, user_id)

    # Get error breakdown
    error_data = await analytics_repo.get_user_error_breakdown(db, user_id)
    error_breakdown = ErrorBreakdown(
        not_in_dictionary=error_data.get("not_in_dictionary", 0),
        not_one_letter=error_data.get("not_one_letter", 0),
        same_word=error_data.get("same_word", 0),
        wrong_length=error_data.get("wrong_length", 0),
        already_used=error_data.get("already_used", 0)
    )

    # Get time metrics
    avg_thinking = await analytics_repo.get_average_thinking_time(db, user_id)
    time_metrics = TimeMetrics(
        average_thinking_time_ms=avg_thinking,
        total_session_time_seconds=0  # Could calculate from session durations
    )

    # Calculate SAM scores
    sam_scores = await _calculate_sam_scores(db, user_id, game_stats)

    # Get recent games
    recent_sessions = await session_repo.get_user_sessions(db, user_id, limit=5)
    recent_games = [
        GameSummary(
            session_id=s.id,
            date=s.start_time,
            start_word=s.target_word_start,
            target_word=s.target_word_end,
            moves=s.moves_count,
            is_won=s.is_won,
            score=s.total_score
        )
        for s in recent_sessions if s.is_completed
    ]

    return PersonalStats(
        user_id=user_id,
        total_games=game_stats["total_games"],
        games_won=game_stats["games_won"],
        games_lost=game_stats["games_lost"],
        win_rate=game_stats["win_rate"],
        total_moves=game_stats["total_moves"],
        average_moves_per_game=game_stats["average_moves"],
        total_hints_used=game_stats["total_hints_used"],
        total_xp=user.current_xp,
        current_streak=0,  # Could implement streak tracking
        best_streak=0,
        error_breakdown=error_breakdown,
        sam_scores=sam_scores,
        time_metrics=time_metrics,
        recent_games=recent_games
    )


async def get_leaderboard(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    limit: int = 10
) -> LeaderboardResponse:
    """
    Get the leaderboard with top players.

    Also returns the current user's rank if they're not in the top list.
    """
    leaderboard_data = await analytics_repo.get_leaderboard_data(db, limit)

    entries = [
        LeaderboardEntry(
            rank=data["rank"],
            user_id=data["user_id"],
            display_name=data["display_name"],
            email=data["email"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            matric_no=data["matric_no"],
            total_xp=data["total_xp"],
            games_won=data["games_won"],
            total_games=data.get("total_games", 0),
            win_rate=data["win_rate"],
            average_moves=data["average_moves"]
        )
        for data in leaderboard_data
    ]

    # Find current user's rank
    user_rank = None
    for entry in entries:
        if entry.user_id == current_user_id:
            user_rank = entry.rank
            break

    # Get total player count
    total_players = await user_repo.get_total_users_count(db)

    return LeaderboardResponse(
        entries=entries,
        total_players=total_players,
        user_rank=user_rank
    )


async def _calculate_sam_scores(
    db: AsyncSession,
    user_id: uuid.UUID,
    game_stats: dict
) -> SAMScores:
    """
    Calculate SAM (Successive Approximation Model) phase scores.

    - Evaluation Score: How effectively the user validates their moves
    - Design Score: Path efficiency (optimal moves vs actual moves)
    - Develop Score: Success rate in completing games
    """
    graph = get_word_graph()

    # Get completed sessions for efficiency analysis
    sessions = await session_repo.get_user_sessions(db, user_id, limit=20)
    completed_sessions = [s for s in sessions if s.is_completed]

    # Evaluation Score: Based on valid move percentage
    total_games = game_stats["total_games"]
    total_moves = game_stats["total_moves"]

    # This would require counting invalid moves from analytics
    # For now, use win rate as proxy
    evaluation_score = game_stats["win_rate"] * 100

    # Design Score: Path efficiency
    if completed_sessions:
        efficiency_scores = []
        for session in completed_sessions:
            if session.is_won:
                optimal = graph.get_distance(
                    session.target_word_start,
                    session.target_word_end
                )
                if optimal > 0 and session.moves_count > 0:
                    efficiency = (optimal / session.moves_count) * 100
                    efficiency_scores.append(min(efficiency, 100))

        design_score = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0
    else:
        design_score = 0

    # Develop Score: Success rate
    develop_score = game_stats["win_rate"] * 100

    return SAMScores(
        evaluation_score=round(evaluation_score, 1),
        design_score=round(design_score, 1),
        develop_score=round(develop_score, 1)
    )
