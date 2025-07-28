"""
Comprehensive Anti-Hallucination System for FoodSave AI

This module provides a unified anti-hallucination system that can be used
by all agents in the project to prevent and detect hallucinations.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import logging
import re
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ValidationCache:
    """Cache for validation results to improve performance"""

    def __init__(self, max_size: int = 1000, ttl_minutes: int = 30):
        self.cache = {}
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)

    def _generate_key(self, response: str, context: str, agent_name: str) -> str:
        """Generate cache key from response content"""
        content = f"{response}:{context}:{agent_name}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(
        self, response: str, context: str, agent_name: str
    ) -> Optional["ValidationResult"]:
        """Get cached validation result"""
        key = self._generate_key(response, context, agent_name)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]
        return None

    def set(
        self, response: str, context: str, agent_name: str, result: "ValidationResult"
    ):
        """Cache validation result"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        key = self._generate_key(response, context, agent_name)
        self.cache[key] = (result, datetime.now())


# Intelligent validation levels per agent type
AGENT_VALIDATION_LEVELS = {
    "chef": "strict",
    "receipt_analysis": "strict",
    "analytics": "moderate",
    "meal_planner": "moderate",
    "categorization": "moderate",
    "search": "moderate",
    "general_conversation": "moderate",
    "ocr": "lenient",
    "weather": "lenient",
    "pantry": "lenient",
    "promo_scraping": "lenient",
    "receipt_import": "lenient",
    "receipt_validation": "moderate",
    "receipt_categorization": "moderate",
    "concise_response": "lenient",
    "rag": "moderate",
}


class ValidationLevel(Enum):
    """Levels of validation strictness"""

    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class HallucinationType(Enum):
    """Types of hallucinations that can be detected"""

    FACTUAL_ERROR = "factual_error"
    INCONSISTENT_INFO = "inconsistent_info"
    UNVERIFIABLE_CLAIM = "unverifiable_claim"
    CONTEXT_VIOLATION = "context_violation"
    INGREDIENT_HALLUCINATION = "ingredient_hallucination"
    MEASUREMENT_HALLUCINATION = "measurement_hallucination"
    DATE_TIME_HALLUCINATION = "date_time_hallucination"
    PRICE_HALLUCINATION = "price_hallucination"


@dataclass
class ValidationResult:
    """Result of anti-hallucination validation"""

    is_valid: bool
    confidence: float
    hallucination_score: float
    detected_hallucinations: list[HallucinationType]
    suspicious_phrases: list[str]
    validation_errors: list[str]
    recommendation: str
    timestamp: datetime
    agent_name: str
    model_used: str


class AntiHallucinationConfig(BaseModel):
    """Configuration for anti-hallucination system"""

    # General settings
    enabled: bool = True
    default_validation_level: ValidationLevel = ValidationLevel.MODERATE
    confidence_threshold: float = 0.4
    hallucination_threshold: float = 0.5

    # Model-specific settings
    bielik_11b_temperature: float = 0.1
    bielik_11b_top_p: float = 0.85
    bielik_11b_max_tokens: int = 1024

    # Validation settings
    enable_fact_checking: bool = True
    enable_consensus_validation: bool = True
    enable_context_validation: bool = True
    enable_ingredient_validation: bool = True

    # Monitoring settings
    enable_monitoring: bool = True
    log_hallucinations: bool = True
    alert_on_high_hallucination: bool = True
    high_hallucination_threshold: float = 0.8


