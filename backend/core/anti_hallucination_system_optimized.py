"""
Optimized Anti-Hallucination System with Specialized Validators

This module provides an optimized anti-hallucination system that uses
agent-specific validators for better accuracy and performance.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from core.anti_hallucination_system import (
    HallucinationType,
    ValidationLevel,
    ValidationResult,
)
from core.specialized_validators import ValidatorFactory
from core.agent_specific_config import get_agent_config

logger = logging.getLogger(__name__)


class OptimizedValidationCache:
    """Optimized cache for validation results with agent-specific TTL"""

    def __init__(self, max_size: int = 2000, default_ttl_minutes: int = 30):
        self.cache = {}
        self.max_size = max_size
        self.default_ttl = timedelta(minutes=default_ttl_minutes)

    def _generate_key(self, response: str, context: str, agent_name: str) -> str:
        """Generate cache key from response content"""
        content = f"{response}:{context}:{agent_name}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(
        self, response: str, context: str, agent_name: str
    ) -> Optional[ValidationResult]:
        """Get cached validation result"""
        key = self._generate_key(response, context, agent_name)
        if key in self.cache:
            result, timestamp, ttl = self.cache[key]
            if datetime.now() - timestamp < ttl:
                return result
            else:
                del self.cache[key]
        return None

    def set(
        self, 
        response: str, 
        context: str, 
        agent_name: str, 
        result: ValidationResult,
        ttl_minutes: Optional[int] = None
    ):
        """Cache validation result with agent-specific TTL"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        key = self._generate_key(response, context, agent_name)
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
        self.cache[key] = (result, datetime.now(), ttl)


