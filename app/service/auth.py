"""Authentication service for user signup, login, password reset, and email verification."""

from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, create_access_token, generate_secure_token
from app.core.config import settings
from app.repo import user as user_repo
from app.model.user import User, UserRole
from app.schema.auth import Token
from app.service.email import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
    send_password_changed_email,
    EmailError
)


class AuthError(Exception):
    """Custom exception for authentication errors."""
    pass


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    matric_no: Optional[str] = None,
    send_email: bool = True
) -> User:
    """
    Register a new user.

    Args:
        db: Database session
        email: User email
        password: User password
        first_name: User's first name
        last_name: User's last name
        matric_no: Optional matriculation number
        send_email: Whether to send verification email

    Raises:
        AuthError: If email or matric_no already exists.
    """
    # Check if email exists
    existing = await user_repo.get_user_by_email(db, email)
    if existing:
        raise AuthError("Email already registered")

    # Check if matric_no exists (if provided)
    if matric_no:
        existing = await user_repo.get_user_by_matric(db, matric_no)
        if existing:
            raise AuthError("Matriculation number already registered")

    # Create the user
    user = await user_repo.create_user(
        db=db,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        matric_no=matric_no,
        role=UserRole.STUDENT
    )

    # Send verification email
    if send_email:
        try:
            await send_email_verification(db, user.id)
        except EmailError:
            # Don't fail registration if email sending fails
            pass

    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Returns:
        User if credentials are valid, None otherwise.
    """
    user = await user_repo.get_user_by_email(db, email)
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Token:
    """
    Login a user and return an access token.

    Raises:
        AuthError: If credentials are invalid.
    """
    user = await authenticate_user(db, email, password)
    if not user:
        raise AuthError("Invalid email or password")

    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        first_name=user.first_name or ""
    )


# ============= Email Verification =============

async def send_email_verification(db: AsyncSession, user_id) -> bool:
    """
    Generate verification token and send verification email.

    Args:
        db: Database session
        user_id: User ID to send verification to

    Returns:
        True if email sent successfully

    Raises:
        AuthError: If user not found or already verified
    """
    user = await user_repo.get_user_by_id(db, user_id)
    if not user:
        raise AuthError("User not found")

    if user.is_email_verified:
        raise AuthError("Email already verified")

    # Generate verification token
    token = generate_secure_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.email_verification_token_expire_hours)

    # Save token to database
    await user_repo.set_email_verification_token(db, user_id, token, expires)

    # Send email
    await send_verification_email(user.email, token)
    return True


async def verify_email(db: AsyncSession, token: str) -> User:
    """
    Verify email using token.

    Args:
        db: Database session
        token: Verification token from email

    Returns:
        Verified user

    Raises:
        AuthError: If token is invalid or expired
    """
    user = await user_repo.get_user_by_verification_token(db, token)
    if not user:
        raise AuthError("Invalid verification token")

    # Check if token expired
    if user.email_verification_token_expires:
        if datetime.now(timezone.utc) > user.email_verification_token_expires:
            raise AuthError("Verification token has expired")

    # Mark email as verified
    user = await user_repo.mark_email_verified(db, user.id)

    # Send welcome email
    try:
        await send_welcome_email(user.email)
    except EmailError:
        pass  # Don't fail verification if welcome email fails

    return user


async def resend_verification_email(db: AsyncSession, email: str) -> bool:
    """
    Resend verification email to user.

    Args:
        db: Database session
        email: User email address

    Returns:
        True if email sent (always returns True for security)
    """
    user = await user_repo.get_user_by_email(db, email)
    if not user:
        # Don't reveal if email exists
        return True

    if user.is_email_verified:
        # Don't reveal if already verified
        return True

    try:
        await send_email_verification(db, user.id)
    except (AuthError, EmailError):
        pass  # Silently fail to not reveal user existence

    return True


# ============= Password Reset =============

async def request_password_reset(db: AsyncSession, email: str) -> bool:
    """
    Generate password reset token and send reset email.

    Args:
        db: Database session
        email: User email address

    Returns:
        True (always, for security - don't reveal if email exists)
    """
    user = await user_repo.get_user_by_email(db, email)
    if not user:
        # Don't reveal if email exists
        return True

    # Generate reset token
    token = generate_secure_token()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_expire_minutes)

    # Save token to database
    await user_repo.set_password_reset_token(db, user.id, token, expires)

    # Send email
    try:
        await send_password_reset_email(user.email, token)
    except EmailError:
        pass  # Silently fail

    return True


async def confirm_password_reset(
    db: AsyncSession,
    token: str,
    new_password: str
) -> User:
    """
    Verify reset token and update password.

    Args:
        db: Database session
        token: Password reset token from email
        new_password: New password to set

    Returns:
        Updated user

    Raises:
        AuthError: If token is invalid or expired
    """
    user = await user_repo.get_user_by_password_reset_token(db, token)
    if not user:
        raise AuthError("Invalid or expired reset token")

    # Check if token expired
    if user.password_reset_token_expires:
        if datetime.now(timezone.utc) > user.password_reset_token_expires:
            raise AuthError("Reset token has expired")

    # Update password and clear token
    user = await user_repo.update_password_and_clear_token(db, user.id, new_password)

    # Send notification email
    try:
        await send_password_changed_email(user.email)
    except EmailError:
        pass  # Don't fail if notification email fails

    return user


# ============= Change Password =============

async def change_password(
    db: AsyncSession,
    user_id,
    current_password: str,
    new_password: str
) -> User:
    """
    Change password for authenticated user.

    Args:
        db: Database session
        user_id: User ID
        current_password: Current password for verification
        new_password: New password to set

    Returns:
        Updated user

    Raises:
        AuthError: If current password is incorrect
    """
    user = await user_repo.get_user_by_id(db, user_id)
    if not user:
        raise AuthError("User not found")

    # Verify current password
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Current password is incorrect")

    # Update password
    user = await user_repo.update_user_password(db, user.id, new_password)

    # Send notification email
    try:
        await send_password_changed_email(user.email)
    except EmailError:
        pass

    return user
