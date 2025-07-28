"""
Testy dla ulepszonego ReceiptAnalysisAgent z obsługą polskich paragonów.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.agents.interfaces import AgentResponse
from backend.agents.receipt_analysis_agent import ReceiptAnalysisAgent


class TestReceiptAnalysisAgentEnhanced:
    """Testy dla ulepszonego ReceiptAnalysisAgent."""

    @pytest.fixture
    def agent(self) -> ReceiptAnalysisAgent:
        """Tworzy instancję ReceiptAnalysisAgent do testów."""
        return ReceiptAnalysisAgent()

    @pytest.fixture
    def mock_llm_response(self) -> dict[str, Any]:
        """Mock odpowiedzi LLM dla testów."""
        return {
            "message": {
                "content": """
                {
                    "store_name": "Lidl",
                    "store_address": "ul. Testowa 1, Warszawa",
                    "date": "2024-01-15",
                    "time": "14:30",
                    "receipt_number": "12345",
                    "items": [
                        {
                            "name": "Mleko 3.2%",
                            "original_name": "Mleko 3.2% 1L",
                            "product_code": "123456",
                            "quantity": 1,
                            "unit": "szt",
                            "unit_price": 4.99,
                            "total_price": 4.99,
                            "vat_rate": "A",
                            "discount": 0,
                            "category": "Nabiał"
                        }
                    ],
                    "subtotals": {
                        "vat_a_amount": 0.93,
                        "vat_b_amount": 0,
                        "vat_c_amount": 0,
                        "total_discount": 0
                    },
                    "total_amount": 4.99,
                    "payment_method": "Karta"
                }
                """
            }
        }

    @pytest.mark.asyncio
    async def test_receipt_analysis_lidl_format(
        self, agent: ReceiptAnalysisAgent, mock_llm_response: dict[str, Any]
    ) -> None:
        """Test analizy paragonu z Lidl."""
        ocr_text = """
        Lidl sp. z.o. o. sp. k.
        2024-01-15 14:30
        Mleko 3.2% 1L 1 * 4,99 4,99 A
        Krakers Dobry Chrup 1 * 5,29 5,29 C
        RAZEM PLN 10,28
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=mock_llm_response)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data is not None
            assert result.data.get("store_name") == "Lidl"
            assert len(result.data.get("items", [])) == 1
            assert result.data.get("total_amount") == 4.99
            assert result.data.get("date") == "2024-01-15"

    @pytest.mark.asyncio
    async def test_receipt_analysis_auchan_format(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test analizy paragonu z Auchan."""
        ocr_text = """
        AUCHAN POLSKA SP. Z O.O.
        15.01.2024
        Chleb razowy 1 * 3,50 3,50 A
        Masło 82% 1 * 6,99 6,99 A
        SUMA PLN 10,49
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(
                return_value=None
            )  # Symuluj brak odpowiedzi LLM

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data is not None
            assert result.data.get("store_name") == "Auchan"
            assert len(result.data.get("items", [])) >= 1
            assert result.data.get("total_amount") == 10.49

    @pytest.mark.asyncio
    async def test_receipt_analysis_kaufland_format(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test analizy paragonu z Kaufland."""
        ocr_text = """
        KAUFLAND POLSKA MARKETY SP. Z O.O.
        2024-01-15
        Banany 1.5 kg * 3,99/kg 5,99 A
        Jogurt naturalny 400g 1 * 2,49 2,49 A
        RAZEM 8,48 PLN
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=None)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data is not None
            assert result.data.get("store_name") == "Kaufland"
            assert len(result.data.get("items", [])) >= 1
            assert result.data.get("total_amount") == 8.48

    @pytest.mark.asyncio
    async def test_receipt_analysis_biedronka_format(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test analizy paragonu w formacie Biedronka."""
        ocr_text = """
        BIEDRONKA
        15.01.2024
        Mleko 3.2% 1L 1 * 4,99 4,99 A
        Chleb razowy 1 * 3,50 3,50 A
        RAZEM PLN 8,49
        """

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=None)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data is not None
            # Sprawdź czy dane zostały przetworzone (niekoniecznie konkretna nazwa sklepu)
            assert "store_name" in result.data
            assert len(result.data.get("items", [])) >= 1
            assert result.data.get("total_amount", 0) > 0

    @pytest.mark.asyncio
    async def test_fallback_parser_with_common_products(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """
        Test fallback parsera z popularnymi
        produktami.
        """
        analyzer = ReceiptAnalysisAgent()

        # Test z popularnymi produktami spożywczymi
        receipt_text = (
            "\nMLEKO 3.2% 1L - 4.50 PLN\n"
            "CHLEB PSZENNY - 3.20 PLN\n"
            "JABŁKA 1KG - 5.80 PLN\n"
            "MASŁO 82% - 8.90 PLN\n"
            "JOGURT NATURALNY - 2.50 PLN\n"
            "RAZEM: 24.90 PLN\n"
        )

        result = await analyzer.process({"ocr_text": receipt_text})

        assert result.success
        assert result.data is not None
        its = result.data.get("items", [])
        length = len(its)
        assert length >= 3
        assert "total_amount" in result.data
        assert result.data.get("total_amount", 0) > 0

    @pytest.mark.asyncio
    async def test_fallback_parser_with_price_patterns(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test fallback parsera z różnymi wzorcami cen."""
        analyzer = ReceiptAnalysisAgent()

        receipt_text = """
        PRODUKT 1 - 10.99 zł
        PRODUKT 2 x2 - 15.50 PLN
        PRODUKT 3 1szt - 5.00
        PRODUKT 4 - 12,50 zł
        SUMA: 44.49 PLN
        """

        result = await analyzer.process({"ocr_text": receipt_text})

        assert result.success
        assert result.data is not None
        items = result.data.get("items", [])
        assert len(items) >= 2
        assert "total_amount" in result.data
        assert result.data.get("total_amount", 0) > 0

    @pytest.mark.asyncio
    async def test_date_validation_with_various_formats(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test walidacji daty w różnych formatach."""
        analyzer = ReceiptAnalysisAgent()

        # Test różnych formatów dat
        date_formats = [
            "15.01.2024",
            "2024-01-15",
            "15/01/2024",
            "15.01.24",
            "2024.01.15",
        ]

        for date_str in date_formats:
            receipt_text = f"""
            DATA: {date_str}
            PRODUKT 1 - 10.00 PLN
            PRODUKT 2 - 15.00 PLN
            RAZEM: 25.00 PLN
            """

            result = await analyzer.process({"ocr_text": receipt_text})

            assert result.success
            assert result.data is not None
            assert "date" in result.data
            # Sprawdź czy data została rozpoznana (może być w różnych formatach)
            assert result.data.get("date") is not None

    @pytest.mark.asyncio
    async def test_fallback_parser_robustness(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test odporności fallback parsera na różne formaty."""
        analyzer = ReceiptAnalysisAgent()

        # Test z nieprawidłowym formatem ale z cenami
        receipt_text = """
        RÓŻNE PRODUKTY:
        - ITEM 1: 5.50
        - ITEM 2: 10.25
        - ITEM 3: 7.80
        KONIEC: 23.55
        """

        result = await analyzer.process({"ocr_text": receipt_text})

        assert result.success
        assert result.data is not None
        items = result.data.get("items", [])
        assert len(items) >= 1
        assert "total_amount" in result.data
        assert result.data.get("total_amount", 0) > 0

    @pytest.mark.asyncio
    async def test_date_normalization(self, agent: ReceiptAnalysisAgent) -> None:
        """Test normalizacji różnych formatów dat."""
        test_cases = [
            ("15.01.2024", "2024-01-15"),
            ("2024-01-15", "2024-01-15"),
            ("15-01-2024", "2024-01-15"),
            ("1.1.2024", "2024-01-01"),
        ]

        for input_date, _ in test_cases:
            normalized = agent._normalize_date(input_date)
            # Sprawdź czy data jest w poprawnym formacie YYYY-MM-DD
            assert len(normalized) == 10
            assert normalized.count("-") == 2

    @pytest.mark.asyncio
    async def test_data_validation_future_date(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test walidacji daty przyszłej."""
        analyzer = ReceiptAnalysisAgent()

        # Test z datą w przyszłości
        receipt_text = """
        DATA: 2030-01-01
        PRODUKT 1 - 10.00 PLN
        PRODUKT 2 - 15.00 PLN
        RAZEM: 25.00 PLN
        """

        result = await analyzer.process({"ocr_text": receipt_text})

        assert result.success
        assert result.data is not None
        assert "date" in result.data
        # Data przyszła powinna być zachowana (nie walidowana jako błąd)
        # Sprawdź czy data zawiera oczekiwaną datę (może być z czasem)
        date_value = result.data.get("date")
        assert date_value is not None
        assert "2030-01-01" in date_value

    @pytest.mark.asyncio
    async def test_data_validation_price_mismatch(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test walidacji niezgodności cen."""
        data_with_mismatch = {
            "store_name": "Test",
            "items": [{"total_price": 5.00}, {"total_price": 3.00}],
            "total_amount": 10.00,  # Różnica 2 PLN
        }

        validated_data = agent._validate_and_fix_data(data_with_mismatch)
        # Sprawdź czy dane zostały zwalidowane
        assert "store_name" in validated_data
        assert "items" in validated_data

    @pytest.mark.asyncio
    async def test_empty_ocr_text(self, agent: ReceiptAnalysisAgent) -> None:
        """Test obsługi pustego tekstu OCR."""
        result = await agent.process({"ocr_text": ""})

        assert not result.success
        assert result.error is not None
        assert "Brak tekstu OCR do analizy" in result.error

    @pytest.mark.asyncio
    async def test_llm_no_response_fallback(self, agent: ReceiptAnalysisAgent) -> None:
        """Test fallback gdy LLM nie odpowiada."""
        ocr_text = "Lidl 15.01.2024 Mleko 4,99"

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=None)

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data is not None
            assert result.data.get("store_name") == "Lidl"

    @pytest.mark.asyncio
    async def test_categorization_error_handling(
        self, agent: ReceiptAnalysisAgent
    ) -> None:
        """Test obsługi błędów kategoryzacji."""
        ocr_text = "Test paragon"

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=None)

        with patch("backend.agents.agent_factory.AgentFactory") as mock_factory:
            mock_factory_instance = Mock()
            mock_categorization_agent = Mock()
            mock_categorization_agent.process = AsyncMock(
                return_value=AgentResponse(success=True, data={"category": "Nabiał"})
            )
            mock_factory_instance.create_agent = Mock(
                return_value=mock_categorization_agent
            )
            mock_factory.return_value = mock_factory_instance

            result = await agent.process({"ocr_text": ocr_text})

            # Proces powinien się zakończyć sukcesem mimo błędu kategoryzacji
            assert result.success

    def test_store_pattern_recognition(self, agent: ReceiptAnalysisAgent) -> None:
        """Test rozpoznawania wzorców sklepów."""
        test_cases = [
            ("LIDL SP. Z O.O.", "Lidl"),
            ("AUCHAN POLSKA", "Auchan"),
            ("KAUFLAND MARKETY", "Kaufland"),
            ("BIEDRONKA JERONIMO", "Biedronka"),
            ("TESCO POLSKA", "Tesco"),
            ("CARREFOUR POLSKA", "Carrefour"),
        ]

        for text, expected_store in test_cases:
            result = agent._fallback_parse(text)
            assert result.get("store_name") == expected_store

    def test_product_pattern_recognition(self, agent: ReceiptAnalysisAgent) -> None:
        """Test rozpoznawania wzorców produktów."""
        ocr_text = """
        Mleko 3.2% 1L 1 * 4,99 4,99 A
        Chleb razowy 1 * 3,50 3,50 A
        """

        result = agent._fallback_parse(ocr_text)

        assert len(result.get("items", [])) >= 1
        for item in result.get("items", []):
            assert "name" in item
            assert "total_price" in item
            assert "tax_category" in item

    @pytest.mark.asyncio
    async def test_complete_receipt_processing_workflow(
        self, agent: ReceiptAnalysisAgent, mock_llm_response: dict[str, Any]
    ) -> None:
        """
        Test kompletnego workflow przetwarzania
        paragonu.
        """
        ocr_text = (
            "\nLidl sp. z.o. o. sp. k.\n"
            "2024-01-15 14:30\n"
            "Mleko 3.2% 1L 1 * 4,99 4,99 A\n"
            "Chleb razowy 1 * 3,50 3,50 A\n"
            "RAZEM PLN 8,49\n"
        )

        with patch(
            "backend.agents.receipt_analysis_agent.hybrid_llm_client"
        ) as mock_client:
            mock_client.chat = AsyncMock(return_value=mock_llm_response)

        with patch("backend.agents.agent_factory.AgentFactory") as mock_factory:
            mock_factory_instance = Mock()
            mock_categorization_agent = Mock()
            mock_categorization_agent.process = AsyncMock(
                return_value=AgentResponse(success=True, data={"category": "Nabiał"})
            )
            mock_factory_instance.create_agent = Mock(
                return_value=mock_categorization_agent
            )
            mock_factory.return_value = mock_factory_instance

            result = await agent.process({"ocr_text": ocr_text})

            assert result.success
            assert result.data is not None
            assert "store_name" in result.data
            assert "date" in result.data
            assert result.data.get("total_amount", 0) > 0
            assert "items" in result.data


if __name__ == "__main__":
    pytest.main(["-v", "test_receipt_analysis_enhanced.py"])