class OptimizedAntiHallucinationSystem:
    """
    Optimized anti-hallucination system with specialized validators.
    
    This system provides:
    - Agent-specific validators for better accuracy
    - Optimized caching with agent-specific TTL
    - Parallel validation for better performance
    - Adaptive thresholds based on agent type
    """

    def __init__(self):
        # Initialize optimized cache
        self.cache = OptimizedValidationCache(max_size=2000, default_ttl_minutes=30)
        
        # Initialize validator factory
        self.validator_factory = ValidatorFactory()
        
        # Performance metrics
        self.metrics = {
            "total_validations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "validation_times": [],
            "agent_metrics": {},
        }
        
        logger.info("Optimized anti-hallucination system initialized")

    async def validate_response(
        self,
        response: str,
        context: str,
        agent_name: str,
        model_used: str,
        validation_level: Optional[ValidationLevel] = None,
        available_ingredients: Optional[List[str]] = None,
        agent_type: Optional[str] = None,
        **kwargs: Any,
    ) -> ValidationResult:
        """
        Optimized validation using agent-specific validators.
        
        Args:
            response: The AI response to validate
            context: The context/query that generated the response
            agent_name: Name of the agent that generated the response
            model_used: Model used to generate the response
            validation_level: How strict the validation should be
            available_ingredients: For recipe agents, list of available ingredients
            agent_type: Specific agent type for specialized validation
            **kwargs: Additional validation parameters
            
        Returns:
            ValidationResult with detailed validation information
        """
        start_time = datetime.now()
        
        # Auto-detect agent type if not provided
        if agent_type is None:
            agent_type = self._detect_agent_type(agent_name)
        
        # Get agent-specific configuration
        agent_config = get_agent_config(agent_type)
        
        # Check cache first
        cached_result = self.cache.get(response, context, agent_name)
        if cached_result:
            self.metrics["cache_hits"] += 1
            logger.debug(f"Cache hit for {agent_name} validation")
            return cached_result
        
        self.metrics["cache_misses"] += 1
        
        # Get specialized validator
        validator = self.validator_factory.get_validator(agent_type)
        
        # Use agent-specific validation level if not specified
        if validation_level is None:
            validation_level = agent_config.validation_level
        
        # Perform validation with specialized validator
        try:
            validation_result = await validator.validate(
                response=response,
                context=context,
                validation_level=validation_level,
                available_ingredients=available_ingredients,
                model_used=model_used,
                agent_name=agent_name,
                **kwargs
            )
            
            # Apply agent-specific thresholds
            validation_result = self._apply_agent_thresholds(
                validation_result, agent_config
            )
            
            # Cache the result with agent-specific TTL
            cache_ttl = agent_config.timeout_seconds / 60  # Convert to minutes
            self.cache.set(
                response, context, agent_name, validation_result, 
                ttl_minutes=int(cache_ttl)
            )
            
            # Update metrics
            self._update_metrics(agent_name, validation_result, start_time)
            
            # Log validation if enabled
            if agent_config.log_validation:
                self._log_validation_result(agent_name, validation_result)
            
            # Raise exception if high hallucination detected and configured
            if (agent_config.raise_on_high_hallucination and 
                validation_result.hallucination_score > agent_config.high_hallucination_threshold):
                raise ValueError(
                    f"High hallucination detected ({validation_result.hallucination_score:.2f}) "
                    f"for {agent_name}"
                )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Validation error for {agent_name}: {e}")
            # Return fallback validation result
            return self._create_fallback_result(agent_name, model_used, str(e))

    def _detect_agent_type(self, agent_name: str) -> str:
        """Detect agent type from agent name"""
        # Normalize agent name
        normalized_name = agent_name.lower().replace("agent", "").replace("_", "")
        
        # Common agent type mappings
        agent_mappings = {
            "chef": "chef",
            "receipt": "receipt_analysis",
            "weather": "weather",
            "search": "search",
            "analytics": "analytics",
            "meal": "meal_planner",
            "categorization": "categorization",
            "general": "general_conversation",
            "ocr": "ocr",
            "pantry": "pantry",
            "promo": "promo_scraping",
            "rag": "rag",
        }
        
        for key, value in agent_mappings.items():
            if key in normalized_name:
                return value
        
        return "general_conversation"

    def _apply_agent_thresholds(
        self, result: ValidationResult, agent_config: Any
    ) -> ValidationResult:
        """Apply agent-specific thresholds to validation result"""
        
        # Update validity based on agent-specific thresholds
        is_valid = (
            result.confidence >= agent_config.confidence_threshold and
            result.hallucination_score <= agent_config.hallucination_threshold
        )
        
        # Create updated result
        return ValidationResult(
            is_valid=is_valid,
            confidence=result.confidence,
            hallucination_score=result.hallucination_score,
            detected_hallucinations=result.detected_hallucinations,
            suspicious_phrases=result.suspicious_phrases,
            validation_errors=result.validation_errors,
            recommendation=result.recommendation,
            timestamp=result.timestamp,
            agent_name=result.agent_name,
            model_used=result.model_used,
        )

    def _update_metrics(
        self, agent_name: str, result: ValidationResult, start_time: datetime
    ):
        """Update performance metrics"""
        self.metrics["total_validations"] += 1
        
        # Calculate validation time
        validation_time = (datetime.now() - start_time).total_seconds()
        self.metrics["validation_times"].append(validation_time)
        
        # Update agent-specific metrics
        if agent_name not in self.metrics["agent_metrics"]:
            self.metrics["agent_metrics"][agent_name] = {
                "total_validations": 0,
                "successful_validations": 0,
                "avg_confidence": 0.0,
                "avg_hallucination_score": 0.0,
                "avg_validation_time": 0.0,
            }
        
        agent_metrics = self.metrics["agent_metrics"][agent_name]
        agent_metrics["total_validations"] += 1
        
        if result.is_valid:
            agent_metrics["successful_validations"] += 1
        
        # Update averages
        current_avg_conf = agent_metrics["avg_confidence"]
        current_avg_hall = agent_metrics["avg_hallucination_score"]
        current_avg_time = agent_metrics["avg_validation_time"]
        total = agent_metrics["total_validations"]
        
        agent_metrics["avg_confidence"] = (
            current_avg_conf * (total - 1) + result.confidence
        ) / total
        
        agent_metrics["avg_hallucination_score"] = (
            current_avg_hall * (total - 1) + result.hallucination_score
        ) / total
        
        agent_metrics["avg_validation_time"] = (
            current_avg_time * (total - 1) + validation_time
        ) / total

    def _log_validation_result(self, agent_name: str, result: ValidationResult):
        """Log validation result if enabled"""
        logger.info(
            f"Validation result for {agent_name}: "
            f"valid={result.is_valid}, "
            f"confidence={result.confidence:.2f}, "
            f"hallucination_score={result.hallucination_score:.2f}, "
            f"hallucinations={len(result.detected_hallucinations)}"
        )

    def _create_fallback_result(
        self, agent_name: str, model_used: str, error_message: str
    ) -> ValidationResult:
        """Create fallback validation result on error"""
        return ValidationResult(
            is_valid=False,
            confidence=0.0,
            hallucination_score=1.0,
            detected_hallucinations=[HallucinationType.FACTUAL_ERROR],
            suspicious_phrases=[],
            validation_errors=[error_message],
            recommendation="Validation failed - manual review required",
            timestamp=datetime.now(),
            agent_name=agent_name,
            model_used=model_used,
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        metrics = self.metrics.copy()
        
        # Calculate overall averages
        if metrics["validation_times"]:
            metrics["avg_validation_time"] = sum(metrics["validation_times"]) / len(metrics["validation_times"])
        else:
            metrics["avg_validation_time"] = 0.0
        
        # Calculate cache hit rate
        total_requests = metrics["cache_hits"] + metrics["cache_misses"]
        if total_requests > 0:
            metrics["cache_hit_rate"] = metrics["cache_hits"] / total_requests
        else:
            metrics["cache_hit_rate"] = 0.0
        
        return metrics

    def clear_cache(self):
        """Clear validation cache"""
        self.cache.cache.clear()
        logger.info("Validation cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache.cache),
            "max_size": self.cache.max_size,
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
        }


# Global optimized instance
optimized_anti_hallucination_system = OptimizedAntiHallucinationSystem() 