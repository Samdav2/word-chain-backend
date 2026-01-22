"""User profile API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import CurrentUser
from app.repo import user as user_repo
from app.repo import game_session as session_repo
from app.core.security import verify_password
from app.schema.user import UserResponse, UserProfile, UserUpdate, UserPasswordUpdate


router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
    description="Get the authenticated user's profile with game statistics."
)
async def get_me(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get the current authenticated user's profile.

    Includes:
    - Basic profile information
    - Game statistics (games played, won, win rate)
    - Total XP and moves
    """
    # Get game statistics
    stats = await session_repo.get_user_game_stats(db, current_user.id)

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        matric_no=current_user.matric_no,
        role=current_user.role,
        current_xp=current_user.current_xp,
        avatar_url=current_user.avatar_url,
        preferred_difficulty=current_user.preferred_difficulty,
        created_at=current_user.created_at,
        games_played=stats["total_games"],
        games_won=stats["games_won"],
        total_moves=stats["total_moves"],
        average_moves_per_game=stats["average_moves"],
        win_rate=stats["win_rate"]
    )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update the authenticated user's profile settings."
)
async def update_me(
    update_data: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update the current user's profile.

    - **avatar_url**: URL to profile avatar image
    - **preferred_difficulty**: "novice" or "expert"
    """
    user = await user_repo.update_user_profile(
        db=db,
        user_id=current_user.id,
        avatar_url=update_data.avatar_url,
        preferred_difficulty=update_data.preferred_difficulty
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put(
    "/me/password",
    response_model=UserResponse,
    summary="Change password",
    description="Change the authenticated user's password."
)
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Change the current user's password.

    Requires the current password for verification.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    user = await user_repo.update_user_password(
        db=db,
        user_id=current_user.id,
        new_password=password_data.new_password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
