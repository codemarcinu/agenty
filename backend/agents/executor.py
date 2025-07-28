"""
Egzekutor Planów - wykonuje plany utworzone przez planistę
Zgodnie z planem ewolucji - Faza 2: Rdzeń Inteligencji
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from agents.general_conversation_agent import GeneralConversationAgent
from agents.planner import ExecutionPlan, PlanStep
from agents.tools.registry import tool_registry

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Wynik wykonania kroku"""

    step: PlanStep
    success: bool
    result: Any
    error: str | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] | None = None


@dataclass
class ExecutionResult:
    """Wynik wykonania całego planu"""

    plan: ExecutionPlan
    step_results: list[StepResult]
    success: bool
    final_result: Any
    total_execution_time: float
    errors: list[str]
    warnings: list[str] = None


class Executor:
    """Egzekutor planów - wykonuje kroki planu i zarządza wynikami"""

    def __init__(self):
        self.tool_registry = tool_registry
        self.general_conversation_agent = GeneralConversationAgent()
        self._initialized = False
        self._stream_callback: Callable[[dict[str, Any]], None] | None = None
        self._execution_context: dict[str, Any] = {}

    async def initialize(self) -> None:
        """Inicjalizuj egzekutora"""
        if self._initialized:
            return

        self.tool_registry = tool_registry
        self._initialized = True
        logger.info("Executor initialized")

    def set_stream_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Ustaw callback dla streamingu statusu"""
        self._stream_callback = callback

    async def execute_plan(
        self, plan: ExecutionPlan, context: dict[str, Any] | None = None
    ) -> ExecutionResult:
        """
        Wykonaj plan krok po kroku

        Args:
            plan: Plan do wykonania
            context: Dodatkowy kontekst

        Returns:
            ExecutionResult z wynikami wszystkich kroków
        """
        start_time = asyncio.get_event_loop().time()
        step_results = []
        errors = []
        warnings = []

        # Inicjalizuj kontekst wykonania
        self._execution_context = {
            "original_query": plan.query,
            "user_context": context or {},
            "step_results": {},
            "shared_data": {},
        }

        logger.info(f"Starting execution of plan with {len(plan.steps)} steps")
        logger.debug(f"Plan query: {plan.query}")
        logger.debug(f"Plan complexity: {plan.estimated_complexity}")

        # Wyślij informację o rozpoczęciu
        self._send_stream_event(
            "plan_started",
            {
                "total_steps": len(plan.steps),
                "complexity": plan.estimated_complexity,
                "query": plan.query,
            },
        )

        try:
            # Wykonuj kroki sekwencyjnie
            for i, step in enumerate(plan.steps):
                step_start_time = asyncio.get_event_loop().time()

                # Wyślij informację o rozpoczęciu kroku
                self._send_stream_event(
                    "step_started",
                    {
                        "step_number": i + 1,
                        "total_steps": len(plan.steps),
                        "tool": step.tool,
                        "description": step.description,
                    },
                )

                logger.info(f"Executing step {i + 1}/{len(plan.steps)}: {step.tool}")
                logger.debug(f"Step args: {step.args}")

                try:
                    # Wykonaj krok
                    step_result = await self._execute_step(step, context, step_results)
                    step_results.append(step_result)

                    # Aktualizuj kontekst wykonania
                    self._execution_context["step_results"][f"step_{i + 1}"] = {
                        "success": step_result.success,
                        "result": step_result.result,
                        "error": step_result.error,
                        "execution_time": step_result.execution_time,
                    }

                    # Wyślij informację o zakończeniu kroku
                    self._send_stream_event(
                        "step_completed",
                        {
                            "step_number": i + 1,
                            "success": step_result.success,
                            "execution_time": step_result.execution_time,
                            "result_summary": self._summarize_result(
                                step_result.result
                            ),
                        },
                    )

                    # Jeśli krok się nie powiódł, dodaj błąd
                    if not step_result.success:
                        error_msg = f"Step {i + 1} failed: {step_result.error}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                    else:
                        logger.info(
                            f"Step {i + 1} completed successfully in {step_result.execution_time:.2f}s"
                        )

                except Exception as e:
                    error_msg = f"Unexpected error in step {i + 1}: {e!s}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)

                    # Utwórz wynik błędu
                    step_result = StepResult(
                        step=step,
                        success=False,
                        result=None,
                        error=error_msg,
                        execution_time=asyncio.get_event_loop().time()
                        - step_start_time,
                    )
                    step_results.append(step_result)

                    # Wyślij informację o błędzie
                    self._send_stream_event(
                        "step_failed", {"step_number": i + 1, "error": error_msg}
                    )

            # Wyślij informację o zakończeniu planu
            successful_steps = len([r for r in step_results if r.success])
            self._send_stream_event(
                "plan_completed",
                {
                    "total_steps": len(plan.steps),
                    "successful_steps": successful_steps,
                    "failed_steps": len(plan.steps) - successful_steps,
                },
            )

        except Exception as e:
            error_msg = f"Critical error during plan execution: {e!s}"
            errors.append(error_msg)
            logger.error(error_msg, exc_info=True)

            # Wyślij informację o krytycznym błędzie
            self._send_stream_event("plan_failed", {"error": error_msg})

        total_execution_time = asyncio.get_event_loop().time() - start_time

        # Określ końcowy wynik
        final_result = self._determine_final_result(step_results, plan)
        success = len(errors) == 0 and any(r.success for r in step_results)

        # Sprawdź czy są ostrzeżenia
        if len(step_results) > 0 and not all(r.success for r in step_results):
            warnings.append("Some steps failed but execution continued")

        execution_result = ExecutionResult(
            plan=plan,
            step_results=step_results,
            success=success,
            final_result=final_result,
            total_execution_time=total_execution_time,
            errors=errors,
            warnings=warnings,
        )

        logger.info(
            f"Plan execution completed in {total_execution_time:.2f}s, success: {success}"
        )
        return execution_result

    async def _execute_step(
        self,
        step: PlanStep,
        context: dict[str, Any] | None,
        previous_results: list[StepResult],
    ) -> StepResult:
        """Wykonaj pojedynczy krok planu"""
        step_start_time = asyncio.get_event_loop().time()

        try:
            if step.tool == "general_conversation":
                # Specjalne traktowanie dla general_conversation_agent
                result = await self._execute_general_conversation(
                    step, context, previous_results
                )
            else:
                # Wykonaj narzędzie z rejestru
                result = await self._execute_tool(step, context, previous_results)

            execution_time = asyncio.get_event_loop().time() - step_start_time

            return StepResult(
                step=step,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"tool_type": step.tool},
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - step_start_time
            logger.error(f"Error executing step {step.step}: {e}")

            return StepResult(
                step=step,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"tool_type": step.tool, "error_type": type(e).__name__},
            )

    async def _execute_tool(
        self,
        step: PlanStep,
        context: dict[str, Any] | None,
        previous_results: list[StepResult],
    ) -> Any:
        """Wykonaj narzędzie z rejestru"""
        tool_def = self.tool_registry.get_tool(step.tool)
        if not tool_def:
            raise ValueError(f"Tool {step.tool} not found in registry")

        # Przygotuj argumenty, uwzględniając wyniki poprzednich kroków
        args = self._prepare_step_args(step.args, context, previous_results)

        # Sprawdź, jakie argumenty przyjmuje funkcja narzędzia
        import inspect

        sig = inspect.signature(tool_def.function)
        valid_args = {}

        for param_name, param_value in args.items():
            if param_name in sig.parameters:
                valid_args[param_name] = param_value
            else:
                logger.debug(
                    f"Tool {step.tool} does not accept parameter '{param_name}', skipping"
                )

        logger.debug(f"Executing tool {step.tool} with args: {valid_args}")

        # Wykonaj narzędzie
        if asyncio.iscoroutinefunction(tool_def.function):
            result = await tool_def.function(**valid_args)
        else:
            result = tool_def.function(**valid_args)

        logger.debug(f"Tool {step.tool} returned: {result}")
        return result

    async def _execute_general_conversation(
        self,
        step: PlanStep,
        context: dict[str, Any] | None,
        previous_results: list[StepResult],
    ) -> Any:
        """Wykonaj general_conversation_agent"""
        # Przygotuj dane wejściowe dla agenta
        # Użyj 'message' z args, jeśli jest dostępne, w przeciwnym razie użyj 'query'
        message = step.args.get("message", step.args.get("query", ""))

        if not message:
            # Jeśli nie ma wiadomości, spróbuj użyć kontekstu
            if context and "query" in context:
                message = context["query"]
            else:
                raise Exception(
                    "General conversation agent failed: No query provided in input_data"
                )

        # Przygotuj kontekst z poprzednich kroków
        conversation_context = []
        for i, result in enumerate(previous_results):
            if result.success and result.result:
                conversation_context.append(f"Step {i + 1} result: {result.result}")

        input_data = {
            "query": message,
            "context": context or {},
            "previous_results": [r.result for r in previous_results if r.success],
            "conversation_context": (
                "\n".join(conversation_context) if conversation_context else None
            ),
        }

        logger.debug(f"General conversation input: {input_data}")

        # Wywołaj agenta
        response = await self.general_conversation_agent.process(input_data)

        if response.success:
            return response.text or response.data
        raise Exception(f"General conversation agent failed: {response.error}")

    def _prepare_step_args(
        self,
        step_args: dict[str, Any],
        context: dict[str, Any] | None,
        previous_results: list[StepResult],
    ) -> dict[str, Any]:
        """Przygotuj argumenty kroku, uwzględniając kontekst i poprzednie wyniki"""
        args = step_args.copy()

        # Dodaj kontekst jeśli jest dostępny
        if context:
            args["context"] = context

        # Dodaj wyniki poprzednich kroków (tylko jeśli narzędzie je obsługuje)
        if previous_results:
            args["previous_results"] = [r.result for r in previous_results if r.success]

        # Dodaj szczegółowe wyniki poprzednich kroków
        for i, result in enumerate(previous_results):
            if result.success and result.result:
                args[f"step_{i + 1}_result"] = result.result
                args[f"step_{i + 1}_success"] = result.success
                args[f"step_{i + 1}_execution_time"] = result.execution_time

        # Dodaj kontekst wykonania
        args["execution_context"] = self._execution_context

        return args

    def _determine_final_result(
        self, step_results: list[StepResult], plan: ExecutionPlan
    ) -> Any:
        """Określ końcowy wynik na podstawie wyników kroków"""
        if not step_results:
            return None

        # Jeśli jest tylko jeden krok, zwróć jego wynik
        if len(step_results) == 1:
            return step_results[0].result

        # Jeśli wszystkie kroki się powiodły, zwróć ostatni wynik
        successful_results = [r for r in step_results if r.success]
        if len(successful_results) == len(step_results):
            return successful_results[-1].result

        # Jeśli niektóre kroki się nie powiodły, zwróć kombinację wyników
        results = [r.result for r in successful_results if r.result is not None]
        if results:
            return results

        return None

    def _summarize_result(self, result: Any) -> str:
        """Utwórz podsumowanie wyniku dla streamingu"""
        if result is None:
            return "No result"

        if isinstance(result, str):
            return result[:100] + "..." if len(result) > 100 else result

        if isinstance(result, list | dict):
            return f"{type(result).__name__} with {len(result)} items"

        return str(result)[:100] + "..." if len(str(result)) > 100 else str(result)

    def _send_stream_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Wyślij zdarzenie przez stream callback"""
        if self._stream_callback:
            try:
                event_data = {
                    "type": event_type,
                    "timestamp": asyncio.get_event_loop().time(),
                    **data,
                }
                self._stream_callback(event_data)
            except Exception as e:
                logger.warning(f"Error sending stream event: {e}")

    def get_execution_summary(self, result: ExecutionResult) -> str:
        """Pobierz podsumowanie wykonania"""
        summary = f"Wykonanie planu: '{result.plan.query}'\n"
        summary += f"Czas wykonania: {result.total_execution_time:.2f}s\n"
        summary += f"Status: {'SUKCES' if result.success else 'BŁĄD'}\n"
        summary += f"Kroki: {len([r for r in result.step_results if r.success])}/{len(result.step_results)} udane\n\n"

        for i, step_result in enumerate(result.step_results):
            status = "✓" if step_result.success else "✗"
            summary += f"{status} Krok {i + 1}: {step_result.step.description}\n"
            if not step_result.success:
                summary += f"   Błąd: {step_result.error}\n"
            summary += f"   Czas: {step_result.execution_time:.2f}s\n\n"

        if result.errors:
            summary += "Błędy:\n"
            for error in result.errors:
                summary += f"- {error}\n"

        if result.warnings:
            summary += "Ostrzeżenia:\n"
            for warning in result.warnings:
                summary += f"- {warning}\n"

        return summary
