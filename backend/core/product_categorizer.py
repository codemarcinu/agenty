import json
import logging
import re
from typing import Any

from core.google_taxonomy_enhancer import get_google_taxonomy_enhancer
from core.hybrid_llm_client import hybrid_llm_client

logger = logging.getLogger(__name__)


class ProductCategorizer:
    """Kategoryzator produktów z integracją modelu Bielik i Google Product Taxonomy"""

    def __init__(
        self, categories_file: str = "data/config/filtered_gpt_categories.json"
    ):
        """Inicjalizuje kategoryzator z plikiem kategorii"""
        self.categories_file = categories_file
        self.categories = self._load_categories()
        self.category_keywords = self._build_keyword_index()
        self.google_taxonomy_enhancer = None
        logger.info(f"Załadowano {len(self.categories)} kategorii produktów")

    async def _ensure_google_taxonomy_loaded(self):
        """Zapewnia załadowanie Google Taxonomy Enhancer"""
        if self.google_taxonomy_enhancer is None:
            self.google_taxonomy_enhancer = await get_google_taxonomy_enhancer()

    def _load_categories(self) -> list[dict]:
        """Ładuje kategorie z pliku JSON"""
        try:
            with open(self.categories_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("categories", [])
        except FileNotFoundError:
            logger.warning(
                f"Plik kategorii {self.categories_file} nie znaleziony, używam domyślnych"
            )
            return self._get_default_categories()
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania pliku kategorii: {e}")
            return self._get_default_categories()

    def _build_keyword_index(self) -> dict[str, list[str]]:
        """Buduje indeks słów kluczowych dla szybkiego wyszukiwania"""
        keyword_index = {}
        for category in self.categories:
            category_id = category["id"]
            keywords = category.get("keywords", [])
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in keyword_index:
                    keyword_index[keyword_lower] = []
                keyword_index[keyword_lower].append(category_id)
        return keyword_index

    def _get_default_categories(self) -> list[dict]:
        """Zwraca domyślne kategorie jeśli plik nie jest dostępny"""
        return [
            {
                "id": "1",
                "name_pl": "Nabiał",
                "name_en": "Dairy Products",
                "keywords": ["mleko", "ser", "jogurt", "masło", "śmietana"],
                "parent_id": None,
            },
            {
                "id": "2",
                "name_pl": "Pieczywo",
                "name_en": "Bread & Bakery",
                "keywords": ["chleb", "bułka", "ciasto", "rogal"],
                "parent_id": None,
            },
            {
                "id": "3",
                "name_pl": "Mięso",
                "name_en": "Meat",
                "keywords": ["mięso", "wędlina", "kiełbasa", "szynka"],
                "parent_id": None,
            },
            {
                "id": "4",
                "name_pl": "Owoce i warzywa",
                "name_en": "Fruits & Vegetables",
                "keywords": ["jabłko", "pomidor", "ogórek", "marchew"],
                "parent_id": None,
            },
            {
                "id": "5",
                "name_pl": "Inne",
                "name_en": "Other",
                "keywords": ["inne", "nieznane"],
                "parent_id": None,
            },
        ]

    async def categorize_product_with_bielik(self, product_name: str) -> dict[str, Any]:
        """
        Kategoryzuje produkt używając modelu Bielik z integracją Google Product Taxonomy

        Args:
            product_name: Nazwa produktu z paragonu

        Returns:
            Dict z informacjami o kategorii
        """
        try:
            # Zapewnij załadowanie Google Taxonomy Enhancer
            await self._ensure_google_taxonomy_loaded()

            # Najpierw spróbuj Google Product Taxonomy
            google_category = (
                await self.google_taxonomy_enhancer.categorize_product_advanced(
                    product_name
                )
            )
            if google_category and google_category.get("confidence", 0) > 0.7:
                logger.info(
                    f"Kategoryzacja Google Taxonomy: {product_name} -> {google_category['name_pl']}"
                )
                return self._merge_google_and_local_categories(google_category)

            # Następnie spróbuj słownik słów kluczowych
            keyword_match = self._categorize_by_keywords(product_name)
            if keyword_match and keyword_match["confidence"] > 0.8:
                logger.info(
                    f"Kategoryzacja słownikowa: {product_name} -> {keyword_match['name_pl']}"
                )
                return keyword_match

            # Jeśli słownik nie pomógł, użyj Bielika
            bielik_category = await self._categorize_with_bielik(product_name)
            if bielik_category:
                logger.info(
                    f"Kategoryzacja Bielik: {product_name} -> {bielik_category['name_pl']}"
                )
                return bielik_category

            # Fallback do kategorii "Inne"
            return self._get_other_category()

        except Exception as e:
            logger.error(f"Błąd podczas kategoryzacji produktu '{product_name}': {e}")
            return self._get_other_category()

    def _merge_google_and_local_categories(
        self, google_category: dict[str, Any]
    ) -> dict[str, Any]:
        """Łączy kategorie Google Taxonomy z lokalnymi kategoriami"""
        merged = google_category.copy()

        # Dodaj lokalne informacje jeśli dostępne
        local_category = self._find_local_category_by_google_path(
            google_category["path"]
        )
        if local_category:
            merged.update(
                {
                    "local_id": local_category["id"],
                    "local_name_pl": local_category["name_pl"],
                    "local_name_en": local_category["name_en"],
                    "method": "google_taxonomy_with_local_mapping",
                }
            )
        else:
            merged["method"] = "google_taxonomy_only"

        return merged

    def _find_local_category_by_google_path(self, google_path: str) -> dict | None:
        """Znajduje lokalną kategorię na podstawie ścieżki Google"""
        for category in self.categories:
            gpt_path = category.get("gpt_path", "")
            if gpt_path and gpt_path in google_path:
                return category
        return None

    def _categorize_by_keywords(self, product_name: str) -> dict[str, Any] | None:
        """
        Kategoryzuje produkt na podstawie słów kluczowych

        Args:
            product_name: Nazwa produktu

        Returns:
            Dict z informacjami o kategorii lub None
        """
        product_lower = product_name.lower()
        best_match = None
        best_score = 0.0

        for category in self.categories:
            keywords = category.get("keywords", [])
            for keyword in keywords:
                keyword_lower = keyword.lower()

                # Sprawdź czy słowo kluczowe jest zawarte w nazwie produktu
                if keyword_lower in product_lower:
                    score = len(keyword_lower) / len(product_lower)
                    if score > best_score:
                        best_score = score
                        best_match = {
                            "id": category["id"],
                            "name_pl": category["name_pl"],
                            "name_en": category["name_en"],
                            "gpt_path": category.get("gpt_path", ""),
                            "confidence": score,
                            "method": "keyword_match",
                        }

        return best_match if best_score > 0.3 else None

    async def _categorize_with_bielik(self, product_name: str) -> dict[str, Any] | None:
        """
        Kategoryzuje produkt używając modelu Bielik

        Args:
            product_name: Nazwa produktu

        Returns:
            Dict z informacjami o kategorii lub None
        """
        try:
            # Przygotuj prompt dla Bielika
            prompt = self._create_categorization_prompt(product_name)

            # Wywołaj model Bielik
            response = await hybrid_llm_client.chat(
                model="SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś ekspertem od kategoryzacji produktów spożywczych. Przypisz każdy produkt do odpowiedniej kategorii.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if isinstance(response, dict) and "message" in response:
                content = response["message"]["content"]
                category_id = self._extract_category_from_bielik_response(content)
                if category_id:
                    category = self._get_category_by_id(category_id)
                    if category:
                        return {
                            "id": category["id"],
                            "name_pl": category["name_pl"],
                            "name_en": category["name_en"],
                            "gpt_path": category.get("gpt_path", ""),
                            "confidence": 0.9,
                            "method": "bielik_ai",
                        }

            return None

        except Exception as e:
            logger.error(f"Błąd podczas kategoryzacji Bielik dla '{product_name}': {e}")
            return None

    def _create_categorization_prompt(self, product_name: str) -> str:
        """Tworzy prompt do kategoryzacji dla modelu Bielik"""
        categories_text = "\n".join(
            [
                f"{cat['id']}: {cat['name_pl']} ({cat['name_en']})"
                for cat in self.categories
            ]
        )

        return f"""
        Kategoryzuj produkt: "{product_name}"

        Dostępne kategorie:
        {categories_text}

        Odpowiedz tylko numerem kategorii (np. "1" dla Nabiał).
        """

    def _extract_category_from_bielik_response(self, response: str) -> str | None:
        """Wyciąga ID kategorii z odpowiedzi Bielika"""
        # Szukaj liczby w odpowiedzi
        match = re.search(r"\b(\d+)\b", response)
        if match:
            category_id = match.group(1)
            # Sprawdź czy kategoria istnieje
            if self._get_category_by_id(category_id):
                return category_id
        return None

    def _get_category_by_id(self, category_id: str) -> dict | None:
        """Zwraca kategorię po ID"""
        for category in self.categories:
            if category["id"] == category_id:
                return category
        return None

    def _get_other_category(self) -> dict[str, Any]:
        """Zwraca kategorię 'Inne'"""
        other_category = self._get_category_by_id("5") or {
            "id": "5",
            "name_pl": "Inne",
            "name_en": "Other",
            "gpt_path": "",
        }

        return {
            "id": other_category["id"],
            "name_pl": other_category["name_pl"],
            "name_en": other_category["name_en"],
            "gpt_path": other_category.get("gpt_path", ""),
            "confidence": 0.1,
            "method": "fallback",
        }

    async def categorize_products_batch(
        self, products: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Kategoryzuje produkty wsadowo z integracją Google Product Taxonomy

        Args:
            products: Lista produktów do kategoryzacji

        Returns:
            Lista skategoryzowanych produktów
        """
        if not products:
            return []

        try:
            # Zapewnij załadowanie Google Taxonomy Enhancer
            await self._ensure_google_taxonomy_loaded()

            logger.info(f"Rozpoczynam wsadową kategoryzację {len(products)} produktów")

            # Kategoryzuj każdy produkt
            categorized_products = []
            for product in products:
                product_name = product.get("name", "")
                if not product_name:
                    continue

                # Kategoryzuj produkt
                category_info = await self.categorize_product_with_bielik(product_name)

                # Dodaj informacje o kategorii do produktu
                product.update(
                    {
                        "category": category_info["name_pl"],
                        "category_en": category_info["name_en"],
                        "category_id": category_info["id"],
                        "category_confidence": category_info["confidence"],
                        "category_method": category_info["method"],
                        "gpt_path": category_info.get("gpt_path", ""),
                        "gpt_id": category_info.get("gpt_id", ""),
                        "is_food_related": category_info.get("is_food_related", True),
                    }
                )

                categorized_products.append(product)

            logger.info(
                f"Wsadowa kategoryzacja zakończona: {len(categorized_products)} produktów"
            )
            return categorized_products

        except Exception as e:
            logger.error(f"Błąd podczas wsadowej kategoryzacji: {e}")
            # Fallback - zwróć produkty bez kategoryzacji
            return products

    async def _categorize_products_with_ai_batch(
        self, products: list[dict[str, Any]]
    ) -> None:
        """
        Kategoryzuje produkty wsadowo używając AI

        Args:
            products: Lista produktów do kategoryzacji
        """
        if not products:
            return

        try:
            # Przygotuj nazwy produktów
            product_names = [
                product.get("name", "") for product in products if product.get("name")
            ]

            if not product_names:
                return

            # Przygotuj prompt dla wsadowej kategoryzacji
            prompt = self._create_batch_categorization_prompt(product_names)

            # Wywołaj model Bielik
            response = await hybrid_llm_client.chat(
                model="SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś ekspertem od kategoryzacji produktów spożywczych. Przypisz każdy produkt do odpowiedniej kategorii.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if isinstance(response, dict) and "message" in response:
                content = response["message"]["content"]
                category_ids = self._extract_batch_categories_from_response(content)

                # Zastosuj kategorie do produktów
                for i, product in enumerate(products):
                    if i < len(category_ids) and product.get("name"):
                        category_id = category_ids[i]
                        category = self._get_category_by_id(category_id)
                        if category:
                            product.update(
                                {
                                    "category": category["name_pl"],
                                    "category_en": category["name_en"],
                                    "category_id": category["id"],
                                    "category_confidence": 0.9,
                                    "category_method": "bielik_ai_batch",
                                }
                            )

        except Exception as e:
            logger.error(f"Błąd podczas wsadowej kategoryzacji AI: {e}")

    def _create_batch_categorization_prompt(self, product_names: list[str]) -> str:
        """Tworzy prompt do wsadowej kategoryzacji"""
        categories_text = "\n".join(
            [
                f"{cat['id']}: {cat['name_pl']} ({cat['name_en']})"
                for cat in self.categories
            ]
        )

        products_text = "\n".join(
            [f"{i + 1}. {name}" for i, name in enumerate(product_names)]
        )

        return f"""
        Kategoryzuj następujące produkty:

        {products_text}

        Dostępne kategorie:
        {categories_text}

        Odpowiedz tylko numerami kategorii oddzielonymi przecinkami (np. "1,2,3").
        """

    def _extract_batch_categories_from_response(self, response: str) -> list[str]:
        """Wyciąga ID kategorii z odpowiedzi wsadowej"""
        # Szukaj liczb oddzielonych przecinkami
        matches = re.findall(r"\b(\d+)\b", response)
        return matches

    def get_category_statistics(self, products: list[dict[str, Any]]) -> dict[str, int]:
        """Zwraca statystyki kategoryzacji produktów"""
        stats = {}
        for product in products:
            category = product.get("category", "Nieznana")
            stats[category] = stats.get(category, 0) + 1
        return stats

    async def get_google_taxonomy_stats(self) -> dict[str, Any]:
        """Zwraca statystyki Google Product Taxonomy"""
        await self._ensure_google_taxonomy_loaded()
        return self.google_taxonomy_enhancer.get_food_categories_stats()

    async def search_google_categories(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Wyszukuje kategorie w Google Product Taxonomy"""
        await self._ensure_google_taxonomy_loaded()
        return self.google_taxonomy_enhancer.search_categories(query, limit)
