import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, computed_field


class ErrorBreakdown(BaseModel):
    """Breakdown of error types."""
    not_in_dictionary: int = 0
    not_one_letter: int = 0
    same_word: int = 0
    wrong_length: int = 0
    already_used: int = 0


class SAMScores(BaseModel):
    """SAM (Successive Approximation Model) phase scores."""
    evaluation_score: float = 0.0  # How often user catches invalid words
    design_score: float = 0.0      # Path efficiency (optimal vs actual moves)
    develop_score: float = 0.0     # Success rate


class TimeMetrics(BaseModel):
    """Time-on-task metrics."""
    average_thinking_time_ms: float = 0.0
    total_session_time_seconds: float = 0.0


class PersonalStats(BaseModel):
    """Complete personal statistics."""
    user_id: uuid.UUID
    total_games: int = 0
    games_won: int = 0
    games_lost: int = 0
    win_rate: float = 0.0
    total_moves: int = 0
    average_moves_per_game: float = 0.0
    total_hints_used: int = 0
    total_xp: int = 0
    current_streak: int = 0
    best_streak: int = 0
    error_breakdown: ErrorBreakdown = ErrorBreakdown()
    sam_scores: SAMScores = SAMScores()
    time_metrics: TimeMetrics = TimeMetrics()
    recent_games: List["GameSummary"] = []

    model_config = {"from_attributes": True}


class GameSummary(BaseModel):
    """Summary of a single game for stats."""
    session_id: uuid.UUID
    date: datetime
    start_word: str
    target_word: str
    moves: int
    is_won: bool
    score: int


# ============= Enhanced Leaderboard Schemas =============

class PlayerTier(str, Enum):
    """Player tier based on XP."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


TIER_THRESHOLDS = {
    PlayerTier.BRONZE: 0,
    PlayerTier.SILVER: 500,
    PlayerTier.GOLD: 1500,
    PlayerTier.PLATINUM: 3500,
    PlayerTier.DIAMOND: 7500
}

TIER_BADGES = {
    PlayerTier.BRONZE: "🥉",
    PlayerTier.SILVER: "🥈",
    PlayerTier.GOLD: "🥇",
    PlayerTier.PLATINUM: "💎",
    PlayerTier.DIAMOND: "👑"
}


def get_tier_from_xp(xp: int) -> PlayerTier:
    """Calculate player tier from XP."""
    if xp >= TIER_THRESHOLDS[PlayerTier.DIAMOND]:
        return PlayerTier.DIAMOND
    elif xp >= TIER_THRESHOLDS[PlayerTier.PLATINUM]:
        return PlayerTier.PLATINUM
    elif xp >= TIER_THRESHOLDS[PlayerTier.GOLD]:
        return PlayerTier.GOLD
    elif xp >= TIER_THRESHOLDS[PlayerTier.SILVER]:
        return PlayerTier.SILVER
    else:
        return PlayerTier.BRONZE


class TierInfo(BaseModel):
    """Information about a tier."""
    tier: PlayerTier
    name: str
    badge: str
    min_xp: int
    max_xp: Optional[int] = None


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""
    rank: int
    user_id: uuid.UUID
    display_name: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    matric_no: Optional[str] = None
    total_xp: int
    games_won: int
    total_games: int = 0
    win_rate: float
    average_moves: float

    @computed_field
    @property
    def tier(self) -> PlayerTier:
        return get_tier_from_xp(self.total_xp)

    @computed_field
    @property
    def tier_badge(self) -> str:
        return TIER_BADGES[self.tier]

    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    """Full leaderboard response."""
    entries: List[LeaderboardEntry]
    total_players: int
    user_rank: Optional[int] = None  # Current user's rank if logged in

    model_config = {"from_attributes": True}


class UserRankDetails(BaseModel):
    """Detailed ranking information for a user."""
    rank: int
    total_players: int
    display_name: str
    total_xp: int
    tier: PlayerTier
    tier_badge: str
    games_won: int
    total_games: int
    win_rate: float
    xp_to_next_tier: int
    next_tier: Optional[PlayerTier] = None
    percentile: float  # Top X% of players

    model_config = {"from_attributes": True}


class AnalyticsEventResponse(BaseModel):
    """Single analytics event."""
    id: uuid.UUID
    event_type: str
    input_word: Optional[str] = None
    is_valid: bool
    error_reason: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
