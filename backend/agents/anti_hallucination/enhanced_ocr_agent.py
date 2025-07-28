"""
Enhanced OCR Agent with anti-hallucination mechanisms.

Implements confidence scoring, progressive validation, and quality assessment
to prevent hallucinations in OCR processing.
"""

import logging
from typing import Any

from pydantic import ValidationError

from agents.interfaces import AgentResponse
from agents.ocr_agent import OCRAgent, OCRAgentInput
from core.decorators import handle_exceptions

from .confidence_scorer import ConfidenceMetrics, ConfidenceScorer

logger = logging.getLogger(__name__)


class EnhancedOCRAgent(OCRAgent):
    """
    Enhanced OCR Agent with anti-hallucination mechanisms.

    Extends the base OCRAgent with:
    - Confidence scoring and progressive validation
    - Quality assessment with configurable thresholds
    - Automatic fallback mechanisms
    - Detailed validation reporting
    """

    def __init__(
        self,
        name: str = "EnhancedOCRAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        """Initialize EnhancedOCRAgent with anti-hallucination features."""
        super().__init__(
            name=name,
            error_handler=error_handler,
            fallback_manager=fallback_manager,
            **kwargs,
        )

        # Initialize confidence scorer
        self.confidence_scorer = ConfidenceScorer(
            confidence_threshold=kwargs.get("confidence_threshold", 0.7),
            require_validation=kwargs.get("require_validation", True),
            min_text_length=kwargs.get("min_text_length", 10),
            max_validation_issues=kwargs.get("max_validation_issues", 3),
        )

        # Anti-hallucination configuration
        self.require_human_review = kwargs.get("require_human_review", True)
        self.auto_fallback = kwargs.get("auto_fallback", True)
        self.quality_metrics = kwargs.get("quality_metrics", True)

    @handle_exceptions(max_retries=1, retry_delay=0.5)
    async def process(
        self, input_data: OCRAgentInput | dict[str, Any]
    ) -> AgentResponse:
        """
        Process OCR with enhanced anti-hallucination validation.

        Args:
            input_data: Input data with file bytes and type

        Returns:
            AgentResponse with OCR results and confidence metrics
        """
        try:
            if not isinstance(input_data, OCRAgentInput):
                input_data = OCRAgentInput.model_validate(input_data)
        except ValidationError as ve:
            return AgentResponse(
                success=False,
                error=f"Błąd walidacji danych wejściowych: {ve}",
            )

        file_bytes: bytes = input_data.file_bytes
        file_type: str = input_data.file_type.lower()

        try:
            # Step 1: Perform standard OCR
            logger.info("Rozpoczynam OCR z walidacją anty-halucynacyjną")

            if file_type == "image":
                ocr_text = self._process_image_file(file_bytes)
            elif file_type == "pdf":
                ocr_text = self._process_pdf_file(file_bytes)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Nieobsługiwany typ pliku: {file_type}",
                )

            if not ocr_text:
                return AgentResponse(
                    success=False,
                    error="Nie udało się rozpoznać tekstu z pliku. Sprawdź czy plik jest czytelny i spróbuj ponownie.",
                )

            # Step 2: Calculate confidence metrics
            confidence_metrics = self.confidence_scorer.calculate_ocr_confidence(
                ocr_text
            )

            # Step 3: Apply anti-hallucination validation
            validation_result = self._validate_ocr_quality(ocr_text, confidence_metrics)

            # Step 4: Determine if processing should proceed
            if not self.confidence_scorer.should_proceed_with_validation(
                confidence_metrics
            ):
                return self._create_low_confidence_response(
                    confidence_metrics, ocr_text
                )

            # Step 5: Apply enhanced prompts if confidence is sufficient
            enhanced_text = self._apply_enhanced_ocr_prompts(
                ocr_text, confidence_metrics
            )

            # Step 6: Create response with comprehensive metadata
            return self._create_success_response(
                enhanced_text, confidence_metrics, validation_result
            )

        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania OCR: {e!s}")
            return AgentResponse(
                success=False,
                error=f"Wystąpił błąd podczas przetwarzania pliku: {e!s}",
            )

    def _process_image_file(self, file_bytes: bytes) -> str:
        """Process image file with timeout handling."""
        from core.ocr import process_image_file

        return process_image_file(file_bytes, timeout=self.TIMEOUT)

    def _process_pdf_file(self, file_bytes: bytes) -> str:
        """Process PDF file with timeout handling."""
        from core.ocr import process_pdf_file

        return process_pdf_file(file_bytes, timeout=self.TIMEOUT)

    def _validate_ocr_quality(
        self, ocr_text: str, confidence_metrics: ConfidenceMetrics
    ) -> dict[str, Any]:
        """
        Validate OCR quality and assess potential hallucinations.

        Args:
            ocr_text: OCR result text
            confidence_metrics: Calculated confidence metrics

        Returns:
            Validation result dictionary
        """
        validation_result = {
            "quality_score": confidence_metrics.text_quality_score,
            "structure_score": confidence_metrics.structure_confidence,
            "business_logic_score": confidence_metrics.business_logic_confidence,
            "overall_confidence": confidence_metrics.overall_confidence,
            "issues": confidence_metrics.validation_issues,
            "requires_human_review": confidence_metrics.requires_human_review,
            "recommendations": self.confidence_scorer.get_validation_recommendations(
                confidence_metrics
            ),
        }

        # Additional quality checks
        validation_result.update(self._perform_additional_quality_checks(ocr_text))

        return validation_result

    def _perform_additional_quality_checks(self, ocr_text: str) -> dict[str, Any]:
        """
        Perform additional quality checks beyond basic confidence scoring.

        Args:
            ocr_text: OCR result text

        Returns:
            Additional quality metrics
        """
        import re

        quality_metrics = {
            "character_density": len(ocr_text.replace(" ", "")) / max(len(ocr_text), 1),
            "line_count": len(ocr_text.split("\n")),
            "word_count": len(ocr_text.split()),
            "has_receipt_patterns": False,
            "has_price_patterns": False,
            "has_date_patterns": False,
            "suspicious_patterns": [],
        }

        # Check for receipt-specific patterns
        receipt_patterns = [
            r"(?:RAZEM|SUMA|KONIEC|TOTAL)",
            r"\d+[,.]?\d*\s*(?:PLN|zł)",
            r"\d{2}[-./]\d{2}[-./]\d{4}",
            r"(?:NIP|VAT|REGON)",
        ]

        pattern_matches = 0
        for pattern in receipt_patterns:
            if re.search(pattern, ocr_text, re.IGNORECASE):
                pattern_matches += 1
                if "RAZEM" in pattern or "SUMA" in pattern:
                    quality_metrics["has_receipt_patterns"] = True
                elif "PLN" in pattern or "zł" in pattern:
                    quality_metrics["has_price_patterns"] = True
                elif r"\d{2}[-./]\d{2}[-./]\d{4}" in pattern:
                    quality_metrics["has_date_patterns"] = True

        # Check for suspicious patterns (potential OCR errors)
        suspicious_patterns = [
            r"[^\w\s\.,\-\(\)\$\€\zł\@\#\&\*\+]{3,}",  # Multiple unusual characters
            r"[A-Z]{8,}",  # Very long all-caps words
            r"\s{5,}",  # Multiple consecutive spaces
        ]

        for pattern in suspicious_patterns:
            matches = re.findall(pattern, ocr_text)
            if matches:
                quality_metrics["suspicious_patterns"].extend(matches)

        return quality_metrics

    def _create_low_confidence_response(
        self, confidence_metrics: ConfidenceMetrics, ocr_text: str
    ) -> AgentResponse:
        """
        Create response for low confidence OCR results.

        Args:
            confidence_metrics: Confidence metrics
            ocr_text: OCR result text

        Returns:
            AgentResponse indicating low confidence
        """
        recommendations = self.confidence_scorer.get_validation_recommendations(
            confidence_metrics
        )

        return AgentResponse(
            success=False,
            text=ocr_text,  # Still provide the text for reference
            error=f"OCR confidence too low ({confidence_metrics.overall_confidence:.2f})",
            metadata={
                "confidence_metrics": {
                    "overall_confidence": confidence_metrics.overall_confidence,
                    "text_quality_score": confidence_metrics.text_quality_score,
                    "structure_confidence": confidence_metrics.structure_confidence,
                    "business_logic_confidence": confidence_metrics.business_logic_confidence,
                    "validation_issues": confidence_metrics.validation_issues,
                    "requires_human_review": confidence_metrics.requires_human_review,
                    "recommendations": recommendations,
                },
                "processing_stage": "ocr_validation_failed",
                "requires_human_review": True,
            },
            confidence=confidence_metrics.overall_confidence,
        )

    def _apply_enhanced_ocr_prompts(
        self, ocr_text: str, confidence_metrics: ConfidenceMetrics
    ) -> str:
        """
        Apply enhanced OCR prompts based on confidence level.

        Args:
            ocr_text: Original OCR text
            confidence_metrics: Confidence metrics

        Returns:
            Enhanced OCR text
        """
        # Apply different enhancement strategies based on confidence
        if confidence_metrics.overall_confidence >= 0.9:
            # High confidence - minimal enhancement
            return self._apply_minimal_enhancement(ocr_text)
        if confidence_metrics.overall_confidence >= 0.7:
            # Medium confidence - moderate enhancement
            return self._apply_moderate_enhancement(ocr_text)
        # Low confidence - aggressive enhancement
        return self._apply_aggressive_enhancement(ocr_text)

    def _apply_minimal_enhancement(self, ocr_text: str) -> str:
        """Apply minimal text enhancement for high confidence results."""
        # Basic cleanup only
        lines = ocr_text.split("\n")
        cleaned_lines = []

        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)

        return "\n".join(cleaned_lines)

    def _apply_moderate_enhancement(self, ocr_text: str) -> str:
        """Apply moderate text enhancement for medium confidence results."""
        import re

        # Apply basic enhancement
        enhanced_text = self._apply_minimal_enhancement(ocr_text)

        # Fix common OCR errors
        enhanced_text = re.sub(
            r"\s{3,}", "  ", enhanced_text
        )  # Multiple spaces to double spaces
        enhanced_text = re.sub(
            r"([0-9])\s*,\s*([0-9]{2})", r"\1,\2", enhanced_text
        )  # Fix decimal places

        return enhanced_text

    def _apply_aggressive_enhancement(self, ocr_text: str) -> str:
        """Apply aggressive text enhancement for low confidence results."""
        import re

        # Apply moderate enhancement first
        enhanced_text = self._apply_moderate_enhancement(ocr_text)

        # Additional aggressive fixes
        enhanced_text = re.sub(
            r"[^\w\s\.,\-\(\)\$\€\zł\@\#\&\*\+]", "", enhanced_text
        )  # Remove unusual characters
        enhanced_text = re.sub(
            r"([A-Z])\1{3,}", r"\1", enhanced_text
        )  # Fix repeated characters

        return enhanced_text

    def _create_success_response(
        self,
        enhanced_text: str,
        confidence_metrics: ConfidenceMetrics,
        validation_result: dict[str, Any],
    ) -> AgentResponse:
        """
        Create successful response with comprehensive metadata.

        Args:
            enhanced_text: Enhanced OCR text
            confidence_metrics: Confidence metrics
            validation_result: Validation result

        Returns:
            AgentResponse with success status and metadata
        """
        return AgentResponse(
            success=True,
            text=enhanced_text,
            message="Pomyślnie wyodrębniono tekst z pliku z walidacją anty-halucynacyjną",
            metadata={
                "confidence_metrics": {
                    "overall_confidence": confidence_metrics.overall_confidence,
                    "text_quality_score": confidence_metrics.text_quality_score,
                    "structure_confidence": confidence_metrics.structure_confidence,
                    "business_logic_confidence": confidence_metrics.business_logic_confidence,
                    "validation_issues": confidence_metrics.validation_issues,
                    "requires_human_review": confidence_metrics.requires_human_review,
                },
                "validation_result": validation_result,
                "processing_stage": "ocr_completed",
                "enhancement_applied": True,
                "quality_metrics": self.quality_metrics,
            },
            confidence=confidence_metrics.overall_confidence,
        )

    def get_metadata(self) -> dict[str, Any]:
        """Return enhanced metadata including anti-hallucination capabilities."""
        base_metadata = super().get_metadata()
        base_metadata.update(
            {
                "capabilities": [
                    "OCR processing",
                    "confidence scoring",
                    "progressive validation",
                    "quality assessment",
                    "anti-hallucination validation",
                ],
                "anti_hallucination_features": [
                    "confidence_threshold_validation",
                    "quality_metrics_calculation",
                    "progressive_enhancement",
                    "human_review_flagging",
                ],
                "confidence_threshold": self.confidence_scorer.confidence_threshold,
                "require_validation": self.confidence_scorer.require_validation,
            }
        )
        return base_metadata
