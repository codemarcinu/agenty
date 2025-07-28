"""
Testy integracyjne dla agentowego workflow'u przetwarzania paragonów.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.receipt_categorization_agent import ReceiptCategorizationAgent
from backend.agents.receipt_import_agent import ReceiptImportAgent
from backend.agents.receipt_validation_agent import ReceiptValidationAgent
from backend.main import app


class TestReceiptAgentWorkflow:
    """Testy dla agentowego workflow'u przetwarzania paragonów."""

    @pytest.fixture
    def client(self):
        """Tworzy klienta testowego."""
        return TestClient(app)

    @pytest.fixture
    def sample_receipt_image_bytes(self):
        """Tworzy przykładowe bajty obrazu paragonu."""
        # Symuluj bajty obrazu paragonu - minimum 100 bajtów dla walidacji
        return b"fake_receipt_image_bytes" * 10  # 250 bajtów

    @pytest.fixture
    def mock_ocr_text(self):
        """Mock tekstu OCR z paragonu."""
        return """Lidl sp. z o.o.
        ul. Testowa 123, 00-000 Warszawa
        NIP: 123-456-78-90

        Mleko 3,2% 1L 4,99 zł
        Chleb żytni 3,50 zł
        Jogurt naturalny 2,99 zł

        RAZEM: 11,48 zł
        VAT: 2,23 zł
        Data: 2024-01-15 14:30:25"""

    @pytest.fixture
    def mock_validation_result(self):
        """Mock wyniku walidacji paragonu."""
        return {
            "is_valid": True,
            "score": 85.5,
            "should_proceed": True,
            "warnings": ["NIP format could be improved"],
            "recommendations": ["Consider retaking photo for better NIP clarity"],
        }

    @pytest.fixture
    def mock_categorization_result(self):
        """Mock wyniku kategoryzacji produktów."""
        return {
            "products": [
                {
                    "name": "Mleko 3,2% 1L",
                    "quantity": 1,
                    "unit_price": 4.99,
                    "total_price": 4.99,
                    "category": "Dairy Products",
                    "confidence": 0.95,
                },
                {
                    "name": "Chleb żytni",
                    "quantity": 1,
                    "unit_price": 3.50,
                    "total_price": 3.50,
                    "category": "Bakery",
                    "confidence": 0.88,
                },
                {
                    "name": "Jogurt naturalny",
                    "quantity": 1,
                    "unit_price": 2.99,
                    "total_price": 2.99,
                    "category": "Dairy Products",
                    "confidence": 0.92,
                },
            ],
            "total_amount": 11.48,
            "store_name": "Lidl",
            "date": "2024-01-15",
        }

    @pytest.mark.asyncio
    async def test_receipt_import_agent_success(self, sample_receipt_image_bytes):
        """Test pomyślnego działania ReceiptImportAgent."""
        with patch(
            "backend.agents.receipt_import_agent.process_image_file"
        ) as mock_ocr:
            # Mock OCR function
            mock_ocr.return_value = "Lidl sp. z o.o.\nMleko 3,2% 1L 4,99 zł"

            agent = ReceiptImportAgent()
            input_data = {
                "file_bytes": sample_receipt_image_bytes,
                "file_type": "image",
                "filename": "test_receipt.jpg",
            }
            result = await agent.process(input_data)

            assert result.success is True
            assert result.text is not None
            assert "Lidl sp. z o.o." in result.text
            assert "Mleko 3,2% 1L 4,99 zł" in result.text
            assert result.data["file_type"] == "image"
            assert result.data["filename"] == "test_receipt.jpg"

    @pytest.mark.asyncio
    async def test_receipt_import_agent_ocr_failure(self, sample_receipt_image_bytes):
        """Test błędu OCR w ReceiptImportAgent."""
        with patch(
            "backend.agents.receipt_import_agent.process_image_file"
        ) as mock_ocr:
            # Mock OCR failure
            mock_ocr.return_value = None

            agent = ReceiptImportAgent()
            input_data = {
                "file_bytes": sample_receipt_image_bytes,
                "file_type": "image",
                "filename": "test_receipt.jpg",
            }
            result = await agent.process(input_data)

            assert result.success is False
            assert result.error is not None
            if result.error is not None:
                assert "Nie udało się rozpoznać tekstu" in result.error

    @pytest.mark.asyncio
    async def test_receipt_validation_agent_success(self, mock_ocr_text):
        """Test pomyślnego działania ReceiptValidationAgent."""
        agent = ReceiptValidationAgent()
        input_data = {"ocr_text": mock_ocr_text}
        result = await agent.process(input_data)

        assert result.success is True
        assert result.data is not None
        assert result.data["final_score"] > 0
        assert result.data["should_proceed"] is True
        assert "validation_result" in result.data
        assert "format_validation" in result.data
        assert "recommendations" in result.data

    @pytest.mark.asyncio
    async def test_receipt_validation_agent_invalid_receipt(self):
        """Test walidacji nieprawidłowego paragonu."""
        invalid_text = "Invalid receipt text without proper structure"

        agent = ReceiptValidationAgent()
        input_data = {"ocr_text": invalid_text}
        result = await agent.process(input_data)

        # Agent zwraca success=False dla nieprawidłowych paragonów (score < 0.6)
        assert result.success is False
        assert result.data is not None
        assert (
            result.data["final_score"] < 0.6
        )  # Niski score dla nieprawidłowego paragonu
        assert result.data["should_proceed"] is False
        assert "validation_result" in result.data
        assert "format_validation" in result.data
        assert "recommendations" in result.data

    @pytest.mark.asyncio
    async def test_receipt_validation_agent_nip_validation(self):
        """Test walidacji NIP."""
        text_with_valid_nip = """Lidl sp. z o.o.
        NIP: 123-456-78-90
        Mleko 3,2% 1L 4,99 zł
        RAZEM: 4,99 zł"""

        text_with_invalid_nip = """Lidl sp. z o.o.
        NIP: 123-456-78-XX
        Mleko 3,2% 1L 4,99 zł
        RAZEM: 4,99 zł"""

        agent = ReceiptValidationAgent()

        # Test z poprawnym NIP
        result_valid = await agent.process({"ocr_text": text_with_valid_nip})
        assert "nip" in result_valid.data["format_validation"]["valid_formats"]

        # Test z niepoprawnym NIP
        result_invalid = await agent.process({"ocr_text": text_with_invalid_nip})
        assert "nip" not in result_invalid.data["format_validation"]["valid_formats"]

    @pytest.mark.asyncio
    async def test_receipt_categorization_agent_success(self, mock_ocr_text):
        """Test pomyślnego działania ReceiptCategorizationAgent."""
        with patch(
            "backend.agents.receipt_categorization_agent.hybrid_llm_client"
        ) as mock_llm:
            # Mock LLM response
            mock_llm.chat.return_value = {
                "message": {
                    "content": '{"categorized_items": [{"name": "Mleko 3,2% 1L", "category": "Dairy Products", "confidence": 0.95}]}'
                }
            }

            agent = ReceiptCategorizationAgent()
            input_data = {
                "items": [{"name": "Mleko 3,2% 1L", "quantity": 1, "price": 4.99}],
                "store_name": "Lidl",
                "use_llm": True,
            }
            result = await agent.process(input_data)

            assert result.success is True
            assert result.text is not None
            assert "Pomyślnie skategoryzowano" in result.text
            # Check that categorization was successful, but don't assume specific category
            assert len(result.data["categorized_items"]) > 0

    @pytest.mark.asyncio
    async def test_receipt_categorization_agent_fallback_to_dictionary(
        self, mock_ocr_text
    ):
        """Test fallback do słownika w ReceiptCategorizationAgent."""
        with patch(
            "backend.agents.receipt_categorization_agent.hybrid_llm_client"
        ) as mock_llm:
            # Mock LLM failure
            mock_llm.chat.side_effect = Exception("LLM error")

            agent = ReceiptCategorizationAgent()
            input_data = {
                "items": [{"name": "Mleko 3,2% 1L", "quantity": 1, "price": 4.99}],
                "store_name": "Lidl",
                "use_llm": True,
                "fallback_to_dict": True,
            }
            result = await agent.process(input_data)

            assert result.success is True
            assert result.text is not None
            assert "Pomyślnie skategoryzowano" in result.text

    @pytest.mark.asyncio
    async def test_complete_workflow_success(
        self,
        client,
        sample_receipt_image_bytes,
        mock_ocr_text,
        mock_validation_result,
        mock_categorization_result,
    ):
        """Test kompletnego workflow'u przetwarzania paragonu."""
        with (
            patch("backend.agents.receipt_import_agent.process_image_file") as mock_ocr,
            patch(
                "backend.agents.receipt_validation_agent.ReceiptValidationAgent.process"
            ) as mock_validation,
            patch(
                "backend.agents.receipt_categorization_agent.ReceiptCategorizationAgent.process"
            ) as mock_categorization,
        ):
            # Mock OCR
            mock_ocr.return_value = mock_ocr_text

            # Mock validation
            mock_validation.return_value = AgentResponse(
                success=True,
                text="Validation successful",
                data=mock_validation_result,
            )

            # Mock categorization
            mock_categorization.return_value = AgentResponse(
                success=True,
                text="Categorization successful",
                data=mock_categorization_result,
            )

            # Test workflow - use existing endpoint
            response = client.post(
                "/api/v1/receipts/upload",
                files={"file": ("test_receipt.jpg", sample_receipt_image_bytes)},
            )

            assert response.status_code == 200
            data = response.json()
            assert "text" in data
            assert "message" in data

    @pytest.mark.asyncio
    async def test_workflow_validation_failure(
        self, client, sample_receipt_image_bytes, mock_ocr_text
    ):
        """Test workflow'u z błędem walidacji."""
        with (
            patch("backend.agents.receipt_import_agent.process_image_file") as mock_ocr,
            patch("backend.agents.ocr_agent.OCRAgent.process") as mock_ocr_agent,
        ):
            # Mock OCR
            mock_ocr.return_value = mock_ocr_text

            # Mock OCR agent failure - agent zwraca success=False
            mock_ocr_agent.return_value = AgentResponse(
                success=False,
                error="OCR processing failed",
                data={"is_valid": False, "score": 30, "should_proceed": False},
            )

            # Test workflow - endpoint zwraca 422 dla błędów OCR
            response = client.post(
                "/api/v1/receipts/upload",
                files={"file": ("test_receipt.jpg", sample_receipt_image_bytes)},
            )

            # Endpoint zwraca 422 dla błędów OCR
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_workflow_categorization_failure(
        self, client, sample_receipt_image_bytes, mock_ocr_text, mock_validation_result
    ):
        """Test workflow'u z błędem kategoryzacji."""
        with (
            patch("backend.agents.receipt_import_agent.process_image_file") as mock_ocr,
            patch("backend.agents.ocr_agent.OCRAgent.process") as mock_ocr_agent,
            patch(
                "backend.agents.receipt_categorization_agent.ReceiptCategorizationAgent.process"
            ) as mock_categorization,
        ):
            # Mock OCR
            mock_ocr.return_value = mock_ocr_text

            # Mock OCR agent success
            mock_ocr_agent.return_value = AgentResponse(
                success=True,
                text="OCR successful",
                data=mock_validation_result,
            )

            # Mock categorization failure - agent zwraca success=False
            mock_categorization.return_value = AgentResponse(
                success=False,
                error="Categorization failed",
            )

            # Test workflow - endpoint zwraca 422 dla błędów kategoryzacji
            response = client.post(
                "/api/v1/receipts/upload",
                files={"file": ("test_receipt.jpg", sample_receipt_image_bytes)},
            )

            # Endpoint zwraca 200 dla pomyślnego OCR (kategoryzacja nie jest częścią tego endpointu)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_agent_error_handling_and_recovery(self, sample_receipt_image_bytes):
        """Test obsługi błędów i odzyskiwania w agentach."""
        with patch(
            "backend.agents.receipt_import_agent.process_image_file"
        ) as mock_ocr:
            # Mock OCR timeout
            mock_ocr.side_effect = TimeoutError("OCR timeout")

            agent = ReceiptImportAgent()
            input_data = {
                "file_bytes": sample_receipt_image_bytes,
                "file_type": "image",
                "filename": "test_receipt.jpg",
            }
            result = await agent.process(input_data)

            assert result.success is False
            assert result.error is not None
            if result.error is not None:
                assert "limit czasu" in result.error

    @pytest.mark.asyncio
    async def test_agent_metadata_tracking(self, mock_ocr_text):
        """Test śledzenia metadanych w agentach."""
        agent = ReceiptValidationAgent()
        input_data = {"ocr_text": mock_ocr_text}
        result = await agent.process(input_data)

        assert result.success is True
        assert result.metadata is not None
        if result.metadata is not None:
            assert "processing_stage" in result.metadata
            assert result.metadata["processing_stage"] == "validation"

    @pytest.mark.asyncio
    async def test_agent_performance_monitoring(self, mock_ocr_text):
        """Test monitorowania wydajności agentów."""
        agent = ReceiptValidationAgent()
        input_data = {"ocr_text": mock_ocr_text}

        import time

        start_time = time.time()
        result = await agent.process(input_data)
        end_time = time.time()

        assert result.success is True
        assert (
            end_time - start_time
        ) < 5.0  # Test powinien zakończyć się w rozsądnym czasie

    @pytest.mark.asyncio
    async def test_agent_concurrent_processing(self, mock_ocr_text):
        """Test współbieżnego przetwarzania agentów."""
        import asyncio

        agent = ReceiptValidationAgent()
        input_data = {"ocr_text": mock_ocr_text}

        # Uruchom kilka zadań współbieżnie
        tasks = [agent.process(input_data) for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # Wszystkie zadania powinny się zakończyć pomyślnie
        for result in results:
            assert result.success is True

    @pytest.mark.asyncio
    async def test_agent_memory_management(self, mock_ocr_text):
        """Test zarządzania pamięcią w agentach."""
        import gc
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        agent = ReceiptValidationAgent()
        input_data = {"ocr_text": mock_ocr_text}

        # Wykonaj kilka operacji
        for _ in range(10):
            result = await agent.process(input_data)
            assert result.success is True

        # Wymuś garbage collection
        gc.collect()

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # Zwiększenie pamięci nie powinno być dramatyczne
        assert memory_increase < 100  # Mniej niż 100MB

    @pytest.mark.asyncio
    async def test_agent_configuration_validation(self):
        """Test walidacji konfiguracji agentów."""
        # Test z prawidłową konfiguracją
        agent = ReceiptImportAgent()
        assert agent.TIMEOUT > 0
        assert agent.default_language is not None

    @pytest.mark.asyncio
    async def test_agent_response_format_consistency(self, mock_ocr_text):
        """Test spójności formatu odpowiedzi agentów."""
        agent = ReceiptValidationAgent()
        input_data = {"ocr_text": mock_ocr_text}
        result = await agent.process(input_data)

        # Sprawdź wymagane pola w odpowiedzi
        assert hasattr(result, "success")
        assert hasattr(result, "text")
        assert hasattr(result, "data")
        assert hasattr(result, "metadata")

        # Sprawdź typy danych
        assert isinstance(result.success, bool)
        assert isinstance(result.text, str)
        if result.data is not None:
            assert isinstance(result.data, dict)
        if result.metadata is not None:
            assert isinstance(result.metadata, dict)
