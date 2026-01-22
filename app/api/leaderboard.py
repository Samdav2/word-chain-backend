"""Advanced Leaderboard API endpoints."""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import CurrentUser
from app.service.analytics import get_leaderboard
from app.repo import analytics as analytics_repo
from app.repo import user as user_repo
from app.schema.analytics import (
    LeaderboardResponse,
    LeaderboardEntry,
    UserRankDetails,
    TierInfo,
    PlayerTier,
    TIER_THRESHOLDS,
    TIER_BADGES,
    get_tier_from_xp
)


router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get(
    "",
    response_model=LeaderboardResponse,
    summary="Get full leaderboard",
    description="Get the full leaderboard with pagination and filtering options."
)
async def get_full_leaderboard(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip")
):
    """
    Get the full leaderboard with optional pagination.

    - **limit**: Number of entries to return (1-100)
    - **offset**: Number of entries to skip for pagination
    """
    leaderboard = await get_leaderboard(
        db=db,
        current_user_id=current_user.id,
        limit=limit + offset  # Get more to handle offset
    )

    # Apply offset
    if offset > 0:
        leaderboard.entries = leaderboard.entries[offset:offset+limit]

    return leaderboard


@router.get(
    "/top",
    response_model=LeaderboardResponse,
    summary="Get top 10 players",
    description="Get the top 10 players ranked by XP."
)
async def get_top_players(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get the top 10 players on the leaderboard.

    This is the quick view for displaying on dashboard or homepage.
    """
    return await get_leaderboard(db=db, current_user_id=current_user.id, limit=10)


@router.get(
    "/me",
    response_model=UserRankDetails,
    summary="Get your ranking details",
    description="Get detailed ranking information for the current user."
)
async def get_my_rank(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get your detailed ranking information.

    Includes:
    - Your current rank and percentile
    - Tier and badge
    - XP needed for next tier
    - Win statistics
    """
    # Get all users for accurate ranking
    all_data = await analytics_repo.get_leaderboard_data(db, limit=10000)
    total_players = await user_repo.get_total_users_count(db)

    # Find current user
    user_data = None
    user_rank = None
    for data in all_data:
        if data["user_id"] == current_user.id:
            user_data = data
            user_rank = data["rank"]
            break

    if not user_data:
        # User hasn't played yet
        user_data = {
            "display_name": f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.email.split("@")[0],
            "total_xp": current_user.current_xp,
            "games_won": 0,
            "total_games": 0,
            "win_rate": 0.0
        }
        user_rank = total_players  # Last place

    xp = user_data["total_xp"]
    current_tier = get_tier_from_xp(xp)

    # Calculate XP to next tier
    tier_order = [PlayerTier.BRONZE, PlayerTier.SILVER, PlayerTier.GOLD, PlayerTier.PLATINUM, PlayerTier.DIAMOND]
    current_tier_index = tier_order.index(current_tier)

    if current_tier_index < len(tier_order) - 1:
        next_tier = tier_order[current_tier_index + 1]
        xp_to_next = TIER_THRESHOLDS[next_tier] - xp
    else:
        next_tier = None
        xp_to_next = 0

    # Calculate percentile
    if total_players > 0:
        percentile = ((total_players - user_rank + 1) / total_players) * 100
    else:
        percentile = 100.0

    return UserRankDetails(
        rank=user_rank,
        total_players=total_players,
        display_name=user_data["display_name"],
        total_xp=xp,
        tier=current_tier,
        tier_badge=TIER_BADGES[current_tier],
        games_won=user_data["games_won"],
        total_games=user_data.get("total_games", 0),
        win_rate=user_data["win_rate"],
        xp_to_next_tier=xp_to_next,
        next_tier=next_tier,
        percentile=round(percentile, 1)
    )


@router.get(
    "/nearby",
    response_model=LeaderboardResponse,
    summary="Get players near your rank",
    description="Get players ranked around your position (±5 ranks)."
)
async def get_nearby_players(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    range_size: int = Query(default=5, ge=1, le=10, description="Number of players above/below")
):
    """
    Get players ranked near your position.

    Shows players ranked above and below you for competitive motivation.
    """
    # Get full leaderboard to find position
    all_data = await analytics_repo.get_leaderboard_data(db, limit=10000)
    total_players = await user_repo.get_total_users_count(db)

    # Find user's rank
    user_rank = None
    for data in all_data:
        if data["user_id"] == current_user.id:
            user_rank = data["rank"]
            break

    if user_rank is None:
        user_rank = total_players

    # Calculate range
    start_rank = max(1, user_rank - range_size)
    end_rank = min(total_players, user_rank + range_size)

    # Get entries in range
    entries = []
    for data in all_data:
        if start_rank <= data["rank"] <= end_rank:
            entries.append(LeaderboardEntry(
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
            ))

    return LeaderboardResponse(
        entries=entries,
        total_players=total_players,
        user_rank=user_rank
    )


@router.get(
    "/tiers",
    response_model=List[TierInfo],
    summary="Get tier information",
    description="Get all tier levels and their XP requirements."
)
async def get_tier_info():
    """
    Get information about all player tiers.

    Returns the XP requirements and badges for each tier level.
    """
    tiers = [
        TierInfo(
            tier=PlayerTier.BRONZE,
            name="Bronze",
            badge=TIER_BADGES[PlayerTier.BRONZE],
            min_xp=TIER_THRESHOLDS[PlayerTier.BRONZE],
            max_xp=TIER_THRESHOLDS[PlayerTier.SILVER] - 1
        ),
        TierInfo(
            tier=PlayerTier.SILVER,
            name="Silver",
            badge=TIER_BADGES[PlayerTier.SILVER],
            min_xp=TIER_THRESHOLDS[PlayerTier.SILVER],
            max_xp=TIER_THRESHOLDS[PlayerTier.GOLD] - 1
        ),
        TierInfo(
            tier=PlayerTier.GOLD,
            name="Gold",
            badge=TIER_BADGES[PlayerTier.GOLD],
            min_xp=TIER_THRESHOLDS[PlayerTier.GOLD],
            max_xp=TIER_THRESHOLDS[PlayerTier.PLATINUM] - 1
        ),
        TierInfo(
            tier=PlayerTier.PLATINUM,
            name="Platinum",
            badge=TIER_BADGES[PlayerTier.PLATINUM],
            min_xp=TIER_THRESHOLDS[PlayerTier.PLATINUM],
            max_xp=TIER_THRESHOLDS[PlayerTier.DIAMOND] - 1
        ),
        TierInfo(
            tier=PlayerTier.DIAMOND,
            name="Diamond",
            badge=TIER_BADGES[PlayerTier.DIAMOND],
            min_xp=TIER_THRESHOLDS[PlayerTier.DIAMOND],
            max_xp=None  # No upper limit
        )
    ]
    return tiers
