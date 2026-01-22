"""Missions service for daily mission tracking."""

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.model.game_session import GameSession
from app.model.analytics_event import AnalyticsEvent, EventType
from app.schema.mission import MissionProgress, MissionReward, DailyMissionsResponse


# Predefined mission templates
DAILY_MISSIONS = [
    {
        "id": "word_warrior",
        "title": "Word Warrior",
        "description": "Win 3 word chain games",
        "max_progress": 3,
        "reward": MissionReward(type="xp", amount=150),
        "query_type": "games_won"
    },
    {
        "id": "speed_demon",
        "title": "Speed Demon",
        "description": "Complete a game in under 10 moves",
        "max_progress": 1,
        "reward": MissionReward(type="xp", amount=100),
        "query_type": "fast_game"
    },
    {
        "id": "vocabulary_builder",
        "title": "Vocabulary Builder",
        "description": "Use 20 unique words across games",
        "max_progress": 20,
        "reward": MissionReward(type="xp", amount=200),
        "query_type": "unique_words"
    },
    {
        "id": "hint_free",
        "title": "No Hints Master",
        "description": "Win a game without using any hints",
        "max_progress": 1,
        "reward": MissionReward(type="xp", amount=75),
        "query_type": "hint_free_win"
    },
    {
        "id": "persistent",
        "title": "Persistent Player",
        "description": "Play 5 games today",
        "max_progress": 5,
        "reward": MissionReward(type="xp", amount=100),
        "query_type": "games_played"
    }
]


def get_today_start() -> datetime:
    """Get the start of today in UTC."""
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def get_tomorrow_start() -> datetime:
    """Get the start of tomorrow in UTC (mission reset time)."""
    return get_today_start() + timedelta(days=1)


async def get_daily_missions(db: AsyncSession, user_id: uuid.UUID) -> DailyMissionsResponse:
    """Get daily missions with current progress."""

    today_start = get_today_start()
    tomorrow_start = get_tomorrow_start()

    # Get today's game sessions for this user
    sessions_result = await db.execute(
        select(GameSession)
        .where(GameSession.user_id == user_id)
        .where(GameSession.start_time >= today_start)
        .where(GameSession.start_time < tomorrow_start)
    )
    today_sessions = list(sessions_result.scalars().all())

    # Count metrics
    games_played = len(today_sessions)
    games_won = len([s for s in today_sessions if s.is_won])
    fast_games = len([s for s in today_sessions if s.is_won and s.moves_count < 10])
    hint_free_wins = len([s for s in today_sessions if s.is_won and s.hints_used == 0])

    # Count unique words used today
    words_result = await db.execute(
        select(func.count(func.distinct(AnalyticsEvent.input_word)))
        .join(GameSession, AnalyticsEvent.session_id == GameSession.id)
        .where(GameSession.user_id == user_id)
        .where(GameSession.start_time >= today_start)
        .where(GameSession.start_time < tomorrow_start)
        .where(AnalyticsEvent.event_type == EventType.MOVE_VALID)
        .where(AnalyticsEvent.input_word.isnot(None))
    )
    unique_words = words_result.scalar() or 0

    # Build mission progress
    missions = []
    for mission in DAILY_MISSIONS:
        if mission["query_type"] == "games_won":
            progress = min(games_won, mission["max_progress"])
        elif mission["query_type"] == "fast_game":
            progress = min(fast_games, mission["max_progress"])
        elif mission["query_type"] == "unique_words":
            progress = min(unique_words, mission["max_progress"])
        elif mission["query_type"] == "hint_free_win":
            progress = min(hint_free_wins, mission["max_progress"])
        elif mission["query_type"] == "games_played":
            progress = min(games_played, mission["max_progress"])
        else:
            progress = 0

        missions.append(MissionProgress(
            id=mission["id"],
            title=mission["title"],
            description=mission["description"],
            progress=progress,
            max_progress=mission["max_progress"],
            reward=mission["reward"],
            completed=progress >= mission["max_progress"]
        ))

    completed_count = len([m for m in missions if m.completed])

    return DailyMissionsResponse(
        missions=missions,
        completed_count=completed_count,
        total_count=len(missions),
        reset_time=tomorrow_start.isoformat()
    )
