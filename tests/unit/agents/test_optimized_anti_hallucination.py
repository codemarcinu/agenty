#!/usr/bin/env python3
"""
Test script for optimized anti-hallucination system
Tests caching, unified validation, and intelligent level selection
"""

import asyncio
import time

from src.backend.core.anti_hallucination_system import (
    AGENT_VALIDATION_LEVELS,
    AntiHallucinationSystem,
)


async def test_caching_performance():
    """Test that caching improves validation performance"""

    system = AntiHallucinationSystem()

    test_response = "Przygotuj makaron z pomidorami. Potrzebujesz 200g makaronu i 3 pomidory."
    test_context = "Jak przygotować makaron?"

    # First validation (no cache)
    start_time = time.time()
    await system.validate_response(
        response=test_response,
        context=test_context,
        agent_name="chef",
        model_used="bielik-11b"
    )
    first_time = time.time() - start_time

    # Second validation (with cache)
    start_time = time.time()
    await system.validate_response(
        response=test_response,
        context=test_context,
        agent_name="chef",
        model_used="bielik-11b"
    )
    second_time = time.time() - start_time


    return second_time < first_time

async def test_intelligent_validation_levels():
    """Test that different agents get appropriate validation levels"""

    AntiHallucinationSystem()

    test_cases = [
        ("ChefAgent", "strict"),
        ("AnalyticsAgent", "moderate"),
        ("WeatherAgent", "lenient"),
        ("UnknownAgent", "moderate")  # fallback
    ]

    for agent_name, expected_level in test_cases:
        agent_type = agent_name.lower().replace("agent", "").replace("_", "")
        actual_level = AGENT_VALIDATION_LEVELS.get(agent_type, "moderate")

        assert actual_level == expected_level, f"Level mismatch for {agent_name}"

    return True

async def test_unified_validator_performance():
    """Test that unified validator processes validation faster"""

    system = AntiHallucinationSystem()

    test_responses = [
        "Dzisiaj jest słonecznie i 25 stopni.",
        "Potrzebujesz 500g makaronu i 2020 roku pomidorów.",  # hallucination
        "Analytics pokazuje wzrost sprzedaży o 15%.",
        "Przepis na kanapkę: chleb, masło, szynka."
    ]

    total_validations = 0
    start_time = time.time()

    for response in test_responses:
        await system.validate_response(
            response=response,
            context="test context",
            agent_name="test_agent",
            model_used="bielik-11b"
        )
        total_validations += 1


    total_time = time.time() - start_time
    avg_time = total_time / total_validations


    return avg_time < 0.1  # Should be very fast with unified validator

async def test_parallel_processing():
    """Test that parallel validation works correctly"""

    system = AntiHallucinationSystem()

    # Test multiple validations simultaneously
    tasks = []
    for i in range(5):
        task = system.validate_response(
            response=f"Test response {i} with some content",
            context=f"Test context {i}",
            agent_name=f"test_agent_{i}",
            model_used="bielik-11b"
        )
        tasks.append(task)

    start_time = time.time()
    results = await asyncio.gather(*tasks)
    time.time() - start_time


    return len(results) == 5

async def main():
    """Run all optimization tests"""

    tests = [
        ("Caching Performance", test_caching_performance),
        ("Intelligent Validation Levels", test_intelligent_validation_levels),
        ("Unified Validator Performance", test_unified_validator_performance),
        ("Parallel Processing", test_parallel_processing)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                pass
        except Exception:
            pass


    if passed == total:
        pass
    else:
        pass

if __name__ == "__main__":
    asyncio.run(main())
