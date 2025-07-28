"""
Optimized Anti-Hallucination Decorator with Specialized Validators

This module provides an optimized decorator that uses agent-specific
validators for better accuracy and performance.
"""

from collections.abc import Callable
from dataclasses import dataclass
import functools
import logging
from typing import Any

from agents.interfaces import AgentResponse
from core.anti_hallucination_system_optimized import (
    ValidationLevel,
    ValidationResult,
    optimized_anti_hallucination_system,
)
from core.agent_specific_config import get_agent_config

logger = logging.getLogger(__name__)


@dataclass
class OptimizedAntiHallucinationConfig:
    """Configuration for optimized anti-hallucination decorator"""
    
    enabled: bool = True
    validation_level: ValidationLevel | None = None  # Auto-detect if None
    context_extractor: Callable | None = None
    ingredient_extractor: Callable | None = None
    fallback_response: str | None = None
    log_validation: bool = True
    raise_on_high_hallucination: bool = False
    high_hallucination_threshold: float = 0.8
    use_specialized_validator: bool = True
    cache_enabled: bool = True
    timeout_seconds: float = 10.0


def with_optimized_anti_hallucination(
    config: OptimizedAntiHallucinationConfig | None = None
):
    """
    Optimized decorator that adds anti-hallucination validation to agent methods.
    
    Uses specialized validators for different agent types and provides
    better performance and accuracy.
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get configuration
            decorator_config = config or OptimizedAntiHallucinationConfig()
            
            if not decorator_config.enabled:
                return await func(self, *args, **kwargs)
            
            # Extract context and ingredients
            context = ""
            available_ingredients = None
            
            if decorator_config.context_extractor:
                context = decorator_config.context_extractor(self, *args, **kwargs)
            else:
                # Default context extraction
                if args and isinstance(args[0], dict):
                    context = str(args[0])
                elif kwargs:
                    context = str(kwargs)
            
            if decorator_config.ingredient_extractor:
                available_ingredients = decorator_config.ingredient_extractor(
                    self, *args, **kwargs
                )
            else:
                # Default ingredient extraction
                if args and isinstance(args[0], dict):
                    available_ingredients = args[0].get("available_ingredients")
                elif kwargs:
                    available_ingredients = kwargs.get("available_ingredients")
            
            # Call the original function
            try:
                result = await func(self, *args, **kwargs)
                
                # Validate the response
                if isinstance(result, AgentResponse) and result.success and result.text:
                    # Auto-detect agent type and validation level
                    agent_name = getattr(self, "name", self.__class__.__name__)
                    agent_type = agent_name.lower().replace("agent", "").replace("_", "")
                    
                    # Get agent-specific configuration
                    agent_config = get_agent_config(agent_type)
                    
                    # Use agent-specific validation level if not specified
                    validation_level = decorator_config.validation_level
                    if validation_level is None:
                        validation_level = agent_config.validation_level
                    
                    # Perform validation with specialized validator
                    validation_result = (
                        await optimized_anti_hallucination_system.validate_response(
                            response=result.text,
                            context=context,
                            agent_name=agent_name,
                            model_used=kwargs.get("model", "unknown"),
                            validation_level=validation_level,
                            available_ingredients=available_ingredients,
                            agent_type=agent_type,
                            **kwargs
                        )
                    )
                    
                    # Log validation results if enabled
                    if decorator_config.log_validation or agent_config.log_validation:
                        logger.info(
                            f"Optimized anti-hallucination validation for {agent_name}: "
                            f"confidence={validation_result.confidence:.2f}, "
                            f"hallucination_score={validation_result.hallucination_score:.2f}, "
                            f"is_valid={validation_result.is_valid}"
                        )
                    
                    # Handle high hallucination detection
                    if (decorator_config.raise_on_high_hallucination and 
                        validation_result.hallucination_score > decorator_config.high_hallucination_threshold):
                        logger.warning(
                            f"High hallucination detected for {agent_name}: "
                            f"{validation_result.hallucination_score:.2f}"
                        )
                        
                        if decorator_config.fallback_response:
                            result.text = decorator_config.fallback_response
                            result.confidence = 0.0
                            result.metadata = result.metadata or {}
                            result.metadata["hallucination_detected"] = True
                            result.metadata["original_confidence"] = validation_result.confidence
                            result.metadata["hallucination_score"] = validation_result.hallucination_score
                    
                    # Add validation metadata to response
                    if result.metadata is None:
                        result.metadata = {}
                    
                    result.metadata.update({
                        "anti_hallucination_validation": {
                            "is_valid": validation_result.is_valid,
                            "confidence": validation_result.confidence,
                            "hallucination_score": validation_result.hallucination_score,
                            "detected_hallucinations": [
                                h.value for h in validation_result.detected_hallucinations
                            ],
                            "suspicious_phrases": validation_result.suspicious_phrases,
                            "validation_errors": validation_result.validation_errors,
                            "recommendation": validation_result.recommendation,
                            "agent_type": agent_type,
                            "validation_level": validation_level.value,
                        }
                    })
                    
                    # Update response confidence if validation failed
                    if not validation_result.is_valid:
                        result.confidence = min(result.confidence or 1.0, validation_result.confidence)
                        result.warnings = result.warnings or []
                        result.warnings.append(
                            f"Anti-hallucination validation failed: {validation_result.recommendation}"
                        )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in optimized anti-hallucination decorator: {e}")
                # Return original result on error
                return await func(self, *args, **kwargs)
        
        return wrapper
    
    return decorator


def with_agent_specific_validation(
    agent_type: str | None = None,
    validation_level: ValidationLevel | None = None,
    **kwargs: Any
):
    """
    Decorator that automatically uses agent-specific validation configuration.
    
    Args:
        agent_type: Specific agent type (auto-detected if None)
        validation_level: Override validation level (uses agent-specific if None)
        **kwargs: Additional configuration options
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs_inner):
            # Auto-detect agent type if not specified
            detected_agent_type = agent_type
            if detected_agent_type is None:
                agent_name = getattr(self, "name", self.__class__.__name__)
                detected_agent_type = agent_name.lower().replace("agent", "").replace("_", "")
            
            # Get agent-specific configuration
            agent_config = get_agent_config(detected_agent_type)
            
            # Create optimized config
            config = OptimizedAntiHallucinationConfig(
                validation_level=validation_level or agent_config.validation_level,
                log_validation=agent_config.log_validation,
                raise_on_high_hallucination=agent_config.raise_on_high_hallucination,
                high_hallucination_threshold=agent_config.high_hallucination_threshold,
                **kwargs
            )
            
            # Use the optimized decorator
            decorated_func = with_optimized_anti_hallucination(config)(func)
            return await decorated_func(self, *args, **kwargs_inner)
        
        return wrapper
    
    return decorator


