from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

# Tutaj można dodać fixture specyficzne dla testów e2e


@pytest_asyncio.fixture
async def db_session():
    """
    Async fixture dla sesji bazodanowej z cleanup.
    """
    # Mock database session for E2E tests
    mock_session = Mock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.query = Mock()

    # Mock query results
    mock_query = Mock()
    mock_query.filter = Mock(return_value=mock_query)
    mock_query.all = Mock(return_value=[])
    mock_query.first = Mock(return_value=None)
    mock_session.query.return_value = mock_query

    yield mock_session


@pytest.fixture
def mock_database_connection():
    """
    Mock dla połączenia z bazą danych.
    """
    with patch("backend.core.database.get_db") as mock_get_db:
        mock_session = Mock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.query = Mock()

        # Mock query results
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_query.first = Mock(return_value=None)
        mock_session.query.return_value = mock_query

        mock_get_db.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_ocr_success(mocker):
    """
    Fixture do mockowania sukcesu OCR (obraz).
    """
    return mocker.patch(
        "backend.agents.ocr_agent.process_image_file", return_value="Test receipt text"
    )


@pytest.fixture
def mock_ocr_pdf_success(mocker):
    """
    Fixture do mockowania sukcesu OCR (PDF).
    """
    return mocker.patch(
        "backend.agents.ocr_agent.process_pdf_file", return_value="Test PDF receipt"
    )


@pytest.fixture
def mock_ocr_failure(mocker):
    """
    Fixture do mockowania błędu OCR (obraz).
    """
    return mocker.patch(
        "backend.agents.ocr_agent.process_image_file", return_value=None
    )


@pytest.fixture
def mock_ocr_exception(mocker):
    """
    Fixture do mockowania wyjątku OCR (obraz).
    """
    return mocker.patch(
        "backend.agents.ocr_agent.process_image_file",
        side_effect=Exception("Unexpected error"),
    )