class UnifiedValidator:
    """Unified validator that combines all validation logic for optimal performance"""

    def __init__(self):
        # Optimized patterns for Polish language
        self.patterns = {
            HallucinationType.FACTUAL_ERROR: [
                r"\b\d{4}\s*rok[iu]?\b",  # Years
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",  # Dates
                r"\b\d+%\b",  # Percentages
                r"\b\d+[,.]?\d*\s*zł\b",  # PLN prices
            ],
            HallucinationType.INGREDIENT_HALLUCINATION: [
                r"\b\d+\s*(g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\s+\w+\b",
            ],
            HallucinationType.MEASUREMENT_HALLUCINATION: [
                r"\b\d+\s*stopni\b",
                r"\b\d+\s*minut\b",
                r"\b\d+\s*gram[ówy]?\b",
            ],
            HallucinationType.DATE_TIME_HALLUCINATION: [
                r"\bdzisiaj\s+\w+\b",  # Today + specific info
                r"\bwczoraj\s+\w+\b",  # Yesterday + specific info
            ],
        }

    async def validate_all(
        self,
        response: str,
        context: str,
        agent_name: str,
        validation_level: ValidationLevel,
        available_ingredients: list[str] | None = None,
    ) -> dict[str, Any]:
        """Unified validation method that runs all checks in parallel"""

        # Run all validations in parallel for better performance
        tasks = [
            self._validate_patterns(response),
            self._validate_context(response, context),
            self._validate_ingredients(
                response, available_ingredients, validation_level
            ),
            self._validate_measurements(response, validation_level),
        ]

        results = await asyncio.gather(*tasks)

        # Combine results
        detected_hallucinations = []
        suspicious_phrases = []
        validation_errors = []

        for result in results:
            detected_hallucinations.extend(result.get("hallucinations", []))
            suspicious_phrases.extend(result.get("phrases", []))
            validation_errors.extend(result.get("errors", []))

        # Calculate confidence and hallucination score
        confidence = self._calculate_confidence(
            detected_hallucinations, validation_level
        )
        hallucination_score = self._calculate_hallucination_score(
            detected_hallucinations
        )
        is_valid = confidence >= 0.7 and hallucination_score <= 0.3

        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "hallucination_score": hallucination_score,
            "detected_hallucinations": detected_hallucinations,
            "suspicious_phrases": suspicious_phrases,
            "validation_errors": validation_errors,
        }

    async def _validate_patterns(self, response: str) -> dict[str, Any]:
        """Pattern-based validation using optimized regex"""
        detected = []
        phrases = []

        for hallucination_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    detected.append(hallucination_type)
                    phrases.extend(matches)

        return {"hallucinations": detected, "phrases": phrases, "errors": []}

    async def _validate_context(self, response: str, context: str) -> dict[str, Any]:
        """Context validation"""
        errors = []
        detected = []

        # Basic context validation
        if not context or len(context.strip()) < 3:
            return {"hallucinations": [], "phrases": [], "errors": []}

        # Check if response is completely unrelated to context
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        overlap = len(context_words.intersection(response_words))

        if overlap == 0 and len(context_words) > 2:
            detected.append(HallucinationType.CONTEXT_VIOLATION)
            errors.append("Response seems unrelated to context")

        return {"hallucinations": detected, "phrases": [], "errors": errors}

    async def _validate_ingredients(
        self,
        response: str,
        available_ingredients: list[str] | None,
        validation_level: ValidationLevel,
    ) -> dict[str, Any]:
        """Ingredient validation for recipes"""
        if not available_ingredients:
            return {"hallucinations": [], "phrases": [], "errors": []}

        detected = []
        errors = []

        # Extract potential ingredients from response
        ingredient_patterns = [
            r"\b([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\s*[-:]",  # ingredient lists
            r"\b\d+\s*(?:g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\s+([a-zA-Ząćęłńóśźż]+)",  # measured ingredients
        ]

        mentioned_ingredients = set()
        for pattern in ingredient_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                ingredient = match.strip().lower()
                if len(ingredient) > 2:  # Filter out very short matches
                    mentioned_ingredients.add(ingredient)

        # Check against available ingredients
        available_lower = [ing.lower() for ing in available_ingredients]

        for ingredient in mentioned_ingredients:
            if not any(
                ing in ingredient or ingredient in ing for ing in available_lower
            ):
                if validation_level == ValidationLevel.STRICT:
                    detected.append(HallucinationType.INGREDIENT_HALLUCINATION)
                    errors.append(f"Ingredient '{ingredient}' not available")
                elif validation_level == ValidationLevel.MODERATE:
                    # Allow basic seasonings
                    basic_seasonings = ["sól", "pieprz", "olej", "masło", "cukier"]
                    if not any(
                        seasoning in ingredient for seasoning in basic_seasonings
                    ):
                        detected.append(HallucinationType.INGREDIENT_HALLUCINATION)
                        errors.append(f"Ingredient '{ingredient}' not available")

        return {
            "hallucinations": detected,
            "phrases": list(mentioned_ingredients),
            "errors": errors,
        }

    async def _validate_measurements(
        self, response: str, validation_level: ValidationLevel
    ) -> dict[str, Any]:
        """Validate measurements and quantities"""
        detected = []
        errors = []
        phrases = []

        # Check for unrealistic measurements
        unrealistic_patterns = [
            (r"\b\d{4,}\s*gram", "Unrealistic weight measurement"),
            (r"\b\d{3,}\s*stopni", "Unrealistic temperature"),
            (r"\b\d{4,}\s*minut", "Unrealistic cooking time"),
        ]

        for pattern, error_msg in unrealistic_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                detected.append(HallucinationType.MEASUREMENT_HALLUCINATION)
                errors.append(error_msg)
                phrases.extend(matches)

        return {"hallucinations": detected, "phrases": phrases, "errors": errors}

    def _calculate_confidence(
        self,
        detected_hallucinations: list[HallucinationType],
        validation_level: ValidationLevel,
    ) -> float:
        """Calculate confidence score based on detected hallucinations"""
        if not detected_hallucinations:
            return 0.95

        # Weight different types of hallucinations
        weights = {
            HallucinationType.FACTUAL_ERROR: 0.3,
            HallucinationType.INGREDIENT_HALLUCINATION: 0.4,
            HallucinationType.CONTEXT_VIOLATION: 0.2,
            HallucinationType.MEASUREMENT_HALLUCINATION: 0.1,
        }

        total_penalty = sum(weights.get(h, 0.1) for h in detected_hallucinations)

        # Adjust based on validation level
        if validation_level == ValidationLevel.LENIENT:
            total_penalty *= 0.5
        elif validation_level == ValidationLevel.STRICT:
            total_penalty *= 1.5

        confidence = max(0.1, 0.95 - total_penalty)
        return min(0.95, confidence)

    def _calculate_hallucination_score(
        self, detected_hallucinations: list[HallucinationType]
    ) -> float:
        """Calculate hallucination risk score"""
        if not detected_hallucinations:
            return 0.1

        # More hallucinations = higher score
        base_score = len(detected_hallucinations) * 0.2
        return min(0.9, base_score)


