# EdTech Word Chain Game Backend

An educational word chain game backend built with FastAPI for LASU students, using the **SAM (Successive Approximation Model)** for learning analytics.

## 🎮 Features

- **Graph-based Word Validation** - NetworkX-powered word chain mechanics with BFS pathfinding
- **AI-Powered Hints** - Breadth-First Search algorithm suggests optimal next moves
- **Learning Analytics** - SAM phase tracking (Evaluate, Design, Develop)
- **Gamification** - XP system and student leaderboards
- **JWT Authentication** - Secure token-based authentication
- **Swagger Documentation** - Interactive API docs at `/docs`

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (or modify for SQLite)
- Redis (optional, for caching)

### Installation

```bash
# Clone and enter directory
cd est_415_game_backend

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials
```

### Database Setup

```bash
# Create PostgreSQL database
createdb wordchain_db

# Or use psql
psql -c "CREATE DATABASE wordchain_db;"
```

### Run the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📚 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/signup` | POST | Register new user |
| `/auth/login` | POST | Get JWT token |

### Game
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/game/start` | POST | Start new game |
| `/game/validate` | POST | Validate word move |
| `/game/hint` | POST | Get AI-powered hint |
| `/game/complete` | POST | Complete/forfeit game |
| `/game/history` | GET | Get game history |

### Statistics
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats/personal` | GET | Personal analytics |
| `/stats/leaderboard` | GET | Top students |

### Users
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/me` | GET | Get profile |
| `/users/me` | PUT | Update profile |
| `/users/me/password` | PUT | Change password |

## 🎯 How to Play

1. **Start a game** - Call `/game/start` to get a start word and target word
2. **Make moves** - Call `/game/validate` changing one letter at a time
3. **Get hints** - Call `/game/hint` if stuck (costs XP)
4. **Win!** - Reach the target word to complete the chain

**Example Chain:** CAT → BAT → BAG → BAD → BID → AID

## 🧪 Testing

```bash
# Run unit tests for word graph engine
pytest app/tests/test_word_graph.py -v

# Run all tests
pytest -v
```

## 📁 Project Structure

```
est_415_game_backend/
├── app/
│   ├── api/           # API route handlers
│   ├── core/          # Config & security
│   ├── db/            # Database setup
│   ├── dependencies/  # FastAPI dependencies
│   ├── model/         # SQLAlchemy models
│   ├── repo/          # Database operations
│   ├── schema/        # Pydantic schemas
│   ├── service/       # Business logic
│   ├── tests/         # Test files
│   └── main.py        # FastAPI app
├── data/              # Word dictionaries
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Technology Stack

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Graph Engine | NetworkX |
| Authentication | JWT (python-jose) |
| Password Hashing | Bcrypt |

## 📊 SAM (Successive Approximation Model)

The game tracks learning through three phases:

1. **Evaluation** - How effectively users validate their moves
2. **Design** - Path efficiency (optimal vs actual moves)
3. **Develop** - Success rate in completing games

## 📝 License

Educational project for EST 415 - LASU
# word-chain-backend
