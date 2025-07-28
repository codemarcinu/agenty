"""
Integration tests for Receipt API v3 - Asynchronous Processing
Tests the new async receipt processing endpoints with Celery tasks.
"""

from typing import Any
from unittest.mock import MagicMock, patch

from celery.result import AsyncResult
import pytest


class TestReceiptV3Async:
    """Test suite for Receipt API v3 async processing."""

    @pytest.fixture
    def sample_image_bytes(self) -> bytes:
        """Sample image bytes for testing."""
        return b"fake_image_data_for_testing"

    @pytest.fixture
    def mock_celery_task(self) -> MagicMock:
        """Mock Celery task result."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id-123"
        return mock_task

    @pytest.fixture
    def mock_async_result(self) -> MagicMock:
        """Mock AsyncResult for task status checking."""
        mock_result = MagicMock(spec=AsyncResult)
        mock_result.status = "PENDING"
        mock_result.info = None
        return mock_result

    def test_process_receipt_async_success(
        self, client: Any, sample_image_bytes: bytes, mock_celery_task: MagicMock
    ) -> None:
        """Test successful async receipt processing."""
        with patch(
            "src.api.v3.receipts.process_receipt_task.delay",
            return_value=mock_celery_task,
        ):
            files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
            response = client.post("/api/v3/receipts/process", files=files)

            assert response.status_code == 202
            data = response.json()

            assert data["status_code"] == 202
            assert data["message"] == "Receipt processing started"
            assert data["data"]["job_id"] == "test-task-id-123"
            assert data["data"]["status"] == "PENDING"
            assert data["data"]["filename"] == "receipt.jpg"
            assert "file_size" in data["data"]
            assert "submitted_at" in data["data"]

    def test_process_receipt_async_with_user_id(
        self, client: Any, sample_image_bytes: bytes, mock_celery_task: MagicMock
    ) -> None:
        """Test async receipt processing with user ID."""
        with patch(
            "src.api.v3.receipts.process_receipt_task.delay",
            return_value=mock_celery_task,
        ):
            files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
            response = client.post(
                "/api/v3/receipts/process?user_id=test_user_123", files=files
            )

            assert response.status_code == 202
            data = response.json()
            assert data["data"]["job_id"] == "test-task-id-123"

    def test_process_receipt_async_invalid_file_type(self, client: Any) -> None:
        """Test async receipt processing with invalid file type."""
        files = {"file": ("receipt.txt", b"text data", "text/plain")}
        response = client.post("/api/v3/receipts/process", files=files)

        assert response.status_code == 400
        data = response.json()
        # FastAPI HTTPException response structure
        assert "detail" in data
        detail = data["detail"]
        assert detail["error_code"] == "BAD_REQUEST"
        assert "Unsupported file type" in detail["message"]

    def test_process_receipt_async_missing_content_type(
        self, client: Any, sample_image_bytes: bytes
    ) -> None:
        """Test async receipt processing with missing content type."""
        # Test with an empty content type string instead of None
        files = {"file": ("receipt.jpg", sample_image_bytes, "")}
        response = client.post("/api/v3/receipts/process", files=files)

        assert response.status_code == 400
        data = response.json()
        # FastAPI HTTPException response structure
        assert "detail" in data
        detail = data["detail"]
        assert detail["error_code"] == "BAD_REQUEST"
        assert "Missing content type header" in detail["message"]

    def test_process_receipt_async_file_too_large(self, client: Any) -> None:
        """Test async receipt processing with file too large."""
        # Create a file larger than 10MB
        large_file = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("receipt.jpg", large_file, "image/jpeg")}
        response = client.post("/api/v3/receipts/process", files=files)

        assert response.status_code == 413
        data = response.json()
        # FastAPI HTTPException response structure
        assert "detail" in data
        detail = data["detail"]
        assert detail["error_code"] == "FILE_TOO_LARGE"
        assert "File too large" in detail["message"]

    def test_get_receipt_status_pending(
        self, client: Any, mock_async_result: MagicMock
    ) -> None:
        """Test getting status of pending task."""
        with patch("src.api.v3.receipts.AsyncResult", return_value=mock_async_result):
            response = client.get("/api/v3/receipts/status/test-task-id-123")

            assert response.status_code == 200
            data = response.json()
            assert data["status_code"] == 200
            assert data["data"]["job_id"] == "test-task-id-123"
            assert data["data"]["status"] == "PENDING"
            assert data["data"]["message"] == "Task is waiting for execution"

    def test_get_receipt_status_progress(self, test_app) -> None:
        """Test getting status of task in progress."""
        from fastapi.testclient import TestClient

        from src.api.v3.receipts import get_async_result_class

        class MockResult:
            def __init__(self, job_id, app=None):
                self.status = "PROGRESS"
                self.info = {
                    "step": "OCR",
                    "progress": 25,
                    "message": "Przetwarzanie OCR",
                    "filename": "receipt.jpg",
                }

        test_app.dependency_overrides = {}
        test_app.dependency_overrides[get_async_result_class] = lambda: MockResult
        with TestClient(test_app) as client:
            response = client.get("/api/v3/receipts/status/test-task-id-123")
        test_app.dependency_overrides = {}
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "PROGRESS"
        assert data["data"]["step"] == "OCR"
        assert data["data"]["progress"] == 25

    def test_get_receipt_status_success(self, test_app) -> None:
        """Test getting status of completed task."""
        from fastapi.testclient import TestClient

        from src.api.v3.receipts import get_async_result_class

        class MockResult:
            def __init__(self, job_id, app=None):
                self.status = "SUCCESS"
                self.result = {
                    "status": "SUCCESS",
                    "filename": "receipt.jpg",
                    "ocr_text": "Sample receipt text",
                    "analysis": {"store_name": "Test Store", "total_amount": 25.50},
                }

        test_app.dependency_overrides = {}
        test_app.dependency_overrides[get_async_result_class] = lambda: MockResult
        with TestClient(test_app) as client:
            response = client.get("/api/v3/receipts/status/test-task-id-123")
        test_app.dependency_overrides = {}
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "SUCCESS"
        assert data["data"]["message"] == "Task completed successfully"
        assert "result" in data["data"]

    def test_get_receipt_status_failure(self, test_app) -> None:
        """Test getting status of failed task."""
        from fastapi.testclient import TestClient

        from src.api.v3.receipts import get_async_result_class

        class MockResult:
            def __init__(self, job_id, app=None):
                self.status = "FAILURE"
                self.info = {"error": "OCR processing failed"}

        test_app.dependency_overrides = {}
        test_app.dependency_overrides[get_async_result_class] = lambda: MockResult
        with TestClient(test_app) as client:
            response = client.get("/api/v3/receipts/status/test-task-id-123")
        test_app.dependency_overrides = {}
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "FAILURE"
        assert data["data"]["message"] == "Task failed"
        assert "error" in data["data"]

    def test_cancel_receipt_processing(self, client: Any) -> None:
        """Test cancelling receipt processing task."""
        with patch("src.api.v3.receipts.celery_app.control.revoke") as mock_revoke:
            response = client.delete("/api/v3/receipts/cancel/test-task-id-123")

            assert response.status_code == 200
            data = response.json()
            assert data["status_code"] == 200
            assert data["message"] == "Task cancellation requested"
            assert data["data"]["job_id"] == "test-task-id-123"

            mock_revoke.assert_called_once_with("test-task-id-123", terminate=True)

    def test_receipt_processing_health(self, client: Any) -> None:
        """Test receipt processing system health check."""
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {
            "worker1": [
                {"name": "src.tasks.receipt_tasks.process_receipt_task", "id": "task1"},
                {"name": "other.task", "id": "task2"},
            ]
        }
        mock_inspect.registered.return_value = {
            "worker1": ["src.tasks.receipt_tasks.process_receipt_task", "other.task"]
        }

        with patch(
            "src.api.v3.receipts.celery_app.control.inspect", return_value=mock_inspect
        ):
            response = client.get("/api/v3/receipts/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status_code"] == 200
            assert data["data"]["status"] == "healthy"
            assert data["data"]["active_receipt_tasks"] == 1
            assert data["data"]["workers_available"] is True
            assert data["data"]["tasks_registered"] is True

    def test_receipt_processing_health_no_workers(self, client: Any) -> None:
        """Test health check when no workers are available."""
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = None
        mock_inspect.registered.return_value = None

        with patch(
            "src.api.v3.receipts.celery_app.control.inspect", return_value=mock_inspect
        ):
            response = client.get("/api/v3/receipts/health")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["workers_available"] is False
            assert data["data"]["tasks_registered"] is False

    def test_celery_task_process_receipt_success(self) -> None:
        """Test the actual Celery task processing."""
        # This test would require a more complex setup with actual Celery worker
        # For now, we'll test the task function directly
        from tasks.receipt_tasks import process_receipt_task

        # Mock the file operations and agent calls
        with (
            patch("builtins.open", create=True) as mock_open,
            patch("os.remove"),
            patch("src.tasks.receipt_tasks.OCRAgent") as mock_ocr_agent,
            patch(
                "src.tasks.receipt_tasks.ReceiptAnalysisAgent"
            ) as mock_analysis_agent,
        ):
            # Mock file reading
            mock_file = MagicMock()
            mock_file.read.return_value = b"fake_image_data"
            mock_open.return_value.__enter__.return_value = mock_file

            # Mock OCR agent
            mock_ocr_instance = MagicMock()
            mock_ocr_result = MagicMock()
            mock_ocr_result.success = True
            mock_ocr_result.text = "Sample receipt text from OCR"
            mock_ocr_instance.process.return_value = mock_ocr_result
            mock_ocr_agent.return_value = mock_ocr_instance

            # Mock analysis agent
            mock_analysis_instance = MagicMock()
            mock_analysis_result = MagicMock()
            mock_analysis_result.success = True
            mock_analysis_result.data = {
                "store_name": "Test Store",
                "total_amount": 25.50,
                "items": [{"name": "Milk", "price": 5.50}],
            }
            mock_analysis_instance.process.return_value = mock_analysis_result
            mock_analysis_agent.return_value = mock_analysis_instance

            # Mock file operations
            with (
                patch("pathlib.Path.exists", return_value=True),
                patch("pathlib.Path.stat") as mock_stat,
            ):
                mock_stat.return_value.st_size = 1024  # 1KB file

                # Call the task function
                result = process_receipt_task.apply(
                    args=["/tmp/test_file.jpg", "test_receipt.jpg", "test_user"]
                ).get()

                # Verify the result
                assert result["status"] == "SUCCESS"
                assert result["filename"] == "test_receipt.jpg"
                assert "ocr_text" in result
                assert "analysis" in result
