"""
Enhanced Receipt Analysis Agent with structured outputs and anti-hallucination.

Implements structured outputs with JSON Schema validation, confidence scoring,
and multi-layer validation to prevent hallucinations in receipt analysis.
"""

from datetime import datetime
import logging
from typing import Any

from agents.interfaces import AgentResponse
from agents.receipt_analysis_agent import ReceiptAnalysisAgent
from core.hybrid_llm_client import hybrid_llm_client

from .confidence_scorer import ConfidenceMetrics, ConfidenceScorer
from .structured_output_validator import StructuredOutputValidator, ValidationResult

logger = logging.getLogger(__name__)


class EnhancedReceiptAnalysisAgent(ReceiptAnalysisAgent):
    """
    Enhanced Receipt Analysis Agent with anti-hallucination mechanisms.

    Extends the base ReceiptAnalysisAgent with:
    - Structured outputs with JSON Schema validation
    - Confidence scoring and progressive validation
    - Multi-layer validation pipeline
    - Automatic fallback mechanisms
    - Detailed validation reporting
    """

    def __init__(
        self,
        name: str = "EnhancedReceiptAnalysisAgent",
        error_handler=None,
        fallback_manager=None,
        **kwargs,
    ) -> None:
        """Initialize EnhancedReceiptAnalysisAgent with anti-hallucination features."""
        super().__init__(
            name=name,
            error_handler=error_handler,
            fallback_manager=fallback_manager,
            **kwargs,
        )

        # Initialize anti-hallucination components
        self.confidence_scorer = ConfidenceScorer(
            confidence_threshold=kwargs.get("confidence_threshold", 0.7),
            require_validation=kwargs.get("require_validation", True),
        )

        self.structured_validator = StructuredOutputValidator(
            strict_mode=kwargs.get("strict_mode", True),
            allow_partial=kwargs.get("allow_partial", False),
        )

        # Anti-hallucination configuration
        self.use_structured_outputs = kwargs.get("use_structured_outputs", True)
        self.require_validation = kwargs.get("require_validation", True)
        self.auto_fallback = kwargs.get("auto_fallback", True)
        self.max_retries = kwargs.get("max_retries", 2)

    async def process(self, context: dict[str, Any]) -> AgentResponse:
        """
        Process receipt analysis with enhanced anti-hallucination validation.

        Args:
            context: Context containing OCR text and other parameters

        Returns:
            AgentResponse with structured receipt data and validation metrics
        """
        ocr_text = context.get("ocr_text", "")
        if not ocr_text:
            return AgentResponse(
                success=False,
                error="Brak tekstu OCR do analizy",
            )

        logger.info(
            "Rozpoczynam analizę paragonu z walidacją anty-halucynacyjną",
            extra={"text_length": len(ocr_text), "agent_name": self.name},
        )

        try:
            # Step 1: Calculate OCR confidence
            ocr_confidence = self.confidence_scorer.calculate_ocr_confidence(ocr_text)

            # Step 2: Use structured outputs if enabled
            if self.use_structured_outputs:
                analysis_result = await self._process_with_structured_outputs(
                    ocr_text, context
                )
            else:
                analysis_result = await self._process_with_standard_llm(
                    ocr_text, context
                )

            # Step 3: Validate analysis results
            validation_result = self._validate_analysis_results(
                analysis_result, ocr_confidence
            )

            # Step 4: Calculate final confidence
            final_confidence = self._calculate_final_confidence(
                ocr_confidence, validation_result
            )

            # Step 5: Determine if processing should proceed
            if not self._should_proceed_with_analysis(
                final_confidence, validation_result
            ):
                return self._create_low_confidence_response(
                    analysis_result, final_confidence, validation_result
                )

            # Step 6: Apply post-processing and normalization
            processed_data = await self._apply_post_processing(
                analysis_result, validation_result
            )

            # Step 7: Create comprehensive response
            return self._create_success_response(
                processed_data, final_confidence, validation_result
            )

        except Exception as e:
            logger.error(f"Błąd podczas analizy paragonu: {e!s}")
            return AgentResponse(
                success=False,
                error=f"Wystąpił błąd podczas analizy paragonu: {e!s}",
            )

    async def _process_with_structured_outputs(
        self, ocr_text: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process receipt analysis using structured outputs with JSON Schema validation.

        Args:
            ocr_text: OCR text to analyze
            context: Processing context

        Returns:
            Structured receipt data
        """
        use_bielik = context.get("use_bielik", True)
        model = (
            "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
            if use_bielik
            else "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        )

        # Create structured output prompt
        structured_prompt = self.structured_validator.get_structured_output_prompt()

        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": "Jesteś specjalistycznym asystentem do analizy paragonów z polskich sklepów. Wyciągnij strukturalne dane z tekstu paragonu używając JSON Schema.",
            },
            {
                "role": "user",
                "content": f"{structured_prompt}\n\nTekst paragonu:\n{ocr_text}",
            },
        ]

        # Call LLM with structured output format
        response = await hybrid_llm_client.chat(
            model=model,
            messages=messages,
            stream=False,
        )

        if not response or "message" not in response:
            logger.warning("LLM nie zwrócił odpowiedzi, używam fallback parser")
            return self._fallback_parse(ocr_text)

        # Extract and validate structured data
        content = response["message"]["content"]
        validation_result = self.structured_validator.validate_receipt_data(content)

        if validation_result.is_valid:
            logger.info("Structured output validation successful")
            return validation_result.validated_data
        logger.warning(
            f"Structured output validation failed: {validation_result.errors}"
        )
        # Fallback to standard parsing
        return self._fallback_parse(ocr_text)

    async def _process_with_standard_llm(
        self, ocr_text: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process receipt analysis using standard LLM approach (fallback).

        Args:
            ocr_text: OCR text to analyze
            context: Processing context

        Returns:
            Receipt data
        """
        # Use parent class method
        response = await super().process(context)

        if response.success and response.data:
            return response.data
        # Fallback to regex parser
        return self._fallback_parse(ocr_text)

    def _validate_analysis_results(
        self, analysis_data: dict[str, Any], ocr_confidence: ConfidenceMetrics
    ) -> ValidationResult:
        """
        Validate analysis results using multiple validation layers.

        Args:
            analysis_data: Analysis results
            ocr_confidence: OCR confidence metrics

        Returns:
            Validation result
        """
        # Validate structured data
        validation_result = self.structured_validator.validate_receipt_data(
            analysis_data
        )

        # Calculate analysis confidence
        analysis_confidence = self.confidence_scorer.calculate_analysis_confidence(
            analysis_data
        )

        # Combine validation results
        combined_validation = ValidationResult(
            is_valid=validation_result.is_valid
            and analysis_confidence.overall_confidence
            >= self.confidence_scorer.confidence_threshold,
            errors=validation_result.errors + analysis_confidence.validation_issues,
            warnings=validation_result.warnings,
            confidence=min(
                validation_result.confidence, analysis_confidence.overall_confidence
            ),
            validated_data=(
                validation_result.validated_data if validation_result.is_valid else None
            ),
            timestamp=datetime.now(),
        )

        return combined_validation

    def _calculate_final_confidence(
        self, ocr_confidence: ConfidenceMetrics, validation_result: ValidationResult
    ) -> float:
        """
        Calculate final confidence score combining OCR and analysis confidence.

        Args:
            ocr_confidence: OCR confidence metrics
            validation_result: Validation result

        Returns:
            Final confidence score
        """
        # Weight OCR confidence and validation confidence
        ocr_weight = 0.4
        validation_weight = 0.6

        final_confidence = (
            ocr_confidence.overall_confidence * ocr_weight
            + validation_result.confidence * validation_weight
        )

        return final_confidence

    def _should_proceed_with_analysis(
        self, final_confidence: float, validation_result: ValidationResult
    ) -> bool:
        """
        Determine if analysis should proceed based on confidence and validation.

        Args:
            final_confidence: Final confidence score
            validation_result: Validation result

        Returns:
            True if processing should continue
        """
        return (
            final_confidence >= self.confidence_scorer.confidence_threshold
            and validation_result.is_valid
            and len(validation_result.errors) <= 3  # Allow some minor errors
        )

    def _create_low_confidence_response(
        self,
        analysis_data: dict[str, Any],
        final_confidence: float,
        validation_result: ValidationResult,
    ) -> AgentResponse:
        """
        Create response for low confidence analysis results.

        Args:
            analysis_data: Analysis data
            final_confidence: Final confidence score
            validation_result: Validation result

        Returns:
            AgentResponse indicating low confidence
        """
        return AgentResponse(
            success=False,
            data=analysis_data,  # Still provide data for reference
            error=f"Analysis confidence too low ({final_confidence:.2f})",
            metadata={
                "confidence_metrics": {
                    "final_confidence": final_confidence,
                    "validation_confidence": validation_result.confidence,
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings,
                    "requires_human_review": True,
                },
                "processing_stage": "analysis_validation_failed",
                "recommendations": self._get_validation_recommendations(
                    validation_result
                ),
            },
            confidence=final_confidence,
        )

    async def _apply_post_processing(
        self, analysis_data: dict[str, Any], validation_result: ValidationResult
    ) -> dict[str, Any]:
        """
        Apply post-processing and normalization to validated data.

        Args:
            analysis_data: Validated analysis data
            validation_result: Validation result

        Returns:
            Processed receipt data
        """
        # Apply parent class post-processing
        processed_data = self._validate_and_fix_data(analysis_data)

        # Apply additional anti-hallucination post-processing
        processed_data = self._apply_anti_hallucination_post_processing(processed_data)

        # Normalize store name and product names
        self._normalize_store_name(processed_data)
        self._normalize_product_names(processed_data.get("items", []))

        # Apply advanced categorization
        await self._categorize_products_advanced(processed_data.get("items", []))

        return processed_data

    def _apply_anti_hallucination_post_processing(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Apply additional anti-hallucination post-processing.

        Args:
            data: Receipt data

        Returns:
            Post-processed data
        """
        # Validate business logic consistency
        data = self._validate_business_logic_consistency(data)

        # Remove suspicious entries
        data = self._remove_suspicious_entries(data)

        # Normalize data formats
        data = self._normalize_data_formats(data)

        return data

    def _validate_business_logic_consistency(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate and fix business logic consistency.

        Args:
            data: Receipt data

        Returns:
            Validated data
        """
        items = data.get("items", [])
        if not items:
            return data

        # Validate item consistency
        for item in items:
            if not isinstance(item, dict):
                continue

            # Ensure quantity and prices are consistent
            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            total_price = item.get("total_price", 0)

            if quantity > 0 and unit_price > 0:
                expected_total = quantity * unit_price
                if abs(expected_total - total_price) > 0.01:
                    item["total_price"] = expected_total
                    logger.info(
                        f"Fixed item total price: {item.get('name', 'Unknown')}"
                    )

        # Validate total amount
        calculated_total = sum(item.get("total_price", 0) for item in items)
        claimed_total = data.get("total_amount", 0)

        if abs(calculated_total - claimed_total) > 0.01:
            data["total_amount"] = calculated_total
            logger.info(f"Fixed total amount: {claimed_total} -> {calculated_total}")

        return data

    def _remove_suspicious_entries(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Remove suspicious entries that might be hallucinations.

        Args:
            data: Receipt data

        Returns:
            Cleaned data
        """
        items = data.get("items", [])
        if not items:
            return data

        # Remove items with suspicious characteristics
        cleaned_items = []
        for item in items:
            if not isinstance(item, dict):
                continue

            # Check for suspicious patterns
            name = item.get("name", "")
            price = item.get("unit_price", 0)

            # Remove items with very high prices (likely errors)
            if price > 1000:
                logger.warning(
                    f"Removed suspicious item with high price: {name} - {price}"
                )
                continue

            # Remove items with very short names (likely OCR errors)
            if len(name.strip()) < 2:
                logger.warning(f"Removed item with very short name: {name}")
                continue

            # Remove items with all caps names (likely OCR errors)
            if name.isupper() and len(name) > 10:
                logger.warning(f"Removed suspicious all-caps item: {name}")
                continue

            cleaned_items.append(item)

        data["items"] = cleaned_items
        return data

    def _normalize_data_formats(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize data formats for consistency.

        Args:
            data: Receipt data

        Returns:
            Normalized data
        """
        # Normalize date format
        if data.get("date"):
            data["date"] = self._normalize_date(data["date"])

        # Normalize numeric values
        if "total_amount" in data:
            try:
                data["total_amount"] = float(
                    str(data["total_amount"]).replace(",", ".")
                )
            except ValueError:
                data["total_amount"] = 0.0

        # Normalize item data
        items = data.get("items", [])
        for item in items:
            if not isinstance(item, dict):
                continue

            for field in ["quantity", "unit_price", "total_price"]:
                if field in item:
                    try:
                        item[field] = float(str(item[field]).replace(",", "."))
                    except ValueError:
                        item[field] = 0.0

        return data

    def _get_validation_recommendations(
        self, validation_result: ValidationResult
    ) -> list[str]:
        """
        Get recommendations for improving validation results.

        Args:
            validation_result: Validation result

        Returns:
            List of recommendations
        """
        recommendations = []

        if validation_result.confidence < 0.8:
            recommendations.append("Consider manual review of analysis results")

        if validation_result.errors:
            recommendations.append(
                f"Fix {len(validation_result.errors)} validation errors"
            )

        if validation_result.warnings:
            recommendations.append(
                f"Address {len(validation_result.warnings)} validation warnings"
            )

        return recommendations

    def _create_success_response(
        self,
        processed_data: dict[str, Any],
        final_confidence: float,
        validation_result: ValidationResult,
    ) -> AgentResponse:
        """
        Create successful response with comprehensive metadata.

        Args:
            processed_data: Processed receipt data
            final_confidence: Final confidence score
            validation_result: Validation result

        Returns:
            AgentResponse with success status and metadata
        """
        logger.info(
            "Analiza paragonu zakończona pomyślnie",
            extra={
                "store_name": processed_data.get("store_name"),
                "items_count": len(processed_data.get("items", [])),
                "total_amount": processed_data.get("total_amount", 0),
                "confidence": final_confidence,
            },
        )

        return AgentResponse(
            success=True,
            text="Paragon został pomyślnie przeanalizowany z walidacją anty-halucynacyjną",
            data=processed_data,
            metadata={
                "confidence_metrics": {
                    "final_confidence": final_confidence,
                    "validation_confidence": validation_result.confidence,
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings,
                    "requires_human_review": False,
                },
                "processing_stage": "analysis_completed",
                "structured_outputs_used": self.use_structured_outputs,
                "validation_passed": validation_result.is_valid,
                "post_processing_applied": True,
            },
            confidence=final_confidence,
        )

    def get_metadata(self) -> dict[str, Any]:
        """Return enhanced metadata including anti-hallucination capabilities."""
        base_metadata = super().get_metadata()
        base_metadata.update(
            {
                "capabilities": [
                    "receipt analysis",
                    "structured outputs",
                    "JSON Schema validation",
                    "confidence scoring",
                    "multi-layer validation",
                    "anti-hallucination validation",
                ],
                "anti_hallucination_features": [
                    "structured_output_validation",
                    "confidence_threshold_validation",
                    "business_logic_validation",
                    "suspicious_entry_removal",
                    "human_review_flagging",
                ],
                "structured_outputs_enabled": self.use_structured_outputs,
                "confidence_threshold": self.confidence_scorer.confidence_threshold,
                "strict_validation": self.structured_validator.strict_mode,
            }
        )
        return base_metadata
