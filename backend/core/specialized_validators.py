"""
Specialized Anti-Hallucination Validators for Different Agent Types

This module provides agent-specific validators that are optimized for different
types of agents and their specific requirements.
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from core.anti_hallucination_system import (
    HallucinationType,
    ValidationLevel,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class SpecializedValidator(ABC):
    """Abstract base class for specialized validators"""

    @abstractmethod
    async def validate(
        self,
        response: str,
        context: str,
        validation_level: ValidationLevel,
        **kwargs: Any,
    ) -> ValidationResult:
        """Validate response using agent-specific logic"""

    @abstractmethod
    def get_validation_patterns(self) -> Dict[HallucinationType, List[str]]:
        """Get agent-specific validation patterns"""

    @abstractmethod
    def get_confidence_threshold(self) -> float:
        """Get agent-specific confidence threshold"""

    @abstractmethod
    def get_hallucination_threshold(self) -> float:
        """Get agent-specific hallucination threshold"""


class ChefValidator(SpecializedValidator):
    """Specialized validator for ChefAgent - recipe generation"""

    def __init__(self):
        self.recipe_patterns = {
            HallucinationType.INGREDIENT_HALLUCINATION: [
                r"\b\d+\s*(g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\s+([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\b",
                r"\b([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\s*[-:]\s*\d+\s*(g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\b",
            ],
            HallucinationType.MEASUREMENT_HALLUCINATION: [
                r"\b\d{4,}\s*gram\b",  # Unrealistic weights
                r"\b\d{3,}\s*stopni\b",  # Unrealistic temperatures
                r"\b\d{4,}\s*minut\b",  # Unrealistic cooking times
            ],
            HallucinationType.FACTUAL_ERROR: [
                r"\b\d{4}\s*rok[iu]?\b",  # Specific years
                r"\b\d+[,.]?\d*\s*zł\b",  # Specific prices
            ],
        }
        
        # Common Polish ingredients that are usually available
        self.common_ingredients = {
            "sól", "pieprz", "olej", "masło", "cukier", "mąka", "jajka", "mleko",
            "cebula", "czosnek", "marchew", "ziemniaki", "pomidory", "papryka",
            "makaron", "ryż", "kasza", "ser", "wędlina", "kurczak", "wieprzowina",
            "wołowina", "ryba", "grzyby", "sałata", "ogórek", "pietruszka",
            "koperek", "bazylia", "oregano", "tymianek", "rozmaryn"
        }

    async def validate(
        self,
        response: str,
        context: str,
        validation_level: ValidationLevel,
        available_ingredients: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ValidationResult:
        """Validate recipe response for hallucinations"""
        
        detected_hallucinations = []
        suspicious_phrases = []
        validation_errors = []
        
        # Extract ingredients from response
        mentioned_ingredients = self._extract_ingredients(response)
        
        # Validate against available ingredients
        if available_ingredients:
            validation_result = await self._validate_ingredients(
                mentioned_ingredients, available_ingredients, validation_level
            )
            detected_hallucinations.extend(validation_result["hallucinations"])
            validation_errors.extend(validation_result["errors"])
        
        # Pattern-based validation
        pattern_result = await self._validate_patterns(response)
        detected_hallucinations.extend(pattern_result["hallucinations"])
        suspicious_phrases.extend(pattern_result["phrases"])
        
        # Calculate scores
        confidence = self._calculate_confidence(detected_hallucinations, validation_level)
        hallucination_score = self._calculate_hallucination_score(detected_hallucinations)
        
        # Generate recommendation
        recommendation = self._generate_chef_recommendation(
            detected_hallucinations, validation_errors, confidence, hallucination_score
        )
        
        return ValidationResult(
            is_valid=confidence >= self.get_confidence_threshold() and 
                     hallucination_score <= self.get_hallucination_threshold(),
            confidence=confidence,
            hallucination_score=hallucination_score,
            detected_hallucinations=detected_hallucinations,
            suspicious_phrases=suspicious_phrases,
            validation_errors=validation_errors,
            recommendation=recommendation,
            timestamp=datetime.now(),
            agent_name="ChefAgent",
            model_used=kwargs.get("model_used", "unknown"),
        )

    def _extract_ingredients(self, response: str) -> Set[str]:
        """Extract ingredients from recipe response"""
        ingredients = set()
        
        # Pattern to match ingredients with measurements
        ingredient_patterns = [
            r"\b\d+\s*(g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\s+([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\b",
            r"\b([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\s*[-:]\s*\d+\s*(g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\b",
        ]
        
        for pattern in ingredient_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Extract ingredient name from tuple
                    ingredient = match[1] if len(match) > 1 else match[0]
                else:
                    ingredient = match
                
                if len(ingredient.strip()) > 2:
                    ingredients.add(ingredient.strip().lower())
        
        return ingredients

    async def _validate_ingredients(
        self,
        mentioned_ingredients: Set[str],
        available_ingredients: List[str],
        validation_level: ValidationLevel,
    ) -> Dict[str, Any]:
        """Validate if mentioned ingredients are available"""
        detected = []
        errors = []
        
        available_lower = [ing.lower() for ing in available_ingredients]
        
        for ingredient in mentioned_ingredients:
            # Check if ingredient is available
            is_available = any(
                ing in ingredient or ingredient in ing for ing in available_lower
            )
            
            # Check if it's a common ingredient
            is_common = any(
                common in ingredient for common in self.common_ingredients
            )
            
            if not is_available:
                if validation_level == ValidationLevel.STRICT:
                    detected.append(HallucinationType.INGREDIENT_HALLUCINATION)
                    errors.append(f"Ingredient '{ingredient}' not available")
                elif validation_level == ValidationLevel.MODERATE and not is_common:
                    detected.append(HallucinationType.INGREDIENT_HALLUCINATION)
                    errors.append(f"Ingredient '{ingredient}' not available")
        
        return {"hallucinations": detected, "errors": errors}

    async def _validate_patterns(self, response: str) -> Dict[str, Any]:
        """Validate response using pattern matching"""
        detected = []
        phrases = []
        
        for hallucination_type, patterns in self.recipe_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    detected.append(hallucination_type)
                    phrases.extend(matches)
        
        return {"hallucinations": detected, "phrases": phrases}

    def _calculate_confidence(
        self, detected_hallucinations: List[HallucinationType], validation_level: ValidationLevel
    ) -> float:
        """Calculate confidence score for chef responses"""
        if not detected_hallucinations:
            return 0.95
        
        # Weight different types of hallucinations
        weights = {
            HallucinationType.INGREDIENT_HALLUCINATION: 0.4,
            HallucinationType.MEASUREMENT_HALLUCINATION: 0.3,
            HallucinationType.FACTUAL_ERROR: 0.2,
        }
        
        total_penalty = sum(weights.get(h, 0.1) for h in detected_hallucinations)
        
        # Adjust based on validation level
        if validation_level == ValidationLevel.LENIENT:
            total_penalty *= 0.5
        elif validation_level == ValidationLevel.STRICT:
            total_penalty *= 1.5
        
        confidence = max(0.1, 0.95 - total_penalty)
        return min(0.95, confidence)

    def _calculate_hallucination_score(self, detected_hallucinations: List[HallucinationType]) -> float:
        """Calculate hallucination score for chef responses"""
        if not detected_hallucinations:
            return 0.1
        
        # More hallucinations = higher score
        base_score = len(detected_hallucinations) * 0.25
        return min(0.9, base_score)

    def _generate_chef_recommendation(
        self,
        detected_hallucinations: List[HallucinationType],
        validation_errors: List[str],
        confidence: float,
        hallucination_score: float,
    ) -> str:
        """Generate chef-specific recommendation"""
        recommendations = []
        
        if HallucinationType.INGREDIENT_HALLUCINATION in detected_hallucinations:
            recommendations.append("Sprawdź dostępność składników w spiżarni.")
        
        if HallucinationType.MEASUREMENT_HALLUCINATION in detected_hallucinations:
            recommendations.append("Zweryfikuj ilości i miary w przepisie.")
        
        if confidence < 0.6:
            recommendations.append(f"Niska pewność ({confidence:.2f}) - sprawdź przepis.")
        
        if hallucination_score > 0.5:
            recommendations.append(f"Wysokie ryzyko halucynacji ({hallucination_score:.2f}).")
        
        return " ".join(recommendations) if recommendations else "Przepis wygląda dobrze."

    def get_validation_patterns(self) -> Dict[HallucinationType, List[str]]:
        return self.recipe_patterns

    def get_confidence_threshold(self) -> float:
        return 0.7

    def get_hallucination_threshold(self) -> float:
        return 0.3


class ReceiptAnalysisValidator(SpecializedValidator):
    """Specialized validator for ReceiptAnalysisAgent"""

    def __init__(self):
        self.receipt_patterns = {
            HallucinationType.FACTUAL_ERROR: [
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",  # Dates
                r"\b\d{1,2}:\d{2}\b",  # Times
                r"\b\d{3}-\d{3}-\d{2}-\d{2}\b",  # NIP format
                r"\b\d{10}\b",  # NIP numbers
            ],
            HallucinationType.PRICE_HALLUCINATION: [
                r"\b\d+[,.]\d{2}\s*zł\b",  # PLN prices
                r"\b\d+[,.]\d{2}\s*PLN\b",  # PLN prices
                r"\b\d+[,.]\d{2}\s*euro\b",  # EUR prices
            ],
            HallucinationType.DATE_TIME_HALLUCINATION: [
                r"\b\d{4}\s*rok\b",  # Years
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",  # Dates
            ],
        }

    async def validate(
        self,
        response: str,
        context: str,
        validation_level: ValidationLevel,
        **kwargs: Any,
    ) -> ValidationResult:
        """Validate receipt analysis response"""
        
        detected_hallucinations = []
        suspicious_phrases = []
        validation_errors = []
        
        # Pattern-based validation
        pattern_result = await self._validate_patterns(response)
        detected_hallucinations.extend(pattern_result["hallucinations"])
        suspicious_phrases.extend(pattern_result["phrases"])
        
        # Context validation
        context_result = await self._validate_context(response, context)
        detected_hallucinations.extend(context_result["hallucinations"])
        validation_errors.extend(context_result["errors"])
        
        # Calculate scores
        confidence = self._calculate_confidence(detected_hallucinations, validation_level)
        hallucination_score = self._calculate_hallucination_score(detected_hallucinations)
        
        recommendation = self._generate_receipt_recommendation(
            detected_hallucinations, validation_errors, confidence, hallucination_score
        )
        
        return ValidationResult(
            is_valid=confidence >= self.get_confidence_threshold() and 
                     hallucination_score <= self.get_hallucination_threshold(),
            confidence=confidence,
            hallucination_score=hallucination_score,
            detected_hallucinations=detected_hallucinations,
            suspicious_phrases=suspicious_phrases,
            validation_errors=validation_errors,
            recommendation=recommendation,
            timestamp=datetime.now(),
            agent_name="ReceiptAnalysisAgent",
            model_used=kwargs.get("model_used", "unknown"),
        )

    async def _validate_patterns(self, response: str) -> Dict[str, Any]:
        """Validate receipt-specific patterns"""
        detected = []
        phrases = []
        
        for hallucination_type, patterns in self.receipt_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    detected.append(hallucination_type)
                    phrases.extend(matches)
        
        return {"hallucinations": detected, "phrases": phrases}

    async def _validate_context(self, response: str, context: str) -> Dict[str, Any]:
        """Validate if response is relevant to receipt context"""
        detected = []
        errors = []
        
        # Check for receipt-specific keywords
        receipt_keywords = ["paragon", "sklep", "zakupy", "kwota", "data", "nip", "vat"]
        context_lower = context.lower()
        response_lower = response.lower()
        
        # If context mentions receipt but response doesn't contain receipt-related terms
        if any(keyword in context_lower for keyword in receipt_keywords):
            if not any(keyword in response_lower for keyword in receipt_keywords):
                detected.append(HallucinationType.CONTEXT_VIOLATION)
                errors.append("Response doesn't seem related to receipt analysis")
        
        return {"hallucinations": detected, "errors": errors}

    def _calculate_confidence(
        self, detected_hallucinations: List[HallucinationType], validation_level: ValidationLevel
    ) -> float:
        """Calculate confidence score for receipt analysis"""
        if not detected_hallucinations:
            return 0.95
        
        weights = {
            HallucinationType.FACTUAL_ERROR: 0.4,
            HallucinationType.PRICE_HALLUCINATION: 0.3,
            HallucinationType.CONTEXT_VIOLATION: 0.2,
        }
        
        total_penalty = sum(weights.get(h, 0.1) for h in detected_hallucinations)
        
        if validation_level == ValidationLevel.LENIENT:
            total_penalty *= 0.5
        elif validation_level == ValidationLevel.STRICT:
            total_penalty *= 1.5
        
        confidence = max(0.1, 0.95 - total_penalty)
        return min(0.95, confidence)

    def _calculate_hallucination_score(self, detected_hallucinations: List[HallucinationType]) -> float:
        """Calculate hallucination score for receipt analysis"""
        if not detected_hallucinations:
            return 0.1
        
        base_score = len(detected_hallucinations) * 0.2
        return min(0.9, base_score)

    def _generate_receipt_recommendation(
        self,
        detected_hallucinations: List[HallucinationType],
        validation_errors: List[str],
        confidence: float,
        hallucination_score: float,
    ) -> str:
        """Generate receipt-specific recommendation"""
        recommendations = []
        
        if HallucinationType.FACTUAL_ERROR in detected_hallucinations:
            recommendations.append("Sprawdź dane paragonu.")
        
        if HallucinationType.PRICE_HALLUCINATION in detected_hallucinations:
            recommendations.append("Zweryfikuj kwoty i ceny.")
        
        if confidence < 0.6:
            recommendations.append(f"Niska pewność ({confidence:.2f}) - sprawdź analizę.")
        
        return " ".join(recommendations) if recommendations else "Analiza paragonu wygląda dobrze."

    def get_validation_patterns(self) -> Dict[HallucinationType, List[str]]:
        return self.receipt_patterns

    def get_confidence_threshold(self) -> float:
        return 0.8

    def get_hallucination_threshold(self) -> float:
        return 0.2


class WeatherValidator(SpecializedValidator):
    """Specialized validator for WeatherAgent"""

    def __init__(self):
        self.weather_patterns = {
            HallucinationType.FACTUAL_ERROR: [
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",  # Specific dates
                r"\b\d{1,2}:\d{2}\b",  # Specific times
            ],
            HallucinationType.MEASUREMENT_HALLUCINATION: [
                r"\b\d+\s*stopni\b",  # Temperature
                r"\b\d+\s*%\b",  # Humidity
                r"\b\d+\s*km/h\b",  # Wind speed
            ],
        }

    async def validate(
        self,
        response: str,
        context: str,
        validation_level: ValidationLevel,
        **kwargs: Any,
    ) -> ValidationResult:
        """Validate weather response"""
        
        detected_hallucinations = []
        suspicious_phrases = []
        validation_errors = []
        
        # Pattern-based validation
        pattern_result = await self._validate_patterns(response)
        detected_hallucinations.extend(pattern_result["hallucinations"])
        suspicious_phrases.extend(pattern_result["phrases"])
        
        # Calculate scores
        confidence = self._calculate_confidence(detected_hallucinations, validation_level)
        hallucination_score = self._calculate_hallucination_score(detected_hallucinations)
        
        recommendation = self._generate_weather_recommendation(
            detected_hallucinations, validation_errors, confidence, hallucination_score
        )
        
        return ValidationResult(
            is_valid=confidence >= self.get_confidence_threshold() and 
                     hallucination_score <= self.get_hallucination_threshold(),
            confidence=confidence,
            hallucination_score=hallucination_score,
            detected_hallucinations=detected_hallucinations,
            suspicious_phrases=suspicious_phrases,
            validation_errors=validation_errors,
            recommendation=recommendation,
            timestamp=datetime.now(),
            agent_name="WeatherAgent",
            model_used=kwargs.get("model_used", "unknown"),
        )

    async def _validate_patterns(self, response: str) -> Dict[str, Any]:
        """Validate weather-specific patterns"""
        detected = []
        phrases = []
        
        for hallucination_type, patterns in self.weather_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    detected.append(hallucination_type)
                    phrases.extend(matches)
        
        return {"hallucinations": detected, "phrases": phrases}

    def _calculate_confidence(
        self, detected_hallucinations: List[HallucinationType], validation_level: ValidationLevel
    ) -> float:
        """Calculate confidence score for weather responses"""
        if not detected_hallucinations:
            return 0.9  # Weather is more lenient
        
        weights = {
            HallucinationType.FACTUAL_ERROR: 0.3,
            HallucinationType.MEASUREMENT_HALLUCINATION: 0.2,
        }
        
        total_penalty = sum(weights.get(h, 0.1) for h in detected_hallucinations)
        
        if validation_level == ValidationLevel.LENIENT:
            total_penalty *= 0.3  # Weather is very lenient
        elif validation_level == ValidationLevel.STRICT:
            total_penalty *= 1.0
        
        confidence = max(0.1, 0.9 - total_penalty)
        return min(0.9, confidence)

    def _calculate_hallucination_score(self, detected_hallucinations: List[HallucinationType]) -> float:
        """Calculate hallucination score for weather responses"""
        if not detected_hallucinations:
            return 0.05  # Very low baseline for weather
        
        base_score = len(detected_hallucinations) * 0.15
        return min(0.8, base_score)

    def _generate_weather_recommendation(
        self,
        detected_hallucinations: List[HallucinationType],
        validation_errors: List[str],
        confidence: float,
        hallucination_score: float,
    ) -> str:
        """Generate weather-specific recommendation"""
        recommendations = []
        
        if HallucinationType.FACTUAL_ERROR in detected_hallucinations:
            recommendations.append("Sprawdź aktualne dane pogodowe.")
        
        if confidence < 0.5:
            recommendations.append(f"Niska pewność ({confidence:.2f}) - sprawdź pogodę.")
        
        return " ".join(recommendations) if recommendations else "Prognoza pogody wygląda dobrze."

    def get_validation_patterns(self) -> Dict[HallucinationType, List[str]]:
        return self.weather_patterns

    def get_confidence_threshold(self) -> float:
        return 0.5  # Lower threshold for weather

    def get_hallucination_threshold(self) -> float:
        return 0.4  # Higher threshold for weather


class SearchValidator(SpecializedValidator):
    """Specialized validator for SearchAgent"""

    def __init__(self):
        self.search_patterns = {
            HallucinationType.FACTUAL_ERROR: [
                r"\b\d{4}\s*rok[iu]?\b",  # Years
                r"\b\d+[,.]?\d*\s*zł\b",  # Prices
            ],
            HallucinationType.UNVERIFIABLE_CLAIM: [
                r"\b(na pewno|zdecydowanie|bez wątpienia)\b",  # Unverifiable claims
                r"\b(jedyny|najlepszy|najgorszy)\b",  # Absolute statements
            ],
        }

    async def validate(
        self,
        response: str,
        context: str,
        validation_level: ValidationLevel,
        **kwargs: Any,
    ) -> ValidationResult:
        """Validate search response"""
        
        detected_hallucinations = []
        suspicious_phrases = []
        validation_errors = []
        
        # Pattern-based validation
        pattern_result = await self._validate_patterns(response)
        detected_hallucinations.extend(pattern_result["hallucinations"])
        suspicious_phrases.extend(pattern_result["phrases"])
        
        # Context validation
        context_result = await self._validate_search_context(response, context)
        detected_hallucinations.extend(context_result["hallucinations"])
        validation_errors.extend(context_result["errors"])
        
        # Calculate scores
        confidence = self._calculate_confidence(detected_hallucinations, validation_level)
        hallucination_score = self._calculate_hallucination_score(detected_hallucinations)
        
        recommendation = self._generate_search_recommendation(
            detected_hallucinations, validation_errors, confidence, hallucination_score
        )
        
        return ValidationResult(
            is_valid=confidence >= self.get_confidence_threshold() and 
                     hallucination_score <= self.get_hallucination_threshold(),
            confidence=confidence,
            hallucination_score=hallucination_score,
            detected_hallucinations=detected_hallucinations,
            suspicious_phrases=suspicious_phrases,
            validation_errors=validation_errors,
            recommendation=recommendation,
            timestamp=datetime.now(),
            agent_name="SearchAgent",
            model_used=kwargs.get("model_used", "unknown"),
        )

    async def _validate_patterns(self, response: str) -> Dict[str, Any]:
        """Validate search-specific patterns"""
        detected = []
        phrases = []
        
        for hallucination_type, patterns in self.search_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    detected.append(hallucination_type)
                    phrases.extend(matches)
        
        return {"hallucinations": detected, "phrases": phrases}

    async def _validate_search_context(self, response: str, context: str) -> Dict[str, Any]:
        """Validate if search response is relevant to query"""
        detected = []
        errors = []
        
        # Simple keyword matching
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        overlap = len(context_words.intersection(response_words))
        
        if overlap == 0 and len(context_words) > 2:
            detected.append(HallucinationType.CONTEXT_VIOLATION)
            errors.append("Search response seems unrelated to query")
        
        return {"hallucinations": detected, "errors": errors}

    def _calculate_confidence(
        self, detected_hallucinations: List[HallucinationType], validation_level: ValidationLevel
    ) -> float:
        """Calculate confidence score for search responses"""
        if not detected_hallucinations:
            return 0.85
        
        weights = {
            HallucinationType.FACTUAL_ERROR: 0.3,
            HallucinationType.UNVERIFIABLE_CLAIM: 0.2,
            HallucinationType.CONTEXT_VIOLATION: 0.4,
        }
        
        total_penalty = sum(weights.get(h, 0.1) for h in detected_hallucinations)
        
        if validation_level == ValidationLevel.LENIENT:
            total_penalty *= 0.6
        elif validation_level == ValidationLevel.STRICT:
            total_penalty *= 1.2
        
        confidence = max(0.1, 0.85 - total_penalty)
        return min(0.85, confidence)

    def _calculate_hallucination_score(self, detected_hallucinations: List[HallucinationType]) -> float:
        """Calculate hallucination score for search responses"""
        if not detected_hallucinations:
            return 0.15
        
        base_score = len(detected_hallucinations) * 0.2
        return min(0.8, base_score)

    def _generate_search_recommendation(
        self,
        detected_hallucinations: List[HallucinationType],
        validation_errors: List[str],
        confidence: float,
        hallucination_score: float,
    ) -> str:
        """Generate search-specific recommendation"""
        recommendations = []
        
        if HallucinationType.UNVERIFIABLE_CLAIM in detected_hallucinations:
            recommendations.append("Sprawdź źródła informacji.")
        
        if HallucinationType.CONTEXT_VIOLATION in detected_hallucinations:
            recommendations.append("Odpowiedź może być niepowiązana z zapytaniem.")
        
        if confidence < 0.6:
            recommendations.append(f"Niska pewność ({confidence:.2f}) - zweryfikuj odpowiedź.")
        
        return " ".join(recommendations) if recommendations else "Wyniki wyszukiwania wyglądają dobrze."

    def get_validation_patterns(self) -> Dict[HallucinationType, List[str]]:
        return self.search_patterns

    def get_confidence_threshold(self) -> float:
        return 0.7

    def get_hallucination_threshold(self) -> float:
        return 0.3


# Validator factory
class ValidatorFactory:
    """Factory for creating specialized validators"""
    
    _validators = {
        "chef": ChefValidator,
        "receipt_analysis": ReceiptAnalysisValidator,
        "weather": WeatherValidator,
        "search": SearchValidator,
    }
    
    @classmethod
    def get_validator(cls, agent_type: str) -> SpecializedValidator:
        """Get specialized validator for agent type"""
        validator_class = cls._validators.get(agent_type.lower())
        if validator_class:
            return validator_class()
        
        # Return default validator if no specialized one exists
        return DefaultValidator()
    
    @classmethod
    def register_validator(cls, agent_type: str, validator_class: type[SpecializedValidator]) -> None:
        """Register a new specialized validator"""
        cls._validators[agent_type.lower()] = validator_class


class DefaultValidator(SpecializedValidator):
    """Default validator for agents without specialized validation"""
    
    def __init__(self):
        self.default_patterns = {
            HallucinationType.FACTUAL_ERROR: [
                r"\b\d{4}\s*rok[iu]?\b",
                r"\b\d+[,.]?\d*\s*zł\b",
            ],
        }
    
    async def validate(
        self,
        response: str,
        context: str,
        validation_level: ValidationLevel,
        **kwargs: Any,
    ) -> ValidationResult:
        """Default validation logic"""
        
        detected_hallucinations = []
        suspicious_phrases = []
        validation_errors = []
        
        # Basic pattern validation
        for hallucination_type, patterns in self.default_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    detected_hallucinations.append(hallucination_type)
                    suspicious_phrases.extend(matches)
        
        # Calculate scores
        confidence = 0.8 if not detected_hallucinations else 0.6
        hallucination_score = len(detected_hallucinations) * 0.2
        
        return ValidationResult(
            is_valid=confidence >= 0.6 and hallucination_score <= 0.4,
            confidence=confidence,
            hallucination_score=hallucination_score,
            detected_hallucinations=detected_hallucinations,
            suspicious_phrases=suspicious_phrases,
            validation_errors=validation_errors,
            recommendation="Standard validation applied",
            timestamp=datetime.now(),
            agent_name=kwargs.get("agent_name", "UnknownAgent"),
            model_used=kwargs.get("model_used", "unknown"),
        )
    
    def get_validation_patterns(self) -> Dict[HallucinationType, List[str]]:
        return self.default_patterns
    
    def get_confidence_threshold(self) -> float:
        return 0.6
    
    def get_hallucination_threshold(self) -> float:
        return 0.4 