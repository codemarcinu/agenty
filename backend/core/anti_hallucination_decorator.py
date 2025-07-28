"""
Anti-Hallucination Decorator for Agents

This module provides a decorator that can be used to add anti-hallucination
validation to any agent method that generates responses.
"""

from collections.abc import Callable
from dataclasses import dataclass
import functools
import logging

from agents.interfaces import AgentResponse
from core.anti_hallucination_system import (
    AGENT_VALIDATION_LEVELS,
    ValidationLevel,
    ValidationResult,
    anti_hallucination_system,
)

logger = logging.getLogger(__name__)


@dataclass
class AntiHallucinationConfig:
    """Configuration for anti-hallucination decorator"""

    enabled: bool = True
    validation_level: ValidationLevel = ValidationLevel.STRICT
    context_extractor: Callable | None = None
    ingredient_extractor: Callable | None = None
    fallback_response: str | None = None
    log_validation: bool = True
    raise_on_high_hallucination: bool = False
    high_hallucination_threshold: float = 0.8


def with_anti_hallucination(config: AntiHallucinationConfig | None = None):
    """
    Decorator that adds anti-hallucination validation to agent methods.

    Usage:
        @with_anti_hallucination()
        async def process(self, input_data: dict[str, Any]) -> AgentResponse:
            # Your agent logic here
            return AgentResponse(...)

    Or with custom config:
        @with_anti_hallucination(AntiHallucinationConfig(
            validation_level=ValidationLevel.MODERATE,
            log_validation=True
        ))
        async def process(self, input_data: dict[str, Any]) -> AgentResponse:
            # Your agent logic here
            return AgentResponse(...)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get configuration
            decorator_config = config or AntiHallucinationConfig()

            if not decorator_config.enabled:
                return await func(self, *args, **kwargs)

            # Extract context from input data
            context = ""
            available_ingredients = None

            # Try to extract context from first argument (usually input_data)
            if args and isinstance(args[0], dict):
                input_data = args[0]
                context = input_data.get("query", input_data.get("message", ""))

                # Extract ingredients if available
                if decorator_config.ingredient_extractor:
                    available_ingredients = decorator_config.ingredient_extractor(
                        input_data
                    )
                else:
                    # Default ingredient extraction
                    available_ingredients = input_data.get("available_ingredients")

            # Call the original function
            try:
                result = await func(self, *args, **kwargs)

                # Validate the response
                if isinstance(result, AgentResponse) and result.success and result.text:
                    # Auto-select validation level if not specified
                    validation_level = decorator_config.validation_level
                    if (
                        validation_level == ValidationLevel.STRICT
                        and not decorator_config.validation_level
                    ):
                        agent_name = getattr(self, "name", self.__class__.__name__)
                        agent_type = (
                            agent_name.lower().replace("agent", "").replace("_", "")
                        )
                        level_str = AGENT_VALIDATION_LEVELS.get(agent_type, "moderate")
                        validation_level = ValidationLevel(level_str)

                    validation_result = (
                        await anti_hallucination_system.validate_response(
                            response=result.text,
                            context=context,
                            agent_name=getattr(self, "name", self.__class__.__name__),
                            model_used=kwargs.get("model", "unknown"),
                            validation_level=validation_level,
                            available_ingredients=available_ingredients,
                        )
                    )

                    # Log validation results
                    if decorator_config.log_validation:
                        logger.info(
                            f"Anti-hallucination validation for {self.__class__.__name__}: "
                            f"confidence={validation_result.confidence:.2f}, "
                            f"hallucination_score={validation_result.hallucination_score:.2f}, "
                            f"is_valid={validation_result.is_valid}"
                        )

                    # Handle high hallucination
                    if (
                        validation_result.hallucination_score
                        > decorator_config.high_hallucination_threshold
                    ):
                        if decorator_config.raise_on_high_hallucination:
                            raise ValueError(
                                f"High hallucination detected: {validation_result.recommendation}"
                            )
                        else:
                            logger.warning(
                                f"High hallucination detected in {self.__class__.__name__}: "
                                f"{validation_result.recommendation}"
                            )

                    # If validation failed, generate fallback response
                    if not validation_result.is_valid:
                        if decorator_config.fallback_response:
                            result.text = decorator_config.fallback_response
                        else:
                            # Generate safe fallback based on validation result
                            result.text = _generate_safe_fallback(
                                validation_result, context, available_ingredients
                            )

                        # Add validation info to response data
                        if not result.data:
                            result.data = {}
                        result.data.update(
                            {
                                "anti_hallucination": {
                                    "validation_failed": True,
                                    "confidence": validation_result.confidence,
                                    "hallucination_score": validation_result.hallucination_score,
                                    "detected_hallucinations": [
                                        h.value
                                        for h in validation_result.detected_hallucinations
                                    ],
                                    "recommendation": validation_result.recommendation,
                                }
                            }
                        )
                    else:
                        # Add validation info to response data
                        if not result.data:
                            result.data = {}
                        result.data.update(
                            {
                                "anti_hallucination": {
                                    "validation_passed": True,
                                    "confidence": validation_result.confidence,
                                    "hallucination_score": validation_result.hallucination_score,
                                }
                            }
                        )

                return result

            except Exception as e:
                logger.error(f"Error in anti-hallucination decorator: {e}")
                # Re-raise the exception
                raise

        return wrapper

    return decorator


def _generate_safe_fallback(
    validation_result: ValidationResult,
    context: str,
    available_ingredients: list[str] | None,
) -> str:
    """Generate a safe fallback response when validation fails"""

    if validation_result.detected_hallucinations:
        hallucination_types = [
            h.value for h in validation_result.detected_hallucinations
        ]

        if "ingredient_hallucination" in hallucination_types and available_ingredients:
            return (
                f"Przepis z dostępnych składników:\n\n"
                f"SKŁADNIKI: {', '.join(available_ingredients)}\n\n"
                f"PRZYGOTOWANIE:\n"
                f"1. Przygotuj wszystkie dostępne składniki\n"
                f"2. Możesz je ugotować, upiec lub usmażyć według własnych preferencji\n"
                f"3. Użyj podstawowych przypraw (sól, pieprz) jeśli dostępne\n"
                f"4. Skup się na prostocie i smaku\n\n"
                f"To bezpieczny przepis wykorzystujący tylko podane składniki."
            )

        elif "factual_error" in hallucination_types:
            return (
                "Przepraszam, nie mogę potwierdzić wszystkich informacji w mojej odpowiedzi. "
                "Zalecam sprawdzenie faktów z wiarygodnych źródeł."
            )

        elif "context_violation" in hallucination_types:
            return (
                "Przepraszam, moja odpowiedź może nie być w pełni zgodna z kontekstem. "
                "Proszę sprecyzować pytanie."
            )

    # Generic fallback
    return (
        "Przepraszam, wykryto potencjalne błędy w mojej odpowiedzi. "
        "Zalecam sprawdzenie informacji z wiarygodnych źródeł."
    )


def validate_ingredients(
    available_ingredients: list[str],
    validation_level: ValidationLevel = ValidationLevel.STRICT,
):
    """
    Decorator specifically for recipe agents that validates ingredients.

    Usage:
        @validate_ingredients(["makaron", "pomidory"], ValidationLevel.STRICT)
        async def generate_recipe(self, input_data: dict[str, Any]) -> AgentResponse:
            # Your recipe generation logic
            return AgentResponse(...)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Add ingredients to input data
            if args and isinstance(args[0], dict):
                input_data = args[0]
                input_data["available_ingredients"] = available_ingredients
                input_data["validation_level"] = validation_level

            # Use anti-hallucination decorator with ingredient validation
            config = AntiHallucinationConfig(
                validation_level=validation_level,
                ingredient_extractor=lambda data: available_ingredients,
            )

            decorated_func = with_anti_hallucination(config)(func)
            return await decorated_func(self, *args, **kwargs)

        return wrapper

    return decorator


def validate_context(
    context_extractor: Callable,
    validation_level: ValidationLevel = ValidationLevel.STRICT,
):
    """
    Decorator for agents that need context validation.

    Usage:
        @validate_context(lambda data: data.get("query", ""), ValidationLevel.STRICT)
        async def process(self, input_data: dict[str, Any]) -> AgentResponse:
            # Your agent logic
            return AgentResponse(...)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Use anti-hallucination decorator with context extraction
            config = AntiHallucinationConfig(
                validation_level=validation_level, context_extractor=context_extractor
            )

            decorated_func = with_anti_hallucination(config)(func)
            return await decorated_func(self, *args, **kwargs)

        return wrapper

    return decorator
