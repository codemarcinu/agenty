"""
Recipe Generation Module

Moduł do generowania przepisów dla ChefAgent.
"""

import logging
from typing import Any

from agents.interfaces import AgentResponse
from core.anti_hallucination_system import ValidationLevel
from core.llm_client import llm_client

logger = logging.getLogger(__name__)


class RecipeGenerator:
    """Generator przepisów kulinarnych"""

    @staticmethod
    async def generate_recipe_with_validation(
        ingredients: list[str],
        dietary_restrictions: str | None = None,
        model: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        validation_level: ValidationLevel = ValidationLevel.STRICT,
        max_additional_ingredients: int = 3,
        user_context: dict | None = None,
        ingredient_availability: dict | None = None,
        validator: Any = None,
    ) -> AgentResponse:
        """
        Generate recipe with comprehensive anti-hallucination validation
        """
        if not ingredients:
            return AgentResponse(
                success=False,
                error="No ingredients provided",
                text="Proszę podać składniki",
            )

        try:
            from .prompt_builders import PromptBuilder

            # Przygotuj prompt z zaawansowanymi anty-halucynacyjnymi instrukcjami
            prompt = PromptBuilder.create_anti_hallucination_prompt(
                ingredients,
                dietary_restrictions,
                validation_level,
                user_context,
                ingredient_availability,
            )

            # Generuj przepis
            response = await llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": PromptBuilder.get_system_prompt(validation_level),
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )

            # Stream the response chunks with proper validation
            full_response = ""
            async for chunk in response:
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

            # ANTY-HALUCYNACYJNA WALIDACJA PO WYGENEROWANIU
            if full_response and validator:
                validation_result = validator.validate_recipe_against_ingredients(
                    full_response,
                    ingredients,
                    validation_level,
                    max_additional_ingredients,
                )

                if not validation_result.is_valid:
                    logger.warning(
                        f"Recipe validation failed: {validation_result.recommendation}"
                    )

                    # Generate safe fallback response
                    safe_response = RecipeGenerator._generate_safe_fallback_recipe(
                        ingredients, dietary_restrictions
                    )

                    return AgentResponse(
                        success=True,
                        text=safe_response,
                        data={
                            "ingredients": ingredients,
                            "dietary_restrictions": dietary_restrictions,
                            "validation_failed": True,
                            "validation_result": validation_result.__dict__,
                            "anti_hallucination": True,
                            "confidence": validation_result.confidence,
                        },
                    )

                # Recipe passed validation
                return AgentResponse(
                    success=True,
                    text=full_response,
                    data={
                        "ingredients": ingredients,
                        "dietary_restrictions": dietary_restrictions,
                        "validation_passed": True,
                        "validation_result": validation_result.__dict__,
                        "anti_hallucination": True,
                        "confidence": validation_result.confidence,
                    },
                )

            # If no response was generated, return error
            return AgentResponse(
                success=False,
                error="No recipe generated",
                text="Przepraszam, nie udało się wygenerować przepisu. Spróbuj ponownie.",
            )

        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd generowania przepisu: {e}",
                text="Przepraszam, nie udało się wygenerować przepisu. Spróbuj ponownie.",
            )

    @staticmethod
    async def generate_recipe_idea(
        db: Any, model: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", validator: Any = None
    ) -> AgentResponse:
        """
        Generates recipe ideas based on available pantry items with
        anti-hallucination protection.
        """
        from agents.tools.tools import get_available_products_from_pantry

        # Get available products from pantry
        products = await get_available_products_from_pantry(db)

        if not products:
            return AgentResponse(
                success=True,
                text="Twoja spiżarnia jest pusta!",
                message="Pantry is empty",
            )

        # Prepare list of available products for the prompt
        product_list = "\n".join(
            f"- {product.name} (ID: {product.id})" for product in products
        )

        # Create LLM prompt with anti-hallucination instructions
        prompt = (
            "Mam następujące produkty w spiżarni:\n"
            f"{product_list}\n\n"
            "Proszę zaproponuj prosty przepis wykorzystujący TYLKO te produkty. "
            "NIE dodawaj żadnych dodatkowych składników.\n"
            "Odpowiedz w formacie:\n"
            "PRZEPIS: [treść przepisu]\n"
            "UŻYTE SKŁADNIKI: [lista nazw użytych składników]"
        )

        try:
            # Call LLM with specified model and get the response
            full_response = ""
            async for chunk in await llm_client.generate_stream(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym szefem kuchni. Używaj TYLKO podanych składników.",
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

            # After streaming, validate the response
            if full_response and validator:
                validation_result = validator.validate_recipe_against_ingredients(
                    full_response, [p.name for p in products], ValidationLevel.STRICT
                )

                if not validation_result.is_valid:
                    logger.warning(
                        f"Recipe idea validation failed: {validation_result.recommendation}"
                    )
                    # Generate safe fallback
                    safe_idea = RecipeGenerator._generate_safe_recipe_idea(products)
                    full_response = (
                        f"{full_response}\n\n[UWAGA: Poprawiony przepis]\n{safe_idea}"
                    )

            # Parse the full response to extract used ingredients
            used_ingredients = []
            if "UŻYTE SKŁADNIKI:" in full_response:
                parts = full_response.split("UŻYTE SKŁADNIKI:")
                ingredient_names = [
                    name.strip() for name in parts[1].split(",") if name.strip()
                ]
                used_ingredients = [
                    {"id": p.id, "name": p.name}
                    for p in products
                    if p.name in ingredient_names
                ]
            logger.info(f"Used ingredients identified: {used_ingredients}")

            return AgentResponse(
                success=True,
                text=full_response,
                message="Recipe generated successfully.",
                data={
                    "used_ingredients": used_ingredients,
                    "validation_result": (
                        validation_result.__dict__
                        if "validation_result" in locals()
                        else None
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Error in recipe idea generation: {e}")
            return AgentResponse(
                success=False, error=str(e), text=f"Przepraszam, wystąpił błąd: {e!s}"
            )

    @staticmethod
    def _generate_safe_fallback_recipe(
        ingredients: list[str], dietary_restrictions: str | None
    ) -> str:
        """Generate a safe fallback recipe when validation fails"""

        fallback = f"""Przepis z dostępnych składników:

SKŁADNIKI: {', '.join(ingredients)}

PRZYGOTOWANIE:
1. Przygotuj wszystkie dostępne składniki
2. Możesz je ugotować, upiec lub usmażyć według własnych preferencji
3. Użyj podstawowych przypraw (sól, pieprz) jeśli dostępne
4. Skup się na prostocie i smaku

{f"UWAGA DIETETYCZNA: {dietary_restrictions}" if dietary_restrictions else ""}

To bezpieczny przepis wykorzystujący tylko podane składniki."""

        return fallback

    @staticmethod
    def _generate_safe_recipe_idea(products: list[Any]) -> str:
        """Generate a safe recipe idea when validation fails"""
        product_names = [p.name for p in products]

        return f"""Bezpieczny przepis z dostępnych składników:

SKŁADNIKI: {', '.join(product_names)}

PRZYGOTOWANIE:
1. Przygotuj wszystkie dostępne składniki
2. Możesz je ugotować, upiec lub usmażyć
3. Użyj podstawowych przypraw jeśli dostępne
4. Skup się na prostocie i smaku

To przepis wykorzystujący tylko podane składniki."""