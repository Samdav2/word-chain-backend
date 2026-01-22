"""
Integration tests for API endpoints.

Uses pytest-asyncio and httpx for async HTTP testing.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.db.database import Base, get_async_session
from app.dependencies.database import get_db

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create a test database and tables."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async def override_get_db():
        async with async_session() as session:
            yield session

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_async_session] = override_get_db

    yield async_session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(test_db):
    """Create a test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_token(client):
    """Create a test user and return auth token."""
    # Register a user
    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@lasu.edu.ng",
            "first_name": "Test",
            "last_name": "Student",
            "password": "testpassword123",
            "matric_no": "2020/001"
        }
    )
    assert response.status_code == 201

    # Login to get token
    response = await client.post(
        "/auth/login",
        data={
            "username": "test@lasu.edu.ng",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token_data = response.json()

    return token_data["access_token"]


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    async def test_signup_success(self, client):
        """Test successful user registration."""
        response = await client.post(
            "/auth/signup",
            json={
                "email": "newuser@lasu.edu.ng",
                "first_name": "Test",
                "last_name": "User",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@lasu.edu.ng"
        assert data["role"] == "student"
        assert "id" in data
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"

    async def test_signup_duplicate_email(self, client):
        """Test registration with duplicate email."""
        # First signup
        await client.post(
            "/auth/signup",
            json={"email": "dupe@test.com", "first_name": "Test", "last_name": "User", "password": "pass123"}
        )
        # Duplicate signup
        response = await client.post(
            "/auth/signup",
            json={"email": "dupe@test.com", "first_name": "Test", "last_name": "User", "password": "pass123"}
        )
        assert response.status_code == 400

    async def test_login_success(self, client):
        """Test successful login."""
        # Register first
        await client.post(
            "/auth/signup",
            json={"email": "login@test.com", "first_name": "Login", "last_name": "User", "password": "pass123"}
        )
        # Login
        response = await client.post(
            "/auth/login",
            data={"username": "login@test.com", "password": "pass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        # Register
        await client.post(
            "/auth/signup",
            json={"email": "wrong@test.com", "password": "correct"}
        )
        # Login with wrong password
        response = await client.post(
            "/auth/login",
            data={"username": "wrong@test.com", "password": "incorrect"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUserEndpoints:
    """Tests for user profile endpoints."""

    async def test_get_me_authenticated(self, client, auth_token):
        """Test getting current user profile."""
        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@lasu.edu.ng"
        assert "games_played" in data

    async def test_get_me_unauthenticated(self, client):
        """Test getting profile without auth."""
        response = await client.get("/users/me")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGameEndpoints:
    """Tests for game endpoints."""

    async def test_start_game(self, client, auth_token):
        """Test starting a new game."""
        response = await client.post(
            "/game/start",
            json={"mode": "standard"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "start_word" in data
        assert "target_word" in data

    async def test_game_history(self, client, auth_token):
        """Test getting game history."""
        response = await client.get(
            "/game/history",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
class TestStatsEndpoints:
    """Tests for statistics endpoints."""

    async def test_get_personal_stats(self, client, auth_token):
        """Test getting personal statistics."""
        response = await client.get(
            "/stats/personal",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_games" in data
        assert "sam_scores" in data
        assert "error_breakdown" in data

    async def test_leaderboard(self, client, auth_token):
        """Test getting leaderboard."""
        response = await client.get(
            "/stats/leaderboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total_players" in data


@pytest.mark.asyncio
class TestRootEndpoints:
    """Tests for root and health endpoints."""

    async def test_root(self, client):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "docs" in data

    async def test_health(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "word_graph" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
