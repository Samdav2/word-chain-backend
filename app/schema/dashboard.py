"""Dashboard schemas."""

import uuid
from typing import Optional
from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    # Level & XP
    level: int
    current_xp: int
    xp_to_next_level: int
    total_xp: int

    # Streak
    current_win_streak: int
    best_win_streak: int

    # Words
    words_mastered: int  # Unique words successfully used

    # Ranking
    global_rank: int
    rank_percentile: str  # e.g., "Top 5%"
    total_players: int

    model_config = {"from_attributes": True}
