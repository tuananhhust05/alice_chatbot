"""
Pytest configuration and fixtures.
"""
import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


# ===== Event Loop =====
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ===== Mock Database =====
@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db = MagicMock()
    
    # Mock collections
    db.users = AsyncMock()
    db.conversations = AsyncMock()
    db.files = AsyncMock()
    
    return db


# ===== Mock User =====
@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    return {
        "_id": "user_id_123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
        "google_id": "google_123",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


# ===== Mock Kafka Producer =====
@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer."""
    with patch("app.services.kafka_producer.publish_chat_request", new_callable=AsyncMock) as mock:
        mock.return_value = None
        yield mock


# ===== Mock Redis =====
@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("app.services.redis_client.get_redis") as mock:
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.set = AsyncMock(return_value=True)
        redis_mock.setex = AsyncMock(return_value=True)
        mock.return_value = redis_mock
        yield redis_mock


# ===== Test App =====
@pytest.fixture
def app():
    """Create test FastAPI app."""
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app) -> Generator:
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app) -> AsyncGenerator:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# ===== Auth Override =====
@pytest.fixture
def auth_override(mock_user):
    """Override authentication dependency."""
    from app.dependencies import get_current_user_dep
    
    async def override_get_current_user():
        return mock_user
    
    return override_get_current_user


# ===== Authenticated Async Client =====
@pytest.fixture
async def authed_async_client(app, mock_user) -> AsyncGenerator:
    """
    Create async test client that bypasses auth middleware.
    Patches get_current_user to return mock user for any token.
    """
    with patch("app.middleware.get_current_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            cookies={"access_token": "fake_token_for_test"}
        ) as ac:
            yield ac


# ===== Sample Files =====
@pytest.fixture
def sample_txt_content():
    """Sample TXT file content."""
    return b"Hello, this is a test file.\nWith multiple lines.\nAnd some content."


@pytest.fixture
def sample_csv_content():
    """Sample CSV file content."""
    return b"name,age,city\nAlice,30,New York\nBob,25,Los Angeles\nCharlie,35,Chicago"


# ===== Temp File Helper =====
@pytest.fixture
def temp_file(tmp_path):
    """Helper to create temporary files."""
    def _create_file(filename: str, content: bytes) -> str:
        file_path = tmp_path / filename
        file_path.write_bytes(content)
        return str(file_path)
    return _create_file
