"""
Global test configuration and fixtures for FoodSave AI
"""

import asyncio
import os
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend.app_factory import create_app
from backend.core.database import Base

# Test configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_REDIS_URL = "redis://localhost:6379/1"  # Use different DB for tests

# Global test state
APP_AVAILABLE = False


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_app():
    """Create test app instance."""
    global APP_AVAILABLE
    try:
        app = create_app()
        APP_AVAILABLE = True
        return app
    except Exception:
        APP_AVAILABLE = False
        return None


@pytest.fixture
def client(test_app):
    """Create test client."""
    if not APP_AVAILABLE:
        pytest.skip("Application not available")

    with TestClient(test_app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(test_app):
    """Create async test client."""
    if not APP_AVAILABLE:
        pytest.skip("Application not available")

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    """Create test database session."""
    # Create async engine for tests
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("redis.Redis") as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        yield mock_client


@pytest.fixture
def mock_ollama():
    """Mock Ollama client."""
    with patch("backend.core.llm_client.llm_client") as mock_ollama:
        mock_client = AsyncMock()
        mock_ollama.return_value = mock_client
        mock_client.chat.return_value = {"message": {"content": "Test response"}}
        mock_client.embed.return_value = [0.1] * 4096
        yield mock_client


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    mock_store = MagicMock()
    mock_store.is_empty = False
    mock_store.similarity_search.return_value = []
    mock_store.add_documents.return_value = None
    mock_store.delete.return_value = None
    return mock_store


@pytest.fixture
def test_data():
    """Test data for various tests."""
    return {
        "user_query": "Test query",
        "session_id": "test-session-123",
        "agent_type": "general",
        "test_food_items": [
            {"name": "Apple", "quantity": 5, "unit": "pieces"},
            {"name": "Milk", "quantity": 2, "unit": "liters"},
            {"name": "Bread", "quantity": 1, "unit": "loaf"},
        ],
        "test_receipt": {
            "items": [
                {"name": "Apple", "price": 2.50, "quantity": 5},
                {"name": "Milk", "price": 3.20, "quantity": 2},
                {"name": "Bread", "price": 4.50, "quantity": 1},
            ],
            "total": 10.20,
            "store": "Test Store",
            "date": "2024-01-01",
        },
    }


@pytest.fixture
def mock_celery_task():
    """Mock Celery task result."""
    mock_task = MagicMock()
    mock_task.id = "test-task-id-123"
    mock_task.status = "PENDING"
    return mock_task


@pytest.fixture
def sample_image_bytes():
    """Sample image bytes for testing."""
    return b"fake_image_data_for_testing"


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ.update(
        {
            "ENVIRONMENT": "test",
            "TESTING_MODE": "true",
            "DATABASE_URL": TEST_DATABASE_URL,
            "REDIS_URL": TEST_REDIS_URL,
            "OLLAMA_URL": "http://localhost:11434",
            "DISABLE_FAISS": "1",
            "PYTHONPATH": "src",
        }
    )
    yield
    # Cleanup
    for key in [
        "ENVIRONMENT",
        "TESTING_MODE",
        "DATABASE_URL",
        "REDIS_URL",
        "OLLAMA_URL",
        "DISABLE_FAISS",
        "PYTHONPATH",
    ]:
        os.environ.pop(key, None)


# Async test configuration
pytest_plugins = ["pytest_asyncio"]


# Database test utilities
@pytest_asyncio.fixture
async def test_db():
    """Create test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_db):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


# Mock external services
@pytest.fixture
def mock_external_services():
    """Mock all external services."""
    with (
        patch("backend.core.llm_client.llm_client") as mock_llm,
        patch("redis.Redis") as mock_redis,
        patch("backend.core.vector_store.VectorStore") as mock_vector,
    ):

        # Configure mocks
        mock_llm.return_value.chat.return_value = {
            "message": {"content": "Mock response"}
        }
        mock_llm.return_value.embed.return_value = [0.1] * 4096

        mock_redis.return_value.ping.return_value = True
        mock_redis.return_value.get.return_value = None
        mock_redis.return_value.set.return_value = True

        mock_vector.return_value.is_empty = False
        mock_vector.return_value.similarity_search.return_value = []

        yield {
            "llm": mock_llm.return_value,
            "redis": mock_redis.return_value,
            "vector": mock_vector.return_value,
        }
