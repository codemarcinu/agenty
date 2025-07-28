"""
Store Recognition Agent

Recognizes Polish store chains from receipt text.
"""

import logging
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType

logger = logging.getLogger(__name__)


class StoreRecognitionAgent(BaseOCRAgentImpl):
    """Store recognition agent for Polish receipts"""

    def __init__(self, name: str = "StoreRecognitionAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=5.0, **kwargs)

        # Polish store patterns
        self.store_patterns = {
            "Lidl": ["lidl", "LIDL", "Licllsp.z.0.0.sp.k."],
            "Biedronka": ["biedronka", "BIEDRONKA", "BIEDRONKA SP Z O.O."],
            "Kaufland": ["kaufland", "KAUFLAND", "KAUFLAND POLSKA"],
            "Tesco": ["tesco", "TESCO", "TESCO POLSKA"],
            "Carrefour": ["carrefour", "CARREFOUR"],
            "Auchan": ["auchan", "AUCHAN"],
            "Żabka": ["żabka", "ŻABKA", "ZABKA"],
        }

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        return "ocr_text" in input_data and isinstance(input_data["ocr_text"], str)

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Recognize store from OCR text"""
        try:
            ocr_text = input_data.get("ocr_text", "")

            # Simple pattern matching for store recognition
            detected_store = "Unknown"
            confidence = 0.0

            for store_name, patterns in self.store_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in ocr_text.lower():
                        detected_store = store_name
                        confidence = 0.9
                        break
                if detected_store != "Unknown":
                    break

            await self.publish_event(
                OCREventType.STORE_RECOGNIZED,
                {"store": detected_store, "confidence": confidence},
            )

            return AgentResponse(
                success=True,
                text="Store recognition completed",
                metadata={"store": detected_store, "confidence": confidence},
                data={"store_info": {"name": detected_store, "confidence": confidence}},
            )

        except Exception as e:
            logger.error(f"Store recognition failed: {e}")
            return AgentResponse(
                success=False, error=f"Store recognition failed: {e!s}"
            )
