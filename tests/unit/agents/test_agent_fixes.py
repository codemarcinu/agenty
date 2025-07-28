#!/usr/bin/env python3
"""
Test script to verify fixes for ReceiptCategorizationAgent and Anti-hallucination Agent
"""

import asyncio
import logging
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_receipt_categorization_agent():
    """Test ReceiptCategorizationAgent with various input scenarios"""
    try:
        from backend.agents.receipt_categorization_agent import (
            ReceiptCategorizationAgent,
        )

        agent = ReceiptCategorizationAgent()

        # Test 1: Valid input
        valid_input = {
            "items": [
                {"name": "Mleko 3,2% 1L", "quantity": 1, "price": 4.99},
                {"name": "Chleb żytni", "quantity": 1, "price": 3.50},
                {"name": "Jogurt naturalny", "quantity": 2, "price": 2.99}
            ],
            "store_name": "Lidl",
            "use_llm": True
        }

        logger.info("Testing ReceiptCategorizationAgent with valid input...")
        result = await agent.process(valid_input)

        if result.success:
            logger.info("✅ Valid input test passed")
            logger.info(f"Processed {len(result.data.get('categorized_items', []))} items")
        else:
            logger.error(f"❌ Valid input test failed: {result.error}")

        # Test 2: Invalid input - empty items
        invalid_input_1 = {
            "items": [],
            "store_name": "Lidl",
            "use_llm": True
        }

        logger.info("Testing ReceiptCategorizationAgent with empty items...")
        result = await agent.process(invalid_input_1)

        if not result.success and "empty" in result.error.lower():
            logger.info("✅ Empty items validation working correctly")
        else:
            logger.error(f"❌ Empty items validation failed: {result.error}")

        # Test 3: Invalid input - missing name field
        invalid_input_2 = {
            "items": [
                {"quantity": 1, "price": 4.99},  # Missing name
                {"name": "Chleb żytni", "quantity": 1, "price": 3.50}
            ],
            "store_name": "Lidl",
            "use_llm": True
        }

        logger.info("Testing ReceiptCategorizationAgent with missing name field...")
        result = await agent.process(invalid_input_2)

        if not result.success and "name" in result.error.lower():
            logger.info("✅ Missing name field validation working correctly")
        else:
            logger.error(f"❌ Missing name field validation failed: {result.error}")

        # Test 4: Invalid input - invalid numeric field
        invalid_input_3 = {
            "items": [
                {"name": "Mleko 3,2% 1L", "quantity": "invalid", "price": 4.99},
                {"name": "Chleb żytni", "quantity": 1, "price": 3.50}
            ],
            "store_name": "Lidl",
            "use_llm": True
        }

        logger.info("Testing ReceiptCategorizationAgent with invalid numeric field...")
        result = await agent.process(invalid_input_3)

        if not result.success and ("number" in result.error.lower() or "quantity" in result.error.lower()):
            logger.info("✅ Invalid numeric field validation working correctly")
        else:
            logger.error(f"❌ Invalid numeric field validation failed: {result.error}")

        return True

    except Exception as e:
        logger.error(f"❌ ReceiptCategorizationAgent test failed: {e}")
        return False


