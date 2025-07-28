"""
Agent Planisty - Rdzeń inteligencji systemu agentowego
Zgodnie z planem ewolucji - Faza 2: Rdzeń Inteligencji
"""

from dataclasses import dataclass
import json
import logging
from typing import Any

from agents.tools.registry import tool_registry
from core.llm_client import llm_client
from core.utils import extract_json_from_text
from settings import settings

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    """Krok w planie wykonania"""

    step: int
    tool: str
    args: dict[str, Any]
    description: str
    expected_result: str | None = None


@dataclass
class ExecutionPlan:
    """Plan wykonania zadania"""

    query: str
    steps: list[PlanStep]
    total_steps: int
    estimated_complexity: str  # 'simple', 'medium', 'complex'


class Planner:
    """Agent planisty - tworzy wieloetapowe plany wykonania zadań"""

    def __init__(self):
        self.tool_registry = tool_registry
        self._initialized = False

    async def initialize(self) -> None:
        """Inicjalizuj planistę"""
        if self._initialized:
            return

        # Inicjalizuj rejestr narzędzi
        self.tool_registry = tool_registry
        self._initialized = True
        logger.info("Planner initialized")

    async def create_plan(
        self, query: str, context: dict[str, Any] | None = None
    ) -> ExecutionPlan:
        """
        Twórz plan wykonania dla zapytania użytkownika

        Args:
            query: Zapytanie użytkownika
            context: Dodatkowy kontekst (np. historia konwersacji)

        Returns:
            ExecutionPlan z krokami do wykonania
        """
        try:
            # Przygotuj prompt dla planisty
            system_prompt = self._create_planner_prompt()
            user_prompt = self._create_user_prompt(query, context)

            # Wywołaj LLM do utworzenia planu
            response = await llm_client.chat(
                model=settings.DEFAULT_MODEL,  # Użyj mocniejszego modelu dla planowania
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=False,
                options={"temperature": 0.1},  # Niska temperatura dla spójności
            )

            if isinstance(response, dict) and response.get("message"):
                content = response["message"]["content"]
                plan_data = self._parse_plan_response(content)

                if plan_data:
                    execution_plan = self._create_execution_plan(query, plan_data)
                    logger.info(
                        f"Created execution plan with {len(execution_plan.steps)} steps"
                    )
                    return execution_plan
                logger.warning("Failed to parse plan response, creating fallback plan")
                return self._create_fallback_plan(query)
            logger.error("Invalid response from LLM for plan creation")
            return self._create_fallback_plan(query)

        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            return self._create_fallback_plan(query)

    def _create_planner_prompt(self) -> str:
        """Twórz zoptymalizowany prompt systemowy dla planisty"""
        available_tools = self.tool_registry.format_tools_for_planner()

        return f"""
Jesteś ekspertem w planowaniu zadań. Stwórz szczegółowy plan wykonania zapytania używając dostępnych narzędzi.

KRYTYCZNE - ZAWSZE ZWRACAJ TYLKO JSON:
- ZAWSZE zwracaj odpowiedź TYLKO w formacie JSON
- NIE dodawaj żadnego innego tekstu, komentarzy, wyjaśnień ani markdown
- NIE używaj nagłówków, list ani innych formatowań
- ZAWSZE zaczynaj odpowiedź od {{ i kończ na }}
- NIE dodawaj żadnego tekstu przed ani po JSON
- NIE używaj markdown, emoji ani specjalnych znaków
- NIE dodawaj numeracji, list ani opisów kroków
- ZAWSZE używaj dokładnie tego formatu JSON:

{{
    "steps": [
        {{
            "step": 1,
            "tool": "nazwa_narzędzia",
            "tool_input": "zapytanie_do_narzędzia",
            "description": "krótki_opis_kroku"
        }}
    ]
}}

Dostępne narzędzia:
{available_tools}

Zapytanie użytkownika: {{query}}

PLAN:
"""

    def _create_user_prompt(
        self, query: str, context: dict[str, Any] | None = None
    ) -> str:
        """Twórz prompt użytkownika"""
        prompt = f"Zapytanie użytkownika: {query}"

        if context:
            if context.get("conversation_summary"):
                prompt += f"\n\nKontekst rozmowy: {context['conversation_summary']}"
            if context.get("user_preferences"):
                prompt += f"\nPreferencje użytkownika: {context['user_preferences']}"

        prompt += "\n\nStwórz plan wykonania tego zapytania:"
        return prompt

    def _parse_plan_response(self, content: str) -> dict[str, Any] | None:
        """Parsuj odpowiedź LLM na strukturę planu"""
        try:
            # Spróbuj wyciągnąć JSON z odpowiedzi
            json_str = extract_json_from_text(content)
            if json_str:
                plan_data = json.loads(json_str)

                # Waliduj strukturę
                if "steps" in plan_data and isinstance(plan_data["steps"], list):
                    return plan_data
                logger.warning("Invalid plan structure in response")
                return None
            # Jeśli nie znaleziono JSON, spróbuj ręcznie wyciągnąć
            logger.warning(
                "No valid JSON found in plan response, attempting manual extraction"
            )
            manual_json = self._manual_json_extraction(content)
            if manual_json:
                return manual_json
            logger.warning("Manual JSON extraction also failed")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing plan JSON: {e}")
            # Spróbuj ręczne wyciągnięcie jako fallback
            manual_json = self._manual_json_extraction(content)
            if manual_json:
                return manual_json
            return None
        except Exception as e:
            logger.error(f"Error parsing plan response: {e}")
            return None

    def _manual_json_extraction(self, content: str) -> dict[str, Any] | None:
        """Ręczne wyciąganie JSON z odpowiedzi LLM lub konwersja markdown na JSON"""
        import json
        import re

        cleaned_content = content.strip()
        # Usuń markdown code blocks
        if "```" in cleaned_content:
            json_match = re.search(
                r"```(?:json)?\s*({.*?})\s*```", cleaned_content, re.DOTALL
            )
            if json_match:
                cleaned_content = json_match.group(1)
        # Usuń nagłówki markdown
        cleaned_content = re.sub(
            r"^#+\s*.*?\n", "", cleaned_content, flags=re.MULTILINE
        )
        # Spróbuj zdekodować JSON
        try:
            return json.loads(cleaned_content)
        except Exception:
            pass
        # Fallback: spróbuj wyciągnąć kroki z różnych formatów markdown
        steps = []
        # Obsługa Step/Krok (PL/EN) z pogrubieniem lub bez
        for match in re.finditer(
            r"(?:\*\*|##+|###)?\s*(Step|Krok)\s*(\d+)[:.\- ]+(.*?)(?:\*\*|\n|$)",
            cleaned_content,
            re.IGNORECASE,
        ):
            step_num = int(match.group(2))
            description = match.group(3).strip()
            tool = "general_conversation"
            args = {"message": description}
            if any(word in description.lower() for word in ["pogod", "weather"]):
                tool = "get_weather_forecast"
                args = {"location": "current"}
            elif any(
                word in description.lower()
                for word in ["przepis", "recipe", "danie", "dish"]
            ):
                tool = "find_recipes"
                args = {"ingredients": ["chicken"]}
            steps.append(
                {
                    "step": step_num,
                    "tool": tool,
                    "args": args,
                    "description": description,
                    "expected_result": "",
                }
            )
        # Obsługa numerowanych list markdown (np. 1. Opis)
        for match in re.finditer(
            r"^(\d+)[).\-]+\s+(.*)$", cleaned_content, re.MULTILINE
        ):
            step_num = int(match.group(1))
            description = match.group(2).strip()
            tool = "general_conversation"
            args = {"message": description}
            if any(word in description.lower() for word in ["pogod", "weather"]):
                tool = "get_weather_forecast"
                args = {"location": "current"}
            elif any(
                word in description.lower()
                for word in ["przepis", "recipe", "danie", "dish"]
            ):
                tool = "find_recipes"
                args = {"ingredients": ["chicken"]}
            # Unikaj duplikatów kroków
            if not any(s["step"] == step_num for s in steps):
                steps.append(
                    {
                        "step": step_num,
                        "tool": tool,
                        "args": args,
                        "description": description,
                        "expected_result": "",
                    }
                )
        if steps:
            return {
                "steps": steps,
                "total_steps": len(steps),
                "estimated_complexity": "medium" if len(steps) > 1 else "simple",
            }
        # Fallback: jeśli parser nie znalazł kroków, przekaż oryginalne zapytanie
        # do general_conversation
        if content.strip():
            return {
                "steps": [
                    {
                        "step": 1,
                        "tool": "general_conversation",
                        "args": {"message": content.strip()},
                        "description": "Odpowiedz na zapytanie użytkownika",
                        "expected_result": "Odpowiedź na zapytanie",
                    }
                ],
                "total_steps": 1,
                "estimated_complexity": "simple",
            }
        return None

    def _create_simple_plan_from_content(self, content: str) -> dict[str, Any] | None:
        """Twórz prosty plan na podstawie treści odpowiedzi LLM"""
        try:
            # Analizuj treść i spróbuj wyciągnąć informacje o narzędziach
            content_lower = content.lower()

            # Sprawdź czy zawiera słowa kluczowe związane z pogodą
            if any(
                word in content_lower
                for word in ["pogoda", "weather", "temperatura", "temperature"]
            ):
                return {
                    "steps": [
                        {
                            "step": 1,
                            "tool": "get_weather_forecast",
                            "args": {"location": "current"},
                            "description": "Pobierz informacje o pogodzie",
                            "expected_result": "Informacje o aktualnej pogodzie",
                        }
                    ],
                    "total_steps": 1,
                    "estimated_complexity": "simple",
                }

            # Sprawdź czy zawiera słowa kluczowe związane z przepisami
            if any(
                word in content_lower
                for word in [
                    "przepis",
                    "recipe",
                    "jedzenie",
                    "food",
                    "kolacja",
                    "dinner",
                ]
            ):
                return {
                    "steps": [
                        {
                            "step": 1,
                            "tool": "find_recipes",
                            "args": {"ingredients": [], "max_results": 3},
                            "description": "Znajdź przepisy",
                            "expected_result": "Lista przepisów",
                        }
                    ],
                    "total_steps": 1,
                    "estimated_complexity": "simple",
                }

            # Dla prostych zapytań konwersacyjnych
            if any(
                word in content_lower
                for word in ["hello", "hi", "cześć", "jak się masz", "how are you"]
            ):
                return {
                    "steps": [
                        {
                            "step": 1,
                            "tool": "general_conversation",
                            "args": {"message": "general_conversation"},
                            "description": "Odpowiedz na zapytanie użytkownika",
                            "expected_result": "Odpowiedź na zapytanie",
                        }
                    ],
                    "total_steps": 1,
                    "estimated_complexity": "simple",
                }

            return None

        except Exception as e:
            logger.debug(f"Simple plan creation failed: {e}")
            return None

    def _fix_common_json_errors(self, json_str: str) -> str | None:
        """Napraw typowe błędy w JSON"""
        try:
            # Usuń komentarze i niepotrzebne znaki
            import re

            # Usuń komentarze //
            json_str = re.sub(r"//.*?$", "", json_str, flags=re.MULTILINE)

            # Usuń komentarze /* */
            json_str = re.sub(r"/\*.*?\*/", "", json_str, flags=re.DOTALL)

            # Napraw nieprawidłowe cudzysłowy
            json_str = re.sub(
                r"([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1 "\2":', json_str
            )

            # Napraw brakujące cudzysłowy w wartościach
            json_str = re.sub(
                r":\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])", r': "\1"\2', json_str
            )

            # Usuń nadmiarowe przecinki
            json_str = re.sub(r",\s*}", "}", json_str)
            json_str = re.sub(r",\s*]", "]", json_str)

            return json_str

        except Exception as e:
            logger.debug(f"JSON fixing failed: {e}")
            return None

    def _create_execution_plan(
        self, query: str, plan_data: dict[str, Any]
    ) -> ExecutionPlan:
        """Twórz obiekt ExecutionPlan z danych"""
        steps = []

        for step_data in plan_data.get("steps", []):
            step = PlanStep(
                step=step_data.get("step", len(steps) + 1),
                tool=step_data.get("tool", ""),
                args=step_data.get("args", {}),
                description=step_data.get("description", ""),
                expected_result=step_data.get("expected_result"),
            )
            steps.append(step)

        return ExecutionPlan(
            query=query,
            steps=steps,
            total_steps=plan_data.get("total_steps", len(steps)),
            estimated_complexity=plan_data.get("estimated_complexity", "medium"),
        )

    def _create_fallback_plan(self, query: str) -> ExecutionPlan:
        """Twórz plan awaryjny dla prostych zapytań"""
        # Dla prostych zapytań, użyj general_conversation_agent
        fallback_step = PlanStep(
            step=1,
            tool="general_conversation",
            args={"message": query},
            description="Odpowiedz na zapytanie użytkownika",
            expected_result="Odpowiedź na zapytanie",
        )

        return ExecutionPlan(
            query=query,
            steps=[fallback_step],
            total_steps=1,
            estimated_complexity="simple",
        )

    def validate_plan(self, plan: ExecutionPlan) -> bool:
        """Sprawdź czy plan jest poprawny"""
        if not plan.steps:
            return False

        for step in plan.steps:
            # Sprawdź czy narzędzie istnieje w rejestrze
            if step.tool != "general_conversation" and not self.tool_registry.get_tool(
                step.tool
            ):
                logger.warning(f"Tool {step.tool} not found in registry")
                return False

            # Sprawdź wymagane argumenty
            if step.tool != "general_conversation":
                tool_def = self.tool_registry.get_tool(step.tool)
                if tool_def:
                    missing_args = [
                        arg for arg in tool_def.required_args if arg not in step.args
                    ]
                    if missing_args:
                        logger.warning(
                            f"Missing required arguments for tool {step.tool}: {missing_args}"
                        )
                        return False

        return True

    def get_plan_summary(self, plan: ExecutionPlan) -> str:
        """Pobierz podsumowanie planu"""
        summary = f"Plan wykonania dla: '{plan.query}'\n"
        summary += f"Złożoność: {plan.estimated_complexity}\n"
        summary += f"Liczba kroków: {plan.total_steps}\n\n"

        for step in plan.steps:
            summary += f"Krok {step.step}: {step.description}\n"
            summary += f"  Narzędzie: {step.tool}\n"
            if step.args:
                summary += f"  Argumenty: {step.args}\n"
            if step.expected_result:
                summary += f"  Oczekiwany wynik: {step.expected_result}\n"
            summary += "\n"

        return summary
