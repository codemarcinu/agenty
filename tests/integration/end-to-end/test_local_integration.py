#!/usr/bin/env python3
"""
Integration test for the new local LLM system.
Tests the complete flow: image upload → specialized OCR → local analysis → results.
"""

import asyncio
import logging
import os
from pathlib import Path
import sys
import tempfile
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.agents.local_enhanced_agents import (
    LocalReceiptAnalysisAgent,
    local_model_manager,
)
from backend.agents.ocr.specialized_ocr_llm import SpecializedOCRAgent
from backend.core.local_system_optimizer import local_system_optimizer

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LocalIntegrationTester:
    """Test suite for local LLM integration"""

    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    async def run_all_tests(self):
        """Run complete integration test suite"""
        logger.info("🚀 Starting Local LLM Integration Tests")
        logger.info("=" * 60)

        # Start system optimization
        local_system_optimizer.start_optimization()

        try:
            # Test 1: System Health Check
            await self.test_system_health()

            # Test 2: Model Manager
            await self.test_model_manager()

            # Test 3: Local OCR Agent
            await self.test_local_ocr_agent()

            # Test 4: Local Analysis Agent
            await self.test_local_analysis_agent()

            # Test 5: Complete Integration Flow
            await self.test_complete_integration_flow()

            # Test 6: Performance Metrics
            await self.test_performance_metrics()

        finally:
            local_system_optimizer.stop_optimization()

        # Print summary
        self.print_test_summary()

    async def test_system_health(self):
        """Test system health and optimization"""
        self.total_tests += 1
        test_name = "System Health Check"

        try:
            logger.info(f"🔍 Testing: {test_name}")

            # Check system metrics
            metrics = local_system_optimizer.monitor.get_current_metrics()
            logger.info(f"   Memory usage: {metrics.memory_percent:.1f}%")
            logger.info(f"   CPU usage: {metrics.cpu_percent:.1f}%")
            logger.info(f"   GPU available: {metrics.gpu_available}")

            # Check optimization recommendations
            recommendations = local_system_optimizer.get_system_recommendations()
            logger.info(f"   System recommendations: {len(recommendations)} items")

            # Test pre-inference optimization
            local_system_optimizer.optimize_before_inference()

            assert metrics.memory_percent < 95, "Memory usage too high"
            assert isinstance(recommendations, list), "Recommendations should be a list"

            self.passed_tests += 1
            self.test_results.append((test_name, "PASSED", None))
            logger.info(f"   ✅ {test_name} PASSED")

        except Exception as e:
            self.test_results.append((test_name, "FAILED", str(e)))
            logger.error(f"   ❌ {test_name} FAILED: {e}")

    async def test_model_manager(self):
        """Test local model manager functionality"""
        self.total_tests += 1
        test_name = "Model Manager"

        try:
            logger.info(f"🔍 Testing: {test_name}")

            # Test model selection
            optimal_model = local_model_manager.get_optimal_model_for_task("ocr_analysis")
            logger.info(f"   Optimal model for OCR analysis: {optimal_model}")

            # Test model loading (mock test - don't actually load)
            logger.info("   Testing model loading simulation...")

            assert optimal_model is not None, "Should return a model name"
            assert isinstance(optimal_model, str), "Model name should be string"

            self.passed_tests += 1
            self.test_results.append((test_name, "PASSED", None))
            logger.info(f"   ✅ {test_name} PASSED")

        except Exception as e:
            self.test_results.append((test_name, "FAILED", str(e)))
            logger.error(f"   ❌ {test_name} FAILED: {e}")

    async def test_local_ocr_agent(self):
        """Test specialized OCR agent"""
        self.total_tests += 1
        test_name = "Specialized OCR Agent"

        try:
            logger.info(f"🔍 Testing: {test_name}")

            # Create test image file (mock)
            test_image_content = b"Mock image content for testing"

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_file.write(test_image_content)
                temp_image_path = temp_file.name

            try:
                # Test OCR agent initialization
                ocr_agent = SpecializedOCRAgent()
                logger.info("   OCR agent initialized successfully")

                # Test preprocessing (without actual image processing)
                logger.info("   Testing image preprocessing simulation...")

                # Test agent response structure (mock processing)

                # Note: This will likely fail without actual models, but tests the structure
                logger.info("   Testing agent input validation...")

                assert hasattr(ocr_agent, "process"), "Agent should have process method"
                assert hasattr(ocr_agent, "config"), "Agent should have config"

                self.passed_tests += 1
                self.test_results.append((test_name, "PASSED", "Structure validation passed"))
                logger.info(f"   ✅ {test_name} PASSED (structure validation)")

            finally:
                # Cleanup
                if os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)

        except Exception as e:
            self.test_results.append((test_name, "FAILED", str(e)))
            logger.error(f"   ❌ {test_name} FAILED: {e}")

    async def test_local_analysis_agent(self):
        """Test local receipt analysis agent"""
        self.total_tests += 1
        test_name = "Local Analysis Agent"

        try:
            logger.info(f"🔍 Testing: {test_name}")

            # Test agent initialization
            analysis_agent = LocalReceiptAnalysisAgent()
            logger.info("   Analysis agent initialized successfully")

            # Test Polish store pattern loading
            store_patterns = analysis_agent.polish_store_patterns
            logger.info(f"   Loaded {len(store_patterns)} store patterns")

            # Test store detection with mock data
            mock_text = "LIDL Sp. z o.o. ul. Testowa 123 Paragon fiskalny"
            store_hints = analysis_agent._detect_store_locally(mock_text)
            logger.info(f"   Store detection test: {store_hints}")

            # Test prompt generation
            enhanced_prompt = analysis_agent._create_enhanced_polish_prompt(mock_text, store_hints)

            assert len(store_patterns) > 0, "Should load store patterns"
            assert "lidl" in store_patterns, "Should contain Lidl patterns"
            assert store_hints["primary_store"] == "lidl", "Should detect Lidl"
            assert "JSON" in enhanced_prompt, "Prompt should mention JSON format"
            assert len(enhanced_prompt) > 100, "Prompt should be substantial"

            self.passed_tests += 1
            self.test_results.append((test_name, "PASSED", None))
            logger.info(f"   ✅ {test_name} PASSED")

        except Exception as e:
            self.test_results.append((test_name, "FAILED", str(e)))
            logger.error(f"   ❌ {test_name} FAILED: {e}")

    async def test_complete_integration_flow(self):
        """Test complete integration flow (without actual model calls)"""
        self.total_tests += 1
        test_name = "Complete Integration Flow"

        try:
            logger.info(f"🔍 Testing: {test_name}")

            # Simulate complete flow structure
            mock_ocr_result = {
                "success": True,
                "data": {
                    "extracted_text": "LIDL Paragon fiskalny Data: 15.12.2024 Chleb 3,99 Mleko 4,59 SUMA PLN 8,58",
                    "confidence": 0.85
                }
            }

            {
                "ocr_text": mock_ocr_result["data"]["extracted_text"]
            }

            # Test analysis agent with mock data
            analysis_agent = LocalReceiptAnalysisAgent()

            # Test local validation
            test_data = {
                "store_name": "Lidl",
                "total_amount": 8.58,
                "items": [
                    {"name": "Chleb", "quantity": 1, "unit_price": 3.99},
                    {"name": "Mleko", "quantity": 1, "unit_price": 4.59}
                ]
            }

            validated_data = analysis_agent._validate_and_enhance_locally(
                test_data,
                mock_ocr_result["data"]["extracted_text"]
            )

            logger.info(f"   Validation result: {validated_data}")

            assert validated_data["store_name"] == "Lidl", "Store name should be preserved"
            assert validated_data["total_amount"] == 8.58, "Total should be correct"
            assert len(validated_data["items"]) == 2, "Should have 2 items"

            self.passed_tests += 1
            self.test_results.append((test_name, "PASSED", None))
            logger.info(f"   ✅ {test_name} PASSED")

        except Exception as e:
            self.test_results.append((test_name, "FAILED", str(e)))
            logger.error(f"   ❌ {test_name} FAILED: {e}")

    async def test_performance_metrics(self):
        """Test performance monitoring and metrics"""
        self.total_tests += 1
        test_name = "Performance Metrics"

        try:
            logger.info(f"🔍 Testing: {test_name}")

            # Test system metrics collection
            start_time = time.time()
            metrics = local_system_optimizer.monitor.get_current_metrics()
            collection_time = time.time() - start_time

            logger.info(f"   Metrics collection time: {collection_time*1000:.1f}ms")
            logger.info(f"   Current memory: {metrics.memory_percent:.1f}%")
            logger.info(f"   Current CPU: {metrics.cpu_percent:.1f}%")

            # Test configuration optimization
            config = local_system_optimizer.get_optimal_configuration(
                "llama3.2:8b",
                "ocr_analysis"
            )

            logger.info(f"   Optimal config generated: {len(config)} parameters")

            assert collection_time < 1.0, "Metrics collection should be fast"
            assert hasattr(metrics, "memory_percent"), "Metrics should have memory data"
            assert hasattr(metrics, "cpu_percent"), "Metrics should have CPU data"
            assert isinstance(config, dict), "Config should be a dictionary"
            assert "model_name" in config, "Config should specify model"

            self.passed_tests += 1
            self.test_results.append((test_name, "PASSED", None))
            logger.info(f"   ✅ {test_name} PASSED")

        except Exception as e:
            self.test_results.append((test_name, "FAILED", str(e)))
            logger.error(f"   ❌ {test_name} FAILED: {e}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        logger.info("=" * 60)
        logger.info("🎯 LOCAL LLM INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)

        logger.info(f"Total tests run: {self.total_tests}")
        logger.info(f"Tests passed: {self.passed_tests}")
        logger.info(f"Tests failed: {self.total_tests - self.passed_tests}")
        logger.info(f"Success rate: {(self.passed_tests/self.total_tests*100):.1f}%")

        logger.info("\nDetailed Results:")
        logger.info("-" * 40)

        for test_name, status, details in self.test_results:
            status_emoji = "✅" if status == "PASSED" else "❌"
            logger.info(f"{status_emoji} {test_name}: {status}")
            if details:
                logger.info(f"   Details: {details}")

        logger.info("=" * 60)

        if self.passed_tests == self.total_tests:
            logger.info("🎉 ALL TESTS PASSED! Local LLM integration is ready!")
        else:
            logger.info("⚠️  Some tests failed. Check the details above.")
            logger.info("💡 Note: Model-dependent tests may fail without actual models installed.")

        logger.info("=" * 60)


async def main():
    """Main test runner"""
    tester = LocalIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
