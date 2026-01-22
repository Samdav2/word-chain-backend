"""Dashboard API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import CurrentUser
from app.service.dashboard import get_dashboard_stats
from app.schema.dashboard import DashboardStats


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Get dashboard statistics",
    description="Get comprehensive dashboard statistics for the current user."
)
async def get_my_dashboard_stats(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get dashboard statistics including:

    - **level**: Current user level (1-20+)
    - **current_xp**: XP earned towards next level
    - **xp_to_next_level**: Total XP needed for next level
    - **total_xp**: Cumulative XP earned
    - **current_win_streak**: Current consecutive wins
    - **words_mastered**: Unique words successfully used
    - **global_rank**: User's rank among all players
    - **rank_percentile**: Percentile ranking (e.g., "Top 5%")
    """
    stats = await get_dashboard_stats(db, current_user.id)
    return stats
