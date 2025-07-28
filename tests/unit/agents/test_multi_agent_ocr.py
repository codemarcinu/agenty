"""
Tests for Multi-Agent OCR System

Tests the new multi-agent OCR architecture with all components.
"""

import io

from PIL import Image
import pytest

from backend.agents.ocr import (
    ImagePreprocessingAgent,
    OCREngineAgent,
    OCROrchestrator,
    ProductClassificationAgent,
    StoreRecognitionAgent,
    StructureParserAgent,
)


class TestMultiAgentOCR:
    """Test suite for multi-agent OCR system"""

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes for testing"""
        # Create a simple test image
        image = Image.new("RGB", (100, 50), color="white")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @pytest.fixture
    async def ocr_orchestrator(self):
        """Create OCR orchestrator for testing"""
        orchestrator = OCROrchestrator(enable_monitoring=False)
        await orchestrator.initialize()
        yield orchestrator
        await orchestrator.shutdown()

    @pytest.mark.asyncio
    async def test_image_preprocessing_agent(self, sample_image_bytes):
        """Test image preprocessing agent"""
        agent = ImagePreprocessingAgent()
        await agent.initialize()

        try:
            result = await agent.process({"image_bytes": sample_image_bytes})

            assert result.success
            assert "processed_image_bytes" in result.data
            assert "quality_metrics" in result.data

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_ocr_engine_agent(self, sample_image_bytes):
        """Test OCR engine agent"""
        agent = OCREngineAgent()
        await agent.initialize()

        try:
            result = await agent.process({"image_bytes": sample_image_bytes})

            assert result.success
            assert "ocr_text" in result.data
            assert "confidence" in result.data

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_store_recognition_agent(self):
        """Test store recognition agent"""
        agent = StoreRecognitionAgent()
        await agent.initialize()

        try:
            # Test with Lidl receipt text
            test_text = "Lidl sp.z o.o. sp.k. Paragon fiskalny"

            result = await agent.process({"ocr_text": test_text})

            assert result.success
            assert "store_info" in result.data
            assert result.data["store_info"]["name"] == "Lidl"

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_structure_parser_agent(self):
        """Test structure parser agent"""
        agent = StructureParserAgent()
        await agent.initialize()

        try:
            # Test with sample receipt text
            test_text = """
            Lidl sp.z o.o. sp.k.
            Paragon fiskalny

            Mleko 3.2% 1L    4.50
            Chleb razowy    3.20
            Jogurt naturalny 2.80

            Suma PLN: 10.50
            """

            result = await agent.process({"ocr_text": test_text})

            assert result.success
            assert "structured_data" in result.data
            structured_data = result.data["structured_data"]

            assert "products" in structured_data
            assert "total" in structured_data
            assert len(structured_data["products"]) > 0

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_product_classification_agent(self):
        """Test product classification agent"""
        agent = ProductClassificationAgent()
        await agent.initialize()

        try:
            # Test with structured data
            structured_data = {
                "products": [
                    {"name": "Mleko 3.2% 1L", "price": 4.50},
                    {"name": "Chleb razowy", "price": 3.20},
                    {"name": "Jogurt naturalny", "price": 2.80},
                ]
            }

            result = await agent.process({"structured_data": structured_data})

            assert result.success
            assert "classified_products" in result.data
            classified_products = result.data["classified_products"]

            assert len(classified_products) == 3

            # Check that products are classified
            for product in classified_products:
                assert "category" in product
                assert "category_confidence" in product

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_complete_pipeline(self, ocr_orchestrator, sample_image_bytes):
        """Test complete OCR pipeline"""
        result = await ocr_orchestrator.process_receipt(
            image_bytes=sample_image_bytes, metadata={"test": True}
        )

        assert result.success
        assert "store" in result.data
        assert "products" in result.data
        assert "total" in result.data
        assert "confidence" in result.data

    @pytest.mark.asyncio
    async def test_pipeline_statistics(self, ocr_orchestrator):
        """Test pipeline statistics"""
        stats = ocr_orchestrator.get_pipeline_stats()

        assert "total_processed" in stats
        assert "successful_processed" in stats
        assert "failed_processed" in stats
        assert "average_pipeline_time" in stats
        assert "agent_performance" in stats

    @pytest.mark.asyncio
    async def test_health_check(self, ocr_orchestrator):
        """Test health check functionality"""
        health = await ocr_orchestrator.health_check()

        assert "orchestrator" in health
        assert "agents" in health
        assert "pipeline_stats" in health
        assert health["orchestrator"] == "healthy"

    @pytest.mark.asyncio
    async def test_error_handling(self, ocr_orchestrator):
        """Test error handling in pipeline"""
        # Test with invalid input
        result = await ocr_orchestrator.process_receipt(
            image_bytes=b"invalid_image_data", metadata={"test": True}
        )

        # Should handle error gracefully
        assert not result.success
        assert "error" in result.text or "error" in result.error

    @pytest.mark.asyncio
    async def test_agent_performance_metrics(self):
        """Test agent performance metrics"""
        agent = ImagePreprocessingAgent()
        await agent.initialize()

        try:
            # Create test image
            image = Image.new("RGB", (100, 50), color="white")
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()

            # Process multiple times to test metrics
            for _ in range(3):
                await agent.process({"image_bytes": image_bytes})

            # Check performance metrics
            stats = agent.get_processing_stats()
            assert stats["total_processed"] == 3
            assert stats["successful_processed"] == 3
            assert stats["average_processing_time"] > 0

            # Check success rate
            success_rate = agent.get_success_rate()
            assert success_rate == 100.0

        finally:
            await agent.shutdown()


class TestOCRIntegration:
    """Integration tests for OCR system"""

    @pytest.mark.asyncio
    async def test_agent_communication(self):
        """Test inter-agent communication"""
        # This would test the message bus functionality
        # For now, just verify agents can be created
        agents = [
            ImagePreprocessingAgent(),
            OCREngineAgent(),
            StoreRecognitionAgent(),
            ProductClassificationAgent(),
            StructureParserAgent(),
        ]

        for agent in agents:
            await agent.initialize()
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_polish_language_support(self):
        """Test Polish language support"""
        agent = OCREngineAgent()
        await agent.initialize()

        try:
            # Test with Polish text

            # This would test Polish character handling
            # For now, just verify the agent can handle Polish corrections
            assert "ą" in agent.polish_corrections
            assert "ć" in agent.polish_corrections

        finally:
            await agent.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])
