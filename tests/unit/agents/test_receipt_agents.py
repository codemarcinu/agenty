#!/usr/bin/env python3
"""
Test Agentów Analizy Paragonu - FoodSave AI
============================================

Ten skrypt testuje wszystkie agenty odpowiedzialne za analizę paragonu:
1. OCRAgent - optyczne rozpoznawanie znaków
2. ReceiptAnalysisAgent - analiza strukturalna
3. ReceiptValidationAgent - walidacja jakości
4. EnhancedReceiptAnalysisAgent - wersja z anti-hallucination
5. ReceiptCategorizationAgent - kategoryzacja produktów
6. ReceiptImportAgent - import paragonów
"""

import asyncio
import os
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.agents.anti_hallucination.enhanced_receipt_analysis_agent import (
    EnhancedReceiptAnalysisAgent as AntiHallucinationAgent,
)
from backend.agents.ocr_agent import OCRAgent, OCRAgentInput
from backend.agents.receipt_analysis_agent import (
    EnhancedReceiptAnalysisAgent,
    ReceiptAnalysisAgent,
)
from backend.agents.receipt_categorization_agent import ReceiptCategorizationAgent
from backend.agents.receipt_import_agent import ReceiptImportAgent, ReceiptImportInput
from backend.agents.receipt_validation_agent import ReceiptValidationAgent


