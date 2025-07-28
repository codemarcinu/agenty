#!/usr/bin/env python3
"""
🧠 Test rozdzielania zadań dla agentów na podstawie intencji użytkownika
Autor: AI Assistant
Data: 26.06.2025

Ten skrypt testuje, jak system rozpoznaje intencje użytkownika w języku naturalnym
i kieruje je do odpowiednich agentów.
"""

import asyncio
import json
import sys
import time

# Dodaj ścieżkę do modułów backend
sys.path.append("src")

from backend.agents.intent_detector import SimpleIntentDetector
from backend.agents.interfaces import MemoryContext
from backend.agents.orchestrator import Orchestrator


class IntentRoutingTester:
    """Tester rozdzielania intencji do agentów"""

    def __init__(self):
        self.intent_detector = SimpleIntentDetector()
        self.orchestrator = None
        self.test_results = []

    async def setup_orchestrator(self):
        """Inicjalizacja orchestratora"""
        try:
            self.orchestrator = Orchestrator()
        except Exception:
            return False
        return True

    async def test_intent_detection(self, text: str, expected_intent: str) -> dict:
        """Test wykrywania intencji dla pojedynczego tekstu"""

        start_time = time.time()

        try:
            # Utwórz kontekst pamięci
            context = MemoryContext(
                session_id="test_session",
                history=[],
                last_command=text,
                request_id="test_request",
            )

            # Wykryj intencję
            intent_data = await self.intent_detector.detect_intent(text, context)

            end_time = time.time()
            detection_time = end_time - start_time

            # Sprawdź wynik
            success = intent_data.type == expected_intent
            confidence = intent_data.confidence

            result = {
                "text": text,
                "expected_intent": expected_intent,
                "detected_intent": intent_data.type,
                "confidence": confidence,
                "success": success,
                "detection_time": detection_time,
                "entities": intent_data.entities,
            }

            if success:
                pass
            else:
                pass

            return result

        except Exception as e:
            return {
                "text": text,
                "expected_intent": expected_intent,
                "detected_intent": "error",
                "confidence": 0.0,
                "success": False,
                "detection_time": time.time() - start_time,
                "error": str(e),
            }

    async def test_full_routing(self, text: str, expected_agent: str) -> dict:
        """Test pełnego routingu od tekstu do agenta"""

        if not self.orchestrator:
            return {"error": "Orchestrator not initialized"}

        start_time = time.time()

        try:
            # Przetwórz komendę przez orchestrator
            response = await self.orchestrator.process_command(
                user_command=text, session_id="test_session"
            )

            end_time = time.time()
            processing_time = end_time - start_time

            result = {
                "text": text,
                "expected_agent": expected_agent,
                "success": response.success,
                "processing_time": processing_time,
                "response_text": (
                    response.text[:200] + "..."
                    if len(response.text) > 200
                    else response.text
                ),
                "error": response.error if not response.success else None,
            }

            if response.success:
                pass
            else:
                pass

            return result

        except Exception as e:
            return {
                "text": text,
                "expected_agent": expected_agent,
                "success": False,
                "processing_time": time.time() - start_time,
                "error": str(e),
            }

    def print_summary(self):
        """Wyświetl podsumowanie testów"""

        if not self.test_results:
            return

        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        total_tests - successful_tests

        # Średni czas wykrywania
        detection_times = [
            r.get("detection_time", 0)
            for r in self.test_results
            if "detection_time" in r
        ]
        if detection_times:
            sum(detection_times) / len(detection_times)

        # Szczegółowe wyniki
        for i, result in enumerate(self.test_results, 1):
            "✅" if result.get("success", False) else "❌"
            result.get("detected_intent", "BŁĄD")
            result.get("confidence", 0.0)


