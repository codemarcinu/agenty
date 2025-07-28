"""
Product Classification Agent

Classifies products using Polish product categories.
"""

import logging
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType

logger = logging.getLogger(__name__)


class ProductClassificationAgent(BaseOCRAgentImpl):
    """Product classification agent for Polish receipts"""

    def __init__(self, name: str = "ProductClassificationAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=10.0, **kwargs)

        # Polish product categories
        self.product_categories = {
            "Nabiał": ["mleko", "jogurt", "ser", "śmietana", "masło", "twaróg"],
            "Pieczywo": ["chleb", "bułka", "rogal", "bagietka"],
            "Mięso i wędliny": [
                "kiełbasa",
                "szynka",
                "boczek",
                "kurczak",
                "wieprzowina",
            ],
            "Owoce i warzywa": ["banan", "jabłko", "pomidor", "ogórek", "marchew"],
            "Napoje": ["woda", "sok", "cola", "piwo", "wino"],
            "Słodycze": ["czekolada", "cukierki", "lizak", "guma"],
            "Przekąski": ["chipsy", "orzeszki", "paluszki", "krakersy"],
        }

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        return "structured_data" in input_data and isinstance(
            input_data["structured_data"], dict
        )

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Classify products from structured data"""
        try:
            structured_data = input_data.get("structured_data", {})
            products = structured_data.get("products", [])

            classified_products = []

            for product in products:
                product_name = product.get("name", "").lower()
                category = "Inne"  # Default category

                # Simple keyword-based classification
                for cat_name, keywords in self.product_categories.items():
                    for keyword in keywords:
                        if keyword in product_name:
                            category = cat_name
                            break
                    if category != "Inne":
                        break

                classified_product = {
                    **product,
                    "category": category,
                    "category_confidence": 0.8 if category != "Inne" else 0.3,
                }
                classified_products.append(classified_product)

            await self.publish_event(
                OCREventType.CLASSIFICATION_COMPLETED,
                {"products_classified": len(classified_products)},
            )

            return AgentResponse(
                success=True,
                text="Product classification completed",
                metadata={"products_classified": len(classified_products)},
                data={"classified_products": classified_products},
            )

        except Exception as e:
            logger.error(f"Product classification failed: {e}")
            return AgentResponse(
                success=False, error=f"Product classification failed: {e!s}"
            )
