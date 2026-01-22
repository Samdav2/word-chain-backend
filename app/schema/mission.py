"""Mission schemas."""

import uuid
from typing import List, Optional
from pydantic import BaseModel


class MissionReward(BaseModel):
    """Reward for completing a mission."""
    type: str  # "xp", "badge", etc.
    amount: int


class MissionProgress(BaseModel):
    """Progress on a single mission."""
    id: str
    title: str
    description: str
    progress: int
    max_progress: int
    reward: MissionReward
    completed: bool


class DailyMissionsResponse(BaseModel):
    """Response with daily missions."""
    missions: List[MissionProgress]
    completed_count: int
    total_count: int
    reset_time: str  # ISO timestamp for when missions reset
