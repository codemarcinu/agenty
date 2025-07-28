"""
Google Product Taxonomy Enhancer
================================

Zaawansowany moduł do integracji z Google Product Taxonomy dla FoodSave AI.
Zgodny z .cursorrules - Python standards, security-first, async operations.

Author: @backend-lead
Version: 2025-01-06
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TaxonomyCategory:
    """Reprezentuje kategorię z Google Product Taxonomy"""

    id: str
    path: str
    name_en: str
    name_pl: str | None = None
    keywords: list[str] | None = None
    parent_id: str | None = None
    level: int = 0
    is_food_related: bool = False

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        self.level = self.path.count(">")
        self.is_food_related = self._check_if_food_related()

    def _check_if_food_related(self) -> bool:
        """Sprawdza czy kategoria jest związana z żywnością"""
        food_keywords = {
            "food",
            "beverage",
            "tobacco",
            "dairy",
            "meat",
            "seafood",
            "fruits",
            "vegetables",
            "bakery",
            "snack",
            "condiment",
            "alcoholic",
            "water",
            "milk",
            "juice",
            "coffee",
            "tea",
            "soda",
            "energy",
            "drink",
            "candy",
            "chocolate",
            "cooking",
            "baking",
            "ingredient",
            "spice",
            "seasoning",
        }
        path_lower = self.path.lower()
        return any(keyword in path_lower for keyword in food_keywords)


class GoogleTaxonomyEnhancer:
    """
    Zaawansowany enhancer do integracji z Google Product Taxonomy.
    Zapewnia kategoryzację produktów, wyszukiwanie i mapowanie na polskie kategorie.
    """

    def __init__(self, taxonomy_file: str = "Google_Product_Taxonomy.txt"):
        """Inicjalizuje enhancer z plikiem taksonomii"""
        self.taxonomy_file = taxonomy_file
        self.categories: dict[str, TaxonomyCategory] = {}
        self.food_categories: dict[str, TaxonomyCategory] = {}
        self.category_cache: dict[str, str] = {}
        self.polish_translations: dict[str, str] = {}
        self._load_taxonomy()
        self._load_polish_translations()
        logger.info(
            f"Google Taxonomy Enhancer zainicjalizowany: {len(self.categories)} kategorii, {len(self.food_categories)} kategorii żywności"
        )

    def _load_taxonomy(self) -> None:
        """Ładuje taksonomię z pliku Google Product Taxonomy"""
        try:
            taxonomy_path = Path(self.taxonomy_file)
            if not taxonomy_path.exists():
                logger.warning(f"Plik taksonomii {self.taxonomy_file} nie znaleziony")
                return

            with open(taxonomy_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Parse line: "ID - Category Path"
                    if " - " in line:
                        parts = line.split(" - ", 1)
                        if len(parts) == 2:
                            category_id = parts[0].strip()
                            category_path = parts[1].strip()

                            # Extract category name (last part of path)
                            category_name = category_path.split(" > ")[-1]

                            # Create category object
                            category = TaxonomyCategory(
                                id=category_id,
                                path=category_path,
                                name_en=category_name,
                            )

                            self.categories[category_id] = category

                            # Add to food categories if food-related
                            if category.is_food_related:
                                self.food_categories[category_id] = category

            logger.info(
                f"Załadowano {len(self.categories)} kategorii z Google Product Taxonomy"
            )

        except Exception as e:
            logger.error(f"Błąd podczas ładowania taksonomii: {e}")

    def _load_polish_translations(self) -> None:
        """Ładuje polskie tłumaczenia kategorii"""
        translations = {
            "Food, Beverages & Tobacco": "Żywność, Napoje i Tytoń",
            "Food Items": "Produkty spożywcze",
            "Beverages": "Napoje",
            "Dairy Products": "Nabiał",
            "Milk": "Mleko",
            "Cheese": "Sery",
            "Yogurt": "Jogurty",
            "Butter & Margarine": "Masło i margaryna",
            "Bread & Bakery Products": "Pieczywo",
            "Bread": "Chleb",
            "Pastries & Sweet Goods": "Słodkie wypieki",
            "Meat & Seafood": "Mięso i owoce morza",
            "Fresh Meat": "Świeże mięso",
            "Processed Meat": "Przetwory mięsne",
            "Fruits & Vegetables": "Owoce i warzywa",
            "Fresh Fruits": "Świeże owoce",
            "Fresh Vegetables": "Świeże warzywa",
            "Canned & Jarred Foods": "Konserwy i przetwory",
            "Frozen Foods": "Mrożonki",
            "Pasta & Noodles": "Makaron i kluski",
            "Rice & Grains": "Ryż i zboża",
            "Snack Foods": "Przekąski",
            "Candy & Chocolate": "Słodycze i czekolada",
            "Baking Supplies": "Produkty do pieczenia",
            "Condiments & Sauces": "Przyprawy i sosy",
            "Oils & Vinegars": "Oleje i octy",
            "Soft Drinks": "Napoje gazowane",
            "Water": "Woda",
            "Juices & Fruit Drinks": "Soki i napoje owocowe",
            "Coffee": "Kawa",
            "Tea": "Herbata",
            "Alcoholic Beverages": "Napoje alkoholowe",
            "Beer": "Piwo",
            "Wine": "Wino",
            "Liquor & Spirits": "Alkohole wysokoprocentowe",
        }

        self.polish_translations = translations
        logger.info(f"Załadowano {len(translations)} polskich tłumaczeń")

    def _find_category_by_path(self, path: str) -> TaxonomyCategory | None:
        """Znajduje kategorię po ścieżce"""
        for category in self.categories.values():
            if category.path == path:
                return category
        return None

    async def categorize_product_advanced(
        self, product_name: str, product_description: str = ""
    ) -> dict[str, Any]:
        """
        Zaawansowana kategoryzacja produktu z Google Product Taxonomy

        Args:
            product_name: Nazwa produktu
            product_description: Opis produktu (opcjonalny)

        Returns:
            Dict z informacjami o kategorii
        """
        try:
            # Check cache first
            cache_key = f"{product_name.lower()}:{product_description.lower()}"
            if cache_key in self.category_cache:
                category_id = self.category_cache[cache_key]
                category = self.categories.get(category_id)
                if category:
                    return self._format_category_result(
                        category, confidence=0.95, method="cache"
                    )

            # Find best matching category
            best_match = await self._find_best_category_match(
                product_name, product_description
            )

            if best_match:
                # Cache the result
                self.category_cache[cache_key] = best_match.id
                return self._format_category_result(
                    best_match, confidence=0.9, method="taxonomy_match"
                )

            # Fallback to general food category
            fallback_category = self._get_fallback_food_category()
            return self._format_category_result(
                fallback_category, confidence=0.5, method="fallback"
            )

        except Exception as e:
            logger.error(
                f"Błąd podczas zaawansowanej kategoryzacji '{product_name}': {e}"
            )
            return self._get_error_category()

    async def _find_best_category_match(
        self, product_name: str, product_description: str = ""
    ) -> TaxonomyCategory | None:
        """Znajduje najlepsze dopasowanie kategorii"""
        search_text = f"{product_name} {product_description}".lower()
        best_match = None
        best_score = 0.0

        # Search in food categories first
        for category in self.food_categories.values():
            score = self._calculate_category_score(category, search_text)
            if score > best_score:
                best_score = score
                best_match = category

        # If no good match in food categories, search in all categories
        if best_score < 0.3:
            for category in self.categories.values():
                score = self._calculate_category_score(category, search_text)
                if score > best_score:
                    best_score = score
                    best_match = category

        return best_match if best_score > 0.2 else None

    def _calculate_category_score(
        self, category: TaxonomyCategory, search_text: str
    ) -> float:
        """Oblicza score dopasowania kategorii"""
        score = 0.0

        # Check category name
        name_score = SequenceMatcher(
            None, category.name_en.lower(), search_text
        ).ratio()
        score = max(score, name_score * 0.4)

        # Check category path
        path_score = SequenceMatcher(None, category.path.lower(), search_text).ratio()
        score = max(score, path_score * 0.3)

        # Check keywords
        for keyword in category.keywords:
            if keyword.lower() in search_text:
                score += 0.2
                break

        # Bonus for food-related categories
        if category.is_food_related:
            score += 0.1

        return min(score, 1.0)

    def _format_category_result(
        self, category: TaxonomyCategory, confidence: float, method: str
    ) -> dict[str, Any]:
        """Formatuje wynik kategoryzacji"""
        return {
            "gpt_id": category.id,
            "gpt_path": category.path,
            "name_en": category.name_en,
            "name_pl": self.polish_translations.get(category.name_en, category.name_en),
            "confidence": confidence,
            "method": method,
            "is_food_related": category.is_food_related,
            "level": category.level,
        }

    def _get_fallback_food_category(self) -> TaxonomyCategory:
        """Zwraca domyślną kategorię żywności"""
        return TaxonomyCategory(
            id="412",
            path="Food, Beverages & Tobacco > Food Items",
            name_en="Food Items",
            name_pl="Produkty spożywcze",
            is_food_related=True,
        )

    def _get_error_category(self) -> dict[str, Any]:
        """Zwraca kategorię błędu"""
        return {
            "gpt_id": "error",
            "gpt_path": "Unknown",
            "name_en": "Unknown",
            "name_pl": "Nieznana",
            "confidence": 0.0,
            "method": "error",
            "is_food_related": False,
            "level": 0,
        }

    def search_categories(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Wyszukuje kategorie na podstawie zapytania

        Args:
            query: Zapytanie wyszukiwania
            limit: Maksymalna liczba wyników

        Returns:
            Lista pasujących kategorii
        """
        query_lower = query.lower()
        matches = []

        for category in self.categories.values():
            score = self._calculate_category_score(category, query_lower)
            if score > 0.1:  # Minimum threshold
                matches.append(
                    {
                        "gpt_id": category.id,
                        "gpt_path": category.path,
                        "name_en": category.name_en,
                        "name_pl": self.polish_translations.get(
                            category.name_en, category.name_en
                        ),
                        "score": score,
                        "is_food_related": category.is_food_related,
                    }
                )

        # Sort by score and limit results
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    def get_food_categories_stats(self) -> dict[str, Any]:
        """Zwraca statystyki kategorii żywności"""
        food_stats = {
            "total_categories": len(self.categories),
            "food_categories": len(self.food_categories),
            "food_percentage": (
                round(len(self.food_categories) / len(self.categories) * 100, 2)
                if self.categories
                else 0
            ),
            "top_level_food_categories": {},
            "polish_translations": len(self.polish_translations),
        }

        # Count top-level food categories
        for category in self.food_categories.values():
            if category.level == 1:  # Top level
                top_category = category.path.split(" > ")[0]
                food_stats["top_level_food_categories"][top_category] = (
                    food_stats["top_level_food_categories"].get(top_category, 0) + 1
                )

        return food_stats

    def get_category_hierarchy(
        self, category_id: str, max_depth: int = 3
    ) -> dict[str, Any]:
        """
        Zwraca hierarchię kategorii

        Args:
            category_id: ID kategorii
            max_depth: Maksymalna głębokość hierarchii

        Returns:
            Hierarchia kategorii
        """
        category = self.categories.get(category_id)
        if not category:
            return {}

        hierarchy = {
            "id": category.id,
            "name_en": category.name_en,
            "name_pl": self.polish_translations.get(category.name_en, category.name_en),
            "path": category.path,
            "level": category.level,
            "children": [],
        }

        if category.level < max_depth:
            # Find children
            for child in self.categories.values():
                if child.path.startswith(category.path + " > "):
                    child_hierarchy = self.get_category_hierarchy(child.id, max_depth)
                    if child_hierarchy:
                        hierarchy["children"].append(child_hierarchy)

        return hierarchy

    def batch_categorize_products(
        self, products: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Kategoryzuje produkty wsadowo

        Args:
            products: Lista produktów do kategoryzacji

        Returns:
            Lista skategoryzowanych produktów
        """
        categorized_products = []

        for product in products:
            product_name = product.get("name", "")
            product_description = product.get("description", "")

            # Use synchronous categorization for batch processing
            search_text = f"{product_name} {product_description}".lower()
            best_match = None
            best_score = 0.0

            # Search in food categories
            for category in self.food_categories.values():
                score = self._calculate_category_score(category, search_text)
                if score > best_score:
                    best_score = score
                    best_match = category

            if best_match and best_score > 0.2:
                category_info = self._format_category_result(
                    best_match, best_score, "batch_taxonomy"
                )
            else:
                category_info = self._format_category_result(
                    self._get_fallback_food_category(), 0.3, "batch_fallback"
                )

            # Add category info to product
            product.update(
                {
                    "gpt_category": category_info["name_en"],
                    "gpt_category_pl": category_info["name_pl"],
                    "gpt_id": category_info["gpt_id"],
                    "gpt_path": category_info["gpt_path"],
                    "gpt_confidence": category_info["confidence"],
                    "gpt_method": category_info["method"],
                    "is_food_related": category_info["is_food_related"],
                }
            )

            categorized_products.append(product)

        return categorized_products


async def get_google_taxonomy_enhancer() -> GoogleTaxonomyEnhancer:
    """Zwraca singleton instance Google Taxonomy Enhancer"""
    if not hasattr(get_google_taxonomy_enhancer, "_instance"):
        get_google_taxonomy_enhancer._instance = GoogleTaxonomyEnhancer()
    return get_google_taxonomy_enhancer._instance
