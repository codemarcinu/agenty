"""
Receipt Categorization Agent - taguje pozycje z użyciem LLM-a i słownika GUS
Zgodnie z rekomendacjami audytu - single responsibility principle
"""

import logging
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.decorators import handle_exceptions
from core.hybrid_llm_client import hybrid_llm_client
from core.product_categorizer import ProductCategorizer

logger = logging.getLogger(__name__)


class ReceiptCategorizationInput(BaseModel):
    """Model wejściowy dla ReceiptCategorizationAgent."""

    items: list[dict[str, Any]]
    store_name: str = ""
    use_llm: bool = True

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        """Validate that items list is not empty and contains valid items"""
        if not v:
            raise ValueError("Items list cannot be empty")

        for i, item in enumerate(v):
            if not isinstance(item, dict):
                raise ValueError(f"Item {i} must be a dictionary")

            if "name" not in item or not item["name"]:
                raise ValueError(f"Item {i} must have a non-empty 'name' field")

            # Validate numeric fields
            for field in ["quantity", "price"]:
                if field in item:
                    try:
                        float(item[field])
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"Item {i} field '{field}' must be a valid number"
                        )

        return v

    @field_validator("store_name")
    @classmethod
    def validate_store_name(cls, v):
        """Validate store name is not too long"""
        if len(v) > 100:
            raise ValueError("Store name cannot exceed 100 characters")
        return v.strip() if v else ""


class CategorizationResult(BaseModel):
    """Wynik kategoryzacji produktów."""

    categorized_items: list[dict[str, Any]]
    categories_used: list[str]
    confidence_scores: dict[str, float]
    llm_used: bool


