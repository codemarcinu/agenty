"""
Normalizer Adapter - Integracja EnhancedNameNormalizer z istniejącymi normalizatorami

Zgodnie z regułami .cursorrules:
- Pełne type hints i docstrings
- Async support gdzie potrzebne
- Integracja z istniejącym systemem logowania
- Zgodność z architekturą FoodSave AI
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.enhanced_name_normalizer import EnhancedNameNormalizer
from core.product_name_normalizer import ProductNameNormalizer
from core.store_normalizer import StoreNormalizer

logger = logging.getLogger(__name__)


class NormalizerAdapter:
    """
    Adapter integrujący EnhancedNameNormalizer z istniejącymi normalizatorami.

    Zapewnia jednolity interfejs do normalizacji nazw produktów i sklepów
    z wykorzystaniem różnych technik normalizacji.
    """

    def __init__(
        self,
        enhanced_config_file: str | None = None,
        product_config_file: str | None = None,
        store_config_file: str | None = None,
        use_enhanced_first: bool = True,
    ):
        """
        Inicjalizuje adapter z różnymi normalizatorami.

        Args:
            enhanced_config_file: Plik konfiguracyjny dla EnhancedNameNormalizer
            product_config_file: Plik konfiguracyjny dla ProductNameNormalizer
            store_config_file: Plik konfiguracyjny dla StoreNormalizer
            use_enhanced_first: Czy używać EnhancedNameNormalizer jako pierwszej opcji
        """
        self.use_enhanced_first = use_enhanced_first

        # Inicjalizacja normalizatorów
        self.enhanced_normalizer = None
        self.product_normalizer = None
        self.store_normalizer = None

        try:
            if enhanced_config_file:
                self.enhanced_normalizer = EnhancedNameNormalizer(
                    config_file=enhanced_config_file
                )
            else:
                # Użyj domyślnej konfiguracji
                default_config = Path("data/config/enhanced_normalizer_config.json")
                if default_config.exists():
                    self.enhanced_normalizer = EnhancedNameNormalizer(
                        config_file=str(default_config)
                    )
                else:
                    self.enhanced_normalizer = EnhancedNameNormalizer()

            logger.info("EnhancedNameNormalizer zainicjalizowany")
        except Exception as e:
            logger.warning(f"Nie udało się zainicjalizować EnhancedNameNormalizer: {e}")

        try:
            if product_config_file:
                self.product_normalizer = ProductNameNormalizer(product_config_file)
            else:
                self.product_normalizer = ProductNameNormalizer()

            logger.info("ProductNameNormalizer zainicjalizowany")
        except Exception as e:
            logger.warning(f"Nie udało się zainicjalizować ProductNameNormalizer: {e}")

        try:
            if store_config_file:
                self.store_normalizer = StoreNormalizer(store_config_file)
            else:
                self.store_normalizer = StoreNormalizer()

            logger.info("StoreNormalizer zainicjalizowany")
        except Exception as e:
            logger.warning(f"Nie udało się zainicjalizować StoreNormalizer: {e}")

    def normalize_product_name(
        self, product_name: str, method: str = "auto"
    ) -> dict[str, Any]:
        """
        Normalizuje nazwę produktu używając dostępnych normalizatorów.

        Args:
            product_name: Nazwa produktu do normalizacji
            method: Metoda normalizacji ('auto', 'enhanced', 'product', 'combined')

        Returns:
            Dict z znormalizowanymi informacjami o produkcie
        """
        if not product_name or not product_name.strip():
            return self._get_unknown_product()

        if method == "auto":
            return self._normalize_product_auto(product_name)
        if method == "enhanced":
            return self._normalize_product_enhanced(product_name)
        if method == "product":
            return self._normalize_product_legacy(product_name)
        if method == "combined":
            return self._normalize_product_combined(product_name)
        logger.warning(f"Nieznana metoda normalizacji produktu: {method}")
        return self._get_unknown_product()

    def normalize_store_name(
        self, store_name: str, method: str = "auto"
    ) -> dict[str, Any]:
        """
        Normalizuje nazwę sklepu używając dostępnych normalizatorów.

        Args:
            store_name: Nazwa sklepu do normalizacji
            method: Metoda normalizacji ('auto', 'enhanced', 'store', 'combined')

        Returns:
            Dict z znormalizowanymi informacjami o sklepie
        """
        if not store_name or not store_name.strip():
            return self._get_unknown_store()

        if method == "auto":
            return self._normalize_store_auto(store_name)
        if method == "enhanced":
            return self._normalize_store_enhanced(store_name)
        if method == "store":
            return self._normalize_store_legacy(store_name)
        if method == "combined":
            return self._normalize_store_combined(store_name)
        logger.warning(f"Nieznana metoda normalizacji sklepu: {method}")
        return self._get_unknown_store()

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        product_column: str | None = None,
        store_column: str | None = None,
        method: str = "auto",
    ) -> pd.DataFrame:
        """
        Normalizuje DataFrame z nazwami produktów i/lub sklepów.

        Args:
            df: DataFrame do normalizacji
            product_column: Nazwa kolumny z nazwami produktów
            store_column: Nazwa kolumny z nazwami sklepów
            method: Metoda normalizacji

        Returns:
            DataFrame z znormalizowanymi danymi
        """
        result_df = df.copy()

        if product_column and product_column in df.columns:
            logger.info(f"Normalizuję kolumnę produktów: {product_column}")
            result_df = self._normalize_product_column(
                result_df, product_column, method
            )

        if store_column and store_column in df.columns:
            logger.info(f"Normalizuję kolumnę sklepów: {store_column}")
            result_df = self._normalize_store_column(result_df, store_column, method)

        return result_df

    def _normalize_product_auto(self, product_name: str) -> dict[str, Any]:
        """Automatyczny wybór najlepszej metody normalizacji produktu."""
        if self.use_enhanced_first and self.enhanced_normalizer:
            # Spróbuj EnhancedNameNormalizer
            enhanced_result = self._normalize_product_enhanced(product_name)
            if enhanced_result.get("confidence", 0) > 0.8:
                return enhanced_result

        if self.product_normalizer:
            # Fallback do ProductNameNormalizer
            return self._normalize_product_legacy(product_name)

        # Ostateczny fallback
        return self._get_unknown_product()

    def _normalize_product_enhanced(self, product_name: str) -> dict[str, Any]:
        """Normalizacja produktu używając EnhancedNameNormalizer."""
        if not self.enhanced_normalizer:
            return self._get_unknown_product()

        try:
            # Spróbuj różne metody EnhancedNameNormalizer
            methods = ["flashtext", "regex", "fuzzy"]

            for method in methods:
                normalized = self.enhanced_normalizer.normalize_single(
                    product_name, method
                )
                if normalized != product_name:
                    return {
                        "original": product_name,
                        "normalized": normalized,
                        "category": "unknown",
                        "confidence": 0.9 if method == "flashtext" else 0.7,
                        "method": f"enhanced_{method}",
                        "normalizer": "enhanced",
                    }

            # Brak dopasowania
            return {
                "original": product_name,
                "normalized": product_name,
                "category": "unknown",
                "confidence": 0.0,
                "method": "enhanced_no_match",
                "normalizer": "enhanced",
            }

        except Exception as e:
            logger.error(f"Błąd w EnhancedNameNormalizer: {e}")
            return self._get_unknown_product()

    def _normalize_product_legacy(self, product_name: str) -> dict[str, Any]:
        """Normalizacja produktu używając ProductNameNormalizer."""
        if not self.product_normalizer:
            return self._get_unknown_product()

        try:
            result = self.product_normalizer.normalize_product_name(product_name)
            # Dodaj informację o normalizatorze
            result["normalizer"] = "product"
            return result
        except Exception as e:
            logger.error(f"Błąd w ProductNameNormalizer: {e}")
            return self._get_unknown_product()

    def _normalize_product_combined(self, product_name: str) -> dict[str, Any]:
        """Kombinacja metod normalizacji produktu."""
        results = []

        if self.enhanced_normalizer:
            enhanced_result = self._normalize_product_enhanced(product_name)
            results.append(enhanced_result)

        if self.product_normalizer:
            legacy_result = self._normalize_product_legacy(product_name)
            results.append(legacy_result)

        # Wybierz najlepszy wynik
        if results:
            best_result = max(results, key=lambda x: x.get("confidence", 0))
            return best_result

        return self._get_unknown_product()

    def _normalize_store_auto(self, store_name: str) -> dict[str, Any]:
        """Automatyczny wybór najlepszej metody normalizacji sklepu."""
        if self.use_enhanced_first and self.enhanced_normalizer:
            # Spróbuj EnhancedNameNormalizer
            enhanced_result = self._normalize_store_enhanced(store_name)
            if enhanced_result.get("confidence", 0) > 0.8:
                return enhanced_result

        if self.store_normalizer:
            # Fallback do StoreNormalizer
            return self._normalize_store_legacy(store_name)

        # Ostateczny fallback
        return self._get_unknown_store()

    def _normalize_store_enhanced(self, store_name: str) -> dict[str, Any]:
        """Normalizacja sklepu używając EnhancedNameNormalizer."""
        if not self.enhanced_normalizer:
            return self._get_unknown_store()

        try:
            # Spróbuj różne metody EnhancedNameNormalizer
            methods = ["flashtext", "regex", "fuzzy"]

            for method in methods:
                normalized = self.enhanced_normalizer.normalize_single(
                    store_name, method
                )
                if normalized != store_name:
                    return {
                        "id": "unknown",
                        "normalized_name": normalized,
                        "normalized_name_en": normalized,
                        "chain": "unknown",
                        "type": "unknown",
                        "confidence": 0.9 if method == "flashtext" else 0.7,
                        "method": f"enhanced_{method}",
                        "original_name": store_name,
                        "normalizer": "enhanced",
                    }

            # Brak dopasowania
            return {
                "id": "unknown",
                "normalized_name": store_name,
                "normalized_name_en": store_name,
                "chain": "unknown",
                "type": "unknown",
                "confidence": 0.0,
                "method": "enhanced_no_match",
                "original_name": store_name,
                "normalizer": "enhanced",
            }

        except Exception as e:
            logger.error(f"Błąd w EnhancedNameNormalizer dla sklepu: {e}")
            return self._get_unknown_store()

    def _normalize_store_legacy(self, store_name: str) -> dict[str, Any]:
        """Normalizacja sklepu używając StoreNormalizer."""
        if not self.store_normalizer:
            return self._get_unknown_store()

        try:
            result = self.store_normalizer.normalize_store_name(store_name)
            # Dodaj informację o normalizatorze
            result["normalizer"] = "store"
            return result
        except Exception as e:
            logger.error(f"Błąd w StoreNormalizer: {e}")
            return self._get_unknown_store()

    def _normalize_store_combined(self, store_name: str) -> dict[str, Any]:
        """Kombinacja metod normalizacji sklepu."""
        results = []

        if self.enhanced_normalizer:
            enhanced_result = self._normalize_store_enhanced(store_name)
            results.append(enhanced_result)

        if self.store_normalizer:
            legacy_result = self._normalize_store_legacy(store_name)
            results.append(legacy_result)

        # Wybierz najlepszy wynik
        if results:
            best_result = max(results, key=lambda x: x.get("confidence", 0))
            return best_result

        return self._get_unknown_store()

    def _normalize_product_column(
        self, df: pd.DataFrame, column: str, method: str
    ) -> pd.DataFrame:
        """Normalizuje kolumnę z nazwami produktów."""
        result_df = df.copy()

        if method == "enhanced" and self.enhanced_normalizer:
            # Użyj EnhancedNameNormalizer dla całej kolumny
            result_df = self.enhanced_normalizer.normalize_all(
                result_df, column, method="flashtext"
            )
        else:
            # Użyj indywidualnej normalizacji
            normalized_names = []
            for name in df[column]:
                normalized = self.normalize_product_name(str(name), method)
                normalized_names.append(normalized.get("normalized", name))

            result_df[column] = normalized_names

        return result_df

    def _normalize_store_column(
        self, df: pd.DataFrame, column: str, method: str
    ) -> pd.DataFrame:
        """Normalizuje kolumnę z nazwami sklepów."""
        result_df = df.copy()

        if method == "enhanced" and self.enhanced_normalizer:
            # Użyj EnhancedNameNormalizer dla całej kolumny
            result_df = self.enhanced_normalizer.normalize_all(
                result_df, column, method="flashtext"
            )
        else:
            # Użyj indywidualnej normalizacji
            normalized_names = []
            for name in df[column]:
                normalized = self.normalize_store_name(str(name), method)
                normalized_names.append(normalized.get("normalized_name", name))

            result_df[column] = normalized_names

        return result_df

    def _get_unknown_product(self) -> dict[str, Any]:
        """Zwraca informacje o nieznanym produkcie."""
        return {
            "original": "",
            "normalized": "Nieznany produkt",
            "category": "unknown",
            "confidence": 0.0,
            "method": "unknown",
            "normalizer": "adapter",
        }

    def _get_unknown_store(self) -> dict[str, Any]:
        """Zwraca informacje o nieznanym sklepie."""
        return {
            "id": "999",
            "normalized_name": "Nieznany sklep",
            "normalized_name_en": "Unknown store",
            "chain": "Unknown",
            "type": "unknown",
            "confidence": 0.0,
            "method": "unknown",
            "original_name": "",
            "normalizer": "adapter",
        }

    def get_statistics(self) -> dict[str, Any]:
        """Zwraca statystyki wszystkich normalizatorów."""
        stats = {
            "enhanced_normalizer": None,
            "product_normalizer": None,
            "store_normalizer": None,
            "total_normalizers": 0,
        }

        if self.enhanced_normalizer:
            stats["enhanced_normalizer"] = self.enhanced_normalizer.get_statistics()
            stats["total_normalizers"] += 1

        if self.product_normalizer:
            stats["product_normalizer"] = {
                "normalizations_count": len(self.product_normalizer.normalizations)
            }
            stats["total_normalizers"] += 1

        if self.store_normalizer:
            stats["store_normalizer"] = {
                "stores_count": len(self.store_normalizer.stores)
            }
            stats["total_normalizers"] += 1

        return stats


# Przykład użycia
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    # Inicjalizacja adaptera
    adapter = NormalizerAdapter()

    # Test normalizacji produktu
    product_result = adapter.normalize_product_name("Coca Cola", method="auto")
    logger.info(f"Produkt: {product_result}")

    # Test normalizacji sklepu
    store_result = adapter.normalize_store_name("BIEDRONKA", method="auto")
    logger.info(f"Sklep: {store_result}")

    # Test DataFrame
    df = pd.DataFrame(
        {
            "produkt": ["Coca Cola", "Pepsi-Co", "Mleko 3,2%"],
            "sklep": ["BIEDRONKA", "LIDL", "ŻABKA"],
        }
    )

    result_df = adapter.normalize_dataframe(
        df, product_column="produkt", store_column="sklep", method="auto"
    )
    logger.info(f"DataFrame po normalizacji:\n{result_df}")

    # Statystyki
    stats = adapter.get_statistics()
    logger.info(f"Statystyki: {stats}")
