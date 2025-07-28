"""
Language Detection Agent

Detects language in OCR text with Polish language support.
"""

import logging
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType

logger = logging.getLogger(__name__)


class LanguageDetectionAgent(BaseOCRAgentImpl):
    """Language detection agent for Polish receipts"""

    def __init__(self, name: str = "LanguageDetectionAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=5.0, **kwargs)

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        return "ocr_text" in input_data and isinstance(input_data["ocr_text"], str)

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Detect language in OCR text"""
        try:
            input_data.get("ocr_text", "")

            # Placeholder language detection
            # In real implementation, this would use langdetect or similar
            detected_language = "pl"  # Assume Polish for Polish receipts
            confidence = 0.9

            await self.publish_event(
                OCREventType.LANGUAGE_DETECTED,
                {"language": detected_language, "confidence": confidence},
            )

            return AgentResponse(
                success=True,
                text="Language detection completed",
                metadata={"language": detected_language, "confidence": confidence},
                data={"language": detected_language, "confidence": confidence},
            )

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return AgentResponse(
                success=False, error=f"Language detection failed: {e!s}"
            )
