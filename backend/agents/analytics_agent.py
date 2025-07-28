from typing import Any

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.anti_hallucination_decorator_optimized import with_agent_specific_validation
from core.anti_hallucination_system import ValidationLevel
from core.crud import get_summary


class AnalyticsAgent(BaseAgent):
    def __init__(
        self,
        name: str = "AnalyticsAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )

    @with_agent_specific_validation(
        agent_type="analytics",
        validation_level=ValidationLevel.MODERATE
    )
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        db = input_data["db"]
        query_params = input_data["query_params"]

        summary = await get_summary(db, query_params)

        return AgentResponse(
            text="Analytics generated.",
            data={"summary": summary},
            success=True,
        )
