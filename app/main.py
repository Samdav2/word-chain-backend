"""
EdTech Word Chain Game Backend

A FastAPI-based backend for an educational word chain game using the SAM model.
Features real-time game logic with NetworkX graph-based word validation,
JWT authentication, and detailed learning analytics.

Production-ready with:
- GZip compression for smaller responses
- ORJSONResponse for faster JSON serialization (if orjson installed)
- Connection pooling for high concurrency
- Comprehensive security headers
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.security_middleware import limiter, SecurityHeadersMiddleware
from app.service.word_graph import initialize_word_graph
from app.db.database import create_tables, get_database_info
from app.api import auth_router, users_router, game_router, stats_router, dashboard_router, missions_router, leaderboard_router

# Try to use ORJSONResponse for faster serialization, fallback to JSONResponse
try:
    from fastapi.responses import ORJSONResponse
    DefaultResponseClass = ORJSONResponse
    print("✅ Using ORJSONResponse (fast JSON)")
except (ImportError, AssertionError):
    DefaultResponseClass = JSONResponse
    print("ℹ️  Using JSONResponse (install orjson for faster performance)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Runs on startup:
    - Initialize the word graph (load dictionary)
    - Create database tables

    Runs on shutdown:
    - Cleanup resources
    """
    # Startup
    print("🚀 Starting EdTech Word Chain API...")
    print(f"   Environment: {settings.environment}")

    # Database info
    db_info = get_database_info()
    print(f"   Database: {db_info['type'].upper()}")
    if db_info['pool_size']:
        print(f"   Pool Size: {db_info['pool_size']} (max overflow: {db_info['max_overflow']})")

    # Initialize the word graph
    word_count = initialize_word_graph()
    print(f"📚 Loaded {word_count} words into the graph")

    # Create database tables (for development - use Alembic in production)
    try:
        await create_tables()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️ Database error (ensure PostgreSQL is running): {e}")

    yield

    # Shutdown
    print("👋 Shutting down EdTech Word Chain API...")


# Create FastAPI application with faster JSON response
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## EdTech Word Chain Game API

An educational word chain game backend built for LASU students, using the
**SAM (Successive Approximation Model)** for learning analytics.

### Features

🎮 **Game Engine**
- Graph-based word validation using NetworkX
- BFS algorithm for AI-powered hints
- Real-time path validation

📊 **Learning Analytics**
- SAM phase tracking (Evaluate, Design, Develop)
- Error analysis and metacognitive data
- Time-on-task metrics

🏆 **Gamification**
- XP-based progression system
- Student leaderboards
- Achievement tracking

### How to Play

1. **Start a game** - You'll get a start word and target word
2. **Make moves** - Change one letter at a time to form valid words
3. **Reach the target** - Complete the chain to win!

Example: CAT → BAT → BAG → BAD → BID → AID

### Authentication

Use the `/auth/signup` and `/auth/login` endpoints to get a JWT token.
Click the "Authorize" button above and enter: `Bearer <your_token>`

### Rate Limits

- **Authentication**: 10 requests/minute (login), 5/minute (signup)
- **Game Operations**: 100 requests/minute
- **API General**: 100 requests/minute

### Database Support

This API supports both SQLite (development) and PostgreSQL (production).
Set the `DATABASE_URL` environment variable to switch between them.
    """,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration and login endpoints"
        },
        {
            "name": "Users",
            "description": "User profile management"
        },
        {
            "name": "Dashboard",
            "description": "Dashboard statistics and user progress"
        },
        {
            "name": "Missions",
            "description": "Daily missions and rewards"
        },
        {
            "name": "Game",
            "description": "Word chain game operations"
        },
        {
            "name": "Statistics",
            "description": "Personal analytics and leaderboards"
        },
        {
            "name": "Leaderboard",
            "description": "Global rankings and tier information"
        },
        {
            "name": "Health",
            "description": "System health and status checks"
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    default_response_class=DefaultResponseClass,  # ORJSONResponse if available, else JSONResponse
    contact={
        "name": "EdTech Word Chain Support",
        "email": "support@wordchain.edu"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add GZip compression middleware (compress responses > 1KB)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(dashboard_router)
app.include_router(missions_router)
app.include_router(game_router)
app.include_router(stats_router)
app.include_router(leaderboard_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "message": "Welcome to the EdTech Word Chain Game API! Visit /docs for interactive documentation."
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns system health status including:
    - Overall status
    - Word graph statistics
    - Database configuration info
    """
    from app.service.word_graph import get_word_graph

    graph = get_word_graph()
    stats = graph.get_stats()
    db_info = get_database_info()

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "word_graph": {
            "loaded": stats["total_words"] > 0,
            "word_count": stats["total_words"],
            "edge_count": stats["total_edges"]
        },
        "database": {
            "type": db_info["type"],
            "production_ready": db_info["is_production_ready"],
            "pool_size": db_info["pool_size"]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers
    )
