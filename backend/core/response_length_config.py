"""
Response Length Configuration Module

This module provides configuration and utilities for controlling response length
in the FoodSave AI system, enabling Perplexity.ai-style concise responses.
"""

from enum import Enum
import logging
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ResponseStyle(str, Enum):
    """Response style enumeration"""

    CONCISE = "concise"  # Perplexity.ai style - 1-2 sentences
    STANDARD = "standard"  # Normal responses
    DETAILED = "detailed"  # Comprehensive responses


class ResponseLengthConfig(BaseModel):
    """
    Configuration for response length control

    This class provides fine-grained control over response generation
    parameters to achieve Perplexity.ai-style concise responses.
    """

    # Core parameters
    max_tokens: int = Field(
        default=100, ge=10, le=1000, description="Maximum tokens for response"
    )
    num_predict: int = Field(
        default=60, ge=10, le=500, description="Ollama num_predict parameter"
    )
    temperature: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Temperature for response generation"
    )

    # Style control
    response_style: ResponseStyle = Field(
        default=ResponseStyle.CONCISE, description="Response style"
    )
    concise_mode: bool = Field(default=True, description="Enable concise mode")

    # Length thresholds
    target_char_length: int = Field(
        default=200, ge=50, le=1000, description="Target character length"
    )
    expand_threshold: int = Field(
        default=150, ge=50, le=500, description="Threshold for expand button"
    )

    # RAG settings
    use_map_reduce: bool = Field(default=True, description="Use map-reduce for RAG")
    chunk_summary_length: int = Field(
        default=100, ge=50, le=300, description="Length of chunk summaries"
    )
    max_chunks_for_summary: int = Field(
        default=5, ge=1, le=10, description="Max chunks to summarize"
    )

    # Validation
    @field_validator("max_tokens", "num_predict")
    @classmethod
    def validate_token_limits(cls, v):
        """Validate token limits are reasonable"""
        if v < 10:
            raise ValueError("Token limit too low, minimum 10 tokens required")
        if v > 1000:
            raise ValueError("Token limit too high, maximum 1000 tokens allowed")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v, info):
        """Validate temperature is in reasonable range for concise responses"""
        if v > 0.5 and info.data.get("concise_mode", True):
            logging.getLogger(__name__).warning(
                "High temperature may reduce response consistency in concise mode"
            )
        return v

    def get_ollama_options(self) -> dict[str, Any]:
        """Get Ollama-compatible options dictionary"""
        return {
            "num_predict": self.num_predict,
            "temperature": self.temperature,
            "top_p": 0.8,  # Obniżone z 0.9 dla bardziej ograniczonego diversity
            "top_k": 20,  # Obniżone z 40 dla bardziej ograniczonego wyboru tokenów
            "repeat_penalty": 1.2,  # Zwiększone z 1.1 dla lepszego zapobiegania powtórzeniom
        }

    def get_system_prompt_modifier(self) -> str:
        """Get system prompt modifier for concise responses"""
        if self.response_style == ResponseStyle.CONCISE:
            return """
            ODPOWIEDŹ ZWIĘZŁA: Maksymalnie 2 zdania. Unikaj zbędnego formatowania.
            Jeśli potrzebujesz więcej szczegółów, poproś o doprecyzowanie.
            """
        if self.response_style == ResponseStyle.STANDARD:
            return """
            ODPOWIEDŹ STANDARDOWA: 3-5 zdań z odpowiednim poziomem szczegółów.
            """
        # DETAILED
        return """
            ODPOWIEDŹ SZCZEGÓŁOWA: Kompletne wyjaśnienie z przykładami i kontekstem.
            """

    def should_truncate_response(self, response_length: int) -> bool:
        """Determine if response should be truncated"""
        return response_length > self.target_char_length

    def get_truncation_point(self, text: str) -> int:
        """Find optimal truncation point in text"""
        if len(text) <= self.target_char_length:
            return len(text)

        # Try to truncate at sentence boundary
        target_pos = self.target_char_length
        for i in range(target_pos, max(0, target_pos - 50), -1):
            if text[i] in ".!?":
                return i + 1

        # Fallback to word boundary
        for i in range(target_pos, max(0, target_pos - 30), -1):
            if text[i] == " ":
                return i

        return target_pos


