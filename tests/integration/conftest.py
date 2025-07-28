from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio

from backend.agents.interfaces import AgentResponse
from backend.app_factory import create_app
from backend.core.database import AsyncSessionLocal

# Tutaj można dodać fixture specyficzne dla testów integracyjnych


@pytest_asyncio.fixture
async def db_session():
    """
    Async fixture dla sesji bazodanowej z cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def test_db():
    """
    Fixture dla testowej bazy danych z cleanup.
    """
    from backend.core.database import Base, engine

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def mock_ocr_agent_process():
    with patch(
        "backend.agents.ocr_agent.OCRAgent.process", new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = AgentResponse(
            success=True,
            text="BIEDRONKA\nData: 2024-06-23\nMleko 4.50zł\nChleb 3.20zł\nRazem: 7.70zł",
            message="Pomyślnie wyodrębniono tekst z pliku",
            metadata={"file_type": "image"},
        )
        yield mock_process


@pytest.fixture
def client():
    """
    Synchroniczny HTTP client dla FastAPI (TestClient) - dla testów synchronicznych
    """
    app = create_app()
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """
    Async HTTP client dla FastAPI (httpx.AsyncClient) - dla testów asynchronicznych
    """
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def client_async():
    """
    Async HTTP client dla FastAPI (httpx.AsyncClient) - FIXED for new httpx version
    """
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
