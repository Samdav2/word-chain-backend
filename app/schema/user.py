import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, computed_field
from app.model.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    password: str = Field(..., min_length=6, max_length=100)
    matric_no: Optional[str] = Field(None, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None
    preferred_difficulty: Optional[str] = Field(None, pattern="^(novice|expert)$")


class UserPasswordUpdate(BaseModel):
    """Schema for password update."""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    """Public user response schema."""
    id: uuid.UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    matric_no: Optional[str] = None
    role: UserRole
    current_xp: int
    avatar_url: Optional[str] = None
    preferred_difficulty: str
    created_at: datetime

    @computed_field
    @property
    def display_name(self) -> str:
        """Generate display name from first and last name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email.split("@")[0]

    model_config = {"from_attributes": True}


class UserProfile(UserResponse):
    """Extended user profile with game statistics."""
    games_played: int = 0
    games_won: int = 0
    total_moves: int = 0
    average_moves_per_game: float = 0.0
    win_rate: float = 0.0

    model_config = {"from_attributes": True}
