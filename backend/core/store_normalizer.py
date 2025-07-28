from difflib import SequenceMatcher
import json
import logging
import re

logger = logging.getLogger(__name__)


class StoreNormalizer:
    """Normalizator nazw sklepów z integracją słownika polskich sklepów"""

    def __init__(self, stores_file: str = "data/config/polish_stores.json"):
        """Inicjalizuje normalizator z plikiem sklepów"""
        self.stores_file = stores_file
        self.stores = self._load_stores()
        self.store_variations = self._build_variations_index()
        logger.info(f"Załadowano {len(self.stores)} sklepów do normalizacji")

    def _load_stores(self) -> list[dict]:
        """Ładuje sklepy z pliku JSON"""
        try:
            with open(self.stores_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("stores", [])
        except FileNotFoundError:
            logger.warning(
                f"Plik sklepów {self.stores_file} nie znaleziony, używam domyślnych"
            )
            return self._get_default_stores()
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania pliku sklepów: {e}")
            return self._get_default_stores()

    def _build_variations_index(self) -> dict[str, dict]:
        """Buduje indeks wariacji nazw sklepów dla szybkiego wyszukiwania"""
        variations_index = {}
        for store in self.stores:
            store_id = store["id"]
            variations = store.get("variations", [])
            for variation in variations:
                variation_lower = variation.lower().strip()
                variations_index[variation_lower] = {
                    "store_id": store_id,
                    "store": store,
                    "original_variation": variation,
                }
        return variations_index

    def _get_default_stores(self) -> list[dict]:
        """Zwraca domyślne sklepy jeśli plik nie jest dostępny"""
        return [
            {
                "id": "1",
                "normalized_name": "Biedronka",
                "normalized_name_en": "Biedronka",
                "variations": ["BIEDRONKA", "Biedronka", "biedronka"],
                "chain": "Biedronka",
                "type": "discount_store",
                "country": "PL",
            },
            {
                "id": "2",
                "normalized_name": "Lidl",
                "normalized_name_en": "Lidl",
                "variations": ["LIDL", "Lidl", "lidl"],
                "chain": "Lidl",
                "type": "discount_store",
                "country": "PL",
            },
            {
                "id": "3",
                "normalized_name": "Żabka",
                "normalized_name_en": "Zabka",
                "variations": ["ŻABKA", "Żabka", "żabka", "ZABKA", "Zabka", "zabka"],
                "chain": "Żabka",
                "type": "convenience_store",
                "country": "PL",
            },
            {
                "id": "999",
                "normalized_name": "Nieznany sklep",
                "normalized_name_en": "Unknown store",
                "variations": [],
                "chain": "Unknown",
                "type": "unknown",
                "country": "PL",
            },
        ]

    def normalize_store_name(self, store_name: str) -> dict[str, str]:
        """
        Normalizuje nazwę sklepu z paragonu

        Args:
            store_name: Nazwa sklepu z paragonu

        Returns:
            Dict z znormalizowanymi informacjami o sklepie
        """
        if not store_name or not store_name.strip():
            return self._get_unknown_store()

        store_name_clean = self._clean_store_name(store_name)

        # Najpierw spróbuj dokładnego dopasowania
        exact_match = self._find_exact_match(store_name_clean)
        if exact_match:
            logger.info(
                f"Dokładne dopasowanie sklepu: {store_name} -> {exact_match['normalized_name']}"
            )
            return exact_match

        # Następnie spróbuj dopasowania częściowego
        partial_match = self._find_partial_match(store_name_clean)
        if partial_match and partial_match["confidence"] > 0.7:
            logger.info(
                f"Częściowe dopasowanie sklepu: {store_name} -> {partial_match['normalized_name']}"
            )
            return partial_match

        # Na końcu spróbuj dopasowania fuzzy
        fuzzy_match = self._find_fuzzy_match(store_name_clean)
        if fuzzy_match and fuzzy_match["confidence"] > 0.6:
            logger.info(
                f"Fuzzy dopasowanie sklepu: {store_name} -> {fuzzy_match['normalized_name']}"
            )
            return fuzzy_match

        # Fallback do nieznanego sklepu
        logger.info(f"Nie znaleziono dopasowania dla sklepu: {store_name}")
        return self._get_unknown_store()

    def _clean_store_name(self, store_name: str) -> str:
        """Czyści nazwę sklepu z niepotrzebnych znaków"""
        # Usuń białe znaki
        cleaned = store_name.strip()

        # Usuń typowe sufixy firmowe
        suffixes_to_remove = [
            r"\s+Sp\.\s+z\s+o\.\s+o\.",
            r"\s+Sp\.\s+z\s+o\.\s+o\.\s+Sp\.\s+k\.",
            r"\s+Spółka\s+z\s+ograniczoną\s+odpowiedzialnością",
            r"\s+Spółka\s+komandytowa",
            r"\s+SA",
            r"\s+Spółka\s+Akcyjna",
            r"\s+Polska",
            r"\s+Sp\.\s+z\s+o\.\s+o\.\s*$",
            r"\s+Sp\.\s+k\.\s*$",
        ]

        for suffix in suffixes_to_remove:
            cleaned = re.sub(suffix, "", cleaned, flags=re.IGNORECASE)

        # Usuń nadmiarowe białe znaki
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    def _find_exact_match(self, store_name: str) -> dict[str, str] | None:
        """Znajduje dokładne dopasowanie nazwy sklepu"""
        store_name_lower = store_name.lower()

        # Sprawdź w indeksie wariacji
        if store_name_lower in self.store_variations:
            store_info = self.store_variations[store_name_lower]["store"]
            return {
                "id": store_info["id"],
                "normalized_name": store_info["normalized_name"],
                "normalized_name_en": store_info["normalized_name_en"],
                "chain": store_info["chain"],
                "type": store_info["type"],
                "confidence": 1.0,
                "method": "exact_match",
                "original_name": store_name,
            }

        return None

    def _find_partial_match(self, store_name: str) -> dict[str, str] | None:
        """Znajduje częściowe dopasowanie nazwy sklepu"""
        store_name_lower = store_name.lower()
        best_match = None
        best_score = 0.0

        for store in self.stores:
            variations = store.get("variations", [])
            for variation in variations:
                variation_lower = variation.lower()

                # Sprawdź czy nazwa sklepu zawiera wariację lub odwrotnie
                if (
                    variation_lower in store_name_lower
                    or store_name_lower in variation_lower
                ):
                    # Oblicz podobieństwo
                    similarity = SequenceMatcher(
                        None, store_name_lower, variation_lower
                    ).ratio()
                    if similarity > best_score:
                        best_score = similarity
                        best_match = {
                            "id": store["id"],
                            "normalized_name": store["normalized_name"],
                            "normalized_name_en": store["normalized_name_en"],
                            "chain": store["chain"],
                            "type": store["type"],
                            "confidence": similarity,
                            "method": "partial_match",
                            "original_name": store_name,
                        }

        return best_match if best_score > 0.5 else None

    def _find_fuzzy_match(self, store_name: str) -> dict[str, str] | None:
        """Znajduje fuzzy dopasowanie nazwy sklepu"""
        store_name_lower = store_name.lower()
        best_match = None
        best_score = 0.0

        for store in self.stores:
            variations = store.get("variations", [])
            for variation in variations:
                variation_lower = variation.lower()

                # Oblicz podobieństwo fuzzy
                similarity = SequenceMatcher(
                    None, store_name_lower, variation_lower
                ).ratio()
                if similarity > best_score:
                    best_score = similarity
                    best_match = {
                        "id": store["id"],
                        "normalized_name": store["normalized_name"],
                        "normalized_name_en": store["normalized_name_en"],
                        "chain": store["chain"],
                        "type": store["type"],
                        "confidence": similarity,
                        "method": "fuzzy_match",
                        "original_name": store_name,
                    }

        return best_match if best_score > 0.6 else None

    def _get_unknown_store(self) -> dict[str, str]:
        """Zwraca informacje o nieznanym sklepie"""
        unknown_store = next(
            (store for store in self.stores if store["id"] == "999"), None
        )
        if unknown_store:
            return {
                "id": unknown_store["id"],
                "normalized_name": unknown_store["normalized_name"],
                "normalized_name_en": unknown_store["normalized_name_en"],
                "chain": unknown_store["chain"],
                "type": unknown_store["type"],
                "confidence": 0.0,
                "method": "unknown",
                "original_name": "Nieznany sklep",
            }
        return {
            "id": "999",
            "normalized_name": "Nieznany sklep",
            "normalized_name_en": "Unknown store",
            "chain": "Unknown",
            "type": "unknown",
            "confidence": 0.0,
            "method": "unknown",
            "original_name": "Nieznany sklep",
        }

    def normalize_stores_batch(self, store_names: list[str]) -> list[dict[str, str]]:
        """
        Normalizuje listę nazw sklepów

        Args:
            store_names: Lista nazw sklepów do normalizacji

        Returns:
            Lista znormalizowanych informacji o sklepach
        """
        normalized_stores = []

        for store_name in store_names:
            normalized_store = self.normalize_store_name(store_name)
            normalized_stores.append(normalized_store)

        return normalized_stores

    def get_store_statistics(
        self, normalized_stores: list[dict[str, str]]
    ) -> dict[str, int]:
        """Zwraca statystyki normalizacji sklepów"""
        stats = {
            "total_stores": len(normalized_stores),
            "known_stores": 0,
            "unknown_stores": 0,
            "by_chain": {},
            "by_type": {},
            "by_method": {},
        }

        for store in normalized_stores:
            if store["id"] != "999":
                stats["known_stores"] += 1
            else:
                stats["unknown_stores"] += 1

            # Statystyki według sieci
            chain = store.get("chain", "Unknown")
            stats["by_chain"][chain] = stats["by_chain"].get(chain, 0) + 1

            # Statystyki według typu
            store_type = store.get("type", "unknown")
            stats["by_type"][store_type] = stats["by_type"].get(store_type, 0) + 1

            # Statystyki według metody dopasowania
            method = store.get("method", "unknown")
            stats["by_method"][method] = stats["by_method"].get(method, 0) + 1

        return stats

    def add_custom_store(self, store_info: dict[str, str]) -> bool:
        """
        Dodaje niestandardowy sklep do słownika

        Args:
            store_info: Informacje o sklepie do dodania

        Returns:
            True jeśli dodano pomyślnie, False w przeciwnym razie
        """
        try:
            # Sprawdź czy sklep już istnieje
            existing_store = next(
                (
                    store
                    for store in self.stores
                    if store["normalized_name"] == store_info["normalized_name"]
                ),
                None,
            )

            if existing_store:
                logger.warning(
                    f"Sklep {store_info['normalized_name']} już istnieje w słowniku"
                )
                return False

            # Dodaj nowy sklep
            new_store = {
                "id": str(len(self.stores) + 1),
                "normalized_name": store_info["normalized_name"],
                "normalized_name_en": store_info.get(
                    "normalized_name_en", store_info["normalized_name"]
                ),
                "variations": store_info.get(
                    "variations", [store_info["normalized_name"]]
                ),
                "chain": store_info.get("chain", "Custom"),
                "type": store_info.get("type", "unknown"),
                "country": store_info.get("country", "PL"),
            }

            self.stores.append(new_store)

            # Zaktualizuj indeks wariacji
            self.store_variations = self._build_variations_index()

            logger.info(f"Dodano niestandardowy sklep: {store_info['normalized_name']}")
            return True

        except Exception as e:
            logger.error(f"Błąd podczas dodawania niestandardowego sklepu: {e}")
            return False
