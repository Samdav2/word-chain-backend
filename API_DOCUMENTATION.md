# Word Chain API - Authentication & Leaderboard Reference

> **Base URL**: `https://your-api-domain.com/api/v1` (or as configured)

---

## Authentication Endpoints

### POST `/auth/signup`
Register a new user.

**Request Body:**
```json
{
  "email": "student@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "minimum6chars",
  "matric_no": "2020/001"  // Optional
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "student@example.com",
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
username=student@example.com
password=minimum6chars
```

**Response (200):**
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
Request password reset email.

**Request:**
```json
{
  "email": "student@example.com"
}
```

**Response (200):**
```json
{
  "message": "If an account with that email exists, a password reset link has been sent.",
  "success": true
}
```

---

### POST `/auth/password-reset/confirm`
Reset password with token.

**Request:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "newpassword123"
}
```

**Response (200):**
```json
{
  "message": "Password has been reset successfully.",
  "success": true
}
```

---

### POST `/auth/change-password`
Change password (authenticated).

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
Verify email with token.

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
  "email": "student@example.com"
}
```

---

## Leaderboard Endpoints

> All leaderboard endpoints require authentication.

### GET `/leaderboard`
Full leaderboard with pagination.

**Query Params:**
- `limit` (1-100, default: 50)
- `offset` (default: 0)

**Response:**
```json
{
  "entries": [
    {
      "rank": 1,
      "user_id": "uuid",
      "display_name": "John Doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "total_xp": 1500,
      "games_won": 25,
      "total_games": 30,
      "win_rate": 0.83,
      "average_moves": 4.2,
      "tier": "gold",
      "tier_badge": "🥇"
    }
  ],
  "total_players": 150,
  "user_rank": 42
}
```

---

### GET `/leaderboard/top`
Top 10 players (quick view for dashboard).

---

### GET `/leaderboard/me`
Current user's detailed ranking.

**Response:**
```json
{
  "rank": 42,
  "total_players": 150,
  "display_name": "John Doe",
  "total_xp": 1500,
  "tier": "gold",
  "tier_badge": "🥇",
  "games_won": 25,
  "total_games": 30,
  "win_rate": 0.83,
  "xp_to_next_tier": 2000,
  "next_tier": "platinum",
  "percentile": 72.0
}
```

---

### GET `/leaderboard/nearby`
Players near your rank (±5).

**Query Params:** `range_size` (1-10, default: 5)

---

### GET `/leaderboard/tiers`
All tier information.

**Response:**
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

## Tier System

| Tier | Badge | XP Required |
|------|-------|-------------|
| Bronze | 🥉 | 0 |
| Silver | 🥈 | 500 |
| Gold | 🥇 | 1,500 |
| Platinum | 💎 | 3,500 |
| Diamond | 👑 | 7,500 |

---

## Error Responses

```json
{
  "detail": "Error message here"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing token) |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |

---

## Authentication Header

```
Authorization: Bearer <access_token>
```
