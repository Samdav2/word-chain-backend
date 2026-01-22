"""Statistics and Leaderboard API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import CurrentUser
from app.service.analytics import get_personal_stats, get_leaderboard
from app.schema.analytics import PersonalStats, LeaderboardResponse


router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get(
    "/personal",
    response_model=PersonalStats,
    summary="Get personal statistics",
    description="Get comprehensive statistics for the current user."
)
async def get_my_stats(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get personal statistics and analytics.

    Includes:
    - Game performance metrics (wins, losses, win rate)
    - SAM phase scores (Evaluation, Design, Develop)
    - Error breakdown analysis
    - Time-on-task metrics
    - Recent game history
    """
    stats = await get_personal_stats(db, current_user.id)
    return stats


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Get leaderboard",
    description="Get the top students ranked by XP."
)
async def get_top_students(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 10
):
    """
    Get the leaderboard showing top students.

    - **limit**: Number of top players to return (default: 10)

    Rankings are based on total XP earned.
    Your own rank is included if you're not in the top list.
    """
    leaderboard = await get_leaderboard(
        db=db,
        current_user_id=current_user.id,
        limit=limit
    )
    return leaderboard