def with_chef_validation(
    available_ingredients: list[str] | None = None,
    validation_level: ValidationLevel = ValidationLevel.STRICT,
    **kwargs: Any
):
    """
    Specialized decorator for ChefAgent with ingredient validation.
    
    Args:
        available_ingredients: List of available ingredients
        validation_level: Validation strictness level
        **kwargs: Additional configuration options
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs_inner):
            # Extract ingredients from input if not provided
            ingredients = available_ingredients
            if ingredients is None and args and isinstance(args[0], dict):
                ingredients = args[0].get("available_ingredients", [])
            
            # Create specialized config for chef
            config = OptimizedAntiHallucinationConfig(
                validation_level=validation_level,
                ingredient_extractor=lambda self, *args, **kwargs: ingredients,
                log_validation=True,
                raise_on_high_hallucination=True,
                high_hallucination_threshold=0.8,
                **kwargs
            )
            
            # Use the optimized decorator
            decorated_func = with_optimized_anti_hallucination(config)(func)
            return await decorated_func(self, *args, **kwargs_inner)
        
        return wrapper
    
    return decorator


def with_receipt_validation(
    validation_level: ValidationLevel = ValidationLevel.STRICT,
    **kwargs: Any
):
    """
    Specialized decorator for receipt analysis agents.
    
    Args:
        validation_level: Validation strictness level
        **kwargs: Additional configuration options
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs_inner):
            # Create specialized config for receipt analysis
            config = OptimizedAntiHallucinationConfig(
                validation_level=validation_level,
                log_validation=True,
                raise_on_high_hallucination=True,
                high_hallucination_threshold=0.7,
                **kwargs
            )
            
            # Use the optimized decorator
            decorated_func = with_optimized_anti_hallucination(config)(func)
            return await decorated_func(self, *args, **kwargs_inner)
        
        return wrapper
    
    return decorator


