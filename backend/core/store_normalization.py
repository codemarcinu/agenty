"""
Store Name Normalization for Polish Receipts

This module provides comprehensive store name normalization for Polish receipts.
Includes mapping of store names, addresses, and common variations.
"""

from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class StoreInfo:
    """Store information with normalized name and metadata"""

    normalized_name: str
    chain: str
    type: str
    confidence: float
    variants: list[str]
    addresses: list[str]


class StoreNormalizer:
    """
    Advanced store name normalizer for Polish receipts.

    Features:
    - Comprehensive store name mapping
    - Address-based store identification
    - Confidence scoring
    - Multiple store chains support
    """

    def __init__(self):
        self.store_patterns = self._initialize_store_patterns()
        self.address_patterns = self._initialize_address_patterns()
        self.store_chains = self._initialize_store_chains()

    def _initialize_store_patterns(self) -> dict[str, StoreInfo]:
        """Initialize comprehensive store name patterns"""
        return {
            # Lidl
            r"LIDL\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Lidl", "Lidl", "supermarket", 0.95, ["LIDL POLSKA", "LIDL"], []
            ),
            r"LIDL\s+POLSKA": StoreInfo(
                "Lidl", "Lidl", "supermarket", 0.90, ["LIDL POLSKA"], []
            ),
            r"LIDL": StoreInfo("Lidl", "Lidl", "supermarket", 0.85, ["LIDL"], []),
            # Biedronka
            r"BIEDRONKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Biedronka",
                "Biedronka",
                "supermarket",
                0.95,
                ["BIEDRONKA SP Z O.O.", "BIEDRONKA"],
                [],
            ),
            r"BIEDRONKA": StoreInfo(
                "Biedronka", "Biedronka", "supermarket", 0.90, ["BIEDRONKA"], []
            ),
            # Kaufland
            r"KAUFLAND\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Kaufland",
                "Kaufland",
                "hypermarket",
                0.95,
                ["KAUFLAND POLSKA", "KAUFLAND"],
                [],
            ),
            r"KAUFLAND": StoreInfo(
                "Kaufland", "Kaufland", "hypermarket", 0.90, ["KAUFLAND"], []
            ),
            # Tesco
            r"TESCO\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Tesco", "Tesco", "hypermarket", 0.95, ["TESCO POLSKA", "TESCO"], []
            ),
            r"TESCO\s+POLSKA": StoreInfo(
                "Tesco", "Tesco", "hypermarket", 0.90, ["TESCO POLSKA"], []
            ),
            r"TESCO": StoreInfo("Tesco", "Tesco", "hypermarket", 0.85, ["TESCO"], []),
            # Carrefour
            r"CARREFOUR\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Carrefour",
                "Carrefour",
                "hypermarket",
                0.95,
                ["CARREFOUR POLSKA", "CARREFOUR"],
                [],
            ),
            r"CARREFOUR": StoreInfo(
                "Carrefour", "Carrefour", "hypermarket", 0.90, ["CARREFOUR"], []
            ),
            # Auchan
            r"AUCHAN\s+POLSKA\s+SA": StoreInfo(
                "Auchan", "Auchan", "hypermarket", 0.95, ["AUCHAN POLSKA", "AUCHAN"], []
            ),
            r"AUCHAN": StoreInfo(
                "Auchan", "Auchan", "hypermarket", 0.90, ["AUCHAN"], []
            ),
            # Żabka
            r"ŻABKA\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Żabka", "Żabka", "convenience", 0.95, ["ŻABKA POLSKA", "ŻABKA"], []
            ),
            r"ŻABKA": StoreInfo("Żabka", "Żabka", "convenience", 0.90, ["ŻABKA"], []),
            r"ZABKA": StoreInfo("Żabka", "Żabka", "convenience", 0.85, ["ZABKA"], []),
            # Netto
            r"NETTO\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Netto", "Netto", "supermarket", 0.95, ["NETTO POLSKA", "NETTO"], []
            ),
            r"NETTO": StoreInfo("Netto", "Netto", "supermarket", 0.90, ["NETTO"], []),
            # Aldi
            r"ALDI\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Aldi", "Aldi", "supermarket", 0.95, ["ALDI POLSKA", "ALDI"], []
            ),
            r"ALDI": StoreInfo("Aldi", "Aldi", "supermarket", 0.90, ["ALDI"], []),
            # Penny
            r"PENNY\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Penny", "Penny", "supermarket", 0.95, ["PENNY POLSKA", "PENNY"], []
            ),
            r"PENNY": StoreInfo("Penny", "Penny", "supermarket", 0.90, ["PENNY"], []),
            # Intermarché
            r"INTERMARCHE": StoreInfo(
                "Intermarché", "Intermarché", "supermarket", 0.90, ["INTERMARCHE"], []
            ),
            r"INTERMARCHE\s+POLSKA": StoreInfo(
                "Intermarché",
                "Intermarché",
                "supermarket",
                0.95,
                ["INTERMARCHE POLSKA"],
                [],
            ),
            # Spar
            r"SPAR\s+POLSKA": StoreInfo(
                "Spar", "Spar", "supermarket", 0.95, ["SPAR POLSKA", "SPAR"], []
            ),
            r"SPAR": StoreInfo("Spar", "Spar", "supermarket", 0.90, ["SPAR"], []),
            # Dino
            r"DINO\s+POLSKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Dino", "Dino", "supermarket", 0.95, ["DINO POLSKA", "DINO"], []
            ),
            r"DINO": StoreInfo("Dino", "Dino", "supermarket", 0.90, ["DINO"], []),
            # Stokrotka
            r"STOKROTKA\s+SP\s+Z\s+O\.O\.": StoreInfo(
                "Stokrotka", "Stokrotka", "supermarket", 0.95, ["STOKROTKA"], []
            ),
            r"STOKROTKA": StoreInfo(
                "Stokrotka", "Stokrotka", "supermarket", 0.90, ["STOKROTKA"], []
            ),
            # ABC
            r"ABC\s+MARKET": StoreInfo(
                "ABC", "ABC", "supermarket", 0.95, ["ABC MARKET", "ABC"], []
            ),
            r"ABC": StoreInfo("ABC", "ABC", "supermarket", 0.85, ["ABC"], []),
            # Delikatesy
            r"DELIKATESY\s+": StoreInfo(
                "Delikatesy", "Delikatesy", "convenience", 0.80, ["DELIKATESY"], []
            ),
            # Groszek
            r"GROSZEK": StoreInfo(
                "Groszek", "Groszek", "convenience", 0.85, ["GROSZEK"], []
            ),
            # Bomi
            r"BOMI": StoreInfo("Bomi", "Bomi", "convenience", 0.85, ["BOMI"], []),
            # PoloMarket
            r"POLOMARKET": StoreInfo(
                "PoloMarket", "PoloMarket", "supermarket", 0.85, ["POLOMARKET"], []
            ),
            # Lewiatan
            r"LEWIATAN": StoreInfo(
                "Lewiatan", "Lewiatan", "convenience", 0.85, ["LEWIATAN"], []
            ),
        }

    def _initialize_address_patterns(self) -> dict[str, str]:
        """Initialize address-based store identification patterns"""
        return {
            r"www\.lidl\.pl": "Lidl",
            r"www\.biedronka\.pl": "Biedronka",
            r"www\.kaufland\.pl": "Kaufland",
            r"www\.tesco\.pl": "Tesco",
            r"www\.carrefour\.pl": "Carrefour",
            r"www\.auchan\.pl": "Auchan",
            r"www\.zabka\.pl": "Żabka",
            r"www\.netto\.pl": "Netto",
            r"www\.aldi\.pl": "Aldi",
            r"www\.penny\.pl": "Penny",
            r"www\.intermarche\.pl": "Intermarché",
            r"www\.spar\.pl": "Spar",
            r"www\.dino\.pl": "Dino",
            r"www\.stokrotka\.pl": "Stokrotka",
        }

    def _initialize_store_chains(self) -> dict[str, dict[str, any]]:
        """Initialize store chain information"""
        return {
            "Lidl": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.lidl.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Biedronka": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.biedronka.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Kaufland": {
                "type": "hypermarket",
                "country": "Poland",
                "website": "www.kaufland.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Tesco": {
                "type": "hypermarket",
                "country": "Poland",
                "website": "www.tesco.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Carrefour": {
                "type": "hypermarket",
                "country": "Poland",
                "website": "www.carrefour.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Auchan": {
                "type": "hypermarket",
                "country": "Poland",
                "website": "www.auchan.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Żabka": {
                "type": "convenience",
                "country": "Poland",
                "website": "www.zabka.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Netto": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.netto.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Aldi": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.aldi.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Penny": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.penny.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Intermarché": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.intermarche.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Spar": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.spar.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Dino": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.dino.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Stokrotka": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.stokrotka.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "ABC": {
                "type": "supermarket",
                "country": "Poland",
                "website": "www.abcmarket.pl",
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Delikatesy": {
                "type": "convenience",
                "country": "Poland",
                "website": None,
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Groszek": {
                "type": "convenience",
                "country": "Poland",
                "website": None,
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Bomi": {
                "type": "convenience",
                "country": "Poland",
                "website": None,
                "common_addresses": ["ul.", "al.", "os."],
            },
            "PoloMarket": {
                "type": "supermarket",
                "country": "Poland",
                "website": None,
                "common_addresses": ["ul.", "al.", "os."],
            },
            "Lewiatan": {
                "type": "convenience",
                "country": "Poland",
                "website": None,
                "common_addresses": ["ul.", "al.", "os."],
            },
        }

    def normalize_store_name(self, text: str) -> dict[str, any]:
        """
        Normalize store name from receipt text.

        Args:
            text: Receipt text

        Returns:
            Dict with normalized store information
        """
        if not text:
            return {
                "normalized_name": "Nieznany sklep",
                "chain": "Unknown",
                "type": "unknown",
                "confidence": 0.0,
                "method": "empty_text",
            }

        # Try pattern matching first
        pattern_result = self._match_store_patterns(text)
        if pattern_result["confidence"] > 0.7:
            return pattern_result

        # Try address-based identification
        address_result = self._identify_by_address(text)
        if address_result["confidence"] > 0.6:
            return address_result

        # Try keyword matching
        keyword_result = self._match_by_keywords(text)
        if keyword_result["confidence"] > 0.5:
            return keyword_result

        return {
            "normalized_name": "Nieznany sklep",
            "chain": "Unknown",
            "type": "unknown",
            "confidence": 0.0,
            "method": "no_match",
        }

    def _match_store_patterns(self, text: str) -> dict[str, any]:
        """Match store names using patterns"""
        text_upper = text.upper()

        for pattern, store_info in self.store_patterns.items():
            if re.search(pattern, text_upper, re.IGNORECASE):
                return {
                    "normalized_name": store_info.normalized_name,
                    "chain": store_info.chain,
                    "type": store_info.type,
                    "confidence": store_info.confidence,
                    "method": "pattern_match",
                    "variants": store_info.variants,
                }

        return {"confidence": 0.0}

    def _identify_by_address(self, text: str) -> dict[str, any]:
        """Identify store by website address"""
        for pattern, store_name in self.address_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                chain_info = self.store_chains.get(store_name, {})
                return {
                    "normalized_name": store_name,
                    "chain": store_name,
                    "type": chain_info.get("type", "unknown"),
                    "confidence": 0.8,
                    "method": "address_match",
                }

        return {"confidence": 0.0}

    def _match_by_keywords(self, text: str) -> dict[str, any]:
        """Match store by keywords in text"""
        text_upper = text.upper()

        # Common keywords for each store
        keyword_mappings = {
            "LIDL": "Lidl",
            "BIEDRONKA": "Biedronka",
            "KAUFLAND": "Kaufland",
            "TESCO": "Tesco",
            "CARREFOUR": "Carrefour",
            "AUCHAN": "Auchan",
            "ZABKA": "Żabka",
            "NETTO": "Netto",
            "ALDI": "Aldi",
            "PENNY": "Penny",
            "INTERMARCHE": "Intermarché",
            "SPAR": "Spar",
            "DINO": "Dino",
            "STOKROTKA": "Stokrotka",
            "ABC": "ABC",
            "DELIKATESY": "Delikatesy",
            "GROSZEK": "Groszek",
            "BOMI": "Bomi",
            "POLOMARKET": "PoloMarket",
            "LEWIATAN": "Lewiatan",
        }

        for keyword, store_name in keyword_mappings.items():
            if keyword in text_upper:
                chain_info = self.store_chains.get(store_name, {})
                return {
                    "normalized_name": store_name,
                    "chain": store_name,
                    "type": chain_info.get("type", "unknown"),
                    "confidence": 0.6,
                    "method": "keyword_match",
                }

        return {"confidence": 0.0}


# Global instance
store_normalizer = StoreNormalizer()


def normalize_store_name(text: str) -> dict[str, any]:
    """Convenience function to normalize store name"""
    return store_normalizer.normalize_store_name(text)