async def main():
    """Główna funkcja testowa"""

    # Inicjalizacja testera
    tester = IntentRoutingTester()

    # Sprawdź czy backend działa
    try:
        import httpx

        response = httpx.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            pass
        else:
            pass
    except Exception:
        return

    # Inicjalizacja orchestratora
    if not await tester.setup_orchestrator():
        return

    # Testy intencji w języku naturalnym
    test_cases = [
        # Konwersacja ogólna
        ("Cześć, jak się masz?", "general_conversation"),
        ("Dzień dobry! Co słychać?", "general_conversation"),
        ("Opowiedz mi żart", "general_conversation"),
        ("Kim jesteś?", "general_conversation"),
        # Zakupy i paragony
        ("Wczoraj wydałem 150 zł w Biedronce", "shopping_conversation"),
        ("Mam paragon z Lidla, chcesz go przeanalizować?", "shopping_conversation"),
        ("Ile wydałem w tym miesiącu na jedzenie?", "shopping_conversation"),
        ("Dodaj ten produkt do listy zakupów", "shopping_conversation"),
        # Jedzenie i gotowanie
        ("Jak ugotować spaghetti?", "food_conversation"),
        ("Mam awokado i jajka, co mogę z tego ugotować?", "food_conversation"),
        ("Czy awokado jest zdrowe?", "food_conversation"),
        ("Podaj mi przepis na pizzę", "food_conversation"),
        # Planowanie posiłków
        ("Zaplanuj mi posiłki na cały tydzień", "meal_planning"),
        ("Co powinienem jeść na śniadanie?", "meal_planning"),
        ("Stwórz plan żywieniowy dla diety wegetariańskiej", "meal_planning"),
        # Pogoda
        ("Jaka jest pogoda w Warszawie?", "weather"),
        ("Czy będzie jutro padać?", "weather"),
        ("Prognoza pogody na weekend", "weather"),
        # Wyszukiwanie informacji
        ("Co to jest sztuczna inteligencja?", "information_query"),
        ("Kto wynalazł komputer?", "information_query"),
        ("Jak działa blockchain?", "information_query"),
        # Kategoryzacja
        ("Kategoryzuj moje wydatki z ostatniego miesiąca", "categorization"),
        ("Przypisz kategorię do tego produktu", "categorization"),
        ("Pogrupuj moje zakupy według kategorii", "categorization"),
        # OCR i analiza obrazów
        ("Przeanalizuj ten paragon", "ocr"),
        ("Skanuj ten obraz", "ocr"),
        ("Wyciągnij tekst z tego zdjęcia", "ocr"),
        # RAG i dokumenty
        ("Przeczytaj ten dokument", "rag"),
        ("Analizuj ten plik PDF", "rag"),
        ("Znajdź informacje w tym tekście", "rag"),
        # Złożone zapytania
        (
            "Mam paragon z wczoraj i chcę wiedzieć, czy wydałem za dużo na jedzenie",
            "shopping_conversation",
        ),
        (
            "Zaplanuj mi posiłki na tydzień, ale uwzględnij, że jestem wegetarianinem",
            "meal_planning",
        ),
        ("Jaka jest pogoda w Krakowie i czy powinienem wziąć parasol?", "weather"),
    ]

    # Wykonaj testy intencji
    for text, expected_intent in test_cases:
        result = await tester.test_intent_detection(text, expected_intent)
        tester.test_results.append(result)

        # Krótka przerwa między testami
        await asyncio.sleep(0.1)

    # Testy pełnego routingu (wybrane przypadki)
    routing_test_cases = [
        ("Cześć, jak się masz?", "general_conversation"),
        ("Jaka jest pogoda w Warszawie?", "weather"),
        ("Jak ugotować spaghetti?", "food_conversation"),
        ("Wczoraj wydałem 150 zł w Biedronce", "shopping_conversation"),
    ]

    for text, expected_agent in routing_test_cases:
        result = await tester.test_full_routing(text, expected_agent)
        # Dodaj do wyników jako routing test
        result["test_type"] = "routing"
        tester.test_results.append(result)

        await asyncio.sleep(0.5)  # Dłuższa przerwa dla routingu

    # Wyświetl podsumowanie
    tester.print_summary()

    # Zapisz wyniki do pliku
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"intent_routing_test_results_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            {
                "test_info": {
                    "timestamp": timestamp,
                    "total_tests": len(tester.test_results),
                    "successful_tests": sum(
                        1 for r in tester.test_results if r.get("success", False)
                    ),
                    "test_type": "intent_routing",
                },
                "results": tester.test_results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    asyncio.run(main())
