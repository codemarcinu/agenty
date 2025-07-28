"""
Text Detection Agent

Detects text regions in receipt images for optimized OCR processing.
"""

import logging
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType

logger = logging.getLogger(__name__)


class TextDetectionAgent(BaseOCRAgentImpl):
    """Text detection agent for identifying text regions in receipts"""

    def __init__(self, name: str = "TextDetectionAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=10.0, **kwargs)

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        return "image_bytes" in input_data and isinstance(
            input_data["image_bytes"], bytes
        )

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Process image to detect text regions"""
        try:
            # Placeholder implementation
            # In real implementation, this would use PaddleOCR or similar for text detection

            await self.publish_event(
                OCREventType.TEXT_DETECTED, {"regions_detected": 0}
            )

            return AgentResponse(
                success=True,
                text="Text detection completed",
                metadata={"regions_detected": 0},
                data={"text_regions": []},
            )

        except Exception as e:
            logger.error(f"Text detection failed: {e}")
            return AgentResponse(success=False, error=f"Text detection failed: {e!s}")
