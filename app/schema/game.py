import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.model.game_session import GameMode, WordCategory


class GameStartRequest(BaseModel):
    """Request to start a new game."""
    mode: GameMode = GameMode.STANDARD
    category: WordCategory = WordCategory.MIXED
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="Difficulty level 1-5")


class GameStartResponse(BaseModel):
    """Response when starting a new game."""
    session_id: uuid.UUID
    start_word: str
    target_word: str
    mode: GameMode
    category: WordCategory
    difficulty_level: int
    message: str = "Game started! Transform the start word to the target word."

    model_config = {"from_attributes": True}


class MoveValidateRequest(BaseModel):
    """Request to validate a word move."""
    session_id: uuid.UUID
    current_word: str = Field(..., min_length=3, max_length=20)
    next_word: str = Field(..., min_length=3, max_length=20)
    thinking_time_ms: Optional[int] = None  # Time spent thinking before move


class MoveValidateResponse(BaseModel):
    """Response after validating a move."""
    valid: bool
    score_delta: int = 0
    reason: Optional[str] = None
    distance_remaining: Optional[int] = None
    current_word: str
    target_word: str
    total_score: int = 0
    moves_count: int = 0
    is_complete: bool = False
    message: str
    # Educational enhancements
    word_definition: Optional[str] = None
    learning_tip: Optional[str] = None
    word_difficulty: Optional[int] = None

    model_config = {"from_attributes": True}


class HintRequest(BaseModel):
    """Request for a hint."""
    session_id: uuid.UUID


class HintResponse(BaseModel):
    """Response with next word suggestion."""
    hint_word: str
    hint_cost: int  # XP penalty for using hint
    message: str
    hints_used: int
    hints_remaining: int  # Hints left based on difficulty
    max_hints_allowed: int  # Max hints for this difficulty level
    learning_tip: Optional[str] = None

    model_config = {"from_attributes": True}


class GameCompleteRequest(BaseModel):
    """Request to complete/forfeit a game."""
    session_id: uuid.UUID
    forfeit: bool = False


class GameCompleteResponse(BaseModel):
    """Response when game is completed."""
    session_id: uuid.UUID
    is_won: bool
    total_score: int
    moves_count: int
    hints_used: int
    xp_earned: int
    message: str
    path_taken: List[str] = []  # Words used in the chain
    optimal_path_length: int = 0
    category: Optional[WordCategory] = None
    difficulty_level: Optional[int] = None
    # Learning summary
    learning_summary: Optional[str] = None

    model_config = {"from_attributes": True}


class GameSessionResponse(BaseModel):
    """Game session summary for history."""
    id: uuid.UUID
    mode: GameMode
    category: WordCategory
    difficulty_level: int
    start_time: datetime
    end_time: Optional[datetime] = None
    target_word_start: str
    target_word_end: str
    moves_count: int
    hints_used: int
    is_completed: bool
    is_won: bool
    total_score: int
    xp_earned: int = 0  # XP earned from this game

    model_config = {"from_attributes": True}


# New educational schemas

class CategoryInfo(BaseModel):
    """Information about a word category."""
    name: str
    description: str
    word_count: int
    sample_words: List[str] = []


class CategoriesResponse(BaseModel):
    """Response listing all available categories."""
    categories: List[CategoryInfo]
    total_words: int


class WordInfo(BaseModel):
    """Detailed information about a word."""
    word: str
    category: Optional[str] = None
    difficulty: int
    definition: Optional[str] = None
    pronunciation: Optional[str] = None
    part_of_speech: Optional[str] = None
    examples: List[str] = []
    etymology: Optional[str] = None
    learning_tip: Optional[str] = None
    neighbors: List[str] = []
