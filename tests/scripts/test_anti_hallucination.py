#!/usr/bin/env python3
"""
Test script for anti-hallucination system

This script tests the anti-hallucination system with various scenarios
to ensure it's working correctly.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend.core.anti_hallucination_system import (
    ValidationLevel,
    anti_hallucination_system,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_anti_hallucination_system():
    """Test the anti-hallucination system with various scenarios"""


    # Test 1: Valid recipe with available ingredients
    response = "Przepis na makaron z pomidorami:\n1. Ugotuj makaron\n2. Pokrój pomidory\n3. Wymieszaj składniki"
    context = "Chcę przepis z makaronu i pomidorów"
    available_ingredients = ["makaron", "pomidory"]

    await anti_hallucination_system.validate_response(
        response=response,
        context=context,
        agent_name="ChefAgent",
        model_used="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        validation_level=ValidationLevel.STRICT,
        available_ingredients=available_ingredients,
    )


    # Test 2: Recipe with hallucinated ingredients
    response = "Przepis na makaron z pomidorami:\n1. Ugotuj makaron\n2. Pokrój pomidory\n3. Dodaj 200g sera parmezan\n4. Wymieszaj składniki"
    context = "Chcę przepis z makaronu i pomidorów"
    available_ingredients = ["makaron", "pomidory"]

    await anti_hallucination_system.validate_response(
        response=response,
        context=context,
        agent_name="ChefAgent",
        model_used="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        validation_level=ValidationLevel.STRICT,
        available_ingredients=available_ingredients,
    )


    # Test 3: Response with factual errors
    response = "Cena makaronu w Polsce wynosi 15.50 zł za kilogram w 2024 roku."
    context = "Jaka jest cena makaronu?"

    await anti_hallucination_system.validate_response(
        response=response,
        context=context,
        agent_name="SearchAgent",
        model_used="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        validation_level=ValidationLevel.STRICT,
    )


    # Test 4: Context violation
    response = (
        "Python to język programowania obiektowy stworzony przez Guido van Rossum."
    )
    context = "Jak ugotować makaron?"

    await anti_hallucination_system.validate_response(
        response=response,
        context=context,
        agent_name="GeneralConversationAgent",
        model_used="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        validation_level=ValidationLevel.STRICT,
    )


    # Test 5: Valid response
    response = (
        "Aby ugotować makaron, zagotuj wodę, dodaj sól i makaron, gotuj 8-10 minut."
    )
    context = "Jak ugotować makaron?"

    await anti_hallucination_system.validate_response(
        response=response,
        context=context,
        agent_name="GeneralConversationAgent",
        model_used="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        validation_level=ValidationLevel.STRICT,
    )


    # Test 6: Different validation levels
    response = "Przepis na makaron z pomidorami:\n1. Ugotuj makaron\n2. Pokrój pomidory\n3. Dodaj 200g sera parmezan\n4. Wymieszaj składniki"
    context = "Chcę przepis z makaronu i pomidorów"
    available_ingredients = ["makaron", "pomidory"]

    for level in [
        ValidationLevel.STRICT,
        ValidationLevel.MODERATE,
        ValidationLevel.LENIENT,
    ]:
        await anti_hallucination_system.validate_response(
            response=response,
            context=context,
            agent_name="ChefAgent",
            model_used="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
            validation_level=level,
            available_ingredients=available_ingredients,
        )




async def test_model_configuration():
    """Test that Bielik-11B is properly configured"""


    # Test model config
    anti_hallucination_system.get_model_config(
        "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    )

    # Test metrics



async def main():
    """Main test function"""
    try:
        await test_anti_hallucination_system()
        await test_model_configuration()


    except Exception:
        logger.exception("Test error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