class ReceiptAgentsTest:
    def __init__(self):
        self.test_file = "tests/fixtures/test_receipt.jpg"
        self.test_ocr_text = """
PARAGON
Data: 2024-01-15
Sklep: Biedronka
Produkty:
- Chleb tostowy 5.99 zł
- Mleko 3.2% 1L 3.50 zł
- Jajka 10 szt 8.00 zł
- Banany 1kg 4.50 zł
SUMA: 21.99 zł
VAT: 4.38 zł
"""

    def test_1_ocr_agent(self):
        """Test 1: OCRAgent - optyczne rozpoznawanie znaków"""

        try:
            if not os.path.exists(self.test_file):
                return False

            # Initialize OCR agent
            ocr_agent = OCRAgent()

            # Read test file
            with open(self.test_file, "rb") as f:
                file_bytes = f.read()

            # Create input data
            input_data = OCRAgentInput(
                file_bytes=file_bytes,
                file_type="image"
            )

            # Process with OCR
            result = asyncio.run(ocr_agent.process(input_data))

            return bool(result.success)

        except Exception:
            return False

    def test_2_receipt_analysis_agent(self):
        """Test 2: ReceiptAnalysisAgent - analiza strukturalna"""

        try:
            # Initialize analysis agent
            analysis_agent = ReceiptAnalysisAgent()

            # Process test OCR text
            result = asyncio.run(analysis_agent.process({
                "ocr_text": self.test_ocr_text
            }))

            return bool(result.success)

        except Exception:
            return False

    def test_3_receipt_validation_agent(self):
        """Test 3: ReceiptValidationAgent - walidacja jakości"""

        try:
            # Initialize validation agent
            validation_agent = ReceiptValidationAgent()

            # Process test OCR text
            result = asyncio.run(validation_agent.process({
                "ocr_text": self.test_ocr_text
            }))

            if result.success:
                data = result.data
                data.get("validation_result", {})
                data.get("final_score", 0)
                data.get("should_proceed", False)

                return True
            else:
                return False

        except Exception:
            return False

    def test_4_receipt_categorization_agent(self):
        """Test 4: ReceiptCategorizationAgent - kategoryzacja produktów"""

        try:
            # Initialize categorization agent
            categorization_agent = ReceiptCategorizationAgent()

            # Test product categorization
            test_products = [
                "Chleb tostowy",
                "Mleko 3.2% 1L",
                "Jajka 10 szt",
                "Banany 1kg"
            ]

            categorized_count = 0
            for product in test_products:
                result = asyncio.run(categorization_agent.process({
                    "product_name": product
                }))

                if result.success:
                    data = result.data
                    data.get("category", "Unknown")
                    data.get("confidence", 0)
                    categorized_count += 1
                else:
                    pass

            success_rate = categorized_count / len(test_products)
            return success_rate >= 0.5  # At least 50% success rate

        except Exception:
            return False

    def test_5_receipt_import_agent(self):
        """Test 5: ReceiptImportAgent - import paragonów"""

        try:
            if not os.path.exists(self.test_file):
                return False

            # Initialize import agent
            import_agent = ReceiptImportAgent()

            # Read test file
            with open(self.test_file, "rb") as f:
                file_bytes = f.read()

            # Create input data
            input_data = ReceiptImportInput(
                file_bytes=file_bytes,
                file_type="image",
                filename="test_receipt.jpg"
            )

            # Process with import agent
            result = asyncio.run(import_agent.process(input_data))

            return bool(result.success)

        except Exception:
            return False

    def test_6_enhanced_receipt_analysis_agent(self):
        """Test 6: EnhancedReceiptAnalysisAgent - wersja z anti-hallucination"""

        try:
            # Initialize enhanced analysis agent
            enhanced_agent = EnhancedReceiptAnalysisAgent()

            # Process test OCR text
            result = asyncio.run(enhanced_agent.process({
                "ocr_text": self.test_ocr_text
            }))

            return bool(result.success)

        except Exception:
            return False

    def test_7_anti_hallucination_agent(self):
        """Test 7: Anti-hallucination agent - walidacja przeciw halucynacjom"""

        try:
            # Initialize anti-hallucination agent
            anti_hallucination_agent = AntiHallucinationAgent()

            # Process test OCR text
            result = asyncio.run(anti_hallucination_agent.process({
                "ocr_text": self.test_ocr_text
            }))

            return bool(result.success)

        except Exception:
            return False

    def test_8_agent_integration(self):
        """Test 8: Integracja agentów - pełny pipeline"""

        try:
            # Test full pipeline: OCR -> Validation -> Analysis -> Categorization

            # Step 1: OCR
            ocr_agent = OCRAgent()
            if os.path.exists(self.test_file):
                with open(self.test_file, "rb") as f:
                    file_bytes = f.read()
                input_data = OCRAgentInput(file_bytes=file_bytes, file_type="image")
                ocr_result = asyncio.run(ocr_agent.process(input_data))

                if not ocr_result.success:
                    ocr_text = self.test_ocr_text
                else:
                    ocr_text = ocr_result.text
            else:
                ocr_text = self.test_ocr_text

            # Step 2: Validation
            validation_agent = ReceiptValidationAgent()
            validation_result = asyncio.run(validation_agent.process({
                "ocr_text": ocr_text
            }))

            if validation_result.success:
                validation_data = validation_result.data
                should_proceed = validation_data.get("should_proceed", False)
                if not should_proceed:
                    pass
            else:
                pass

            # Step 3: Analysis
            analysis_agent = ReceiptAnalysisAgent()
            analysis_result = asyncio.run(analysis_agent.process({
                "ocr_text": ocr_text
            }))

            if analysis_result.success:
                analysis_data = analysis_result.data
                items = analysis_data.get("items", [])

                # Step 4: Categorization (for first few items)
                categorization_agent = ReceiptCategorizationAgent()
                categorized_items = 0
                for item in items[:3]:  # Test first 3 items
                    product_name = item.get("name", "")
                    if product_name:
                        cat_result = asyncio.run(categorization_agent.process({
                            "product_name": product_name
                        }))
                        if cat_result.success:
                            categorized_items += 1


                return True
            else:
                return False

        except Exception:
            return False

    def test_9_agent_performance(self):
        """Test 9: Wydajność agentów"""

        try:
            import time

            # Test OCR agent performance
            start_time = time.time()
            ocr_agent = OCRAgent()
            if os.path.exists(self.test_file):
                with open(self.test_file, "rb") as f:
                    file_bytes = f.read()
                input_data = OCRAgentInput(file_bytes=file_bytes, file_type="image")
                ocr_result = asyncio.run(ocr_agent.process(input_data))
                ocr_time = time.time() - start_time
            else:
                pass

            # Test analysis agent performance
            start_time = time.time()
            analysis_agent = ReceiptAnalysisAgent()
            analysis_result = asyncio.run(analysis_agent.process({
                "ocr_text": self.test_ocr_text
            }))
            analysis_time = time.time() - start_time

            # Test validation agent performance
            start_time = time.time()
            validation_agent = ReceiptValidationAgent()
            validation_result = asyncio.run(validation_agent.process({
                "ocr_text": self.test_ocr_text
            }))
            validation_time = time.time() - start_time

            # Performance thresholds
            max_ocr_time = 30.0  # 30 seconds
            max_analysis_time = 60.0  # 60 seconds
            max_validation_time = 10.0  # 10 seconds

            performance_ok = True
            if "ocr_time" in locals() and ocr_time > max_ocr_time:
                performance_ok = False
            if analysis_time > max_analysis_time:
                performance_ok = False
            if validation_time > max_validation_time:
                performance_ok = False

            return bool(performance_ok)

        except Exception:
            return False

    def run_all_tests(self):
        """Uruchom wszystkie testy agentów"""

        tests = [
            ("OCR Agent", self.test_1_ocr_agent),
            ("Receipt Analysis Agent", self.test_2_receipt_analysis_agent),
            ("Receipt Validation Agent", self.test_3_receipt_validation_agent),
            ("Receipt Categorization Agent", self.test_4_receipt_categorization_agent),
            ("Receipt Import Agent", self.test_5_receipt_import_agent),
            ("Enhanced Receipt Analysis Agent", self.test_6_enhanced_receipt_analysis_agent),
            ("Anti-hallucination Agent", self.test_7_anti_hallucination_agent),
            ("Agent Integration", self.test_8_agent_integration),
            ("Agent Performance", self.test_9_agent_performance),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    pass
            except Exception:
                pass


        if passed == total:
            pass
        else:
            pass

        return passed == total

if __name__ == "__main__":
    tester = ReceiptAgentsTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