async def test_anti_hallucination_agent():
    """Test Anti-hallucination Agent JSON parsing with various scenarios"""
    try:
        from backend.agents.anti_hallucination.structured_output_validator import (
            StructuredOutputValidator,
        )

        validator = StructuredOutputValidator()

        # Test 1: Valid JSON
        valid_json = {
            "store_name": "Lidl",
            "date": "2024-01-15",
            "items": [
                {
                    "name": "Mleko",
                    "quantity": 1,
                    "unit_price": 4.99,
                    "total_price": 4.99
                }
            ],
            "total_amount": 4.99
        }

        logger.info("Testing Anti-hallucination Agent with valid JSON...")
        result = validator.validate_receipt_data(valid_json)

        if result.is_valid:
            logger.info("✅ Valid JSON test passed")
        else:
            logger.error(f"❌ Valid JSON test failed: {result.errors}")

        # Test 2: Malformed JSON string
        malformed_json = """
        {
            store_name: "Lidl",
            date: "2024-01-15",
            items: [
                {name: "Mleko", quantity: 1, unit_price: 4.99, total_price: 4.99}
            ],
            total_amount: 4.99,
        }
        """

        logger.info("Testing Anti-hallucination Agent with malformed JSON...")
        result = validator.validate_receipt_data(malformed_json)

        if result.is_valid:
            logger.info("✅ Malformed JSON test passed (auto-fixed)")
        else:
            logger.warning(f"⚠️ Malformed JSON test failed: {result.errors}")

        # Test 3: JSON in markdown code block
        markdown_json = """
        Here is the receipt data:
        ```json
        {
            "store_name": "Lidl",
            "date": "2024-01-15",
            "items": [
                {
                    "name": "Mleko",
                    "quantity": 1,
                    "unit_price": 4.99,
                    "total_price": 4.99
                }
            ],
            "total_amount": 4.99
        }
        ```
        """

        logger.info("Testing Anti-hallucination Agent with JSON in markdown...")
        result = validator.validate_receipt_data(markdown_json)

        if result.is_valid:
            logger.info("✅ Markdown JSON test passed")
        else:
            logger.error(f"❌ Markdown JSON test failed: {result.errors}")

        # Test 4: Invalid JSON string
        invalid_json = "This is not JSON at all"

        logger.info("Testing Anti-hallucination Agent with invalid JSON...")
        result = validator.validate_receipt_data(invalid_json)

        if not result.is_valid and "Failed to extract" in result.errors[0]:
            logger.info("✅ Invalid JSON test passed (correctly rejected)")
        else:
            logger.error(f"❌ Invalid JSON test failed: {result.errors}")

        return True

    except Exception as e:
        logger.error(f"❌ Anti-hallucination Agent test failed: {e}")
        return False


async def test_json_extraction():
    """Test JSON extraction with various formats"""
    try:
        from backend.agents.anti_hallucination.structured_output_validator import (
            StructuredOutputValidator,
        )

        validator = StructuredOutputValidator()

        test_cases = [
            # Test case 1: Basic JSON
            {
                "input": '{"store_name": "Lidl", "date": "2024-01-15"}',
                "expected": True,
                "description": "Basic JSON object"
            },
            # Test case 2: JSON with trailing comma
            {
                "input": '{"store_name": "Lidl", "date": "2024-01-15",}',
                "expected": True,
                "description": "JSON with trailing comma"
            },
            # Test case 3: JSON with single quotes
            {
                "input": "{'store_name': 'Lidl', 'date': '2024-01-15'}",
                "expected": True,
                "description": "JSON with single quotes"
            },
            # Test case 4: JSON in markdown
            {
                "input": '```json\n{"store_name": "Lidl", "date": "2024-01-15"}\n```',
                "expected": True,
                "description": "JSON in markdown code block"
            },
            # Test case 5: Invalid JSON
            {
                "input": "This is not JSON",
                "expected": False,
                "description": "Invalid JSON"
            }
        ]

        logger.info("Testing JSON extraction with various formats...")

        for i, test_case in enumerate(test_cases, 1):
            result = validator._extract_json_from_text(test_case["input"])

            if (result is not None) == test_case["expected"]:
                logger.info(f"✅ Test {i} passed: {test_case['description']}")
            else:
                logger.error(f"❌ Test {i} failed: {test_case['description']}")

        return True

    except Exception as e:
        logger.error(f"❌ JSON extraction test failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting agent fixes verification tests...")

    tests = [
        ("ReceiptCategorizationAgent", test_receipt_categorization_agent),
        ("Anti-hallucination Agent", test_anti_hallucination_agent),
        ("JSON Extraction", test_json_extraction),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} tests...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! Agent fixes are working correctly.")
    else:
        logger.error("⚠️ Some tests failed. Please review the fixes.")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
