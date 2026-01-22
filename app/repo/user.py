import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.user import User, UserRole
from app.core.security import hash_password


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    matric_no: Optional[str] = None,
    role: UserRole = UserRole.STUDENT
) -> User:
    """Create a new user."""
    password_hash = hash_password(password)

    user = User(
        email=email.lower(),
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        matric_no=matric_no,
        role=role
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Get a user by their ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by their email address."""
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_matric(db: AsyncSession, matric_no: str) -> Optional[User]:
    """Get a user by their matriculation number."""
    result = await db.execute(
        select(User).where(User.matric_no == matric_no)
    )
    return result.scalar_one_or_none()


async def update_user_xp(db: AsyncSession, user_id: uuid.UUID, xp_delta: int) -> Optional[User]:
    """Add or subtract XP from a user."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.current_xp = max(0, user.current_xp + xp_delta)  # Don't go below 0
        await db.commit()
        await db.refresh(user)
    return user


async def update_user_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    avatar_url: Optional[str] = None,
    preferred_difficulty: Optional[str] = None
) -> Optional[User]:
    """Update user profile information."""
    user = await get_user_by_id(db, user_id)
    if user:
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if preferred_difficulty is not None:
            user.preferred_difficulty = preferred_difficulty
        await db.commit()
        await db.refresh(user)
    return user


async def update_user_password(
    db: AsyncSession,
    user_id: uuid.UUID,
    new_password: str
) -> Optional[User]:
    """Update user password."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.password_hash = hash_password(new_password)
        await db.commit()
        await db.refresh(user)
    return user


async def get_all_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    """Get all users with pagination."""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_total_users_count(db: AsyncSession) -> int:
    """Get total number of users."""
    result = await db.execute(select(func.count(User.id)))
    return result.scalar() or 0


# ============= Email Verification Functions =============

async def set_email_verification_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    token: str,
    expires: datetime
) -> Optional[User]:
    """Set email verification token for a user."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.email_verification_token = token
        user.email_verification_token_expires = expires
        await db.commit()
        await db.refresh(user)
    return user


async def get_user_by_verification_token(db: AsyncSession, token: str) -> Optional[User]:
    """Get a user by their email verification token."""
    result = await db.execute(
        select(User).where(User.email_verification_token == token)
    )
    return result.scalar_one_or_none()


async def mark_email_verified(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Mark a user's email as verified and clear the token."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_token_expires = None
        await db.commit()
        await db.refresh(user)
    return user


# ============= Password Reset Functions =============

async def set_password_reset_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    token: str,
    expires: datetime
) -> Optional[User]:
    """Set password reset token for a user."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.password_reset_token = token
        user.password_reset_token_expires = expires
        await db.commit()
        await db.refresh(user)
    return user


async def get_user_by_password_reset_token(db: AsyncSession, token: str) -> Optional[User]:
    """Get a user by their password reset token."""
    result = await db.execute(
        select(User).where(User.password_reset_token == token)
    )
    return result.scalar_one_or_none()


async def clear_password_reset_token(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Clear the password reset token after successful reset."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.password_reset_token = None
        user.password_reset_token_expires = None
        await db.commit()
        await db.refresh(user)
    return user


async def update_password_and_clear_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    new_password: str
) -> Optional[User]:
    """Update user password and clear reset token."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.password_hash = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_token_expires = None
        await db.commit()
        await db.refresh(user)
    return user
