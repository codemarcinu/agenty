"""
Enhanced Name Normalizer Module

Zawiera implementację trzech głównych technik normalizacji nazw:
1. Wektorowa zamiana z pandas (DataFrame.replace)
2. FlashText dla szybkiego dopasowania słów kluczowych
3. RapidFuzz dla fuzzy matching

Zgodnie z regułami .cursorrules:
- Pełne type hints i docstrings
- Async support gdzie potrzebne
- Integracja z istniejącym systemem logowania
- Zgodność z architekturą FoodSave AI
"""

import json
import logging
from pathlib import Path
import re
from typing import Any

from flashtext import KeywordProcessor
import pandas as pd
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


class EnhancedNameNormalizer:
    """
    Zaawansowany normalizator nazw z trzema technikami normalizacji:
    - Wektorowa zamiana (pandas)
    - FlashText (szybkie dopasowanie słów kluczowych)
    - RapidFuzz (fuzzy matching)
    """

    def __init__(
        self,
        replace_dict: dict[str, str] | None = None,
        flashtext_map: dict[str, str] | None = None,
        fuzzy_choices: list[str] | None = None,
        fuzzy_threshold: int = 80,
        config_file: str | None = None,
    ):
        """
        Inicjalizuje normalizator z różnymi technikami normalizacji.

        Args:
            replace_dict: Słownik {wzorzec: zamiana} do wektorowej zamiany pandas
            flashtext_map: Słownik {alias: canonical} dla FlashText
            fuzzy_choices: Lista standardowych nazw do fuzzy matching
            fuzzy_threshold: Minimalny próg dopasowania (0-100) dla RapidFuzz
            config_file: Opcjonalny plik konfiguracyjny JSON
        """
        self.replace_dict = replace_dict or {}
        self._compile_regex_map()

        # FlashText setup
        self.kp = KeywordProcessor(case_sensitive=False)
        if flashtext_map:
            for alias, canonical in flashtext_map.items():
                self.kp.add_keyword(alias, canonical)

        # RapidFuzz setup
        self.fuzzy_choices = fuzzy_choices or []
        self.fuzzy_threshold = fuzzy_threshold

        # Load configuration if provided
        if config_file:
            self._load_config(config_file)

        logger.info(
            f"EnhancedNameNormalizer initialized with "
            f"{len(self.replace_dict)} regex patterns, "
            f"{len(self.kp.get_all_keywords())} FlashText keywords, "
            f"{len(self.fuzzy_choices)} fuzzy choices"
        )

    def _compile_regex_map(self) -> None:
        """Prekompiluje wzorce regex dla replace_dict."""
        self.regex_map = {re.compile(k): v for k, v in self.replace_dict.items()}

    def _load_config(self, config_file: str) -> None:
        """Ładuje konfigurację z pliku JSON."""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)

                # Load replace patterns
                if "replace_patterns" in config:
                    self.replace_dict.update(config["replace_patterns"])
                    self._compile_regex_map()

                # Load FlashText mappings
                if "flashtext_mappings" in config:
                    for alias, canonical in config["flashtext_mappings"].items():
                        self.kp.add_keyword(alias, canonical)

                # Load fuzzy choices
                if "fuzzy_choices" in config:
                    self.fuzzy_choices.extend(config["fuzzy_choices"])

                # Update threshold if provided
                if "fuzzy_threshold" in config:
                    self.fuzzy_threshold = config["fuzzy_threshold"]

                logger.info(f"Loaded configuration from {config_file}")
            else:
                logger.warning(f"Configuration file {config_file} not found")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")

    def normalize_vectorized(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Zamiana wszystkich wzorców z replace_dict na wartości w jednej operacji wektorowej.

        Args:
            df: DataFrame do normalizacji
            column: Nazwa kolumny do normalizacji

        Returns:
            DataFrame z znormalizowanymi danymi
        """
        if not self.replace_dict:
            logger.debug(
                "No replace patterns defined, skipping vectorized normalization"
            )
            return df

        try:
            df[column] = df[column].replace(self.replace_dict, regex=True)
            logger.debug(f"Applied vectorized normalization to {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error in vectorized normalization: {e}")
            return df

    def normalize_flashtext(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Jednoprzebiegowa zamiana pełnych słów/aliasów zgodnie z flashtext_map.

        Args:
            df: DataFrame do normalizacji
            column: Nazwa kolumny do normalizacji

        Returns:
            DataFrame z znormalizowanymi danymi
        """
        if not self.kp.get_all_keywords():
            logger.debug(
                "No FlashText keywords defined, skipping FlashText normalization"
            )
            return df

        try:
            # Obsługa wartości NaN/None w pandas
            def safe_replace(text):
                if pd.isna(text) or text is None:
                    return text
                return self.kp.replace_keywords(str(text))

            df[column] = df[column].apply(safe_replace)
            logger.debug(f"Applied FlashText normalization to {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error in FlashText normalization: {e}")
            return df

    def normalize_regex_apply(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Zastosowanie prekompilowanych regexów przez .apply (wolniejsze od vectorized).

        Args:
            df: DataFrame do normalizacji
            column: Nazwa kolumny do normalizacji

        Returns:
            DataFrame z znormalizowanymi danymi
        """
        if not self.regex_map:
            logger.debug("No regex patterns defined, skipping regex normalization")
            return df

        def _replace(s: Any) -> str:
            """Funkcja pomocnicza do zastępowania wzorców regex."""
            if pd.isna(s) or not isinstance(s, str):
                return str(s) if s is not None else ""
            for pat, repl in self.regex_map.items():
                s = pat.sub(repl, s)
            return s

        try:
            df[column] = df[column].apply(_replace)
            logger.debug(f"Applied regex normalization to {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error in regex normalization: {e}")
            return df

    def normalize_fuzzy(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Fuzzy matching nazw z wykorzystaniem RapidFuzz.

        Args:
            df: DataFrame do normalizacji
            column: Nazwa kolumny do normalizacji

        Returns:
            DataFrame z znormalizowanymi danymi
        """
        if not self.fuzzy_choices:
            logger.debug("No fuzzy choices defined, skipping fuzzy normalization")
            return df

        def _fuzzy_norm(name: Any) -> str:
            """Funkcja pomocnicza do fuzzy matching."""
            if pd.isna(name) or not isinstance(name, str):
                return str(name) if name is not None else ""

            try:
                best, score, _ = process.extractOne(
                    name, self.fuzzy_choices, scorer=fuzz.token_sort_ratio
                )
                return best if score >= self.fuzzy_threshold else name
            except Exception as e:
                logger.debug(f"Error in fuzzy matching for '{name}': {e}")
                return name

        try:
            df[column] = df[column].apply(_fuzzy_norm)
            logger.debug(f"Applied fuzzy normalization to {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error in fuzzy normalization: {e}")
            return df

    def normalize_all(
        self, df: pd.DataFrame, column: str, method: str = "vectorized"
    ) -> pd.DataFrame:
        """
        Główna metoda wybierająca technikę normalizacji.

        Args:
            df: DataFrame do normalizacji
            column: Nazwa kolumny do normalizacji
            method: Metoda normalizacji ('vectorized', 'flashtext', 'regex', 'fuzzy')

        Returns:
            DataFrame z znormalizowanymi danymi

        Raises:
            ValueError: Jeśli podano nieznaną metodę
        """
        if method == "vectorized":
            return self.normalize_vectorized(df, column)
        if method == "flashtext":
            return self.normalize_flashtext(df, column)
        if method == "regex":
            return self.normalize_regex_apply(df, column)
        if method == "fuzzy":
            return self.normalize_fuzzy(df, column)
        raise ValueError(f"Nieznana metoda normalizacji: {method}")

    def normalize_single(self, text: str, method: str = "flashtext") -> str:
        """
        Normalizuje pojedynczy tekst.

        Args:
            text: Tekst do normalizacji
            method: Metoda normalizacji

        Returns:
            Znormalizowany tekst
        """
        if not text or not isinstance(text, str):
            return ""

        try:
            if method == "flashtext":
                return self.kp.replace_keywords(text)
            if method == "regex":
                for pat, repl in self.regex_map.items():
                    text = pat.sub(repl, text)
                return text
            if method == "fuzzy":
                if self.fuzzy_choices:
                    best, score, _ = process.extractOne(
                        text, self.fuzzy_choices, scorer=fuzz.token_sort_ratio
                    )
                    return best if score >= self.fuzzy_threshold else text
                return text
            logger.warning(f"Unknown method '{method}' for single text normalization")
            return text
        except Exception as e:
            logger.error(f"Error normalizing text '{text}' with method '{method}': {e}")
            return text

    def get_statistics(self) -> dict[str, Any]:
        """
        Zwraca statystyki konfiguracji normalizatora.

        Returns:
            Słownik ze statystykami
        """
        return {
            "regex_patterns": len(self.replace_dict),
            "flashtext_keywords": len(self.kp.get_all_keywords()),
            "fuzzy_choices": len(self.fuzzy_choices),
            "fuzzy_threshold": self.fuzzy_threshold,
        }

    def add_regex_pattern(self, pattern: str, replacement: str) -> None:
        """
        Dodaje nowy wzorzec regex do normalizatora.

        Args:
            pattern: Wzorzec regex
            replacement: Zastąpienie
        """
        self.replace_dict[pattern] = replacement
        self._compile_regex_map()
        logger.info(f"Added regex pattern: '{pattern}' -> '{replacement}'")

    def add_flashtext_mapping(self, alias: str, canonical: str) -> None:
        """
        Dodaje nowe mapowanie FlashText.

        Args:
            alias: Alias do zamiany
            canonical: Nazwa kanoniczna
        """
        self.kp.add_keyword(alias, canonical)
        logger.info(f"Added FlashText mapping: '{alias}' -> '{canonical}'")

    def add_fuzzy_choice(self, choice: str) -> None:
        """
        Dodaje nowy wybór do fuzzy matching.

        Args:
            choice: Nowy wybór
        """
        if choice not in self.fuzzy_choices:
            self.fuzzy_choices.append(choice)
            logger.info(f"Added fuzzy choice: '{choice}'")


# Przykład użycia i testy
if __name__ == "__main__":
    # Konfiguracja logowania
    logging.basicConfig(level=logging.INFO)

    # Załaduj przykładowe dane
    df = pd.DataFrame(
        {
            "nazwa": [
                "Coca Cola",
                "Coke",
                "Pepsi-Co",
                "Coffe",
                "Lipton tea",
                "Liptom Tea",
            ]
        }
    )

    # Słowniki i listy
    replace_dict = {r"Pepsi[- ]?Co": "Pepsi", r"Lipton\s+tea": "Lipton Tea"}
    flashtext_map = {"Coca Cola": "Coca-Cola", "Coke": "Coca-Cola"}
    fuzzy_choices = ["Lipton Tea", "Coffee"]

    # Inicjalizacja normalizatora
    normalizer = EnhancedNameNormalizer(
        replace_dict=replace_dict,
        flashtext_map=flashtext_map,
        fuzzy_choices=fuzzy_choices,
        fuzzy_threshold=75,
    )

    # Test różnych metod
    methods = ["vectorized", "flashtext", "regex", "fuzzy"]

    for method in methods:
        df_test = df.copy()
        df_result = normalizer.normalize_all(df_test, "nazwa", method=method)

    # Test statystyk
    stats = normalizer.get_statistics()
    for key, value in stats.items():
        pass
