"""
Confidence scoring system for anti-hallucination validation.

Provides mechanisms to assess confidence in OCR results and data analysis,
with progressive validation thresholds and quality metrics.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceMetrics:
    """Confidence metrics for data validation"""

    overall_confidence: float
    text_quality_score: float
    structure_confidence: float
    business_logic_confidence: float
    validation_issues: list[str]
    requires_human_review: bool
    timestamp: datetime


class ConfidenceScorer:
    """
    Confidence scoring system for OCR and data analysis validation.

    Implements progressive validation with configurable thresholds
    and quality assessment metrics.
    """

    def __init__(self, **kwargs):
        self.confidence_threshold = kwargs.get("confidence_threshold", 0.7)
        self.require_validation = kwargs.get("require_validation", True)
        self.min_text_length = kwargs.get("min_text_length", 10)
        self.max_validation_issues = kwargs.get("max_validation_issues", 3)

    def calculate_ocr_confidence(self, ocr_result: str) -> ConfidenceMetrics:
        """
        Calculate confidence score for OCR results.

        Args:
            ocr_result: Raw OCR text

        Returns:
            ConfidenceMetrics with detailed confidence assessment
        """
        issues = []
        text_quality_score = 1.0
        structure_confidence = 1.0

        # Check text length
        if len(ocr_result.strip()) < self.min_text_length:
            issues.append(f"Text too short: {len(ocr_result)} chars")
            text_quality_score *= 0.3

        # Check for common OCR artifacts
        artifact_patterns = [
            r"[^\w\s\.,\-\(\)\$\€\zł\@\#\&\*\+]",  # Unusual characters
            r"\s{3,}",  # Multiple consecutive spaces
            r"[A-Z]{5,}",  # All caps words (likely OCR error)
        ]

        for pattern in artifact_patterns:
            matches = re.findall(pattern, ocr_result)
            if matches:
                issues.append(f"OCR artifacts detected: {len(matches)} instances")
                text_quality_score *= 0.8

        # Check for receipt-specific patterns
        receipt_patterns = [
            r"\d{2}[-./]\d{2}[-./]\d{4}",  # Date patterns
            r"\d+[,.]?\d*\s*(?:PLN|zł)",  # Price patterns
            r"(?:RAZEM|SUMA|KONIEC)",  # Total indicators
        ]

        pattern_matches = 0
        for pattern in receipt_patterns:
            if re.search(pattern, ocr_result, re.IGNORECASE):
                pattern_matches += 1

        if pattern_matches < 2:
            issues.append("Missing receipt-specific patterns")
            structure_confidence *= 0.6

        # Calculate business logic confidence
        business_logic_confidence = self._assess_business_logic(ocr_result)

        # Overall confidence calculation
        overall_confidence = (
            text_quality_score * 0.4
            + structure_confidence * 0.3
            + business_logic_confidence * 0.3
        )

        requires_human_review = (
            overall_confidence < self.confidence_threshold
            or len(issues) > self.max_validation_issues
        )

        return ConfidenceMetrics(
            overall_confidence=overall_confidence,
            text_quality_score=text_quality_score,
            structure_confidence=structure_confidence,
            business_logic_confidence=business_logic_confidence,
            validation_issues=issues,
            requires_human_review=requires_human_review,
            timestamp=datetime.now(),
        )

    def _assess_business_logic(self, text: str) -> float:
        """
        Assess business logic consistency in receipt data.

        Args:
            text: OCR text to analyze

        Returns:
            Confidence score for business logic
        """
        confidence = 1.0

        # Check for price consistency
        prices = re.findall(r"(\d+[,.]?\d*)\s*(?:PLN|zł)", text)
        if prices:
            try:
                price_values = [float(p.replace(",", ".")) for p in prices]
                if max(price_values) > 10000:  # Unrealistic price
                    confidence *= 0.5
                if min(price_values) < 0:  # Negative price
                    confidence *= 0.3
            except ValueError:
                confidence *= 0.7

        # Check for date consistency
        dates = re.findall(r"\d{2}[-./]\d{2}[-./]\d{4}", text)
        if dates:
            try:
                from datetime import datetime

                for date_str in dates:
                    parsed_date = datetime.strptime(date_str, "%d.%m.%Y")
                    if parsed_date.year < 2020 or parsed_date.year > 2030:
                        confidence *= 0.6
            except ValueError:
                confidence *= 0.8

        return confidence

    def calculate_analysis_confidence(
        self, analysis_data: dict[str, Any]
    ) -> ConfidenceMetrics:
        """
        Calculate confidence score for receipt analysis results.

        Args:
            analysis_data: Structured receipt data

        Returns:
            ConfidenceMetrics with detailed confidence assessment
        """
        issues = []
        structure_confidence = 1.0
        business_logic_confidence = 1.0

        # Validate required fields
        required_fields = ["store_name", "items", "total_amount"]
        for field in required_fields:
            if field not in analysis_data or not analysis_data[field]:
                issues.append(f"Missing required field: {field}")
                structure_confidence *= 0.5

        # Validate items structure
        items = analysis_data.get("items", [])
        if not isinstance(items, list):
            issues.append("Items field is not a list")
            structure_confidence *= 0.3
        else:
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    issues.append(f"Item {i} is not a dictionary")
                    structure_confidence *= 0.8
                    continue

                item_required = ["name", "quantity", "unit_price"]
                for field in item_required:
                    if field not in item:
                        issues.append(f"Item {i} missing {field}")
                        structure_confidence *= 0.9

        # Business logic validation
        if items:
            total_calculated = sum(
                item.get("total_price", 0) for item in items if isinstance(item, dict)
            )
            total_claimed = analysis_data.get("total_amount", 0)

            if abs(total_calculated - total_claimed) > 0.01:
                issues.append(
                    f"Total mismatch: calculated {total_calculated}, claimed {total_claimed}"
                )
                business_logic_confidence *= 0.4

        # Overall confidence calculation
        overall_confidence = (
            structure_confidence * 0.6 + business_logic_confidence * 0.4
        )

        requires_human_review = (
            overall_confidence < self.confidence_threshold
            or len(issues) > self.max_validation_issues
        )

        return ConfidenceMetrics(
            overall_confidence=overall_confidence,
            text_quality_score=1.0,  # Not applicable for analysis
            structure_confidence=structure_confidence,
            business_logic_confidence=business_logic_confidence,
            validation_issues=issues,
            requires_human_review=requires_human_review,
            timestamp=datetime.now(),
        )

    def should_proceed_with_validation(
        self, confidence_metrics: ConfidenceMetrics
    ) -> bool:
        """
        Determine if processing should proceed based on confidence.

        Args:
            confidence_metrics: Calculated confidence metrics

        Returns:
            True if processing should continue, False if human review needed
        """
        return (
            confidence_metrics.overall_confidence >= self.confidence_threshold
            and not confidence_metrics.requires_human_review
        )

    def get_validation_recommendations(
        self, confidence_metrics: ConfidenceMetrics
    ) -> list[str]:
        """
        Get recommendations for improving confidence.

        Args:
            confidence_metrics: Calculated confidence metrics

        Returns:
            List of recommendations
        """
        recommendations = []

        if confidence_metrics.text_quality_score < 0.8:
            recommendations.append("Improve image quality for better OCR results")

        if confidence_metrics.structure_confidence < 0.8:
            recommendations.append("Verify receipt structure and format")

        if confidence_metrics.business_logic_confidence < 0.8:
            recommendations.append("Check for data consistency and business logic")

        if confidence_metrics.overall_confidence < self.confidence_threshold:
            recommendations.append("Consider manual review of results")

        return recommendations
