"""
Learning Agent

Learns from OCR errors and improves performance over time.
"""

import logging
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl

logger = logging.getLogger(__name__)


class LearningAgent(BaseOCRAgentImpl):
    """Learning agent for OCR improvement"""

    def __init__(self, name: str = "LearningAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=10.0, **kwargs)

        self.learning_data = {
            "error_patterns": {},
            "corrections": {},
            "performance_trends": {},
        }

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        return True  # Accept any input for learning

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Process learning data"""
        try:
            # Update learning data
            if "error_data" in input_data:
                self._update_error_patterns(input_data["error_data"])

            if "correction_data" in input_data:
                self._update_corrections(input_data["correction_data"])

            return AgentResponse(
                success=True,
                text="Learning data updated",
                metadata={
                    "patterns_learned": len(self.learning_data["error_patterns"])
                },
                data={"learning_data": self.learning_data},
            )

        except Exception as e:
            logger.error(f"Learning agent failed: {e}")
            return AgentResponse(success=False, error=f"Learning agent failed: {e!s}")

    def _update_error_patterns(self, error_data: dict[str, Any]) -> None:
        """Update error patterns"""
        error_type = error_data.get("type", "unknown")
        if error_type not in self.learning_data["error_patterns"]:
            self.learning_data["error_patterns"][error_type] = 0
        self.learning_data["error_patterns"][error_type] += 1

    def _update_corrections(self, correction_data: dict[str, Any]) -> None:
        """Update correction data"""
        original = correction_data.get("original", "")
        corrected = correction_data.get("corrected", "")

        if original and corrected:
            self.learning_data["corrections"][original] = corrected