class ConciseMetrics:
    """Metrics for measuring response conciseness"""

    @staticmethod
    def calculate_concise_score(response: str) -> float:
        """
        Calculate conciseness score (0-1)

        Args:
            response: Response text to analyze

        Returns:
            Float between 0-1, where 1 is most concise
        """
        if not response or not response.strip():
            return 0.0

        char_count = len(response.strip())
        word_count = len(response.split())
        sentence_count = len([s for s in response.split(".") if s.strip()])

        # Scoring algorithm based on Perplexity.ai patterns
        if char_count < 100 and word_count < 20 and sentence_count <= 2:
            return 1.0
        if char_count < 200 and word_count < 40 and sentence_count <= 3:
            return 0.8
        if char_count < 500 and word_count < 100 and sentence_count <= 5:
            return 0.6
        if char_count < 1000 and word_count < 200:
            return 0.4
        return 0.2

    @staticmethod
    def validate_concise_response(response: str, target_length: int = 200) -> bool:
        """
        Validate if response meets conciseness criteria

        Args:
            response: Response text to validate
            target_length: Maximum character length

        Returns:
            True if response meets criteria
        """
        if not response or not response.strip():
            return False

        char_count = len(response.strip())
        word_count = len(response.split())
        sentence_count = len([s for s in response.split(".") if s.strip()])

        return (
            char_count <= target_length
            and word_count <= target_length // 5  # Rough word estimate
            and sentence_count <= 3
        )

    @staticmethod
    def get_response_stats(response: str) -> dict[str, Any]:
        """
        Get comprehensive statistics about response

        Args:
            response: Response text to analyze

        Returns:
            Dictionary with response statistics
        """
        if not response or not response.strip():
            return {
                "char_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "concise_score": 0.0,
                "is_concise": False,
            }

        char_count = len(response.strip())
        word_count = len(response.split())
        sentence_count = len([s for s in response.split(".") if s.strip()])
        concise_score = ConciseMetrics.calculate_concise_score(response)

        return {
            "char_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "concise_score": concise_score,
            "is_concise": concise_score >= 0.7,
            "avg_words_per_sentence": word_count / max(sentence_count, 1),
            "avg_chars_per_word": char_count / max(word_count, 1),
        }


# Default configurations for different use cases
DEFAULT_CONCISE_CONFIG = ResponseLengthConfig(
    max_tokens=100,
    num_predict=60,
    temperature=0.1,
    response_style=ResponseStyle.CONCISE,
    concise_mode=True,
    target_char_length=200,
    expand_threshold=150,
)

DEFAULT_STANDARD_CONFIG = ResponseLengthConfig(
    max_tokens=300,
    num_predict=150,
    temperature=0.15,
    response_style=ResponseStyle.STANDARD,
    concise_mode=False,
    target_char_length=500,
    expand_threshold=400,
)

DEFAULT_DETAILED_CONFIG = ResponseLengthConfig(
    max_tokens=800,
    num_predict=400,
    temperature=0.2,
    response_style=ResponseStyle.DETAILED,
    concise_mode=False,
    target_char_length=1000,
    expand_threshold=500,
)


def get_config_for_style(style: ResponseStyle) -> ResponseLengthConfig:
    """
    Get default configuration for response style

    Args:
        style: Response style to get config for

    Returns:
        ResponseLengthConfig instance
    """
    configs = {
        ResponseStyle.CONCISE: DEFAULT_CONCISE_CONFIG,
        ResponseStyle.STANDARD: DEFAULT_STANDARD_CONFIG,
        ResponseStyle.DETAILED: DEFAULT_DETAILED_CONFIG,
    }
    return configs.get(style, DEFAULT_CONCISE_CONFIG).copy()
