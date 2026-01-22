"""
Security middleware for rate limiting and security headers.

Provides protection against brute force attacks and adds comprehensive security headers.
Optimized for game workloads with higher rate limits for gameplay endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from typing import Callable


# Initialize rate limiter with client IP as key
limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again later.",
            "retry_after": exc.detail
        }
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add comprehensive security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000
    - Content-Security-Policy: Configured for API use
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: Disable unnecessary features
    - Cache-Control: Security-oriented caching
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS - enforce HTTPS (only affects production with HTTPS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (disable unnecessary features)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"

        # Content Security Policy for API (restrictive since we're an API, not serving HTML)
        # Allow 'self' for API docs (Swagger UI)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # Cache control for security (prevent caching of sensitive data)
        if "/auth/" in str(request.url) or "/users/me" in str(request.url):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


# Rate limit configurations for different endpoints
# Optimized for game workloads: higher limits for gameplay, stricter for auth
RATE_LIMITS = {
    "auth": {
        "login": "10/minute",           # Prevent brute force
        "signup": "5/minute",           # Prevent spam accounts
        "password_reset": "3/minute",   # Prevent email spam
        "verify_email": "10/minute",
        "change_password": "5/minute",
    },
    "game": {
        "start": "30/minute",           # Game starts per minute
        "move": "120/minute",           # Moves are frequent during gameplay
        "hint": "30/minute",            # Limit hint usage
        "history": "60/minute",
    },
    "stats": {
        "personal": "60/minute",
        "leaderboard": "60/minute",
    },
    "dashboard": {
        "stats": "60/minute",
    },
    "default": "100/minute"  # General API rate limit
}


def get_rate_limit_string(endpoint_type: str, action: str) -> str:
    """Get the rate limit string for a specific endpoint."""
    if endpoint_type in RATE_LIMITS and action in RATE_LIMITS[endpoint_type]:
        return RATE_LIMITS[endpoint_type][action]
    return RATE_LIMITS["default"]


def get_game_rate_limit(action: str) -> str:
    """Get rate limit for game endpoints."""
    return get_rate_limit_string("game", action)


def get_auth_rate_limit(action: str) -> str:
    """Get rate limit for auth endpoints."""
    return get_rate_limit_string("auth", action)
