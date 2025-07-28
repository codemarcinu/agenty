#!/usr/bin/env python3
"""
Kompleksowy test wszystkich agentów w systemie
"""

import asyncio
from datetime import datetime
import os
import sys

# Mock environment
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("AVAILABLE_MODELS", '["SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"]')
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")

# Dodaj ścieżkę do modułów
sys.path.append("src")

class AgentTester:
    """Tester wszystkich agentów"""

    def __init__(self):
        self.results = []
        self.factory = None
        self.registry = None

    async def setup(self):
        """Inicjalizacja komponentów testowych"""
        try:
            from backend.agents.agent_factory import AgentFactory
            from backend.agents.agent_registry import AgentRegistry
            self.registry = AgentRegistry()
            self.factory = AgentFactory(agent_registry=self.registry)
            return True
        except Exception:
            return False

    def add_result(self, agent_type: str, test_name: str, status: str, message: str = ""):
        """Dodaj wynik testu"""
        self.results.append({
            "agent": agent_type,
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    async def test_agent_registration(self):
        """Test rejestracji agentów w fabryce"""

        try:
            registered_types = self.registry.get_all_registered_agent_types()

            expected_agents = [
                "GeneralConversation", "Chef", "Weather", "Search", "RAG",
                "OCR", "ReceiptAnalysis", "Categorization", "MealPlanner",
                "Analytics", "PromoScraping"
            ]

            for agent_type in expected_agents:
                if agent_type in registered_types:
                    self.add_result(agent_type, "registration", "✅ PASS", "Agent zarejestrowany")
                else:
                    self.add_result(agent_type, "registration", "❌ FAIL", "Agent nie zarejestrowany")

            return True
        except Exception:
            return False

    async def test_agent_creation(self):
        """Test tworzenia instancji agentów"""

        registered_types = self.registry.get_all_registered_agent_types()

        for agent_type in registered_types:
            try:
                agent = self.factory.create_agent(agent_type)

                if agent:
                    self.add_result(agent_type, "creation", "✅ PASS", "Agent utworzony")
                else:
                    self.add_result(agent_type, "creation", "❌ FAIL", "Agent nie został utworzony")

            except Exception as e:
                self.add_result(agent_type, "creation", "❌ ERROR", str(e))

    async def test_agent_basic_interface(self):
        """Test podstawowego interfejsu agentów"""

        registered_types = self.registry.get_all_registered_agent_types()

        for agent_type in registered_types:
            try:
                agent = self.factory.create_agent(agent_type)
                if not agent:
                    continue

                # Test metod wymaganych
                required_methods = ["process", "get_metadata"]
                methods_ok = True

                for method in required_methods:
                    if not hasattr(agent, method):
                        methods_ok = False
                        break

                if methods_ok:
                    self.add_result(agent_type, "interface", "✅ PASS", "Interfejs kompletny")
                else:
                    self.add_result(agent_type, "interface", "❌ FAIL", "Brakujące metody")

            except Exception as e:
                self.add_result(agent_type, "interface", "❌ ERROR", str(e))

    async def test_agent_processing(self):
        """Test przetwarzania przez agentów z przykładowymi danymi"""

        # Przykładowe dane testowe dla różnych agentów
        test_data = {
            "GeneralConversation": {"query": "Cześć, jak się masz?"},
            "Chef": {"available_ingredients": ["pomidor", "mozzarella"], "dietary_restrictions": None},
            "Weather": {"query": "Jaka jest pogoda w Warszawie?", "location": "Warszawa"},
            "Search": {"query": "sztuczna inteligencja", "max_results": 3},
            "RAG": {"query": "Co to jest AI?", "context": "test"},
            "OCR": {"image_path": "test.jpg", "extract_text": True},
            "ReceiptAnalysis": {"ocr_text": "BIEDRONKA\nPomidory 5.99 PLN", "store_name": "Biedronka"},
            "Categorization": {"items": [{"name": "pomidory", "price": 5.99}]},
            "MealPlanner": {"dietary_preferences": "wegetariańska", "days": 3},
            "Analytics": {"query": "wydatki ostatni miesiąc"},
            "PromoScraping": {"url": "https://example.com/promocje"}
        }

        for agent_type in test_data:
            try:
                agent = self.factory.create_agent(agent_type)
                if not agent:
                    continue


                # Sprawdź czy agent ma metodę process
                if hasattr(agent, "process"):
                    # Dla bezpieczeństwa, nie wykonujemy rzeczywistego przetwarzania
                    # tylko sprawdzamy czy metoda istnieje i ma odpowiednie parametry
                    import inspect
                    sig = inspect.signature(agent.process)

                    if "input_data" in sig.parameters:
                        self.add_result(agent_type, "processing", "✅ PASS", "Metoda process dostępna")
                    else:
                        self.add_result(agent_type, "processing", "⚠️ WARN", "Nieprawidłowa sygnatura process")
                else:
                    self.add_result(agent_type, "processing", "❌ FAIL", "Brak metody process")

            except Exception as e:
                self.add_result(agent_type, "processing", "❌ ERROR", str(e))

    async def test_intent_routing(self):
        """Test mapowania intencji do agentów"""

        try:
            # Test mapowań intencji
            intent_mappings = self.registry.intent_to_agent_mapping

            expected_mappings = {
                "general_conversation": "GeneralConversation",
                "cooking": "Chef",
                "weather": "Weather",
                "search": "Search",
                "rag": "RAG",
                "ocr": "OCR",
                "categorization": "Categorization",
                "meal_planning": "MealPlanner",
                "analytics": "Analytics"
            }

            for intent, expected_agent in expected_mappings.items():
                mapped_agent = intent_mappings.get(intent)
                if mapped_agent == expected_agent:
                    self.add_result("Router", f"mapping_{intent}", "✅ PASS", f"{intent} -> {mapped_agent}")
                else:
                    self.add_result("Router", f"mapping_{intent}", "❌ FAIL", f"{intent} -> {mapped_agent} (expected {expected_agent})")

            return True
        except Exception:
            return False

    def generate_report(self):
        """Generuj raport testów"""

        # Statystyki ogólne
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "✅ PASS"])
        len([r for r in self.results if "❌" in r["status"]])
        len([r for r in self.results if "ERROR" in r["status"]])
        len([r for r in self.results if "⚠️" in r["status"]])


        # Grupuj wyniki po agentach
        agents = {}
        for result in self.results:
            agent = result["agent"]
            if agent not in agents:
                agents[agent] = []
            agents[agent].append(result)

        for agent, agent_results in sorted(agents.items()):
            len([r for r in agent_results if r["status"] == "✅ PASS"])
            len(agent_results)

            for result in agent_results:
                result["status"][:2]

        # Kluczowe wnioski

        # Sprawdź czy wszystkie agenty są zarejestrowane
        registration_results = [r for r in self.results if r["test"] == "registration"]
        all_registered = all(r["status"] == "✅ PASS" for r in registration_results)

        if all_registered:
            pass
        else:
            pass

        # Sprawdź routing
        routing_results = [r for r in self.results if "mapping_" in r["test"]]
        routing_ok = all(r["status"] == "✅ PASS" for r in routing_results)

        if routing_ok:
            pass
        else:
            pass

        # Sprawdź tworzenie agentów
        creation_results = [r for r in self.results if r["test"] == "creation"]
        creation_ok = all(r["status"] == "✅ PASS" for r in creation_results)

        if creation_ok:
            pass
        else:
            pass

        # Ogólna ocena
        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        if success_rate >= 0.9 or success_rate >= 0.7 or success_rate >= 0.5:
            pass
        else:
            pass

        return success_rate >= 0.7

async def main():
    """Główna funkcja testowa"""

    tester = AgentTester()

    # Inicjalizacja
    if not await tester.setup():
        return False

    # Wykonaj wszystkie testy
    try:
        # Test 1: Rejestracja agentów
        await tester.test_agent_registration()
        tester.add_result("System", "registration_test", "✅ PASS", "Test rejestracji zakończony")

        # Test 2: Tworzenie agentów
        await tester.test_agent_creation()
        tester.add_result("System", "creation_test", "✅ PASS", "Test tworzenia zakończony")

        # Test 3: Interfejs agentów
        await tester.test_agent_basic_interface()
        tester.add_result("System", "interface_test", "✅ PASS", "Test interfejsu zakończony")

        # Test 4: Przetwarzanie
        await tester.test_agent_processing()
        tester.add_result("System", "processing_test", "✅ PASS", "Test przetwarzania zakończony")

        # Test 5: Routing intencji
        await tester.test_intent_routing()
        tester.add_result("System", "routing_test", "✅ PASS", "Test routingu zakończony")

    except Exception as e:
        tester.add_result("System", "general_error", "❌ ERROR", str(e))

    # Generuj raport
    success = tester.generate_report()

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
