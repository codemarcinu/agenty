"""
Structure Parser Agent

Parses receipt structure and extracts structured data.
"""

import logging
import re
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType

logger = logging.getLogger(__name__)


class StructureParserAgent(BaseOCRAgentImpl):
    """Structure parser agent for receipt data extraction"""

    def __init__(self, name: str = "StructureParserAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=15.0, **kwargs)

        # Receipt parsing patterns
        self.patterns = {
            "total": r"(?:suma|total|razem|ogółem)[\s:]*(\d+[.,]\d{2})",
            "date": r"(\d{2}[./-]\d{2}[./-]\d{4})",
            "product": r"([A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż\s]+)\s+(\d+[.,]\d{2})",
        }

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        return "ocr_text" in input_data and isinstance(input_data["ocr_text"], str)

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Parse receipt structure from OCR text"""
        try:
            ocr_text = input_data.get("ocr_text", "")

            # Parse structured data
            structured_data = await self._parse_receipt_structure(ocr_text)

            await self.publish_event(
                OCREventType.STRUCTURE_PARSED,
                {"products_found": len(structured_data.get("products", []))},
            )

            return AgentResponse(
                success=True,
                text="Structure parsing completed",
                metadata={"products_found": len(structured_data.get("products", []))},
                data={"structured_data": structured_data},
            )

        except Exception as e:
            logger.error(f"Structure parsing failed: {e}")
            return AgentResponse(
                success=False, error=f"Structure parsing failed: {e!s}"
            )

    async def _parse_receipt_structure(self, ocr_text: str) -> dict[str, Any]:
        """Parse receipt structure from OCR text"""
        lines = ocr_text.split("\n")

        structured_data = {"products": [], "total": 0.0, "date": "", "store": "Unknown"}

        # Extract products
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to match product pattern
            product_match = re.search(self.patterns["product"], line)
            if product_match:
                product_name = product_match.group(1).strip()
                price = float(product_match.group(2).replace(",", "."))

                structured_data["products"].append(
                    {"name": product_name, "price": price, "quantity": 1, "unit": "szt"}
                )

        # Extract total
        total_match = re.search(self.patterns["total"], ocr_text, re.IGNORECASE)
        if total_match:
            structured_data["total"] = float(total_match.group(1).replace(",", "."))

        # Extract date
        date_match = re.search(self.patterns["date"], ocr_text)
        if date_match:
            structured_data["date"] = date_match.group(1)

        return structured_data
