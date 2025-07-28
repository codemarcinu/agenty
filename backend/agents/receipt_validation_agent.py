"""
Receipt Validation Agent - ocenia kompletność danych paragonu
Zgodnie z rekomendacjami audytu - single responsibility principle
"""

import logging
import re
from typing import Any

from pydantic import BaseModel, ValidationError

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.decorators import handle_exceptions

logger = logging.getLogger(__name__)


class ReceiptValidationInput(BaseModel):
    """Model wejściowy dla ReceiptValidationAgent."""

    ocr_text: str
    raw_data: dict[str, Any] = {}


class ValidationResult(BaseModel):
    """Wynik walidacji paragonu."""

    is_valid: bool
    score: float
    issues: list[str] = []
    missing_fields: list[str] = []
    confidence_score: float
    recommendations: list[str] = []


class ReceiptValidationAgent(BaseAgent):
    """
    Agent walidacji paragonów - ocenia kompletność i jakość danych.

    Zgodnie z zasadą single responsibility:
    - Ocena kompletności danych
    - Score > X przekazuje dalej, inaczej zgłasza "action required"
    - Walidacja formatów (NIP, data, kwoty)
    """

    def __init__(
        self,
        name: str = "ReceiptValidationAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        """Inicjalizuje ReceiptValidationAgent."""
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )
        self.min_score_threshold = kwargs.get("min_score_threshold", 0.6)
        self.min_confidence_threshold = kwargs.get("min_confidence_threshold", 0.5)

    @handle_exceptions(max_retries=1, retry_delay=0.5)
    async def process(
        self, input_data: ReceiptValidationInput | dict[str, Any]
    ) -> AgentResponse:
        """
        Waliduje dane paragonu i ocenia kompletność.

        Args:
            input_data: Dane wejściowe z tekstem OCR do walidacji

        Returns:
            AgentResponse: Odpowiedź z wynikiem walidacji
        """
        try:
            if not isinstance(input_data, ReceiptValidationInput):
                input_data = ReceiptValidationInput.model_validate(input_data)
        except ValidationError as ve:
            return AgentResponse(
                success=False,
                error=f"Błąd walidacji danych wejściowych: {ve}",
            )

        ocr_text: str = input_data.ocr_text

        try:
            logger.info("Rozpoczynam walidację paragonu")

            # Step 1: Podstawowa walidacja tekstu
            if not ocr_text or len(ocr_text.strip()) < 10:
                return AgentResponse(
                    success=False,
                    error="Tekst OCR jest zbyt krótki lub pusty",
                )

            # Step 2: Analiza kompletności
            validation_result = self._validate_completeness(ocr_text)

            # Step 3: Walidacja formatów
            format_validation = self._validate_formats(ocr_text)
            validation_result.issues.extend(format_validation.get("issues", []))

            # Step 4: Oblicz końcowy score
            final_score = self._calculate_final_score(
                validation_result, format_validation
            )

            # Step 5: Przygotuj odpowiedź
            validation_data = {
                "validation_result": validation_result.dict(),
                "format_validation": format_validation,
                "final_score": final_score,
                "should_proceed": final_score >= self.min_score_threshold,
                "recommendations": self._generate_recommendations(
                    validation_result, format_validation
                ),
            }

            logger.info(
                "Walidacja paragonu zakończona",
                extra={
                    "final_score": final_score,
                    "should_proceed": validation_data["should_proceed"],
                    "issues_count": len(validation_result.issues),
                },
            )

            if final_score >= self.min_score_threshold:
                return AgentResponse(
                    success=True,
                    text=f"Paragon przeszedł walidację (score: {final_score:.2f})",
                    data=validation_data,
                    message="Paragon jest gotowy do dalszego przetwarzania",
                    metadata={
                        "validation_score": final_score,
                        "should_proceed": True,
                        "processing_stage": "validation",
                    },
                )
            return AgentResponse(
                success=False,
                text=f"Paragon wymaga poprawy (score: {final_score:.2f})",
                data=validation_data,
                error="Paragon nie spełnia wymagań jakościowych",
                metadata={
                    "validation_score": final_score,
                    "should_proceed": False,
                    "processing_stage": "validation",
                },
            )

        except Exception as e:
            logger.error(f"Błąd podczas walidacji paragonu: {e!s}")
            return AgentResponse(
                success=False,
                error=f"Wystąpił błąd podczas walidacji: {e!s}",
            )

    def _validate_completeness(self, ocr_text: str) -> ValidationResult:
        """Waliduje kompletność danych paragonu."""
        issues = []
        missing_fields = []
        confidence_score = 0.0

        # Sprawdź obecność kluczowych elementów
        required_elements = {
            "store_name": [
                "SKLEP",
                "MARKET",
                "SUPERMARKET",
                "BIEDRONKA",
                "LIDL",
                "CARREFOUR",
                "AUCHAN",
            ],
            "receipt_header": ["PARAGON", "RACHUNEK", "RECEIPT"],
            "total_amount": ["SUMA", "TOTAL", "DO ZAPŁATY", "PLN"],
            "items": ["PRODUKT", "NAZWA", "ILOŚĆ", "CENA"],
            "date": ["DATA", "DZIEŃ", "GODZINA"],
        }

        text_upper = ocr_text.upper()
        found_elements = 0

        for element_name, keywords in required_elements.items():
            found = any(keyword in text_upper for keyword in keywords)
            if not found:
                missing_fields.append(element_name)
                issues.append(f"Brak elementu: {element_name}")
            else:
                found_elements += 1

        # Oblicz confidence score
        confidence_score = found_elements / len(required_elements)

        # Sprawdź długość tekstu
        if len(ocr_text) < 50:
            issues.append("Tekst jest zbyt krótki")
            confidence_score *= 0.5

        # Sprawdź obecność liczb (cen)
        numbers = re.findall(r"\d+[.,]\d{2}", ocr_text)
        if len(numbers) < 2:
            issues.append("Brak wystarczającej liczby cen")
            confidence_score *= 0.7

        return ValidationResult(
            is_valid=confidence_score >= self.min_confidence_threshold,
            score=confidence_score,
            issues=issues,
            missing_fields=missing_fields,
            confidence_score=confidence_score,
            recommendations=[],
        )

    def _validate_formats(self, ocr_text: str) -> dict[str, Any]:
        """Waliduje formaty danych w tekście paragonu."""
        issues = []
        valid_formats = {}

        # Walidacja NIP
        nip_pattern = r"\b\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b"
        nips = re.findall(nip_pattern, ocr_text)
        if nips:
            valid_formats["nip"] = nips[0]
        else:
            issues.append("Nie znaleziono poprawnego NIP")

        # Walidacja daty
        date_patterns = [
            r"\b\d{2}[./-]\d{2}[./-]\d{4}\b",
            r"\b\d{4}[./-]\d{2}[./-]\d{2}\b",
            r"\b\d{2}\s+\w+\s+\d{4}\b",
        ]

        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, ocr_text))

        if dates:
            valid_formats["date"] = dates[0]
        else:
            issues.append("Nie znaleziono poprawnej daty")

        # Walidacja kwot
        amount_pattern = r"\b\d+[.,]\d{2}\s*(?:PLN|zł)?\b"
        amounts = re.findall(amount_pattern, ocr_text)
        if len(amounts) >= 2:
            valid_formats["amounts"] = amounts
        else:
            issues.append("Nie znaleziono wystarczającej liczby kwot")

        return {"issues": issues, "valid_formats": valid_formats}

    def _calculate_final_score(
        self, validation_result: ValidationResult, format_validation: dict[str, Any]
    ) -> float:
        """Oblicza końcowy score walidacji."""
        base_score = validation_result.confidence_score

        # Bonus za poprawne formaty
        format_bonus = 0.0
        if "nip" in format_validation.get("valid_formats", {}):
            format_bonus += 0.1
        if "date" in format_validation.get("valid_formats", {}):
            format_bonus += 0.1
        if "amounts" in format_validation.get("valid_formats", {}):
            format_bonus += 0.1

        # Kara za problemy z formatami
        format_penalty = len(format_validation.get("issues", [])) * 0.05

        final_score = base_score + format_bonus - format_penalty
        return max(0.0, min(1.0, final_score))

    def _generate_recommendations(
        self, validation_result: ValidationResult, format_validation: dict[str, Any]
    ) -> list[str]:
        """Generuje rekomendacje na podstawie wyników walidacji."""
        recommendations = []

        if validation_result.confidence_score < 0.5:
            recommendations.append(
                "Rozważ ponowne zeskanowanie paragonu w lepszej jakości"
            )

        if "store_name" in validation_result.missing_fields:
            recommendations.append(
                "Sprawdź czy nazwa sklepu jest widoczna na paragonie"
            )

        if "total_amount" in validation_result.missing_fields:
            recommendations.append("Sprawdź czy suma do zapłaty jest czytelna")

        if len(format_validation.get("issues", [])) > 0:
            recommendations.append(
                "Sprawdź czytelność kluczowych danych (NIP, data, kwoty)"
            )

        if not recommendations:
            recommendations.append("Paragon wygląda dobrze, można przejść do analizy")

        return recommendations

    def get_metadata(self) -> dict[str, Any]:
        """Zwraca metadane agenta."""
        return {
            "name": self.name,
            "type": "ReceiptValidationAgent",
            "capabilities": [
                "completeness validation",
                "format validation",
                "quality scoring",
            ],
            "version": "1.0",
            "processing_stage": "validation",
            "min_score_threshold": self.min_score_threshold,
        }

    def get_dependencies(self) -> list:
        """Lista zależności agenta."""
        return []

    def is_healthy(self) -> bool:
        """Sprawdza czy agent jest zdrowy."""
        return True
