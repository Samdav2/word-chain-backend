"""Missions API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import CurrentUser
from app.service.missions import get_daily_missions
from app.schema.mission import DailyMissionsResponse


router = APIRouter(prefix="/missions", tags=["Missions"])


@router.get(
    "/daily",
    response_model=DailyMissionsResponse,
    summary="Get daily missions",
    description="Get current daily missions and progress."
)
async def get_my_daily_missions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get daily missions with current progress.

    Missions reset at midnight UTC each day.

    Available missions:
    - **Word Warrior**: Win 3 word chain games
    - **Speed Demon**: Complete a game in under 10 moves
    - **Vocabulary Builder**: Use 20 unique words
    - **No Hints Master**: Win without hints
    - **Persistent Player**: Play 5 games today
    """
    missions = await get_daily_missions(db, current_user.id)
    return missions
