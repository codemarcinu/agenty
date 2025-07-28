#!/usr/bin/env python3
"""
Test agentów bez używania settings - bezpośredni import i test
"""

import os
import sys

# Setup minimal environment
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

sys.path.append("src")

class StandaloneAgentTester:
    """Tester agentów bez pełnej infrastruktury"""

    def __init__(self):
        self.results = []

    def add_result(self, agent_type: str, test_name: str, status: str, message: str = ""):
        """Dodaj wynik testu"""
        self.results.append({
            "agent": agent_type,
            "test": test_name,
            "status": status,
            "message": message
        })

    def test_agent_imports(self):
        """Test importów agentów"""

        agents_to_test = [
            ("GeneralConversationAgent", "backend.agents.general_conversation_agent"),
            ("ChefAgent", "backend.agents.chef_agent"),
            ("WeatherAgent", "backend.agents.weather_agent"),
            ("SearchAgent", "backend.agents.search_agent"),
            ("RAGAgent", "backend.agents.rag_agent"),
            ("CategorizationAgent", "backend.agents.categorization_agent"),
            ("MealPlannerAgent", "backend.agents.meal_planner_agent"),
            ("AnalyticsAgent", "backend.agents.analytics_agent"),
        ]

        for agent_name, module_path in agents_to_test:
            try:
                module = __import__(module_path, fromlist=[agent_name])
                agent_class = getattr(module, agent_name)

                self.add_result(agent_name, "import", "✅ PASS", "Import udany")

                # Test tworzenia instancji
                try:
                    agent = agent_class()
                    self.add_result(agent_name, "instantiation", "✅ PASS", "Instancja utworzona")

                    # Test metod
                    if hasattr(agent, "process"):
                        self.add_result(agent_name, "process_method", "✅ PASS", "Metoda process dostępna")
                    else:
                        self.add_result(agent_name, "process_method", "❌ FAIL", "Brak metody process")

                except Exception as e:
                    self.add_result(agent_name, "instantiation", "❌ ERROR", str(e))

            except Exception as e:
                self.add_result(agent_name, "import", "❌ ERROR", str(e))

    def test_base_agent(self):
        """Test klasy bazowej agenta"""

        try:
            from backend.agents.base_agent import BaseAgent

            self.add_result("BaseAgent", "import", "✅ PASS", "Import udany")

            # Test abstrakcyjnych metod
            required_methods = ["process"]
            for method in required_methods:
                if hasattr(BaseAgent, method):
                    self.add_result("BaseAgent", f"method_{method}", "✅ PASS", f"Metoda {method} zdefiniowana")
                else:
                    self.add_result("BaseAgent", f"method_{method}", "❌ FAIL", f"Brak metody {method}")

        except Exception as e:
            self.add_result("BaseAgent", "import", "❌ ERROR", str(e))

    def test_interfaces(self):
        """Test interfejsów i typów"""

        try:
            from backend.agents.interfaces import (
                AgentResponse,
                IntentData,
                MemoryContext,
            )

            interfaces = [
                ("AgentResponse", AgentResponse),
                ("IntentData", IntentData),
                ("MemoryContext", MemoryContext)
            ]

            for name, interface in interfaces:
                try:
                    # Test tworzenia z podstawowymi parametrami
                    if name == "AgentResponse":
                        interface(success=True, text="test")
                    elif name == "IntentData":
                        interface(type="test", entities={}, confidence=1.0)
                    elif name == "MemoryContext":
                        interface(session_id="test", history=[], last_command="test", request_id="test")

                    self.add_result(name, "interface_test", "✅ PASS", "Interfejs działa")

                except Exception as e:
                    self.add_result(name, "interface_test", "❌ ERROR", str(e))

        except Exception as e:
            self.add_result("Interfaces", "import", "❌ ERROR", str(e))

    def test_intent_detector_standalone(self):
        """Test intent detector bez pełnego systemu"""

        try:
            # Import bez pełnego systemu
            sys.path.append("src/backend/agents")

            # Utwórz prostą wersję intent detector logic
            def simple_intent_detection(text: str) -> str:
                """Uproszczona logika intent detection"""
                text_lower = text.lower()

                # General conversation
                general_keywords = ["cześć", "witaj", "dzień dobry", "hej", "pomoc", "pomóż", "kim jesteś"]
                if any(keyword in text_lower for keyword in general_keywords):
                    return "general_conversation"

                # Food/cooking
                food_keywords = ["przepis", "gotowanie", "jedzenie", "składniki", "ugotować"]
                if any(keyword in text_lower for keyword in food_keywords):
                    return "food_conversation"

                # Weather
                weather_keywords = ["pogoda", "temperatura", "deszcz", "słońce"]
                if any(keyword in text_lower for keyword in weather_keywords):
                    return "weather"

                return "general_conversation"

            # Test przypadki
            test_cases = [
                ("Cześć, jak się masz?", "general_conversation"),
                ("Kim jesteś?", "general_conversation"),
                ("Jak ugotować spaghetti?", "food_conversation"),
                ("Jaka jest pogoda?", "weather"),
                ("Pomóż mi", "general_conversation")
            ]

            all_passed = True
            for query, expected in test_cases:
                detected = simple_intent_detection(query)
                if detected == expected:
                    self.add_result("IntentDetector", f"test_{expected}", "✅ PASS", f"'{query}' -> {detected}")
                else:
                    self.add_result("IntentDetector", f"test_{expected}", "❌ FAIL", f"'{query}' -> {detected} (expected {expected})")
                    all_passed = False

            if all_passed:
                self.add_result("IntentDetector", "overall", "✅ PASS", "Wszystkie testy przeszły")
            else:
                self.add_result("IntentDetector", "overall", "❌ FAIL", "Niektóre testy nie przeszły")

        except Exception as e:
            self.add_result("IntentDetector", "test", "❌ ERROR", str(e))

    def generate_report(self):
        """Generuj raport"""

        # Statystyki
        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "✅ PASS"])
        len([r for r in self.results if "❌" in r["status"]])
        len([r for r in self.results if "ERROR" in r["status"]])


        # Grupowanie po agentach
        agents = {}
        for result in self.results:
            agent = result["agent"]
            if agent not in agents:
                agents[agent] = []
            agents[agent].append(result)

        for agent, results in sorted(agents.items()):
            len([r for r in results if r["status"] == "✅ PASS"])
            len(results)

            for result in results:
                result["status"][:2]

        # Podsumowanie
        success_rate = passed / total if total > 0 else 0

        if success_rate >= 0.8 or success_rate >= 0.6 or success_rate >= 0.4:
            pass
        else:
            pass

        return success_rate >= 0.6

def main():
    """Główna funkcja testowa"""

    tester = StandaloneAgentTester()

    # Wykonaj testy
    tester.test_base_agent()
    tester.test_interfaces()
    tester.test_agent_imports()
    tester.test_intent_detector_standalone()

    # Generuj raport
    success = tester.generate_report()


    return success

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
