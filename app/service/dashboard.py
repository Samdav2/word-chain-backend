"""Dashboard service for user dashboard statistics."""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.model.user import User
from app.model.game_session import GameSession
from app.model.analytics_event import AnalyticsEvent, EventType
from app.schema.dashboard import DashboardStats


# XP thresholds for each level (cumulative)
# Level 1: 0 XP, Level 2: 100 XP, Level 3: 250 XP, etc.
LEVEL_THRESHOLDS = [
    0,      # Level 1
    100,    # Level 2
    250,    # Level 3
    500,    # Level 4
    850,    # Level 5
    1300,   # Level 6
    1850,   # Level 7
    2500,   # Level 8
    3250,   # Level 9
    4100,   # Level 10
    5050,   # Level 11
    6100,   # Level 12
    7250,   # Level 13
    8500,   # Level 14
    9850,   # Level 15
    11300,  # Level 16
    12850,  # Level 17
    14500,  # Level 18
    16250,  # Level 19
    18100,  # Level 20
]


def calculate_level(total_xp: int) -> tuple[int, int, int]:
    """
    Calculate level from total XP.

    Returns:
        Tuple of (level, current_xp_in_level, xp_to_next_level)
    """
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if total_xp >= threshold:
            level = i + 1
        else:
            break

    # Cap at max level
    if level >= len(LEVEL_THRESHOLDS):
        level = len(LEVEL_THRESHOLDS)
        current_in_level = total_xp - LEVEL_THRESHOLDS[-1]
        xp_to_next = 2000  # Constant after max
    else:
        current_threshold = LEVEL_THRESHOLDS[level - 1]
        next_threshold = LEVEL_THRESHOLDS[level] if level < len(LEVEL_THRESHOLDS) else current_threshold + 2000
        current_in_level = total_xp - current_threshold
        xp_to_next = next_threshold - current_threshold

    return level, current_in_level, xp_to_next


async def get_dashboard_stats(db: AsyncSession, user_id: uuid.UUID) -> DashboardStats:
    """Get comprehensive dashboard statistics for a user."""

    # Get user
    user = await db.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    total_xp = user.current_xp
    level, current_xp, xp_to_next_level = calculate_level(total_xp)

    # Calculate win streak
    streak_result = await db.execute(
        select(GameSession)
        .where(GameSession.user_id == user_id)
        .where(GameSession.is_completed == True)
        .order_by(GameSession.end_time.desc())
        .limit(50)
    )
    sessions = list(streak_result.scalars().all())

    current_win_streak = 0
    best_win_streak = 0
    temp_streak = 0

    for session in sessions:
        if session.is_won:
            temp_streak += 1
            if current_win_streak == 0:
                current_win_streak = temp_streak
        else:
            if current_win_streak == 0:
                current_win_streak = temp_streak
            best_win_streak = max(best_win_streak, temp_streak)
            temp_streak = 0

    best_win_streak = max(best_win_streak, temp_streak)
    if current_win_streak == 0:
        current_win_streak = temp_streak

    # Count unique words mastered (valid moves made)
    words_result = await db.execute(
        select(func.count(func.distinct(AnalyticsEvent.input_word)))
        .join(GameSession, AnalyticsEvent.session_id == GameSession.id)
        .where(GameSession.user_id == user_id)
        .where(AnalyticsEvent.event_type == EventType.MOVE_VALID)
        .where(AnalyticsEvent.input_word.isnot(None))
    )
    words_mastered = words_result.scalar() or 0

    # Calculate global rank
    rank_result = await db.execute(
        select(func.count(User.id))
        .where(User.current_xp > total_xp)
    )
    users_ahead = rank_result.scalar() or 0
    global_rank = users_ahead + 1

    # Get total players
    total_result = await db.execute(select(func.count(User.id)))
    total_players = total_result.scalar() or 1

    # Calculate percentile
    if total_players > 0:
        percentile = ((total_players - global_rank) / total_players) * 100
        if percentile >= 99:
            rank_percentile = "Top 1%"
        elif percentile >= 95:
            rank_percentile = "Top 5%"
        elif percentile >= 90:
            rank_percentile = "Top 10%"
        elif percentile >= 75:
            rank_percentile = "Top 25%"
        elif percentile >= 50:
            rank_percentile = "Top 50%"
        else:
            rank_percentile = f"Top {100 - int(percentile)}%"
    else:
        rank_percentile = "Top 1%"

    return DashboardStats(
        level=level,
        current_xp=current_xp,
        xp_to_next_level=xp_to_next_level,
        total_xp=total_xp,
        current_win_streak=current_win_streak,
        best_win_streak=best_win_streak,
        words_mastered=words_mastered,
        global_rank=global_rank,
        rank_percentile=rank_percentile,
        total_players=total_players
    )
