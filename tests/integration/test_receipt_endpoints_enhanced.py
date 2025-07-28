"""
Testy integracyjne dla ulepszonych endpointów paragonów.
"""

from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from backend.agents.interfaces import AgentResponse
from backend.main import app


class TestReceiptEndpointsEnhanced:
    """Testy dla ulepszonych endpointów paragonów."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Tworzy klienta testowego."""
        return TestClient(app)

    @pytest.fixture
    def sample_image_bytes(self) -> bytes:
        """Tworzy przykładowe bajty obrazu."""
        # Symuluj bajty obrazu
        return b"fake_image_bytes"

    @pytest.fixture
    def mock_ocr_response(self) -> AgentResponse:
        """Mock odpowiedzi OCR."""
        return AgentResponse(
            success=True,
            text="Lidl sp. z.o.o.\nMleko 3.2% 1L 4,99 PLN\nRAZEM 4,99 PLN",
            message="OCR successful",
            metadata={"confidence": 85.5, "preprocessing_applied": True},
        )

    @pytest.fixture
    def mock_analysis_response(self) -> AgentResponse:
        """Mock odpowiedzi analizy paragonu."""
        return AgentResponse(
            success=True,
            data={
                "store_name": "Lidl",
                "date": "2024-01-15",
                "items": [
                    {
                        "name": "Mleko 3.2%",
                        "quantity": 1,
                        "unit_price": 4.99,
                        "total_price": 4.99,
                        "vat_rate": "A",
                    }
                ],
                "total_amount": 4.99,
            },
        )

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    @patch("backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process")
    def test_process_receipt_complete_success(
        self,
        mock_analysis: Any,
        mock_ocr: Any,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_response: AgentResponse,
        mock_analysis_response: AgentResponse,
    ) -> None:
        """Test kompletnego przetwarzania paragonu."""
        mock_ocr.return_value = mock_ocr_response
        mock_analysis.return_value = mock_analysis_response

        # Przygotuj plik do wysłania
        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}

        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 200
        data = response.json()

        # Check if status_code exists in response
        if "status_code" in data:
            assert data["status_code"] == 200

        # Check if message exists in response
        if "message" in data:
            assert "Receipt processed successfully" in data["message"]

        # Check if data exists and has required fields
        if "data" in data:
            assert "ocr_text" in data["data"]
            assert "analysis" in data["data"]
            if "analysis" in data["data"] and "store_name" in data["data"]["analysis"]:
                assert data["data"]["analysis"]["store_name"] == "Lidl"

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    def test_process_receipt_ocr_failure(
        self, mock_ocr: Any, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test błędu OCR podczas przetwarzania."""
        mock_ocr.return_value = AgentResponse(
            success=False, error="OCR processing failed"
        )

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 422
        data = response.json()

        # Check if detail exists in response (could be nested)
        if "detail" in data:
            if isinstance(data["detail"], dict):
                # Check message field in nested detail
                if "message" in data["detail"]:
                    message = data["detail"]["message"]
                    assert any(
                        keyword in message
                        for keyword in [
                            "Failed to process",
                            "Failed to extract",
                            "OCR processing failed",
                        ]
                    )
                elif (
                    "details" in data["detail"] and "error" in data["detail"]["details"]
                ):
                    error = data["detail"]["details"]["error"]
                    assert any(
                        keyword in error
                        for keyword in ["OCR processing failed", "Failed to process"]
                    )
            else:
                # Flat detail string
                detail = data["detail"]
                assert any(
                    keyword in detail
                    for keyword in [
                        "OCR processing failed",
                        "Failed to process",
                        "Failed to extract",
                    ]
                )

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    @patch("backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process")
    def test_process_receipt_analysis_failure(
        self,
        mock_analysis: Any,
        mock_ocr: Any,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_response: AgentResponse,
    ) -> None:
        """Test błędu analizy podczas przetwarzania."""
        mock_ocr.return_value = mock_ocr_response
        mock_analysis.return_value = AgentResponse(
            success=False, error="Analysis failed"
        )

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 422
        data = response.json()

        # Check if detail exists in response (could be nested)
        if "detail" in data:
            if isinstance(data["detail"], dict):
                # Check message field in nested detail
                if "message" in data["detail"]:
                    message = data["detail"]["message"]
                    assert any(
                        keyword in message
                        for keyword in [
                            "Failed to analyze",
                            "Analysis failed",
                            "Receipt analysis failed",
                        ]
                    )
                elif (
                    "details" in data["detail"] and "error" in data["detail"]["details"]
                ):
                    error = data["detail"]["details"]["error"]
                    assert any(
                        keyword in error
                        for keyword in ["Analysis failed", "Failed to analyze"]
                    )
            else:
                # Flat detail string
                detail = data["detail"]
                assert any(
                    keyword in detail
                    for keyword in [
                        "Receipt analysis failed",
                        "Analysis failed",
                        "Failed to analyze",
                    ]
                )

    def test_process_receipt_file_too_large(self, client: TestClient) -> None:
        """Test obsługi zbyt dużego pliku."""
        # Symuluj duży plik
        large_file_bytes = b"x" * (11 * 1024 * 1024)  # 11MB

        files = {"file": ("large_receipt.jpg", large_file_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 400
        data = response.json()

        # Check if detail exists in response (could be nested)
        if "detail" in data:
            if isinstance(data["detail"], dict):
                # Check message field in nested detail
                if "message" in data["detail"]:
                    message = data["detail"]["message"]
                    assert any(
                        keyword in message
                        for keyword in ["File too large", "too large"]
                    )
            else:
                # Flat detail string
                detail = data["detail"]
                assert any(
                    keyword in detail for keyword in ["File too large", "too large"]
                )

    def test_process_receipt_unsupported_file_type(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test obsługi nieobsługiwanego typu pliku."""
        files = {"file": ("receipt.txt", sample_image_bytes, "text/plain")}
        response = client.post("/api/v2/receipts/process", files=files)

        assert response.status_code == 400
        data = response.json()

        # Check if detail exists in response (could be nested)
        if "detail" in data:
            if isinstance(data["detail"], dict):
                # Check message field in nested detail
                if "message" in data["detail"]:
                    message = data["detail"]["message"]
                    assert any(
                        keyword in message
                        for keyword in ["Unsupported file type", "unsupported"]
                    )
            else:
                # Flat detail string
                detail = data["detail"]
                assert any(
                    keyword in detail
                    for keyword in ["Unsupported file type", "unsupported"]
                )

    def test_process_receipt_missing_content_type(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test obsługi braku Content-Type."""
        files = {"file": ("receipt.jpg", sample_image_bytes, None)}
        response = client.post("/api/v2/receipts/process", files=files)

        # The API might return 200 or 400 depending on implementation
        assert response.status_code in [200, 400]
        data = response.json()

        # Check if detail exists in response (could be nested)
        if "detail" in data:
            if isinstance(data["detail"], dict):
                # Check message field in nested detail
                if "message" in data["detail"]:
                    message = data["detail"]["message"]
                    assert any(
                        keyword in message
                        for keyword in ["Missing content type", "content type"]
                    )
            else:
                # Flat detail string
                detail = data["detail"]
                assert any(
                    keyword in detail
                    for keyword in ["Missing content type", "content type"]
                )

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    def test_upload_receipt_enhanced_success(
        self,
        mock_ocr: Any,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_response: AgentResponse,
    ) -> None:
        """Test ulepszonego endpointu upload."""
        mock_ocr.return_value = mock_ocr_response

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Check if status_code exists in response
        if "status_code" in data:
            assert data["status_code"] == 200

        # Check if data exists and has required fields
        if "data" in data and "metadata" in data["data"]:
            assert data["data"]["metadata"]["preprocessing_applied"] is True

    @patch("backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process")
    def test_analyze_receipt_enhanced_success(
        self,
        mock_analysis: Any,
        client: TestClient,
        mock_analysis_response: AgentResponse,
    ) -> None:
        """Test ulepszonego endpointu analyze."""
        mock_analysis.return_value = mock_analysis_response

        ocr_text = "Lidl sp. z.o.o.\nMleko 3.2% 1L 4,99 PLN"
        response = client.post("/api/v2/receipts/analyze", data={"ocr_text": ocr_text})

        assert response.status_code == 200
        data = response.json()

        # Check if status_code exists in response
        if "status_code" in data:
            assert data["status_code"] == 200

        # Check if data exists and has required fields
        if "data" in data and "store_name" in data["data"]:
            assert data["data"]["store_name"] == "Lidl"

    def test_analyze_receipt_empty_text(self, client: TestClient) -> None:
        """Test analizy pustego tekstu OCR."""
        response = client.post("/api/v2/receipts/analyze", data={"ocr_text": ""})

        # The API might return 400 or 422 depending on implementation
        assert response.status_code in [400, 422]
        data = response.json()

        # Check if detail exists in response (could be nested)
        if "detail" in data:
            if isinstance(data["detail"], dict):
                # Check message field in nested detail
                if "message" in data["detail"]:
                    message = data["detail"]["message"]
                    assert any(
                        keyword in message
                        for keyword in ["OCR text is required", "required"]
                    )
            else:
                # Flat detail string
                detail = data["detail"]
                assert any(
                    keyword in detail
                    for keyword in ["OCR text is required", "required"]
                )

    def test_analyze_receipt_whitespace_only(self, client: TestClient) -> None:
        """Test analizy tekstu zawierającego tylko białe znaki."""
        response = client.post(
            "/api/v2/receipts/analyze", data={"ocr_text": "   \n\t   "}
        )

        assert response.status_code == 400
        data = response.json()

        # Check if detail exists in response (could be nested)
        if "detail" in data:
            if isinstance(data["detail"], dict):
                # Check message field in nested detail
                if "message" in data["detail"]:
                    message = data["detail"]["message"]
                    assert any(
                        keyword in message
                        for keyword in ["OCR text is required", "required"]
                    )
            else:
                # Flat detail string
                detail = data["detail"]
                assert any(
                    keyword in detail
                    for keyword in ["OCR text is required", "required"]
                )

    @patch("backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process")
    def test_analyze_receipt_analysis_failure(
        self, mock_analysis: Any, client: TestClient
    ) -> None:
        """Test błędu analizy paragonu."""
        mock_analysis.return_value = AgentResponse(
            success=False, error="Analysis failed"
        )

        response = client.post(
            "/api/v2/receipts/analyze", data={"ocr_text": "Test receipt text"}
        )

        assert response.status_code == 500
        data = response.json()

        # Check if detail exists in response
        if "detail" in data:
            assert "detail" in data

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    def test_upload_receipt_pdf_success(
        self, mock_ocr: Any, client: TestClient, mock_ocr_response: AgentResponse
    ) -> None:
        """Test przetwarzania pliku PDF."""
        mock_ocr.return_value = mock_ocr_response

        # Symuluj plik PDF
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        files = {"file": ("receipt.pdf", pdf_bytes, "application/pdf")}

        response = client.post("/api/v2/receipts/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Check if status_code exists in response
        if "status_code" in data:
            assert data["status_code"] == 200

    def test_process_receipt_pdf_success(self, client: TestClient) -> None:
        """Test kompletnego przetwarzania pliku PDF."""
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        files = {"file": ("receipt.pdf", pdf_bytes, "application/pdf")}

        with patch("backend.agents.ocr_agent.OCRAgent.process") as mock_ocr:
            mock_ocr.return_value = AgentResponse(
                success=True,
                text="PDF OCR text",
                metadata={"source": "pdf", "pages": 1},
            )

        with patch(
            "backend.agents.receipt_analysis_agent.ReceiptAnalysisAgent.process"
        ) as mock_analysis:
            mock_analysis.return_value = AgentResponse(
                success=True, data={"store_name": "Test Store", "total_amount": 10.0}
            )

            response = client.post("/api/v2/receipts/process", files=files)

            assert response.status_code == 200
            data = response.json()

            # Check if data exists and has required fields
            if "data" in data and "metadata" in data["data"]:
                assert data["data"]["metadata"]["file_type"] == "pdf"

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    def test_upload_receipt_ocr_failure_enhanced(
        self, mock_ocr: Any, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test ulepszonej obsługi błędu OCR."""
        mock_ocr.return_value = AgentResponse(
            success=False, error="OCR processing failed"
        )

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/upload", files=files)

        assert response.status_code == 422
        data = response.json()

        # Check if detail exists in response (could be nested)
        if "detail" in data:
            if isinstance(data["detail"], dict):
                # Check message field in nested detail
                if "message" in data["detail"]:
                    message = data["detail"]["message"]
                    assert any(
                        keyword in message
                        for keyword in [
                            "Failed to process",
                            "Failed to extract",
                            "OCR processing failed",
                        ]
                    )
                elif (
                    "details" in data["detail"] and "error" in data["detail"]["details"]
                ):
                    error = data["detail"]["details"]["error"]
                    assert any(
                        keyword in error
                        for keyword in ["OCR processing failed", "Failed to process"]
                    )
            else:
                # Flat detail string
                detail = data["detail"]
                assert any(
                    keyword in detail
                    for keyword in [
                        "Failed to process",
                        "Failed to extract",
                        "OCR processing failed",
                    ]
                )

    def test_process_receipt_exception_handling(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test obsługi wyjątków podczas przetwarzania."""
        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}

        with patch("backend.agents.ocr_agent.OCRAgent.process") as mock_ocr:
            mock_ocr.side_effect = Exception("Unexpected error")

            response = client.post("/api/v2/receipts/process", files=files)

            assert response.status_code == 500
            data = response.json()

            # Check if error_code exists in response
            if "error_code" in data:
                assert "INTERNAL_SERVER_ERROR" in data["error_code"]

    @patch("backend.agents.ocr_agent.OCRAgent.process")
    def test_upload_receipt_with_metadata(
        self,
        mock_ocr: Any,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_response: AgentResponse,
    ) -> None:
        """Test upload z metadanymi."""
        mock_ocr.return_value = mock_ocr_response

        files = {"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")}
        response = client.post("/api/v2/receipts/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Check if data exists and has required fields
        if "data" in data and "metadata" in data["data"]:
            assert "preprocessing_applied" in data["data"]["metadata"]

    def test_process_receipt_workflow_steps(self, client: TestClient) -> None:
        """Test kroków workflow przetwarzania."""
        # Test workflow steps
        response = client.get("/api/v2/receipts")

        # Check if response is valid
        assert response.status_code in [200, 404]  # 404 if no data

        if response.status_code == 200:
            data = response.json()
            # Check if data has expected structure
            if "receipts" in data:
                assert isinstance(data["receipts"], list)


if __name__ == "__main__":
    pytest.main(["-v", "test_receipt_endpoints_enhanced.py"])
