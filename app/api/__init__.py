# API exports
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.game import router as game_router
from app.api.stats import router as stats_router
from app.api.dashboard import router as dashboard_router
from app.api.missions import router as missions_router
from app.api.leaderboard import router as leaderboard_router

__all__ = [
    "auth_router",
    "users_router",
    "game_router",
    "stats_router",
    "dashboard_router",
    "missions_router",
    "leaderboard_router"
]