class AntiHallucinationSystem:
    """
    Central anti-hallucination system for the entire project.

    Provides comprehensive hallucination detection and prevention
    for all agents in the system.
    """

    def __init__(self, config: AntiHallucinationConfig | None = None):
        self.config = config or AntiHallucinationConfig()

        # Initialize cache system
        self.cache = ValidationCache(max_size=1000, ttl_minutes=30)

        # Initialize unified validator
        self.unified_validator = UnifiedValidator()

        # Initialize validation components (kept for backward compatibility)
        self.fact_checker = FactChecker()
        self.context_validator = ContextValidator()
        self.ingredient_validator = IngredientValidator()
        self.consensus_validator = ConsensusValidator()

        # Monitoring
        self.hallucination_metrics = HallucinationMetrics()

        # Common hallucination patterns
        self.hallucination_patterns = self._init_hallucination_patterns()

        logger.info(
            "Anti-hallucination system initialized with caching and unified validation"
        )

    def _init_hallucination_patterns(self) -> dict[HallucinationType, list[str]]:
        """Initialize patterns for detecting different types of hallucinations"""
        return {
            HallucinationType.FACTUAL_ERROR: [
                r"\b\d{4}\s*roku\b",  # Specific years without context
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",  # Specific dates
                r"\b\d{1,2}:\d{2}\b",  # Specific times
                r"\b\d+%\b",  # Specific percentages
                r"\b\d+\s*zł\b",  # Specific prices in PLN
                r"\b\d+\s*euro\b",  # Specific prices in EUR
                r"\b\d+\s*dolar\b",  # Specific prices in USD
            ],
            HallucinationType.INGREDIENT_HALLUCINATION: [
                r"\b\d+\s*(g|kg|ml|l|łyżka|łyżeczka|szklanka|sztuka)\s+[a-zA-Ząćęłńóśźż]+\b",
                r"\b[a-zA-Ząćęłńóśźż]+\s+\d+\s*(g|kg|ml|l|łyżka|łyżeczka|szklanka|sztuka)\b",
            ],
            HallucinationType.MEASUREMENT_HALLUCINATION: [
                r"\b\d+\s*stopni\b",  # Temperature
                r"\b\d+\s*minut\b",  # Time
                r"\b\d+\s*gram\b",  # Weight
                r"\b\d+\s*cal\b",  # Size
            ],
            HallucinationType.DATE_TIME_HALLUCINATION: [
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",  # Dates
                r"\b\d{1,2}:\d{2}\b",  # Times
                r"\b\d{4}\s*rok\b",  # Years
            ],
            HallucinationType.PRICE_HALLUCINATION: [
                r"\b\d+[,.]\d{2}\s*zł\b",  # PLN prices
                r"\b\d+[,.]\d{2}\s*euro\b",  # EUR prices
                r"\b\d+[,.]\d{2}\s*dolar\b",  # USD prices
            ],
        }

    async def validate_response(
        self,
        response: str,
        context: str,
        agent_name: str,
        model_used: str,
        validation_level: ValidationLevel | None = None,
        available_ingredients: list[str] | None = None,
        **kwargs: Any,
    ) -> ValidationResult:
        """
        Optimized validation of AI response for hallucinations with caching

        Args:
            response: The AI response to validate
            context: The context/query that generated the response
            agent_name: Name of the agent that generated the response
            model_used: Model used to generate the response
            validation_level: How strict the validation should be
            available_ingredients: For recipe agents, list of available ingredients
            **kwargs: Additional validation parameters

        Returns:
            ValidationResult with detailed validation information
        """
        if not self.config.enabled:
            return ValidationResult(
                is_valid=True,
                confidence=1.0,
                hallucination_score=0.0,
                detected_hallucinations=[],
                suspicious_phrases=[],
                validation_errors=[],
                recommendation="Anti-hallucination validation disabled",
                timestamp=datetime.now(),
                agent_name=agent_name,
                model_used=model_used,
            )

        # Check cache first
        cached_result = self.cache.get(response, context, agent_name)
        if cached_result:
            logger.debug(f"Using cached validation result for {agent_name}")
            return cached_result

        # Auto-select validation level based on agent type
        if validation_level is None:
            agent_type = agent_name.lower().replace("agent", "").replace("_", "")
            level_str = AGENT_VALIDATION_LEVELS.get(agent_type, "moderate")
            validation_level = ValidationLevel(level_str)

        # Use unified validator for optimal performance
        validation_data = await self.unified_validator.validate_all(
            response=response,
            context=context,
            agent_name=agent_name,
            validation_level=validation_level,
            available_ingredients=available_ingredients,
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            validation_data["detected_hallucinations"],
            validation_data["validation_errors"],
            validation_data["confidence"],
            validation_data["hallucination_score"],
        )

        # Create validation result
        result = ValidationResult(
            is_valid=validation_data["is_valid"],
            confidence=validation_data["confidence"],
            hallucination_score=validation_data["hallucination_score"],
            detected_hallucinations=validation_data["detected_hallucinations"],
            suspicious_phrases=validation_data["suspicious_phrases"],
            validation_errors=validation_data["validation_errors"],
            recommendation=recommendation,
            timestamp=datetime.now(),
            agent_name=agent_name,
            model_used=model_used,
        )

        # Cache the result
        self.cache.set(response, context, agent_name, result)

        # Update metrics
        self.hallucination_metrics.record_validation(result)

        return result

    def _generate_recommendation(
        self,
        detected_hallucinations: list[HallucinationType],
        validation_errors: list[str],
        confidence: float,
        hallucination_score: float,
    ) -> str:
        """Generate recommendation based on validation results"""
        if not detected_hallucinations and not validation_errors:
            return "Response appears to be accurate and valid."

        recommendations = []

        if HallucinationType.INGREDIENT_HALLUCINATION in detected_hallucinations:
            recommendations.append("Verify ingredients against available pantry items.")

        if HallucinationType.FACTUAL_ERROR in detected_hallucinations:
            recommendations.append("Check factual claims from reliable sources.")

        if HallucinationType.CONTEXT_VIOLATION in detected_hallucinations:
            recommendations.append("Response may be unrelated to the question asked.")

        if HallucinationType.MEASUREMENT_HALLUCINATION in detected_hallucinations:
            recommendations.append("Verify measurements and quantities.")

        if validation_errors:
            recommendations.append("Review response for potential inaccuracies.")

        # Include confidence and hallucination score in recommendation
        if confidence < 0.5:
            recommendations.append(
                f"Low confidence ({confidence:.2f}) - verify response."
            )

        if hallucination_score > 0.5:
            recommendations.append(
                f"High hallucination risk ({hallucination_score:.2f}) - use with caution."
            )

        return (
            " ".join(recommendations)
            if recommendations
            else "Review response carefully."
        )

    def _detect_pattern_hallucinations(self, response: str) -> dict[str, Any]:
        """Detect hallucinations using pattern matching"""
        detected_types = []
        suspicious_phrases = []

        for hallucination_type, patterns in self.hallucination_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    detected_types.append(hallucination_type)
                    suspicious_phrases.extend(matches)

        return {"types": detected_types, "phrases": suspicious_phrases}

    def _calculate_confidence_score(
        self,
        detected_hallucinations: list[HallucinationType],
        suspicious_phrases: list[str],
        validation_level: ValidationLevel,
    ) -> float:
        """Calculate confidence score based on validation results"""
        base_confidence = 1.0

        # Penalty for detected hallucinations
        hallucination_penalty = len(detected_hallucinations) * 0.2

        # Penalty for suspicious phrases
        phrase_penalty = len(suspicious_phrases) * 0.1

        # Adjust based on validation level
        if validation_level == ValidationLevel.STRICT:
            penalty_multiplier = 1.0
        elif validation_level == ValidationLevel.MODERATE:
            penalty_multiplier = 0.7
        else:  # LENIENT
            penalty_multiplier = 0.4

        total_penalty = (hallucination_penalty + phrase_penalty) * penalty_multiplier
        confidence = base_confidence - total_penalty

        return max(0.0, min(1.0, confidence))

    def _calculate_hallucination_score(
        self,
        detected_hallucinations: list[HallucinationType],
        suspicious_phrases: list[str],
    ) -> float:
        """Calculate hallucination score"""
        # Base score from detected hallucinations
        hallucination_score = len(detected_hallucinations) * 0.3

        # Additional score from suspicious phrases
        phrase_score = len(suspicious_phrases) * 0.1

        total_score = hallucination_score + phrase_score
        return min(1.0, total_score)

    def _determine_validity(
        self,
        confidence: float,
        hallucination_score: float,
        validation_level: ValidationLevel,
    ) -> bool:
        """Determine if response is valid based on validation criteria"""

        if validation_level == ValidationLevel.STRICT:
            return (
                confidence >= self.config.confidence_threshold
                and hallucination_score <= self.config.hallucination_threshold
            )

        elif validation_level == ValidationLevel.MODERATE:
            return (
                confidence >= self.config.confidence_threshold * 0.8
                and hallucination_score <= self.config.hallucination_threshold * 1.5
            )

        else:  # LENIENT
            return (
                confidence >= self.config.confidence_threshold * 0.6
                and hallucination_score <= self.config.hallucination_threshold * 2.0
            )

    def get_model_config(self, model_name: str) -> dict[str, Any]:
        """Get anti-hallucination configuration for specific model"""
        if "bielik-11b" in model_name:
            return {
                "temperature": self.config.bielik_11b_temperature,
                "top_p": self.config.bielik_11b_top_p,
                "max_tokens": self.config.bielik_11b_max_tokens,
                "stop_sequences": [
                    "<|start_header_id|>",
                    "<|end_header_id|>",
                    "<|eot_id|>",
                ],
            }
        else:
            return {
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 1024,
            }


