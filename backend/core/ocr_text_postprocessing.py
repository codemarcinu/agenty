"""
OCR Text Postprocessing for Polish Receipts

This module provides functions to fix common OCR errors in Polish receipt text.
Implements rules for character correction, amount formatting, date parsing, and store name normalization.
"""

from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class OCRTextPostprocessor:
    """
    Advanced OCR text postprocessing for Polish receipts.

    Features:
    - Character error correction (O/0, l/1, etc.)
    - Amount and price formatting
    - Date parsing and validation
    - Store name normalization
    - Receipt structure validation
    """

    def __init__(self):
        # Common OCR character substitutions for Polish receipts
        self.char_substitutions = {
            # Numbers and letters commonly confused
            "O": "0",
            "l": "1",
            "I": "1",
            "S": "5",
            "G": "6",
            "B": "8",
            "0": "O",
            "1": "l",
            "5": "S",
            "6": "G",
            "8": "B",
            # Polish specific
            "ą": "a",
            "ć": "c",
            "ę": "e",
            "ł": "l",
            "ń": "n",
            "ó": "o",
            "ś": "s",
            "ź": "z",
            "ż": "z",
            "Ą": "A",
            "Ć": "C",
            "Ę": "E",
            "Ł": "L",
            "Ń": "N",
            "Ó": "O",
            "Ś": "S",
            "Ź": "Z",
            "Ż": "Z",
        }

        # Store name normalization patterns
        self.store_patterns = {
            r"LIDL\s+POLSKA\s+SP\s+Z\s+O\.O\.": "Lidl",
            r"BIEDRONKA\s+SP\s+Z\s+O\.O\.": "Biedronka",
            r"KAUFLAND": "Kaufland",
            r"TESCO\s+POLSKA": "Tesco",
            r"CARREFOUR": "Carrefour",
            r"AUCHAN": "Auchan",
            r"LEWIATAN": "Lewiatan",
            r"ŻABKA": "Żabka",
            r"NETTO": "Netto",
            r"ALDI": "Aldi",
            r"PENNY": "Penny",
            r"INTERMARCHE": "Intermarché",
            r"SPAR": "Spar",
            r"BOMI": "Bomi",
            r"POLOMARKET": "PoloMarket",
            r"DINO": "Dino",
            r"STOKROTKA": "Stokrotka",
            r"ABC": "ABC",
            r"DELIKATESY": "Delikatesy",
            r"GROSZEK": "Groszek",
        }

        # Common receipt keywords to preserve
        self.receipt_keywords = [
            "PARAGON",
            "RACHUNEK",
            "SUMA",
            "PLN",
            "ZŁ",
            "ZŁOTY",
            "ZŁOTE",
            "PTU",
            "VAT",
            "RABAT",
            "PROMOCJA",
            "SKIDKA",
            "SKIŁKA",
            "KASA",
            "KASJER",
            "KASJERKA",
            "NR",
            "NUMER",
            "DATA",
            "GODZINA",
            "KARTA",
            "GOTÓWKA",
            "KARTA PŁATNICZA",
            "BLIK",
        ]

    def postprocess_ocr_text(
        self, text: str, confidence: float = 0.0
    ) -> dict[str, any]:
        """
        Apply comprehensive postprocessing to OCR text.

        Args:
            text: Raw OCR text
            confidence: OCR confidence score (0.0-1.0)

        Returns:
            Dict with processed text and metadata
        """
        if not text or not text.strip():
            return {
                "processed_text": "",
                "original_text": text,
                "confidence": confidence,
                "improvements": [],
                "errors": ["Empty or invalid text"],
            }

        original_text = text
        improvements = []

        try:
            # Step 1: Basic cleanup
            text = self._basic_cleanup(text)
            improvements.append("basic_cleanup")

            # Step 2: Character error correction
            text = self._fix_character_errors(text)
            improvements.append("character_correction")

            # Step 3: Amount and price formatting
            text = self._fix_amount_formatting(text)
            improvements.append("amount_formatting")

            # Step 4: Date parsing and validation
            text = self._fix_date_formatting(text)
            improvements.append("date_formatting")

            # Step 5: Store name normalization
            text = self._normalize_store_names(text)
            improvements.append("store_normalization")

            # Step 6: Receipt structure validation
            text = self._validate_receipt_structure(text)
            improvements.append("structure_validation")

            # Step 7: Final cleanup
            text = self._final_cleanup(text)
            improvements.append("final_cleanup")

            return {
                "processed_text": text,
                "original_text": original_text,
                "confidence": confidence,
                "improvements": improvements,
                "text_length_change": len(text) - len(original_text),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in OCR postprocessing: {e}")
            return {
                "processed_text": original_text,
                "original_text": original_text,
                "confidence": confidence,
                "improvements": [],
                "errors": [str(e)],
                "success": False,
            }

    def _basic_cleanup(self, text: str) -> str:
        """Basic text cleanup"""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Fix common line breaks
        text = re.sub(r"\n\s*\n", "\n", text)
        return text

    def _fix_character_errors(self, text: str) -> str:
        """Fix common OCR character errors"""
        # Apply character substitutions in specific contexts
        lines = text.split("\n")
        corrected_lines = []

        for line in lines:
            corrected_line = line

            # Fix numbers in price contexts (e.g., "2,99" -> "2.99")
            corrected_line = re.sub(r"(\d+),(\d{2})", r"\1.\2", corrected_line)

            # Fix common OCR errors in amounts
            corrected_line = re.sub(
                r"(\d+)O(\d*)", r"\g<1>0\g<2>", corrected_line
            )  # O -> 0 in numbers
            corrected_line = re.sub(
                r"(\d+)l(\d*)", r"\g<1>1\g<2>", corrected_line
            )  # l -> 1 in numbers

            # Fix common OCR errors in text
            for wrong_char, correct_char in self.char_substitutions.items():
                # Only replace in specific contexts to avoid over-correction
                if wrong_char in corrected_line:
                    # Be more conservative with replacements
                    if wrong_char in "O0l1I":
                        # Only replace in number contexts
                        corrected_line = re.sub(
                            rf"(\d){re.escape(wrong_char)}(\d)",
                            rf"\g<1>{correct_char}\g<2>",
                            corrected_line,
                        )
                    else:
                        # For other characters, replace more broadly
                        corrected_line = corrected_line.replace(
                            wrong_char, correct_char
                        )

            corrected_lines.append(corrected_line)

        return "\n".join(corrected_lines)

    def _fix_amount_formatting(self, text: str) -> str:
        """Fix amount and price formatting"""
        lines = text.split("\n")
        corrected_lines = []

        for line in lines:
            corrected_line = line

            # Fix price patterns (e.g., "2,99 PLN" -> "2.99 PLN")
            corrected_line = re.sub(
                r"(\d+),(\d{2})\s*(PLN|ZŁ|ZŁOTY|ZŁOTE)?", r"\1.\2 \3", corrected_line
            )

            # Fix quantity patterns (e.g., "2x" -> "2 x")
            corrected_line = re.sub(r"(\d+)x", r"\1 x", corrected_line)

            # Fix weight patterns (e.g., "0,5kg" -> "0.5 kg")
            corrected_line = re.sub(
                r"(\d+),(\d+)\s*(kg|l|g)", r"\1.\2 \3", corrected_line
            )

            corrected_lines.append(corrected_line)

        return "\n".join(corrected_lines)

    def _fix_date_formatting(self, text: str) -> str:
        """Fix date formatting and validation"""
        lines = text.split("\n")
        corrected_lines = []

        for line in lines:
            corrected_line = line

            # Fix date patterns (e.g., "15.01.2024" -> "2024-01-15")
            date_patterns = [
                r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # DD.MM.YYYY
                r"(\d{1,2})\.(\d{1,2})\.(\d{2})",  # DD.MM.YY
                r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
            ]

            for pattern in date_patterns:
                match = re.search(pattern, corrected_line)
                if match:
                    try:
                        if len(match.group(3)) == 2:
                            # Convert YY to YYYY
                            year = "20" + match.group(3)
                        else:
                            year = match.group(3)

                        day = match.group(1).zfill(2)
                        month = match.group(2).zfill(2)

                        # Validate date
                        datetime(int(year), int(month), int(day))

                        # Format as YYYY-MM-DD
                        formatted_date = f"{year}-{month}-{day}"
                        corrected_line = re.sub(pattern, formatted_date, corrected_line)
                        break
                    except ValueError:
                        # Invalid date, keep original
                        pass

            corrected_lines.append(corrected_line)

        return "\n".join(corrected_lines)

    def _normalize_store_names(self, text: str) -> str:
        """Normalize store names using patterns"""
        normalized_text = text

        for pattern, replacement in self.store_patterns.items():
            normalized_text = re.sub(
                pattern, replacement, normalized_text, flags=re.IGNORECASE
            )

        return normalized_text

    def _validate_receipt_structure(self, text: str) -> str:
        """Validate and fix receipt structure"""
        lines = text.split("\n")
        validated_lines = []

        for line in lines:
            # Remove lines that are clearly not receipt content
            if self._is_noise_line(line):
                continue

            # Fix common structural issues
            corrected_line = self._fix_structure_issues(line)
            validated_lines.append(corrected_line)

        return "\n".join(validated_lines)

    def _is_noise_line(self, line: str) -> bool:
        """Check if line is noise (not relevant receipt content)"""
        line_lower = line.lower().strip()

        # Skip empty lines
        if not line_lower:
            return True

        # Skip lines that are clearly not receipt content
        noise_patterns = [
            r"^\s*$",  # Empty lines
            r"^\s*[^\w\s]+\s*$",  # Only special characters
            r"^\s*\d+\s*$",  # Only numbers
            r"^\s*[A-Z]{1,2}\s*$",  # Only 1-2 letters
        ]

        return any(re.match(pattern, line_lower) for pattern in noise_patterns)

    def _fix_structure_issues(self, line: str) -> str:
        """Fix common structural issues in receipt lines"""
        corrected_line = line

        # Fix spacing issues
        corrected_line = re.sub(
            r"(\d)\s*,\s*(\d)", r"\1,\2", corrected_line
        )  # Fix decimal spacing
        corrected_line = re.sub(
            r"(\w)\s*(\d)", r"\1 \2", corrected_line
        )  # Fix word-number spacing

        # Fix common OCR artifacts
        corrected_line = re.sub(
            r"[^\w\s\d,\.\-]", "", corrected_line
        )  # Remove special characters except essential ones

        return corrected_line.strip()

    def _final_cleanup(self, text: str) -> str:
        """Final cleanup of processed text"""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove empty lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Join lines
        text = "\n".join(lines)

        return text.strip()


# Global instance for easy access
ocr_postprocessor = OCRTextPostprocessor()


def postprocess_ocr_text(text: str, confidence: float = 0.0) -> dict[str, any]:
    """
    Convenience function to postprocess OCR text.

    Args:
        text: Raw OCR text
        confidence: OCR confidence score

    Returns:
        Dict with processed text and metadata
    """
    return ocr_postprocessor.postprocess_ocr_text(text, confidence)
