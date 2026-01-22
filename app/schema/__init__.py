# Schema exports
from app.schema.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserProfile
)
from app.schema.auth import Token, TokenPayload
from app.schema.game import (
    GameStartRequest,
    GameStartResponse,
    MoveValidateRequest,
    MoveValidateResponse,
    HintRequest,
    HintResponse,
    GameCompleteRequest,
    GameCompleteResponse,
    GameSessionResponse
)
from app.schema.analytics import (
    ErrorBreakdown,
    SAMScores,
    TimeMetrics,
    PersonalStats,
    GameSummary,
    LeaderboardEntry,
    LeaderboardResponse,
    AnalyticsEventResponse
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserProfile",
    # Auth schemas
    "Token",
    "TokenPayload",
    # Game schemas
    "GameStartRequest",
    "GameStartResponse",
    "MoveValidateRequest",
    "MoveValidateResponse",
    "HintRequest",
    "HintResponse",
    "GameCompleteRequest",
    "GameCompleteResponse",
    "GameSessionResponse",
    # Analytics schemas
    "ErrorBreakdown",
    "SAMScores",
    "TimeMetrics",
    "PersonalStats",
    "GameSummary",
    "LeaderboardEntry",
    "LeaderboardResponse",
    "AnalyticsEventResponse"
]