class ReceiptCategorizationAgent(BaseAgent):
    """
    Agent kategoryzacji paragonów - taguje pozycje z użyciem LLM-a + słownika GUS.

    Zgodnie z zasadą single responsibility:
    - Kategoryzacja produktów spożywczych
    - Kategoryzacja chemii gospodarczej
    - Użycie LLM-a + słownika GUS
    - Mapowanie na Google Product Taxonomy
    """

    def __init__(
        self,
        name: str = "ReceiptCategorizationAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        """Inicjalizuje ReceiptCategorizationAgent."""
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )
        self.product_categorizer = ProductCategorizer()
        self.use_llm = kwargs.get("use_llm", True)
        self.fallback_to_dict = kwargs.get("fallback_to_dict", True)

    @handle_exceptions(max_retries=1, retry_delay=0.5)
    async def process(
        self, input_data: ReceiptCategorizationInput | dict[str, Any]
    ) -> AgentResponse:
        """
        Kategoryzuje produkty z paragonu.

        Args:
            input_data: Dane wejściowe z produktami do kategoryzacji

        Returns:
            AgentResponse: Odpowiedź z skategoryzowanymi produktami
        """
        try:
            # Enhanced input validation with detailed error messages
            if not isinstance(input_data, ReceiptCategorizationInput):
                try:
                    input_data = ReceiptCategorizationInput.model_validate(input_data)
                except ValidationError as ve:
                    error_details = []
                    for error in ve.errors():
                        field = (
                            error.get("loc", ["unknown"])[0]
                            if error.get("loc")
                            else "unknown"
                        )
                        message = error.get("msg", "Validation error")
                        error_details.append(f"{field}: {message}")

                    return AgentResponse(
                        success=False,
                        error=f"Błąd walidacji danych wejściowych: {'; '.join(error_details)}",
                        text="Nieprawidłowe dane wejściowe. Sprawdź format produktów.",
                    )
        except Exception as e:
            logger.error(f"Unexpected error during input validation: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd przetwarzania danych wejściowych: {e!s}",
                text="Wystąpił błąd podczas przetwarzania danych.",
            )

        items: list[dict[str, Any]] = input_data.items
        store_name: str = input_data.store_name
        use_llm: bool = input_data.use_llm

        try:
            logger.info(f"Rozpoczynam kategoryzację {len(items)} produktów")

            if not items:
                return AgentResponse(
                    success=False,
                    error="Brak produktów do kategoryzacji",
                    text="Nie podano żadnych produktów do kategoryzacji.",
                )

            # Step 1: Przygotuj dane do kategoryzacji
            items_for_categorization = self._prepare_items_for_categorization(items)

            # Step 2: Kategoryzacja z LLM (jeśli włączona)
            categorized_items = []
            llm_used = False

            if use_llm:
                try:
                    categorized_items = await self._categorize_with_llm(
                        items_for_categorization, store_name
                    )
                    llm_used = True
                    logger.info("Kategoryzacja z LLM zakończona pomyślnie")
                except Exception as e:
                    logger.warning(f"Błąd kategoryzacji z LLM: {e}, używam fallback")
                    if self.fallback_to_dict:
                        categorized_items = await self._categorize_with_dictionary(
                            items_for_categorization
                        )
                    else:
                        categorized_items = items_for_categorization
            else:
                # Użyj tylko słownika
                categorized_items = await self._categorize_with_dictionary(
                    items_for_categorization
                )

            # Step 3: Mapowanie na Google Product Taxonomy
            categorized_items = await self._map_to_google_taxonomy(categorized_items)

            # Step 4: Oblicz confidence scores
            confidence_scores = self._calculate_confidence_scores(categorized_items)

            # Step 5: Przygotuj wynik
            categories_used = list(
                {item.get("category", "unknown") for item in categorized_items}
            )

            categorization_result = CategorizationResult(
                categorized_items=categorized_items,
                categories_used=categories_used,
                confidence_scores=confidence_scores,
                llm_used=llm_used,
            )

            logger.info(
                "Kategoryzacja paragonu zakończona",
                extra={
                    "items_count": len(categorized_items),
                    "categories_count": len(categories_used),
                    "llm_used": llm_used,
                    "avg_confidence": (
                        sum(confidence_scores.values()) / len(confidence_scores)
                        if confidence_scores
                        else 0
                    ),
                },
            )

            return AgentResponse(
                success=True,
                text=f"Pomyślnie skategoryzowano {len(categorized_items)} produktów",
                data=categorization_result.dict(),
                message="Kategoryzacja produktów zakończona",
                metadata={
                    "items_categorized": len(categorized_items),
                    "categories_used": len(categories_used),
                    "llm_used": llm_used,
                    "processing_stage": "categorization",
                },
            )

        except Exception as e:
            logger.error(f"Błąd podczas kategoryzacji paragonu: {e!s}")
            return AgentResponse(
                success=False,
                error=f"Wystąpił błąd podczas kategoryzacji: {e!s}",
                text="Wystąpił błąd podczas kategoryzacji produktów. Spróbuj ponownie.",
            )

    def _prepare_items_for_categorization(
        self, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Przygotowuje produkty do kategoryzacji."""
        prepared_items = []

        for item in items:
            prepared_item = {
                "name": item.get("name", "").strip(),
                "original_name": item.get("name", ""),
                "quantity": item.get("quantity", 1),
                "unit": item.get("unit", ""),
                "price": item.get("price", 0.0),
                "category": "unknown",
                "confidence": 0.0,
            }

            if prepared_item["name"]:
                prepared_items.append(prepared_item)

        return prepared_items

    async def _categorize_with_llm(
        self, items: list[dict[str, Any]], store_name: str
    ) -> list[dict[str, Any]]:
        """Kategoryzuje produkty z użyciem LLM."""
        try:
            # Przygotuj prompt dla LLM
            prompt = self._create_categorization_prompt(items, store_name)

            # Wywołaj LLM
            response = await hybrid_llm_client.chat(
                model="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś ekspertem od kategoryzacji produktów spożywczych i chemii gospodarczej. Kategoryzuj produkty zgodnie z polskimi standardami.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or "message" not in response:
                raise Exception("LLM nie zwrócił odpowiedzi")

            # Parsuj odpowiedź LLM
            categorized_items = self._parse_llm_categorization_response(
                response["message"]["content"], items
            )

            return categorized_items

        except Exception as e:
            logger.error(f"Błąd kategoryzacji z LLM: {e}")
            raise

    def _create_categorization_prompt(
        self, items: list[dict[str, Any]], store_name: str
    ) -> str:
        """Tworzy prompt dla LLM do kategoryzacji."""
        items_text = "\n".join(
            [
                f"- {item['name']} (ilość: {item['quantity']}, cena: {item['price']} zł)"
                for item in items
            ]
        )

        prompt = f"""Kategoryzuj poniższe produkty z paragonu ze sklepu "{store_name}".

Produkty:
{items_text}

Kategorie do użycia:
- pieczywo (chleb, bułki, ciastka)
- nabiał (mleko, ser, jogurt, masło)
- mięso (wędliny, mięso świeże, konserwy)
- warzywa (świeże warzywa, owoce)
- napoje (woda, soki, napoje gazowane)
- słodycze (cukierki, czekolada, lody)
- chemia (proszki, płyny, kosmetyki)
- alkohol (piwo, wino, wódka)
- inne

Zwróć JSON w formacie:
{{
  "categorized_items": [
    {{
      "name": "nazwa produktu",
      "category": "kategoria",
      "confidence": 0.95
    }}
  ]
}}

Zwróć tylko JSON, bez dodatkowych komentarzy."""

        return prompt

    def _parse_llm_categorization_response(
        self, response: str, original_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Parsuje odpowiedź LLM z kategoryzacją."""
        try:
            import json
            import re

            # Enhanced JSON extraction with multiple patterns
            json_patterns = [
                r"\{[\s\S]*\}",  # Basic JSON object
                r"```json\s*(\{[\s\S]*?\})\s*```",  # JSON in markdown code block
                r"```\s*(\{[\s\S]*?\})\s*```",  # JSON in code block
            ]

            parsed_data = None
            for pattern in json_patterns:
                matches = re.findall(pattern, response)
                for match in matches:
                    try:
                        # Handle both direct matches and group matches
                        json_str = (
                            match
                            if isinstance(match, str)
                            else match[0] if match else ""
                        )
                        if json_str:
                            parsed_data = json.loads(json_str)
                            logger.info("Successfully parsed JSON from LLM response")
                            break
                    except json.JSONDecodeError as e:
                        logger.debug(
                            f"Failed to parse JSON with pattern {pattern}: {e}"
                        )
                        continue

                if parsed_data:
                    break

            if not parsed_data:
                logger.warning("No valid JSON found in LLM response")
                return original_items

            categorized_items = parsed_data.get("categorized_items", [])

            if not isinstance(categorized_items, list):
                logger.warning("categorized_items is not a list in LLM response")
                return original_items

            # Mapuj wyniki na oryginalne produkty z enhanced matching
            result = []
            for original_item in enumerate(original_items):
                original_name = original_item[1].get("name", "").lower().strip()

                # Find matching categorized item with multiple strategies
                categorized_item = None

                # Strategy 1: Exact name match
                for item in categorized_items:
                    if item.get("name", "").lower().strip() == original_name:
                        categorized_item = item
                        break

                # Strategy 2: Partial name match
                if not categorized_item:
                    for item in categorized_items:
                        item_name = item.get("name", "").lower().strip()
                        if (
                            item_name in original_name
                            or original_name in item_name
                            or any(word in original_name for word in item_name.split())
                        ):
                            categorized_item = item
                            break

                # Strategy 3: Fuzzy matching for similar names
                if not categorized_item:
                    for item in categorized_items:
                        item_name = item.get("name", "").lower().strip()
                        # Simple similarity check
                        if len(set(original_name.split()) & set(item_name.split())) > 0:
                            categorized_item = item
                            break

                if categorized_item:
                    # Validate confidence score
                    confidence = categorized_item.get("confidence", 0.5)
                    try:
                        confidence = float(confidence)
                        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
                    except (ValueError, TypeError):
                        confidence = 0.5

                    result.append(
                        {
                            **original_item[1],
                            "category": categorized_item.get("category", "unknown"),
                            "confidence": confidence,
                        }
                    )
                else:
                    result.append(
                        {**original_item[1], "category": "unknown", "confidence": 0.0}
                    )

            return result

        except Exception as e:
            logger.warning(f"Błąd parsowania odpowiedzi LLM: {e}")
            # Zwróć oryginalne produkty bez kategoryzacji
            return original_items

    async def _categorize_with_dictionary(
        self, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Kategoryzuje produkty z użyciem słownika."""
        try:
            categorized_items = []

            for item in items:
                (
                    category,
                    confidence,
                ) = await self.product_categorizer.categorize_product(item["name"])

                categorized_items.append(
                    {**item, "category": category, "confidence": confidence}
                )

            return categorized_items

        except Exception as e:
            logger.warning(f"Błąd kategoryzacji ze słownikiem: {e}")
            # Zwróć oryginalne produkty bez kategoryzacji
            return items

    async def _map_to_google_taxonomy(
        self, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Mapuje kategorie na Google Product Taxonomy."""
        try:
            # Podstawowe mapowanie polskich kategorii na Google Product Taxonomy
            category_mapping = {
                "pieczywo": "Food & Beverage > Food Items > Bread & Baked Goods",
                "nabiał": "Food & Beverage > Food Items > Dairy Products",
                "mięso": "Food & Beverage > Food Items > Meat & Seafood",
                "warzywa": "Food & Beverage > Food Items > Fruits & Vegetables",
                "napoje": "Food & Beverage > Beverages",
                "słodycze": "Food & Beverage > Food Items > Candy & Sweets",
                "chemia": "Home & Garden > Household Supplies > Cleaning Products",
                "alkohol": "Food & Beverage > Beverages > Alcoholic Beverages",
                "inne": "Food & Beverage > Food Items",
            }

            for item in items:
                polish_category = item.get("category", "inne")
                google_category = category_mapping.get(
                    polish_category, "Food & Beverage > Food Items"
                )
                item["google_category"] = google_category

            return items

        except Exception as e:
            logger.warning(f"Błąd mapowania na Google Taxonomy: {e}")
            return items

    def _calculate_confidence_scores(
        self, items: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Oblicza confidence scores dla kategoryzacji."""
        confidence_scores = {}

        for item in items:
            item_name = item.get("name", "unknown")
            confidence = item.get("confidence", 0.0)
            confidence_scores[item_name] = confidence

        return confidence_scores

    def get_metadata(self) -> dict[str, Any]:
        """Zwraca metadane agenta."""
        return {
            "name": self.name,
            "type": "ReceiptCategorizationAgent",
            "capabilities": [
                "product categorization",
                "LLM integration",
                "Google taxonomy mapping",
            ],
            "version": "1.0",
            "processing_stage": "categorization",
            "use_llm": self.use_llm,
        }

    def get_dependencies(self) -> list:
        """Lista zależności agenta."""
        return []

    def is_healthy(self) -> bool:
        """Sprawdza czy agent jest zdrowy."""
        return True
