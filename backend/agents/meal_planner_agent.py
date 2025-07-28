from collections.abc import AsyncGenerator
import json
import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from agents.prompts import get_meal_plan_prompt
from agents.utils import extract_json_from_text
from core.anti_hallucination_decorator import (
    AntiHallucinationConfig,
    with_anti_hallucination,
)
from core.anti_hallucination_system import ValidationLevel
from core.crud import get_available_products
from core.llm_client import llm_client

logger = logging.getLogger(__name__)


class MealPlannerAgent(BaseAgent):
    def __init__(
        self,
        name: str = "MealPlannerAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )

    @with_anti_hallucination(
        AntiHallucinationConfig(
            validation_level=ValidationLevel.MODERATE,
            ingredient_extractor=lambda data: [
                p.get("name", "") for p in data.get("available_products", [])
            ],
            log_validation=True,
        )
    )
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        try:
            db = input_data["db"]
            available_products = await get_available_products(db)

            # Sprawdź flagę use_bielik
            use_bielik = input_data.get("use_bielik", True)
            model = (
                "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
                if use_bielik
                else "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
            )

            products_list = []
            for p in available_products:
                if hasattr(p, "name"):
                    products_list.append(
                        {"name": p.name, "quantity": getattr(p, "quantity", 1)}
                    )
                elif isinstance(p, dict) and "name" in p:
                    products_list.append(
                        {"name": p["name"], "quantity": p.get("quantity", 1)}
                    )
                else:
                    continue

            prompt = get_meal_plan_prompt(products_list)

            async def response_generator() -> AsyncGenerator[str, None]:
                full_response = ""
                try:
                    async for chunk in llm_client.generate_stream(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful meal planning assistant.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                    ):
                        # Validate chunk structure
                        if not isinstance(chunk, dict):
                            logger.warning(f"Invalid chunk type: {type(chunk)}")
                            continue

                        if "message" not in chunk:
                            logger.warning(f"Chunk missing 'message' key: {chunk}")
                            continue

                        message = chunk["message"]
                        if not isinstance(message, dict) or "content" not in message:
                            logger.warning(f"Invalid message structure: {message}")
                            continue

                        content = message["content"]
                        if not isinstance(content, str):
                            logger.warning(f"Invalid content type: {type(content)}")
                            continue

                        full_response += content
                        yield content

                    # After streaming, parse the full_response to extract
                    # structured data
                    json_str = extract_json_from_text(full_response)
                    if json_str:
                        parsed_data = json.loads(json_str)
                        logger.debug(f"Meal plan data extracted: {parsed_data}")
                    else:
                        logger.warning("No valid JSON found in meal plan response")
                except Exception as e:
                    logger.error(f"Error in meal plan streaming: {e}", exc_info=True)
                    yield "Wystąpił błąd podczas generowania planu posiłków."

            return AgentResponse(
                success=True,
                text_stream=response_generator(),
                message="Meal plan stream started.",
            )
        except Exception as e:
            logger.error(f"Error in meal planner process: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                text="Wystąpił błąd podczas planowania posiłków.",
            )