def with_weather_validation(
    validation_level: ValidationLevel = ValidationLevel.LENIENT,
    **kwargs: Any
):
    """
    Specialized decorator for weather agents with lenient validation.
    
    Args:
        validation_level: Validation strictness level (default: LENIENT)
        **kwargs: Additional configuration options
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs_inner):
            # Create specialized config for weather
            config = OptimizedAntiHallucinationConfig(
                validation_level=validation_level,
                log_validation=False,
                raise_on_high_hallucination=False,
                high_hallucination_threshold=0.9,
                **kwargs
            )
            
            # Use the optimized decorator
            decorated_func = with_optimized_anti_hallucination(config)(func)
            return await decorated_func(self, *args, **kwargs_inner)
        
        return wrapper
    
    return decorator


def with_search_validation(
    validation_level: ValidationLevel = ValidationLevel.MODERATE,
    **kwargs: Any
):
    """
    Specialized decorator for search agents.
    
    Args:
        validation_level: Validation strictness level
        **kwargs: Additional configuration options
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs_inner):
            # Create specialized config for search
            config = OptimizedAntiHallucinationConfig(
                validation_level=validation_level,
                log_validation=True,
                raise_on_high_hallucination=False,
                high_hallucination_threshold=0.8,
                **kwargs
            )
            
            # Use the optimized decorator
            decorated_func = with_optimized_anti_hallucination(config)(func)
            return await decorated_func(self, *args, **kwargs_inner)
        
        return wrapper
    
    return decorator


def with_general_validation(
    validation_level: ValidationLevel = ValidationLevel.LENIENT,
    **kwargs: Any
):
    """
    Specialized decorator for general conversation agents.
    
    Args:
        validation_level: Validation strictness level (default: LENIENT)
        **kwargs: Additional configuration options
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs_inner):
            # Create specialized config for general conversation
            config = OptimizedAntiHallucinationConfig(
                validation_level=validation_level,
                log_validation=False,
                raise_on_high_hallucination=False,
                high_hallucination_threshold=0.9,
                **kwargs
            )
            
            # Use the optimized decorator
            decorated_func = with_optimized_anti_hallucination(config)(func)
            return await decorated_func(self, *args, **kwargs_inner)
        
        return wrapper
    
    return decorator


# Convenience functions for common agent types
def with_strict_validation(**kwargs: Any):
    """Decorator for strict validation (chef, receipt analysis)"""
    return with_agent_specific_validation(validation_level=ValidationLevel.STRICT, **kwargs)


def with_moderate_validation(**kwargs: Any):
    """Decorator for moderate validation (search, analytics)"""
    return with_agent_specific_validation(validation_level=ValidationLevel.MODERATE, **kwargs)


def with_lenient_validation(**kwargs: Any):
    """Decorator for lenient validation (weather, general conversation)"""
    return with_agent_specific_validation(validation_level=ValidationLevel.LENIENT, **kwargs) 