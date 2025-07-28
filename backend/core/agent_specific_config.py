"""
Agent-Specific Configuration for Anti-Hallucination System

This module provides agent-specific configurations that determine
validation levels, patterns, and thresholds for different agent types.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from core.anti_hallucination_system import ValidationLevel


@dataclass
class AgentValidationConfig:
    """Configuration for agent-specific validation"""
    
    validation_level: ValidationLevel
    confidence_threshold: float
    hallucination_threshold: float
    enabled_patterns: List[str]
    custom_patterns: Dict[str, List[str]]
    timeout_seconds: float
    cache_enabled: bool
    log_validation: bool
    raise_on_high_hallucination: bool
    high_hallucination_threshold: float


# Agent-specific configurations
AGENT_CONFIGS = {
    "chef": AgentValidationConfig(
        validation_level=ValidationLevel.STRICT,
        confidence_threshold=0.7,
        hallucination_threshold=0.3,
        enabled_patterns=["ingredient", "measurement", "factual"],
        custom_patterns={
            "ingredient_patterns": [
                r"\b\d+\s*(g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\s+([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\b",
                r"\b([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\s*[-:]\s*\d+\s*(g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\b",
            ],
            "measurement_patterns": [
                r"\b\d{4,}\s*gram\b",
                r"\b\d{3,}\s*stopni\b",
                r"\b\d{4,}\s*minut\b",
            ],
        },
        timeout_seconds=15.0,
        cache_enabled=True,
        log_validation=True,
        raise_on_high_hallucination=True,
        high_hallucination_threshold=0.8,
    ),
    
    "receipt_analysis": AgentValidationConfig(
        validation_level=ValidationLevel.STRICT,
        confidence_threshold=0.8,
        hallucination_threshold=0.2,
        enabled_patterns=["factual", "price", "date"],
        custom_patterns={
            "price_patterns": [
                r"\b\d+[,.]\d{2}\s*zł\b",
                r"\b\d+[,.]\d{2}\s*PLN\b",
            ],
            "date_patterns": [
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",
                r"\b\d{1,2}:\d{2}\b",
            ],
            "nip_patterns": [
                r"\b\d{3}-\d{3}-\d{2}-\d{2}\b",
                r"\b\d{10}\b",
            ],
        },
        timeout_seconds=10.0,
        cache_enabled=True,
        log_validation=True,
        raise_on_high_hallucination=True,
        high_hallucination_threshold=0.7,
    ),
    
    "weather": AgentValidationConfig(
        validation_level=ValidationLevel.LENIENT,
        confidence_threshold=0.5,
        hallucination_threshold=0.4,
        enabled_patterns=["measurement"],
        custom_patterns={
            "temperature_patterns": [
                r"\b\d+\s*stopni\b",
                r"\b\d+\s*°C\b",
            ],
            "humidity_patterns": [
                r"\b\d+\s*%\b",
            ],
            "wind_patterns": [
                r"\b\d+\s*km/h\b",
                r"\b\d+\s*m/s\b",
            ],
        },
        timeout_seconds=8.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.9,
    ),
    
    "search": AgentValidationConfig(
        validation_level=ValidationLevel.MODERATE,
        confidence_threshold=0.7,
        hallucination_threshold=0.3,
        enabled_patterns=["factual", "unverifiable"],
        custom_patterns={
            "unverifiable_patterns": [
                r"\b(na pewno|zdecydowanie|bez wątpienia)\b",
                r"\b(jedyny|najlepszy|najgorszy)\b",
            ],
            "factual_patterns": [
                r"\b\d{4}\s*rok[iu]?\b",
                r"\b\d+[,.]?\d*\s*zł\b",
            ],
        },
        timeout_seconds=12.0,
        cache_enabled=True,
        log_validation=True,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.8,
    ),
    
    "analytics": AgentValidationConfig(
        validation_level=ValidationLevel.MODERATE,
        confidence_threshold=0.75,
        hallucination_threshold=0.25,
        enabled_patterns=["factual", "measurement"],
        custom_patterns={
            "percentage_patterns": [
                r"\b\d+[,.]?\d*\s*%\b",
            ],
            "number_patterns": [
                r"\b\d+[,.]?\d*\s*zł\b",
                r"\b\d+[,.]?\d*\s*euro\b",
            ],
        },
        timeout_seconds=15.0,
        cache_enabled=True,
        log_validation=True,
        raise_on_high_hallucination=True,
        high_hallucination_threshold=0.7,
    ),
    
    "meal_planner": AgentValidationConfig(
        validation_level=ValidationLevel.MODERATE,
        confidence_threshold=0.7,
        hallucination_threshold=0.3,
        enabled_patterns=["ingredient", "measurement"],
        custom_patterns={
            "ingredient_patterns": [
                r"\b\d+\s*(g|kg|ml|l|łyżk[ai]|łyżeczk[ai]|szklank[ai]|sztuk[ai]?)\s+([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\b",
            ],
            "time_patterns": [
                r"\b\d+\s*minut\b",
                r"\b\d+\s*godzin\b",
            ],
        },
        timeout_seconds=12.0,
        cache_enabled=True,
        log_validation=True,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.8,
    ),
    
    "categorization": AgentValidationConfig(
        validation_level=ValidationLevel.MODERATE,
        confidence_threshold=0.6,
        hallucination_threshold=0.4,
        enabled_patterns=["factual"],
        custom_patterns={
            "category_patterns": [
                r"\b(żywność|jedzenie|spożywcze)\b",
                r"\b(chemia|środki czystości)\b",
                r"\b(ubrania|odzież)\b",
            ],
        },
        timeout_seconds=8.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.9,
    ),
    
    "general_conversation": AgentValidationConfig(
        validation_level=ValidationLevel.LENIENT,
        confidence_threshold=0.5,
        hallucination_threshold=0.5,
        enabled_patterns=["factual"],
        custom_patterns={
            "factual_patterns": [
                r"\b\d{4}\s*rok[iu]?\b",
                r"\b\d+[,.]?\d*\s*zł\b",
            ],
        },
        timeout_seconds=10.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.9,
    ),
    
    "ocr": AgentValidationConfig(
        validation_level=ValidationLevel.LENIENT,
        confidence_threshold=0.4,
        hallucination_threshold=0.6,
        enabled_patterns=["factual"],
        custom_patterns={
            "ocr_patterns": [
                r"\b\d+[,.]?\d*\s*zł\b",
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",
            ],
        },
        timeout_seconds=5.0,
        cache_enabled=False,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.9,
    ),
    
    "pantry": AgentValidationConfig(
        validation_level=ValidationLevel.LENIENT,
        confidence_threshold=0.6,
        hallucination_threshold=0.4,
        enabled_patterns=["ingredient"],
        custom_patterns={
            "ingredient_patterns": [
                r"\b([a-zA-Ząćęłńóśźż]+(?:\s+[a-zA-Ząćęłńóśźż]+)*)\b",
            ],
        },
        timeout_seconds=8.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.8,
    ),
    
    "promo_scraping": AgentValidationConfig(
        validation_level=ValidationLevel.LENIENT,
        confidence_threshold=0.5,
        hallucination_threshold=0.5,
        enabled_patterns=["price"],
        custom_patterns={
            "price_patterns": [
                r"\b\d+[,.]?\d*\s*zł\b",
                r"\b\d+[,.]?\d*\s*euro\b",
            ],
        },
        timeout_seconds=6.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.9,
    ),
    
    "receipt_import": AgentValidationConfig(
        validation_level=ValidationLevel.LENIENT,
        confidence_threshold=0.5,
        hallucination_threshold=0.5,
        enabled_patterns=["factual"],
        custom_patterns={
            "receipt_patterns": [
                r"\b\d+[,.]?\d*\s*zł\b",
                r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",
            ],
        },
        timeout_seconds=8.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.9,
    ),
    
    "receipt_validation": AgentValidationConfig(
        validation_level=ValidationLevel.MODERATE,
        confidence_threshold=0.7,
        hallucination_threshold=0.3,
        enabled_patterns=["factual", "price"],
        custom_patterns={
            "validation_patterns": [
                r"\b(valid|invalid|complete|incomplete)\b",
                r"\b\d+[,.]?\d*\s*zł\b",
            ],
        },
        timeout_seconds=10.0,
        cache_enabled=True,
        log_validation=True,
        raise_on_high_hallucination=True,
        high_hallucination_threshold=0.7,
    ),
    
    "receipt_categorization": AgentValidationConfig(
        validation_level=ValidationLevel.MODERATE,
        confidence_threshold=0.6,
        hallucination_threshold=0.4,
        enabled_patterns=["factual"],
        custom_patterns={
            "category_patterns": [
                r"\b(żywność|jedzenie|spożywcze)\b",
                r"\b(chemia|środki czystości)\b",
                r"\b(ubrania|odzież)\b",
            ],
        },
        timeout_seconds=8.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.8,
    ),
    
    "concise_response": AgentValidationConfig(
        validation_level=ValidationLevel.LENIENT,
        confidence_threshold=0.5,
        hallucination_threshold=0.5,
        enabled_patterns=["factual"],
        custom_patterns={
            "factual_patterns": [
                r"\b\d{4}\s*rok[iu]?\b",
                r"\b\d+[,.]?\d*\s*zł\b",
            ],
        },
        timeout_seconds=5.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.9,
    ),
    
    "rag": AgentValidationConfig(
        validation_level=ValidationLevel.MODERATE,
        confidence_threshold=0.7,
        hallucination_threshold=0.3,
        enabled_patterns=["factual", "context"],
        custom_patterns={
            "factual_patterns": [
                r"\b\d{4}\s*rok[iu]?\b",
                r"\b\d+[,.]?\d*\s*zł\b",
            ],
        },
        timeout_seconds=12.0,
        cache_enabled=True,
        log_validation=True,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.8,
    ),
}


def get_agent_config(agent_type: str) -> AgentValidationConfig:
    """Get agent-specific configuration"""
    # Normalize agent type
    normalized_type = agent_type.lower().replace("agent", "").replace("_", "")
    
    # Get configuration or return default
    config = AGENT_CONFIGS.get(normalized_type)
    if config:
        return config
    
    # Return default configuration for unknown agent types
    return AgentValidationConfig(
        validation_level=ValidationLevel.MODERATE,
        confidence_threshold=0.6,
        hallucination_threshold=0.4,
        enabled_patterns=["factual"],
        custom_patterns={},
        timeout_seconds=10.0,
        cache_enabled=True,
        log_validation=False,
        raise_on_high_hallucination=False,
        high_hallucination_threshold=0.8,
    )


def register_agent_config(agent_type: str, config: AgentValidationConfig) -> None:
    """Register a new agent configuration"""
    normalized_type = agent_type.lower().replace("agent", "").replace("_", "")
    AGENT_CONFIGS[normalized_type] = config


def get_all_agent_types() -> List[str]:
    """Get list of all configured agent types"""
    return list(AGENT_CONFIGS.keys())


def get_agent_validation_level(agent_type: str) -> ValidationLevel:
    """Get validation level for specific agent type"""
    config = get_agent_config(agent_type)
    return config.validation_level


def get_agent_thresholds(agent_type: str) -> tuple[float, float]:
    """Get confidence and hallucination thresholds for agent type"""
    config = get_agent_config(agent_type)
    return config.confidence_threshold, config.hallucination_threshold 