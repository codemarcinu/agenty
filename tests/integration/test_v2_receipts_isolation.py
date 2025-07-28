from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest

from backend.agents.base_agent import BaseAgent
from backend.agents.interfaces import AgentResponse
from backend.api.v2.endpoints.receipts import router

app = FastAPI()
app.include_router(router)


class DummyAgent(BaseAgent):
    async def process(self, input_data):
        return AgentResponse(success=True, text="dummy")

    def get_metadata(self):
        return {}

    def get_dependencies(self):
        return []

    def is_healthy(self):
        return True


@pytest.fixture
async def async_client():
    """Async HTTP client for testing - FIXED for new httpx version."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_upload_receipt_success(async_client):
    """Test successful receipt upload."""
    with patch("backend.agents.agent_factory.get_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.process.return_value = AgentResponse(
            success=True,
            text="Receipt processed successfully",
            metadata={"items": [{"name": "Mleko", "price": 4.50}]},
        )
        mock_get_agent.return_value = mock_agent

        # Create test image
        test_image = BytesIO(b"fake_image_data")
        test_image.name = "test_receipt.jpg"

        response = await async_client.post(
            "/api/v2/receipts/upload",
            files={"file": ("test_receipt.jpg", test_image, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Receipt processed successfully" in data["text"]


@pytest.mark.asyncio
async def test_upload_receipt_agent_failure(async_client):
    """Test receipt upload when agent fails."""
    with patch("backend.agents.agent_factory.get_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.process.return_value = AgentResponse(
            success=False,
            error="Agent processing failed",
        )
        mock_get_agent.return_value = mock_agent

        # Create test image
        test_image = BytesIO(b"fake_image_data")
        test_image.name = "test_receipt.jpg"

        response = await async_client.post(
            "/api/v2/receipts/upload",
            files={"file": ("test_receipt.jpg", test_image, "image/jpeg")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Agent processing failed" in data["error"]


@pytest.mark.asyncio
async def test_upload_receipt_no_file(async_client):
    """Test receipt upload without file."""
    response = await async_client.post("/api/v2/receipts/upload")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_upload_receipt_invalid_file_type(async_client):
    """Test receipt upload with invalid file type."""
    # Create test file with invalid type
    test_file = BytesIO(b"fake_text_data")
    test_file.name = "test_receipt.txt"

    response = await async_client.post(
        "/api/v2/receipts/upload",
        files={"file": ("test_receipt.txt", test_file, "text/plain")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "Invalid file type" in data["detail"]


@pytest.mark.asyncio
async def test_upload_receipt_large_file(async_client):
    """Test receipt upload with file too large."""
    # Create large test image (simulate > 10MB)
    large_image = BytesIO(b"x" * (11 * 1024 * 1024))  # 11MB
    large_image.name = "large_receipt.jpg"

    response = await async_client.post(
        "/api/v2/receipts/upload",
        files={"file": ("large_receipt.jpg", large_image, "image/jpeg")},
    )

    assert response.status_code == 413  # Request Entity Too Large
