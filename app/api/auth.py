"""Authentication API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import CurrentUser
from app.service.auth import (
    register_user,
    login_user,
    request_password_reset,
    confirm_password_reset,
    verify_email,
    resend_verification_email,
    change_password,
    AuthError
)
from app.schema.user import UserCreate, UserResponse
from app.schema.auth import (
    Token,
    MessageResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePassword,
    EmailVerificationRequest,
    EmailVerificationConfirm
)



router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new student account with email and password."
)
async def signup(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Register a new user (student).

    - **email**: Valid email address (required)
    - **first_name**: User's first name (required)
    - **last_name**: User's last name (required)
    - **password**: At least 6 characters (required)
    - **matric_no**: LASU matriculation number (optional)
    """
    try:
        user = await register_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            matric_no=user_data.matric_no
        )
        return user
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
    description="Authenticate with email and password to receive a JWT token."
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Login with email and password.

    Returns a JWT access token for authenticating subsequent requests.
    Use the token in the Authorization header: `Bearer <token>`
    """
    try:
        token = await login_user(
            db=db,
            email=form_data.username,  # OAuth2 form uses "username" field
            password=form_data.password
        )
        return token
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


# ============= Password Reset Endpoints =============

@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Send a password reset email to the specified email address."
)
async def password_reset_request(
    data: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Request a password reset email.

    For security, this endpoint always returns success even if the email is not registered.
    """
    await request_password_reset(db, data.email)
    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent.",
        success=True
    )


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    summary="Confirm password reset",
    description="Reset password using the token received via email."
)
async def password_reset_confirm(
    data: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Reset password using the token from the reset email.

    - **token**: The reset token from the email link
    - **new_password**: New password (minimum 8 characters)
    """
    try:
        await confirm_password_reset(db, data.token, data.new_password)
        return MessageResponse(
            message="Password has been reset successfully. You can now login with your new password.",
            success=True
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============= Change Password Endpoint =============

@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change password for the currently authenticated user."
)
async def change_user_password(
    data: ChangePassword,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Change password for the authenticated user.

    - **current_password**: Your current password
    - **new_password**: New password (minimum 8 characters)
    """
    try:
        await change_password(db, current_user.id, data.current_password, data.new_password)
        return MessageResponse(
            message="Password changed successfully.",
            success=True
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============= Email Verification Endpoints =============

@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email",
    description="Verify email address using the token received via email."
)
async def verify_user_email(
    data: EmailVerificationConfirm,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Verify email using the token from the verification email.

    - **token**: The verification token from the email link
    """
    try:
        await verify_email(db, data.token)
        return MessageResponse(
            message="Email verified successfully. Welcome to EdTech Word Chain!",
            success=True
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
    description="Resend the email verification link."
)
async def resend_verification(
    data: EmailVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Resend verification email.

    For security, this endpoint always returns success even if the email is not registered.
    """
    await resend_verification_email(db, data.email)
    return MessageResponse(
        message="If an account with that email exists and is not verified, a verification link has been sent.",
        success=True
    )
