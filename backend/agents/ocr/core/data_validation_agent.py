"""
Data Validation Agent

Validates OCR results and applies quality checks.
"""

import logging
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType

logger = logging.getLogger(__name__)


class DataValidationAgent(BaseOCRAgentImpl):
    """Data validation agent for OCR results"""

    def __init__(self, name: str = "DataValidationAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=10.0, **kwargs)

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        return "ocr_text" in input_data and isinstance(input_data["ocr_text"], str)

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Validate OCR text data"""
        try:
            ocr_text = input_data.get("ocr_text", "")

            # Placeholder validation logic
            validation_result = {
                "is_valid": len(ocr_text) > 0,
                "confidence": 0.8 if len(ocr_text) > 0 else 0.0,
                "issues_found": 0,
            }

            await self.publish_event(
                OCREventType.VALIDATION_COMPLETED, validation_result
            )

            return AgentResponse(
                success=True,
                text="Data validation completed",
                metadata=validation_result,
                data={"validated_text": ocr_text},
            )

        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return AgentResponse(success=False, error=f"Data validation failed: {e!s}")
