# Repository exports
from app.repo.user import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    get_user_by_matric,
    update_user_xp,
    update_user_profile,
    update_user_password,
    get_all_users,
    get_total_users_count
)
from app.repo.game_session import (
    create_game_session,
    get_game_session,
    get_user_active_session,
    update_game_session,
    complete_game_session,
    get_user_sessions,
    get_user_game_stats
)
from app.repo.analytics import (
    log_event,
    get_session_events,
    get_session_words_used,
    get_user_error_breakdown,
    get_average_thinking_time,
    get_leaderboard_data
)

__all__ = [
    # User repo
    "create_user",
    "get_user_by_id",
    "get_user_by_email",
    "get_user_by_matric",
    "update_user_xp",
    "update_user_profile",
    "update_user_password",
    "get_all_users",
    "get_total_users_count",
    # Game session repo
    "create_game_session",
    "get_game_session",
    "get_user_active_session",
    "update_game_session",
    "complete_game_session",
    "get_user_sessions",
    "get_user_game_stats",
    # Analytics repo
    "log_event",
    "get_session_events",
    "get_session_words_used",
    "get_user_error_breakdown",
    "get_average_thinking_time",
    "get_leaderboard_data"
]
