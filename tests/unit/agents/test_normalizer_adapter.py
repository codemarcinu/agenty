"""
Testy jednostkowe dla NormalizerAdapter

Zgodnie z regułami .cursorrules:
- Minimum 80% pokrycia kodu
- Używanie pytest i pytest-asyncio
- Testy deterministyczne (bez sleep())
"""

from unittest.mock import patch

import pandas as pd
import pytest

from backend.core.normalizer_adapter import NormalizerAdapter


class TestNormalizerAdapter:
    """Testy dla klasy NormalizerAdapter"""

    @pytest.fixture
    def sample_data(self):
        """Przykładowe dane testowe"""
        return pd.DataFrame(
            {
                "produkt": ["Coca Cola", "Pepsi-Co", "Mleko 3,2%"],
                "sklep": ["BIEDRONKA", "LIDL", "ŻABKA"],
                "cena": [5.99, 4.50, 3.99],
            }
        )

    @pytest.fixture
    def adapter(self):
        """Instancja adaptera do testów"""
        return NormalizerAdapter()

    def test_init_default(self):
        """Test inicjalizacji z domyślnymi parametrami"""
        adapter = NormalizerAdapter()

        assert adapter.use_enhanced_first is True
        # Sprawdź czy normalizatory zostały zainicjalizowane (mogą być None jeśli pliki nie istnieją)
        assert hasattr(adapter, "enhanced_normalizer")
        assert hasattr(adapter, "product_normalizer")
        assert hasattr(adapter, "store_normalizer")

    def test_init_with_config_files(self):
        """Test inicjalizacji z plikami konfiguracyjnymi"""
        with patch("pathlib.Path.exists", return_value=True):
            adapter = NormalizerAdapter(
                enhanced_config_file="test_enhanced.json",
                product_config_file="test_product.json",
                store_config_file="test_store.json",
                use_enhanced_first=False,
            )

            assert adapter.use_enhanced_first is False

    def test_normalize_product_name_auto(self, adapter):
        """Test automatycznej normalizacji nazwy produktu"""
        result = adapter.normalize_product_name("Coca Cola", method="auto")

        assert isinstance(result, dict)
        assert "original" in result
        assert "normalized" in result
        assert "confidence" in result
        assert "method" in result

    def test_normalize_product_name_enhanced(self, adapter):
        """Test normalizacji produktu metodą enhanced"""
        result = adapter.normalize_product_name("Coca Cola", method="enhanced")

        assert isinstance(result, dict)
        assert "normalizer" in result
        assert result["normalizer"] in ["enhanced", "adapter"]

    def test_normalize_product_name_product(self, adapter):
        """Test normalizacji produktu metodą product"""
        result = adapter.normalize_product_name("Coca Cola", method="product")

        assert isinstance(result, dict)
        assert "normalizer" in result
        assert result["normalizer"] in ["enhanced", "adapter", "product"]

    def test_normalize_product_name_combined(self, adapter):
        """Test normalizacji produktu metodą combined"""
        result = adapter.normalize_product_name("Coca Cola", method="combined")

        assert isinstance(result, dict)
        assert "confidence" in result

    def test_normalize_product_name_invalid_method(self, adapter):
        """Test normalizacji produktu z nieprawidłową metodą"""
        result = adapter.normalize_product_name("Coca Cola", method="invalid")

        assert isinstance(result, dict)
        assert result["normalized"] == "Nieznany produkt"

    def test_normalize_product_name_empty_input(self, adapter):
        """Test normalizacji produktu z pustym inputem"""
        result = adapter.normalize_product_name("", method="auto")

        assert isinstance(result, dict)
        assert result["normalized"] == "Nieznany produkt"

    def test_normalize_store_name_auto(self, adapter):
        """Test automatycznej normalizacji nazwy sklepu"""
        result = adapter.normalize_store_name("BIEDRONKA", method="auto")

        assert isinstance(result, dict)
        assert "normalized_name" in result
        assert "confidence" in result
        assert "method" in result

    def test_normalize_store_name_enhanced(self, adapter):
        """Test normalizacji sklepu metodą enhanced"""
        result = adapter.normalize_store_name("BIEDRONKA", method="enhanced")

        assert isinstance(result, dict)
        assert "normalizer" in result
        assert result["normalizer"] in ["enhanced", "adapter"]

    def test_normalize_store_name_store(self, adapter):
        """Test normalizacji sklepu metodą store"""
        result = adapter.normalize_store_name("BIEDRONKA", method="store")

        assert isinstance(result, dict)
        assert "normalizer" in result
        assert result["normalizer"] in ["enhanced", "adapter", "store"]

    def test_normalize_store_name_combined(self, adapter):
        """Test normalizacji sklepu metodą combined"""
        result = adapter.normalize_store_name("BIEDRONKA", method="combined")

        assert isinstance(result, dict)
        assert "confidence" in result

    def test_normalize_store_name_invalid_method(self, adapter):
        """Test normalizacji sklepu z nieprawidłową metodą"""
        result = adapter.normalize_store_name("BIEDRONKA", method="invalid")

        assert isinstance(result, dict)
        assert result["normalized_name"] == "Nieznany sklep"

    def test_normalize_store_name_empty_input(self, adapter):
        """Test normalizacji sklepu z pustym inputem"""
        result = adapter.normalize_store_name("", method="auto")

        assert isinstance(result, dict)
        assert result["normalized_name"] == "Nieznany sklep"

    def test_normalize_dataframe_products_only(self, adapter, sample_data):
        """Test normalizacji DataFrame z tylko produktami"""
        result = adapter.normalize_dataframe(
            sample_data.copy(), product_column="produkt", method="auto"
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)
        assert "produkt" in result.columns

    def test_normalize_dataframe_stores_only(self, adapter, sample_data):
        """Test normalizacji DataFrame z tylko sklepami"""
        result = adapter.normalize_dataframe(
            sample_data.copy(), store_column="sklep", method="auto"
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)
        assert "sklep" in result.columns

    def test_normalize_dataframe_both_columns(self, adapter, sample_data):
        """Test normalizacji DataFrame z produktami i sklepami"""
        result = adapter.normalize_dataframe(
            sample_data.copy(),
            product_column="produkt",
            store_column="sklep",
            method="auto",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)
        assert "produkt" in result.columns
        assert "sklep" in result.columns

    def test_normalize_dataframe_no_columns(self, adapter, sample_data):
        """Test normalizacji DataFrame bez kolumn do normalizacji"""
        result = adapter.normalize_dataframe(sample_data.copy(), method="auto")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)
        # DataFrame powinien być identyczny
        pd.testing.assert_frame_equal(result, sample_data)

    def test_normalize_dataframe_nonexistent_column(self, adapter, sample_data):
        """Test normalizacji DataFrame z nieistniejącą kolumną"""
        result = adapter.normalize_dataframe(
            sample_data.copy(), product_column="nieistniejaca_kolumna", method="auto"
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)
        # DataFrame powinien być identyczny
        pd.testing.assert_frame_equal(result, sample_data)

    def test_get_statistics(self, adapter):
        """Test pobierania statystyk"""
        stats = adapter.get_statistics()

        assert isinstance(stats, dict)
        assert "enhanced_normalizer" in stats
        assert "product_normalizer" in stats
        assert "store_normalizer" in stats
        assert "total_normalizers" in stats
        assert isinstance(stats["total_normalizers"], int)

    def test_enhanced_normalizer_fallback(self, adapter):
        """Test fallback gdy EnhancedNameNormalizer nie jest dostępny"""
        # Symuluj brak EnhancedNameNormalizer
        adapter.enhanced_normalizer = None

        result = adapter.normalize_product_name("Coca Cola", method="auto")

        assert isinstance(result, dict)
        # Powinien użyć fallback - może być różny wynik w zależności od konfiguracji
        assert "normalized" in result

    def test_product_normalizer_fallback(self, adapter):
        """Test fallback gdy ProductNameNormalizer nie jest dostępny"""
        # Symuluj brak ProductNameNormalizer
        adapter.product_normalizer = None

        result = adapter.normalize_product_name("Coca Cola", method="product")

        assert isinstance(result, dict)
        assert result["normalized"] == "Nieznany produkt"

    def test_store_normalizer_fallback(self, adapter):
        """Test fallback gdy StoreNormalizer nie jest dostępny"""
        # Symuluj brak StoreNormalizer
        adapter.store_normalizer = None

        result = adapter.normalize_store_name("BIEDRONKA", method="store")

        assert isinstance(result, dict)
        assert result["normalized_name"] == "Nieznany sklep"

    def test_combined_method_with_multiple_normalizers(self, adapter):
        """Test metody combined z wieloma normalizatorami"""
        result = adapter.normalize_product_name("Coca Cola", method="combined")

        assert isinstance(result, dict)
        assert "confidence" in result
        # Powinien wybrać najlepszy wynik
        assert result["confidence"] >= 0.0

    def test_auto_method_enhanced_first_true(self, adapter):
        """Test metody auto z use_enhanced_first=True"""
        adapter.use_enhanced_first = True

        result = adapter.normalize_product_name("Coca Cola", method="auto")

        assert isinstance(result, dict)
        assert "method" in result

    def test_auto_method_enhanced_first_false(self, adapter):
        """Test metody auto z use_enhanced_first=False"""
        adapter.use_enhanced_first = False

        result = adapter.normalize_product_name("Coca Cola", method="auto")

        assert isinstance(result, dict)
        assert "method" in result

    def test_error_handling_in_normalization(self, adapter):
        """Test obsługi błędów podczas normalizacji"""
        # Symuluj błąd w normalizatorze przez ustawienie enhanced_normalizer na None
        adapter.enhanced_normalizer = None

        result = adapter.normalize_product_name("Coca Cola", method="enhanced")

        assert isinstance(result, dict)
        assert result["normalized"] == "Nieznany produkt"

    def test_handle_pandas_na_values(self, adapter, sample_data):
        """Test obsługi wartości NaN w pandas"""
        # Dodaj wartości NaN do DataFrame
        sample_data.loc[1, "produkt"] = None
        sample_data.loc[2, "sklep"] = pd.NA

        result = adapter.normalize_dataframe(
            sample_data.copy(),
            product_column="produkt",
            store_column="sklep",
            method="auto",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)

    def test_normalize_single_text_with_enhanced(self, adapter):
        """Test normalizacji pojedynczego tekstu z EnhancedNameNormalizer"""
        if adapter.enhanced_normalizer:
            result = adapter._normalize_product_enhanced("Coca Cola")

            assert isinstance(result, dict)
            assert "normalizer" in result
            assert result["normalizer"] == "enhanced"

    def test_normalize_single_text_without_enhanced(self, adapter):
        """Test normalizacji pojedynczego tekstu bez EnhancedNameNormalizer"""
        adapter.enhanced_normalizer = None

        result = adapter._normalize_product_enhanced("Coca Cola")

        assert isinstance(result, dict)
        assert result["normalized"] == "Nieznany produkt"

    def test_get_unknown_product(self, adapter):
        """Test metody _get_unknown_product"""
        result = adapter._get_unknown_product()

        assert isinstance(result, dict)
        assert result["normalized"] == "Nieznany produkt"
        assert result["confidence"] == 0.0
        assert result["normalizer"] == "adapter"

    def test_get_unknown_store(self, adapter):
        """Test metody _get_unknown_store"""
        result = adapter._get_unknown_store()

        assert isinstance(result, dict)
        assert result["normalized_name"] == "Nieznany sklep"
        assert result["confidence"] == 0.0
        assert result["normalizer"] == "adapter"
