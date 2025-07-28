#!/usr/bin/env python3
"""
Test naprawy intent detection - prosty test bez pełnej inicjalizacji
"""

import asyncio
import os
import sys

# Dodaj ścieżkę do modułów
sys.path.append("src")

# Mock environment
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["AVAILABLE_MODELS"] = '["SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"]'
os.environ["ENVIRONMENT"] = "test"

async def test_intent_detection():
    """Test czy intent detection działa poprawnie"""

    try:
        from backend.agents.intent_detector import SimpleIntentDetector
        from backend.agents.interfaces import MemoryContext


        # Inicjalizacja detektora
        detector = SimpleIntentDetector()

        # Test przypadki
        test_cases = [
            ("Cześć, jak się masz?", "general_conversation"),
            ("Dzień dobry!", "general_conversation"),
            ("Opowiedz mi żart", "general_conversation"),
            ("Kim jesteś?", "general_conversation"),
            ("Pomóż mi", "general_conversation"),
        ]

        all_passed = True

        for query, expected in test_cases:
            MemoryContext(
                session_id="test_session",
                history=[],
                last_command=query,
                request_id="test_request"
            )

            # Test fallback intent detection (bez LLM)
            result = detector._fallback_intent_detection(query)


            if result.type == expected:
                pass
            else:
                all_passed = False


        return all_passed

    except Exception:
        return False

async def test_router_mapping():
    """Test mapowania w routerze"""

    try:
        # Test importu
        from backend.agents.agent_factory import AgentFactory
        from backend.agents.agent_registry import AgentRegistry
        from backend.agents.router_service import AgentRouter


        # Inicjalizacja komponentów
        registry = AgentRegistry()
        factory = AgentFactory(agent_registry=registry)
        router = AgentRouter(factory, registry)

        # Sprawdź mapowania
        mappings = router.agent_registry._intent_to_agent_mapping

        for intent, agent_type in mappings.items():
            pass

        # Sprawdź czy ogólna konwersacja jest zmapowana prawidłowo
        general_mapping = mappings.get("general_conversation")
        return general_mapping == "GeneralConversation"

    except Exception:
        return False

async def main():
    """Główna funkcja testowa"""


    # Test 1: Intent detection
    intent_test = await test_intent_detection()

    # Test 2: Router mapping
    router_test = await test_router_mapping()

    # Podsumowanie
    if intent_test and router_test:
        pass
    else:
        pass

    return intent_test and router_test

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
