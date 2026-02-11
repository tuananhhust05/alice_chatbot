"""
Pytest configuration and fixtures for orchestrator tests.
"""
import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from contextlib import asynccontextmanager

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
    db.prompts = AsyncMock()
    db.dead_letter_queue = AsyncMock()
    
    return db


# ===== Mock Settings =====
@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.MAX_RETRY_COUNT = 5
    settings.RETRY_BACKOFF_BASE = 1.0
    settings.RETRY_BACKOFF_MULTIPLIER = 2.0
    settings.RETRY_BACKOFF_MAX = 120.0
    settings.RETRY_JITTER_MAX = 2.0
    settings.REDIS_RESULT_TTL = 300
    settings.GROQ_API_KEY = "test_api_key"
    settings.KAFKA_CHAT_TOPIC = "chat_requests"
    settings.KAFKA_FILE_TOPIC = "file_requests"
    settings.KAFKA_RETRY_TOPIC = "retry_requests"
    return settings


# ===== Mock Conversation =====
@pytest.fixture
def mock_conversation():
    """Create mock conversation."""
    from bson import ObjectId
    return {
        "_id": ObjectId(),
        "user_id": "test@example.com",
        "title": "Test Conversation",
        "messages": [
            {"role": "user", "content": "Hello", "timestamp": datetime.utcnow()},
            {"role": "assistant", "content": "Hi there!", "timestamp": datetime.utcnow()},
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


# ===== Mock DLQ Item =====
@pytest.fixture
def mock_dlq_item():
    """Create mock DLQ item."""
    from bson import ObjectId
    return {
        "_id": ObjectId(),
        "request_id": "req_123",
        "original_topic": "chat_requests",
        "message_data": {"message": "Hello", "user_id": "test@example.com"},
        "last_error": "Rate limit exceeded",
        "retry_count": 5,
        "error_history": [
            {"error": "Rate limit exceeded", "timestamp": datetime.utcnow()}
        ],
        "first_failed_at": datetime.utcnow(),
        "last_failed_at": datetime.utcnow(),
        "status": "pending",
        "created_at": datetime.utcnow(),
    }


# ===== Null Lifespan for Testing =====
@asynccontextmanager
async def null_lifespan(app):
    """Empty lifespan that doesn't connect to real services."""
    yield


# ===== Test App =====
@pytest.fixture
def app():
    """Create test FastAPI app with disabled lifespan."""
    from app.main import app as fastapi_app
    # Store original lifespan
    original_lifespan = fastapi_app.router.lifespan_context
    # Replace with null lifespan for testing
    fastapi_app.router.lifespan_context = null_lifespan
    yield fastapi_app
    # Restore original lifespan
    fastapi_app.router.lifespan_context = original_lifespan


@pytest.fixture
def client(app) -> Generator:
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app) -> AsyncGenerator:
    """Create async test client (lifespan disabled via app fixture)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
