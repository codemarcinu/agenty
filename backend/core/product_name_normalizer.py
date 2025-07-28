from difflib import SequenceMatcher
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ProductNameNormalizer:
    """Normalizator nazw produktów z integracją słownika normalizacji"""

    def __init__(
        self, normalization_file: str = "data/config/product_name_normalization.json"
    ):
        """Inicjalizuje normalizator z plikiem normalizacji"""
        self.normalization_file = normalization_file
        self.normalizations = self._load_normalizations()
        self.normalization_index = self._build_normalization_index()
        logger.info(
            f"Załadowano {len(self.normalizations)} reguł normalizacji nazw produktów"
        )

    def _load_normalizations(self) -> list[dict]:
        """Ładuje reguły normalizacji z pliku JSON"""
        try:
            with open(self.normalization_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("normalizations", [])
        except FileNotFoundError:
            logger.warning(
                f"Plik normalizacji {self.normalization_file} nie znaleziony, używam domyślnych"
            )
            return self._get_default_normalizations()
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania pliku normalizacji: {e}")
            return self._get_default_normalizations()

    def _build_normalization_index(self) -> dict[str, dict]:
        """Buduje indeks normalizacji dla szybkiego wyszukiwania"""
        normalization_index = {}
        for norm in self.normalizations:
            original_lower = norm["original"].lower()
            normalization_index[original_lower] = norm

            # Dodaj również wariacje z keywords
            keywords = norm.get("keywords", [])
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in normalization_index:
                    normalization_index[keyword_lower] = norm
        return normalization_index

    def _get_default_normalizations(self) -> list[dict]:
        """Zwraca domyślne reguły normalizacji jeśli plik nie jest dostępny"""
        return [
            {
                "original": "mleko 3,2%",
                "normalized": "Mleko 3.2%",
                "category": "dairy",
                "keywords": ["mleko", "3.2%", "3,2%"],
            },
            {
                "original": "ser żółty",
                "normalized": "Ser żółty",
                "category": "dairy",
                "keywords": ["ser", "żółty", "zolty"],
            },
            {
                "original": "chleb żytni",
                "normalized": "Chleb żytni",
                "category": "bread",
                "keywords": ["chleb", "żytni", "zytni"],
            },
            {
                "original": "jabłko",
                "normalized": "Jabłko",
                "category": "fruits",
                "keywords": ["jabłko", "jablko"],
            },
            {
                "original": "pomidor",
                "normalized": "Pomidor",
                "category": "vegetables",
                "keywords": ["pomidor"],
            },
        ]

    def normalize_product_name(self, product_name: str) -> dict[str, str]:
        """
        Normalizuje nazwę produktu z paragonu

        Args:
            product_name: Nazwa produktu z paragonu

        Returns:
            Dict z znormalizowanymi informacjami o produkcie
        """
        if not product_name or not product_name.strip():
            return self._get_unknown_product()

        product_name_clean = self._clean_product_name(product_name)

        # Najpierw spróbuj dokładnego dopasowania
        exact_match = self._find_exact_match(product_name_clean)
        if exact_match:
            logger.info(
                f"Dokładne dopasowanie produktu: {product_name} -> {exact_match['normalized']}"
            )
            return exact_match

        # Następnie spróbuj dopasowania częściowego
        partial_match = self._find_partial_match(product_name_clean)
        if partial_match and partial_match["confidence"] > 0.7:
            logger.info(
                f"Częściowe dopasowanie produktu: {product_name} -> {partial_match['normalized']}"
            )
            return partial_match

        # Na końcu spróbuj dopasowania fuzzy
        fuzzy_match = self._find_fuzzy_match(product_name_clean)
        if fuzzy_match and fuzzy_match["confidence"] > 0.6:
            logger.info(
                f"Fuzzy dopasowanie produktu: {product_name} -> {fuzzy_match['normalized']}"
            )
            return fuzzy_match

        # Fallback do oryginalnej nazwy
        logger.info(f"Nie znaleziono dopasowania dla produktu: {product_name}")
        return self._get_original_product(product_name)

    def _clean_product_name(self, product_name: str) -> str:
        """Czyści nazwę produktu z niepotrzebnych znaków"""
        # Usuń białe znaki
        cleaned = product_name.strip()

        # Usuń typowe sufixy produktowe
        suffixes_to_remove = [
            r"\s+kg\s*$",
            r"\s+g\s*$",
            r"\s+l\s*$",
            r"\s+ml\s*$",
            r"\s+szt\s*$",
            r"\s+op\s*$",
            r"\s+opak\s*$",
            r"\s+paczka\s*$",
            r"\s+butelka\s*$",
            r"\s+puszka\s*$",
            r"\s*\*\s*$",  # Usuń gwiazdki na końcu (naprawiony pattern)
            r"\s+-\s*$",  # Usuń myślniki na końcu
        ]

        for suffix in suffixes_to_remove:
            cleaned = re.sub(suffix, "", cleaned, flags=re.IGNORECASE)

        # Usuń nadmiarowe białe znaki
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    def _find_exact_match(self, product_name: str) -> dict[str, str] | None:
        """Znajduje dokładne dopasowanie nazwy produktu"""
        product_name_lower = product_name.lower()

        # Sprawdź w indeksie normalizacji
        if product_name_lower in self.normalization_index:
            norm_info = self.normalization_index[product_name_lower]
            return {
                "original": product_name,
                "normalized": norm_info["normalized"],
                "category": norm_info.get("category", "unknown"),
                "confidence": 1.0,
                "method": "exact_match",
            }

        return None

    def _find_partial_match(self, product_name: str) -> dict[str, str] | None:
        """Znajduje częściowe dopasowanie nazwy produktu"""
        product_name_lower = product_name.lower()
        best_match = None
        best_score = 0.0

        for norm in self.normalizations:
            original_lower = norm["original"].lower()
            keywords = norm.get("keywords", [])

            # Sprawdź czy nazwa produktu zawiera oryginalną nazwę lub słowa kluczowe
            if (
                original_lower in product_name_lower
                or product_name_lower in original_lower
            ):
                similarity = SequenceMatcher(
                    None, product_name_lower, original_lower
                ).ratio()
                if similarity > best_score:
                    best_score = similarity
                    best_match = {
                        "original": product_name,
                        "normalized": norm["normalized"],
                        "category": norm.get("category", "unknown"),
                        "confidence": similarity,
                        "method": "partial_match",
                    }

            # Sprawdź słowa kluczowe
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in product_name_lower:
                    similarity = len(keyword_lower) / len(product_name_lower)
                    if similarity > best_score:
                        best_score = similarity
                        best_match = {
                            "original": product_name,
                            "normalized": norm["normalized"],
                            "category": norm.get("category", "unknown"),
                            "confidence": similarity,
                            "method": "keyword_match",
                        }

        return best_match if best_score > 0.5 else None

    def _find_fuzzy_match(self, product_name: str) -> dict[str, str] | None:
        """Znajduje fuzzy dopasowanie nazwy produktu"""
        product_name_lower = product_name.lower()
        best_match = None
        best_score = 0.0

        for norm in self.normalizations:
            original_lower = norm["original"].lower()

            # Oblicz podobieństwo fuzzy
            similarity = SequenceMatcher(
                None, product_name_lower, original_lower
            ).ratio()
            if similarity > best_score:
                best_score = similarity
                best_match = {
                    "original": product_name,
                    "normalized": norm["normalized"],
                    "category": norm.get("category", "unknown"),
                    "confidence": similarity,
                    "method": "fuzzy_match",
                }

        return best_match if best_score > 0.6 else None

    def _get_unknown_product(self) -> dict[str, str]:
        """Zwraca informacje o nieznanym produkcie"""
        return {
            "original": "Nieznany produkt",
            "normalized": "Nieznany produkt",
            "category": "unknown",
            "confidence": 0.0,
            "method": "unknown",
        }

    def _get_original_product(self, product_name: str) -> dict[str, str]:
        """Zwraca oryginalną nazwę produktu bez normalizacji"""
        return {
            "original": product_name,
            "normalized": product_name,
            "category": "unknown",
            "confidence": 0.0,
            "method": "no_match",
        }

    def normalize_products_batch(
        self, products: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Normalizuje listę produktów

        Args:
            products: Lista produktów z paragonu

        Returns:
            Lista produktów z znormalizowanymi nazwami
        """
        normalized_products = []

        for product in products:
            product_name = product.get("name", "")
            if product_name:
                normalized_info = self.normalize_product_name(product_name)
                product["original_name"] = normalized_info["original"]
                product["normalized_name"] = normalized_info["normalized"]
                product["product_category"] = normalized_info["category"]
                product["normalization_confidence"] = normalized_info["confidence"]
                product["normalization_method"] = normalized_info["method"]
            else:
                # Domyślne wartości dla produktów bez nazwy
                product["original_name"] = "Nieznany produkt"
                product["normalized_name"] = "Nieznany produkt"
                product["product_category"] = "unknown"
                product["normalization_confidence"] = 0.0
                product["normalization_method"] = "no_name"

            normalized_products.append(product)

        return normalized_products

    def get_normalization_statistics(
        self, products: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Zwraca statystyki normalizacji produktów"""
        stats = {
            "total_products": len(products),
            "normalized_products": 0,
            "original_products": 0,
            "by_method": {},
            "by_category": {},
            "by_confidence": {
                "high": 0,  # > 0.8
                "medium": 0,  # 0.5-0.8
                "low": 0,  # < 0.5
            },
        }

        for product in products:
            confidence = product.get("normalization_confidence", 0.0)
            method = product.get("normalization_method", "unknown")
            category = product.get("product_category", "unknown")

            if confidence > 0.5:
                stats["normalized_products"] += 1
            else:
                stats["original_products"] += 1

            # Statystyki według metody
            stats["by_method"][method] = stats["by_method"].get(method, 0) + 1

            # Statystyki według kategorii
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # Statystyki według pewności
            if confidence > 0.8:
                stats["by_confidence"]["high"] += 1
            elif confidence > 0.5:
                stats["by_confidence"]["medium"] += 1
            else:
                stats["by_confidence"]["low"] += 1

        return stats

    def add_custom_normalization(self, normalization_info: dict[str, str]) -> bool:
        """
        Dodaje niestandardową regułę normalizacji

        Args:
            normalization_info: Informacje o normalizacji do dodania

        Returns:
            True jeśli dodano pomyślnie, False w przeciwnym razie
        """
        try:
            # Sprawdź czy normalizacja już istnieje
            existing_norm = next(
                (
                    norm
                    for norm in self.normalizations
                    if norm["original"] == normalization_info["original"]
                ),
                None,
            )

            if existing_norm:
                logger.warning(
                    f"Normalizacja {normalization_info['original']} już istnieje w słowniku"
                )
                return False

            # Dodaj nową normalizację
            new_norm = {
                "original": normalization_info["original"],
                "normalized": normalization_info["normalized"],
                "category": normalization_info.get("category", "unknown"),
                "keywords": normalization_info.get(
                    "keywords", [normalization_info["original"]]
                ),
            }

            self.normalizations.append(new_norm)

            # Zaktualizuj indeks normalizacji
            self.normalization_index = self._build_normalization_index()

            logger.info(
                f"Dodano niestandardową normalizację: {normalization_info['original']} -> {normalization_info['normalized']}"
            )
            return True

        except Exception as e:
            logger.error(f"Błąd podczas dodawania niestandardowej normalizacji: {e}")
            return False
