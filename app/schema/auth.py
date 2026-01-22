from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    first_name: str


class TokenPayload(BaseModel):
    """JWT token payload (decoded)."""
    sub: str  # User ID
    exp: int  # Expiration timestamp


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


# ============= Password Reset Schemas =============

class PasswordResetRequest(BaseModel):
    """Request for password reset email."""
    email: EmailStr = Field(..., description="Email address to send reset link to")


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


# ============= Change Password Schema =============

class ChangePassword(BaseModel):
    """Change password for authenticated users."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


# ============= Email Verification Schemas =============

class EmailVerificationRequest(BaseModel):
    """Request to resend verification email."""
    email: EmailStr = Field(..., description="Email address to send verification to")


class EmailVerificationConfirm(BaseModel):
    """Confirm email verification with token."""
    token: str = Field(..., description="Email verification token")
