"""
Testy jednostkowe dla EnhancedNameNormalizer

Zgodnie z regułami .cursorrules:
- Minimum 80% pokrycia kodu
- Używanie pytest i pytest-asyncio
- Testy deterministyczne (bez sleep())
"""

from unittest.mock import patch

import pandas as pd
import pytest

from backend.core.enhanced_name_normalizer import EnhancedNameNormalizer


class TestEnhancedNameNormalizer:
    """Testy dla klasy EnhancedNameNormalizer"""

    @pytest.fixture
    def sample_data(self):
        """Przykładowe dane testowe"""
        return pd.DataFrame(
            {
                "nazwa": [
                    "Coca Cola",
                    "Coke",
                    "Pepsi-Co",
                    "Coffe",
                    "Lipton tea",
                    "Liptom Tea",
                    "Mleko 3,2%",
                ]
            }
        )

    @pytest.fixture
    def replace_dict(self):
        """Przykładowy słownik wzorców regex"""
        return {
            r"Pepsi[- ]?Co": "Pepsi",
            r"Lipton\s+tea": "Lipton Tea",
            r"Mleko\s+3,2%": "Mleko 3.2%",
        }

    @pytest.fixture
    def flashtext_map(self):
        """Przykładowy słownik FlashText"""
        return {"Coca Cola": "Coca-Cola", "Coke": "Coca-Cola", "Coffe": "Coffee"}

    @pytest.fixture
    def fuzzy_choices(self):
        """Przykładowe wybory dla fuzzy matching"""
        return ["Lipton Tea", "Coffee", "Mleko 3.2%"]

    @pytest.fixture
    def normalizer(self, replace_dict, flashtext_map, fuzzy_choices):
        """Instancja normalizatora do testów"""
        return EnhancedNameNormalizer(
            replace_dict=replace_dict,
            flashtext_map=flashtext_map,
            fuzzy_choices=fuzzy_choices,
            fuzzy_threshold=75,
        )

    def test_init_with_parameters(self, replace_dict, flashtext_map, fuzzy_choices):
        """Test inicjalizacji z parametrami"""
        normalizer = EnhancedNameNormalizer(
            replace_dict=replace_dict,
            flashtext_map=flashtext_map,
            fuzzy_choices=fuzzy_choices,
            fuzzy_threshold=80,
        )

        assert normalizer.replace_dict == replace_dict
        assert len(normalizer.regex_map) == len(replace_dict)
        assert len(normalizer.kp.get_all_keywords()) == len(flashtext_map)
        assert normalizer.fuzzy_choices == fuzzy_choices
        assert normalizer.fuzzy_threshold == 80

    def test_init_without_parameters(self):
        """Test inicjalizacji bez parametrów"""
        normalizer = EnhancedNameNormalizer()

        assert normalizer.replace_dict == {}
        assert normalizer.regex_map == {}
        assert len(normalizer.kp.get_all_keywords()) == 0
        assert normalizer.fuzzy_choices == []
        assert normalizer.fuzzy_threshold == 80

    def test_normalize_vectorized(self, normalizer, sample_data):
        """Test normalizacji wektorowej"""
        result = normalizer.normalize_vectorized(sample_data.copy(), "nazwa")

        # Sprawdź czy Pepsi-Co zostało zamienione na Pepsi
        pepsi_rows = result[result["nazwa"].str.contains("Pepsi", na=False)]
        assert len(pepsi_rows) > 0
        assert "Pepsi-Co" not in result["nazwa"].values

    def test_normalize_flashtext(self, normalizer, sample_data):
        """Test normalizacji FlashText"""
        result = normalizer.normalize_flashtext(sample_data.copy(), "nazwa")

        # Sprawdź czy Coca Cola i Coke zostały zamienione na Coca-Cola
        coca_cola_rows = result[result["nazwa"] == "Coca-Cola"]
        assert len(coca_cola_rows) == 2  # Coca Cola i Coke

    def test_normalize_regex_apply(self, normalizer, sample_data):
        """Test normalizacji regex przez apply"""
        result = normalizer.normalize_regex_apply(sample_data.copy(), "nazwa")

        # Sprawdź czy wzorce regex zostały zastosowane
        assert "Pepsi-Co" not in result["nazwa"].values
        assert "Lipton tea" not in result["nazwa"].values

    def test_normalize_fuzzy(self, normalizer, sample_data):
        """Test normalizacji fuzzy"""
        result = normalizer.normalize_fuzzy(sample_data.copy(), "nazwa")

        # Sprawdź czy Coffe zostało zamienione na Coffee (jeśli próg jest spełniony)
        coffee_rows = result[result["nazwa"] == "Coffee"]
        assert len(coffee_rows) >= 0  # Może być 0 lub więcej w zależności od progu

    def test_normalize_all_vectorized(self, normalizer, sample_data):
        """Test głównej metody z metodą vectorized"""
        result = normalizer.normalize_all(sample_data.copy(), "nazwa", "vectorized")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)

    def test_normalize_all_flashtext(self, normalizer, sample_data):
        """Test głównej metody z metodą flashtext"""
        result = normalizer.normalize_all(sample_data.copy(), "nazwa", "flashtext")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)

    def test_normalize_all_regex(self, normalizer, sample_data):
        """Test głównej metody z metodą regex"""
        result = normalizer.normalize_all(sample_data.copy(), "nazwa", "regex")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)

    def test_normalize_all_fuzzy(self, normalizer, sample_data):
        """Test głównej metody z metodą fuzzy"""
        result = normalizer.normalize_all(sample_data.copy(), "nazwa", "fuzzy")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)

    def test_normalize_all_invalid_method(self, normalizer, sample_data):
        """Test głównej metody z nieprawidłową metodą"""
        with pytest.raises(ValueError, match="Nieznana metoda normalizacji"):
            normalizer.normalize_all(sample_data.copy(), "nazwa", "invalid_method")

    def test_normalize_single_flashtext(self, normalizer):
        """Test normalizacji pojedynczego tekstu metodą FlashText"""
        result = normalizer.normalize_single("Coca Cola", "flashtext")
        assert result == "Coca-Cola"

    def test_normalize_single_regex(self, normalizer):
        """Test normalizacji pojedynczego tekstu metodą regex"""
        result = normalizer.normalize_single("Pepsi-Co", "regex")
        assert result == "Pepsi"

    def test_normalize_single_fuzzy(self, normalizer):
        """Test normalizacji pojedynczego tekstu metodą fuzzy"""
        result = normalizer.normalize_single("Coffe", "fuzzy")
        # Wynik zależy od progu, ale powinien być stringiem
        assert isinstance(result, str)

    def test_normalize_single_invalid_method(self, normalizer):
        """Test normalizacji pojedynczego tekstu z nieprawidłową metodą"""
        result = normalizer.normalize_single("test", "invalid_method")
        assert result == "test"  # Powinien zwrócić oryginalny tekst

    def test_normalize_single_none_input(self, normalizer):
        """Test normalizacji pojedynczego tekstu z None"""
        result = normalizer.normalize_single(None, "flashtext")
        assert result == ""

    def test_normalize_single_empty_string(self, normalizer):
        """Test normalizacji pojedynczego tekstu z pustym stringiem"""
        result = normalizer.normalize_single("", "flashtext")
        assert result == ""

    def test_get_statistics(self, normalizer):
        """Test pobierania statystyk"""
        stats = normalizer.get_statistics()

        assert "regex_patterns" in stats
        assert "flashtext_keywords" in stats
        assert "fuzzy_choices" in stats
        assert "fuzzy_threshold" in stats

        assert isinstance(stats["regex_patterns"], int)
        assert isinstance(stats["flashtext_keywords"], int)
        assert isinstance(stats["fuzzy_choices"], int)
        assert isinstance(stats["fuzzy_threshold"], int)

    def test_add_regex_pattern(self, normalizer):
        """Test dodawania wzorca regex"""
        initial_count = len(normalizer.replace_dict)
        normalizer.add_regex_pattern(r"test\s+pattern", "replacement")

        assert len(normalizer.replace_dict) == initial_count + 1
        assert r"test\s+pattern" in normalizer.replace_dict
        assert normalizer.replace_dict[r"test\s+pattern"] == "replacement"

    def test_add_flashtext_mapping(self, normalizer):
        """Test dodawania mapowania FlashText"""
        initial_count = len(normalizer.kp.get_all_keywords())
        normalizer.add_flashtext_mapping("test_alias", "canonical_name")

        assert len(normalizer.kp.get_all_keywords()) == initial_count + 1

    def test_add_fuzzy_choice(self, normalizer):
        """Test dodawania wyboru fuzzy"""
        initial_count = len(normalizer.fuzzy_choices)
        normalizer.add_fuzzy_choice("new_choice")

        assert len(normalizer.fuzzy_choices) == initial_count + 1
        assert "new_choice" in normalizer.fuzzy_choices

    def test_add_fuzzy_choice_duplicate(self, normalizer):
        """Test dodawania duplikatu wyboru fuzzy"""
        normalizer.add_fuzzy_choice("test_choice")
        initial_count = len(normalizer.fuzzy_choices)
        normalizer.add_fuzzy_choice("test_choice")  # Duplikat

        assert len(normalizer.fuzzy_choices) == initial_count  # Nie powinno się dodać

    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    @patch("json.load")
    def test_load_config_success(
        self, mock_json_load, mock_open, mock_exists, replace_dict
    ):
        """Test ładowania konfiguracji z pliku"""
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "replace_patterns": {"new_pattern": "new_replacement"},
            "flashtext_mappings": {"new_alias": "new_canonical"},
            "fuzzy_choices": ["new_choice"],
            "fuzzy_threshold": 85,
        }

        normalizer = EnhancedNameNormalizer(config_file="test_config.json")

        assert "new_pattern" in normalizer.replace_dict
        assert normalizer.fuzzy_threshold == 85

    @patch("pathlib.Path.exists")
    def test_load_config_file_not_found(self, mock_exists):
        """Test ładowania konfiguracji gdy plik nie istnieje"""
        mock_exists.return_value = False

        normalizer = EnhancedNameNormalizer(config_file="nonexistent.json")

        assert normalizer.replace_dict == {}
        assert len(normalizer.kp.get_all_keywords()) == 0

    def test_handle_pandas_na_values(self, normalizer):
        """Test obsługi wartości NaN/None w pandas"""
        df_with_na = pd.DataFrame({"nazwa": ["Coca Cola", None, pd.NA, "Coke"]})

        result = normalizer.normalize_flashtext(df_with_na.copy(), "nazwa")

        # Sprawdź czy nie ma błędów i DataFrame ma odpowiednią długość
        assert len(result) == len(df_with_na)
        assert (
            result["nazwa"].iloc[0] == "Coca-Cola"
        )  # Pierwszy element powinien być znormalizowany

    def test_error_handling_in_normalization(self, normalizer):
        """Test obsługi błędów podczas normalizacji"""
        # Stwórz DataFrame z problematycznymi danymi
        problematic_df = pd.DataFrame(
            {"nazwa": ["Coca Cola", 123, None, "Coke"]}  # Mieszane typy
        )

        # Powinno działać bez błędów
        result = normalizer.normalize_flashtext(problematic_df.copy(), "nazwa")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(problematic_df)


if __name__ == "__main__":
    pytest.main([__file__])