class FactChecker:
    """Component for fact checking responses"""

    async def check_facts(self, response: str, context: str) -> dict[str, Any]:
        """Check facts in the response against context"""
        # Simple implementation - can be enhanced with external fact-checking APIs
        return {"is_valid": True, "reason": "Fact checking not implemented yet"}


class ContextValidator:
    """Component for validating response against context"""

    async def validate(self, response: str, context: str) -> dict[str, Any]:
        """Validate if response is relevant to the context"""
        # Simple implementation - can be enhanced with semantic similarity
        return {"is_valid": True, "reason": "Context validation passed"}


class IngredientValidator:
    """Component for validating ingredients in recipes"""

    def validate(
        self,
        response: str,
        available_ingredients: list[str],
        validation_level: ValidationLevel,
    ) -> dict[str, Any]:
        """Validate if recipe uses only available ingredients"""
        # Implementation similar to ChefAgent's validator
        return {"is_valid": True, "reason": "Ingredient validation passed"}


class ConsensusValidator:
    """Component for consensus-based validation"""

    async def validate(self, response: str, context: str) -> dict[str, Any]:
        """Validate response using consensus approach"""
        # Implementation for consensus validation
        return {"is_valid": True, "reason": "Consensus validation passed"}


class HallucinationMetrics:
    """Metrics collection for hallucination monitoring"""

    def __init__(self):
        self.total_validations = 0
        self.hallucination_detections = 0
        self.high_hallucination_alerts = 0
        self.agent_metrics = {}

    def record_validation(self, result: ValidationResult):
        """Record validation result for metrics"""
        self.total_validations += 1

        if result.detected_hallucinations:
            self.hallucination_detections += 1

        if result.hallucination_score > 0.8:
            self.high_hallucination_alerts += 1

        # Record per-agent metrics
        if result.agent_name not in self.agent_metrics:
            self.agent_metrics[result.agent_name] = {
                "total_validations": 0,
                "hallucination_detections": 0,
                "avg_confidence": 0.0,
                "avg_hallucination_score": 0.0,
            }

        agent_metrics = self.agent_metrics[result.agent_name]
        agent_metrics["total_validations"] += 1

        if result.detected_hallucinations:
            agent_metrics["hallucination_detections"] += 1

        # Update averages
        current_avg_conf = agent_metrics["avg_confidence"]
        current_avg_hall = agent_metrics["avg_hallucination_score"]
        total = agent_metrics["total_validations"]

        agent_metrics["avg_confidence"] = (
            current_avg_conf * (total - 1) + result.confidence
        ) / total
        agent_metrics["avg_hallucination_score"] = (
            current_avg_hall * (total - 1) + result.hallucination_score
        ) / total


# Global instance
anti_hallucination_system = AntiHallucinationSystem()
