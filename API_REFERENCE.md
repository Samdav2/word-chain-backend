# EdTech Word Chain API Reference

> **Version**: 1.0.0 | **Base URL**: `/api/v1` (or as configured)

This API provides endpoints for an educational word chain game designed for LASU students. The game uses the SAM (Successive Approximation Model) for learning analytics.

---

## Quick Links

- **Interactive Docs**: [Swagger UI](/docs)
- **ReDoc**: [/redoc](/redoc)
- **OpenAPI Schema**: [/openapi.json](/openapi.json)

---

## Contents

1. [Authentication](#authentication)
2. [Game Operations](#game-operations)
3. [Dashboard & Missions](#dashboard--missions)
4. [Statistics & Analytics](#statistics--analytics)
5. [Leaderboard](#leaderboard)
6. [System Endpoints](#system-endpoints)
7. [Error Handling](#error-handling)
8. [Rate Limits](#rate-limits)

---

## Authentication

All endpoints except public ones require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### POST `/auth/signup`
Register a new user account.

**Request Body:**
```json
{
  "email": "student@lasu.edu.ng",
  "first_name": "John",
  "last_name": "Doe",
  "password": "minimum6chars",
  "matric_no": "2020/001"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | ✅ | Valid email address |
| first_name | string | ✅ | User's first name |
| last_name | string | ✅ | User's last name |
| password | string | ✅ | Minimum 6 characters |
| matric_no | string | ❌ | LASU matriculation number |

**Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "student@lasu.edu.ng",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "matric_no": "2020/001",
  "role": "student",
  "current_xp": 0,
  "preferred_difficulty": "novice",
  "created_at": "2026-01-21T12:00:00Z"
}
```

---

### POST `/auth/login`
Authenticate and receive JWT tokens.

**Request Body (form-data):**
```
username=student@lasu.edu.ng
password=minimum6chars
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "refresh_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "first_name": "John"
}
```

---

### POST `/auth/password-reset/request`
Request a password reset email.

**Request:**
```json
{
  "email": "student@lasu.edu.ng"
}
```

**Response (200 OK):**
```json
{
  "message": "If an account with that email exists, a password reset link has been sent.",
  "success": true
}
```

---

### POST `/auth/password-reset/confirm`
Reset password using the token from email.

**Request:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "newpassword123"
}
```

---

### POST `/auth/change-password`
Change password (requires authentication).

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

---

### POST `/auth/verify-email`
Verify email with token from verification email.

**Request:**
```json
{
  "token": "verification-token-from-email"
}
```

---

### POST `/auth/resend-verification`
Resend verification email.

**Request:**
```json
{
  "email": "student@lasu.edu.ng"
}
```

---

## Game Operations

All game endpoints require authentication.

### GET `/game/active`
Check if user has an active game session.

**Response (200 OK):**
```json
{
  "has_active_game": true,
  "session": {
    "session_id": "uuid",
    "start_word": "cat",
    "target_word": "dog",
    "current_word": "bat",
    "moves_made": 1,
    "hints_used": 0,
    "status": "active",
    "started_at": "2026-01-21T12:00:00Z"
  }
}
```

---

### POST `/game/start`
Start a new word chain game.

**Request:**
```json
{
  "mode": "standard",
  "category": "general",
  "difficulty": "novice"
}
```

| Field | Type | Options | Description |
|-------|------|---------|-------------|
| mode | string | `standard`, `edtech_only` | Game mode |
| category | string | `general`, `science`, `biology`, `physics`, `education`, `mixed` | Word category |
| difficulty | string | `novice`, `intermediate`, `expert`, `master` | Difficulty level |

**Response (201 Created):**
```json
{
  "session_id": "uuid",
  "start_word": "cat",
  "target_word": "dog",
  "optimal_moves": 3,
  "mode": "standard",
  "category": "general",
  "difficulty": "novice",
  "hints_available": 3,
  "time_limit_seconds": null
}
```

---

### POST `/game/move`
Validate and make a move.

**Request:**
```json
{
  "session_id": "uuid",
  "current_word": "cat",
  "next_word": "bat",
  "thinking_time_ms": 5000
}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "is_target": false,
  "moves_remaining_to_target": 2,
  "xp_earned": 10,
  "message": "Good move! 'bat' is a valid word."
}
```

**Error Response (400 Bad Request):**
```json
{
  "valid": false,
  "is_target": false,
  "error_type": "INVALID_WORD",
  "message": "'xyz' is not a valid dictionary word"
}
```

---

### POST `/game/hint`
Get a hint for the current game (costs XP).

**Request:**
```json
{
  "session_id": "uuid"
}
```

**Response (200 OK):**
```json
{
  "hint_word": "bat",
  "hints_remaining": 2,
  "xp_deducted": 5,
  "message": "Try changing 'c' to 'b' to make 'bat'"
}
```

---

### POST `/game/complete`
Complete or forfeit the current game.

**Request:**
```json
{
  "session_id": "uuid",
  "forfeit": false
}
```

**Response (200 OK):**
```json
{
  "result": "won",
  "total_moves": 5,
  "optimal_moves": 3,
  "xp_earned": 45,
  "time_taken_seconds": 120,
  "stats": {
    "efficiency": 0.6,
    "sam_scores": {...}
  }
}
```

---

### GET `/game/history`
Get the user's past game sessions.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| skip | int | 0 | Offset for pagination |
| limit | int | 20 | Number of results |

**Response (200 OK):**
```json
[
  {
    "session_id": "uuid",
    "start_word": "cat",
    "target_word": "dog",
    "result": "won",
    "moves_made": 5,
    "xp_earned": 45,
    "completed_at": "2026-01-21T12:05:00Z"
  }
]
```

---

### GET `/game/categories`
Get available word categories.

**Response (200 OK):**
```json
{
  "categories": [
    {
      "name": "science",
      "description": "Scientific terminology",
      "word_count": 2500,
      "sample_words": ["atom", "cell", "wave"]
    }
  ]
}
```

---

### GET `/game/word/{word}`
Get detailed information about a word.

**Response (200 OK):**
```json
{
  "word": "atom",
  "category": "science",
  "difficulty": 2,
  "definition": "The smallest unit of matter...",
  "learning_tip": "Root word from Greek 'atomos' meaning indivisible",
  "valid_next_moves": ["atop", "atom"]
}
```

---

## Dashboard & Missions

### GET `/dashboard/stats`
Get dashboard statistics.

**Response (200 OK):**
```json
{
  "current_xp": 1500,
  "current_tier": "gold",
  "tier_badge": "🥇",
  "games_played": 30,
  "games_won": 25,
  "win_rate": 0.83,
  "current_streak": 5,
  "xp_to_next_tier": 500
}
```

---

### GET `/missions/daily`
Get daily missions.

**Response (200 OK):**
```json
{
  "missions": [
    {
      "id": "play_3_games",
      "title": "Play 3 Games",
      "description": "Complete 3 word chain games",
      "progress": 1,
      "target": 3,
      "xp_reward": 50,
      "completed": false
    }
  ],
  "resets_at": "2026-01-22T00:00:00Z"
}
```

---

## Statistics & Analytics

### GET `/stats/personal`
Get comprehensive personal statistics.

**Response (200 OK):**
```json
{
  "total_games": 30,
  "games_won": 25,
  "games_lost": 5,
  "win_rate": 0.83,
  "total_xp": 1500,
  "average_moves": 4.2,
  "sam_scores": {
    "evaluate": 0.85,
    "design": 0.78,
    "develop": 0.92
  },
  "error_breakdown": {
    "INVALID_WORD": 5,
    "MULTIPLE_CHANGES": 3,
    "SAME_WORD": 1
  },
  "recent_games": [...]
}
```

---

### GET `/stats/leaderboard`
Get student leaderboard.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 10 | Number of top players |

**Response (200 OK):**
```json
{
  "entries": [
    {
      "rank": 1,
      "user_id": "uuid",
      "display_name": "John Doe",
      "total_xp": 5000,
      "tier": "diamond",
      "tier_badge": "👑",
      "games_won": 100
    }
  ],
  "total_players": 150,
  "user_rank": 42
}
```

---

## Leaderboard

### GET `/leaderboard`
Full leaderboard with pagination.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 50 | Max 100 |
| offset | int | 0 | Pagination offset |

---

### GET `/leaderboard/top`
Get top 10 players (quick view).

---

### GET `/leaderboard/me`
Get current user's detailed ranking.

**Response (200 OK):**
```json
{
  "rank": 42,
  "total_players": 150,
  "display_name": "John Doe",
  "total_xp": 1500,
  "tier": "gold",
  "tier_badge": "🥇",
  "xp_to_next_tier": 500,
  "next_tier": "platinum",
  "percentile": 72.0
}
```

---

### GET `/leaderboard/nearby`
Get players near your rank (±5 by default).

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| range_size | int | 5 | Range (1-10) |

---

### GET `/leaderboard/tiers`
Get all tier information.

**Response (200 OK):**
```json
[
  {"tier": "bronze", "name": "Bronze", "badge": "🥉", "min_xp": 0, "max_xp": 499},
  {"tier": "silver", "name": "Silver", "badge": "🥈", "min_xp": 500, "max_xp": 1499},
  {"tier": "gold", "name": "Gold", "badge": "🥇", "min_xp": 1500, "max_xp": 3499},
  {"tier": "platinum", "name": "Platinum", "badge": "💎", "min_xp": 3500, "max_xp": 7499},
  {"tier": "diamond", "name": "Diamond", "badge": "👑", "min_xp": 7500, "max_xp": null}
]
```

---

## System Endpoints

### GET `/`
Root endpoint with API info.

**Response (200 OK):**
```json
{
  "name": "EdTech Word Chain API",
  "version": "1.0.0",
  "environment": "production",
  "docs": "/docs",
  "redoc": "/redoc",
  "openapi": "/openapi.json"
}
```

---

### GET `/health`
Health check endpoint for monitoring and load balancers.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "word_graph": {
    "loaded": true,
    "word_count": 10500,
    "edge_count": 45000
  },
  "database": {
    "type": "postgresql",
    "production_ready": true,
    "pool_size": 20
  }
}
```

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

### Game Error Types

| Error Type | Description |
|------------|-------------|
| `INVALID_WORD` | Word not in dictionary |
| `MULTIPLE_CHANGES` | Changed more than one letter |
| `SAME_WORD` | Word is same as current |
| `NO_CHANGE` | No letters were changed |

---

## Rate Limits

Rate limits protect the API and are tracked per IP address.

### Authentication Endpoints
| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 10/minute |
| `/auth/signup` | 5/minute |
| `/auth/password-reset` | 3/minute |

### Game Endpoints
| Endpoint | Limit |
|----------|-------|
| `/game/start` | 30/minute |
| `/game/move` | 120/minute |
| `/game/hint` | 30/minute |

### General API
| Category | Limit |
|----------|-------|
| All other endpoints | 100/minute |

**Rate Limit Response (429):**
```json
{
  "detail": "Too many requests. Please try again later.",
  "retry_after": "60"
}
```

---

## Tier System

| Tier | Badge | XP Required |
|------|-------|-------------|
| Bronze | 🥉 | 0 |
| Silver | 🥈 | 500 |
| Gold | 🥇 | 1,500 |
| Platinum | 💎 | 3,500 |
| Diamond | 👑 | 7,500 |

---

## SDKs & Examples

### cURL Example
```bash
# Login
curl -X POST "https://api.yoursite.com/auth/login" \
  -d "username=student@lasu.edu.ng&password=yourpassword"

# Start a game
curl -X POST "https://api.yoursite.com/game/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode": "standard", "category": "general"}'
```

### JavaScript/TypeScript Example
```javascript
const response = await fetch('/game/start', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    mode: 'standard',
    category: 'science'
  })
});

const game = await response.json();
console.log(`Start: ${game.start_word} → Target: ${game.target_word}`);
```

---

## Database Configuration

The API supports both SQLite (development) and PostgreSQL (production).

### SQLite (Development)
```env
DATABASE_URL=sqlite+aiosqlite:///./data/wordchain.db
```

### PostgreSQL (Production)
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/wordchain_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

---

*Generated for EdTech Word Chain API v1.0.0*
