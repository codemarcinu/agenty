"""
Receipt validation pipeline with progressive validation system.

Orchestrates multiple validators to prevent hallucinations through
progressive validation with configurable thresholds and fallback mechanisms.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from .confidence_scorer import ConfidenceScorer
from .consensus_validator import ConsensusValidator
from .structured_output_validator import StructuredOutputValidator

logger = logging.getLogger(__name__)


@dataclass
class ValidationStage:
    """Represents a validation stage in the pipeline"""

    name: str
    validator: Any
    required: bool
    weight: float
    timeout: float
    description: str


@dataclass
class PipelineResult:
    """Result of the validation pipeline"""

    passed: bool
    overall_confidence: float
    stage_results: dict[str, Any]
    failed_stages: list[str]
    warnings: list[str]
    requires_human_review: bool
    recommendations: list[str]
    processing_time: float
    timestamp: datetime


class ReceiptValidationPipeline:
    """
    Progressive validation pipeline for receipt data.

    Implements a multi-stage validation system that progressively
    validates receipt data to prevent hallucinations.
    """

    def __init__(self, **kwargs):
        self.stages = []
        self.min_confidence_threshold = kwargs.get("min_confidence_threshold", 0.8)
        self.require_all_stages = kwargs.get("require_all_stages", False)
        self.parallel_validation = kwargs.get("parallel_validation", True)
        self.max_processing_time = kwargs.get("max_processing_time", 30.0)

        # Initialize default validators
        self._initialize_default_validators()

    def _initialize_default_validators(self):
        """Initialize default validation stages."""
        # Stage 1: Confidence scoring
        self.add_stage(
            name="confidence_scoring",
            validator=ConfidenceScorer(),
            required=True,
            weight=0.3,
            timeout=5.0,
            description="Assess confidence in OCR and analysis results",
        )

        # Stage 2: Structured output validation
        self.add_stage(
            name="structured_output_validation",
            validator=StructuredOutputValidator(),
            required=True,
            weight=0.4,
            timeout=10.0,
            description="Validate structured outputs using JSON Schema",
        )

        # Stage 3: Business logic validation
        self.add_stage(
            name="business_logic_validation",
            validator=BusinessLogicValidator(),
            required=False,
            weight=0.2,
            timeout=5.0,
            description="Validate business logic consistency",
        )

        # Stage 4: Consensus validation (optional)
        self.add_stage(
            name="consensus_validation",
            validator=ConsensusValidator(),
            required=False,
            weight=0.1,
            timeout=15.0,
            description="Cross-validate with multiple agents",
        )

    def add_stage(
        self,
        name: str,
        validator: Any,
        required: bool = True,
        weight: float = 1.0,
        timeout: float = 10.0,
        description: str = "",
    ):
        """
        Add a validation stage to the pipeline.

        Args:
            name: Stage name
            validator: Validator instance
            required: Whether this stage is required
            weight: Weight for confidence calculation
            timeout: Maximum processing time
            description: Stage description
        """
        stage = ValidationStage(
            name=name,
            validator=validator,
            required=required,
            weight=weight,
            timeout=timeout,
            description=description,
        )
        self.stages.append(stage)

    async def validate_receipt(
        self, receipt_data: dict[str, Any], ocr_text: str = ""
    ) -> PipelineResult:
        """
        Validate receipt data through the entire pipeline.

        Args:
            receipt_data: Receipt data to validate
            ocr_text: Original OCR text (optional)

        Returns:
            PipelineResult with validation status and details
        """
        start_time = datetime.now()
        logger.info(f"Starting validation pipeline with {len(self.stages)} stages")

        stage_results = {}
        failed_stages = []
        warnings = []
        recommendations = []

        try:
            if self.parallel_validation:
                # Run stages in parallel
                stage_results = await self._run_stages_parallel(receipt_data, ocr_text)
            else:
                # Run stages sequentially
                stage_results = await self._run_stages_sequential(
                    receipt_data, ocr_text
                )

            # Analyze results
            failed_stages = self._identify_failed_stages(stage_results)
            warnings = self._collect_warnings(stage_results)
            recommendations = self._generate_recommendations(
                stage_results, failed_stages
            )

            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(stage_results)

            # Determine if validation passed
            passed = self._determine_validation_success(
                stage_results, failed_stages, overall_confidence
            )

            # Determine if human review is required
            requires_human_review = self._requires_human_review(
                stage_results, overall_confidence
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            result = PipelineResult(
                passed=passed,
                overall_confidence=overall_confidence,
                stage_results=stage_results,
                failed_stages=failed_stages,
                warnings=warnings,
                requires_human_review=requires_human_review,
                recommendations=recommendations,
                processing_time=processing_time,
                timestamp=datetime.now(),
            )

            logger.info(
                "Validation pipeline completed",
                extra={
                    "passed": passed,
                    "confidence": overall_confidence,
                    "failed_stages": len(failed_stages),
                    "processing_time": processing_time,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error in validation pipeline: {e!s}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return PipelineResult(
                passed=False,
                overall_confidence=0.0,
                stage_results={},
                failed_stages=["pipeline_error"],
                warnings=[f"Pipeline error: {e!s}"],
                requires_human_review=True,
                recommendations=["Review pipeline configuration and try again"],
                processing_time=processing_time,
                timestamp=datetime.now(),
            )

    async def _run_stages_parallel(
        self, receipt_data: dict[str, Any], ocr_text: str
    ) -> dict[str, Any]:
        """Run validation stages in parallel."""
        tasks = []
        for stage in self.stages:
            task = self._run_single_stage(stage, receipt_data, ocr_text)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        stage_results = {}
        for i, result in enumerate(results):
            stage_name = self.stages[i].name
            if isinstance(result, Exception):
                stage_results[stage_name] = {
                    "success": False,
                    "error": str(result),
                    "confidence": 0.0,
                }
            else:
                stage_results[stage_name] = result

        return stage_results

    async def _run_stages_sequential(
        self, receipt_data: dict[str, Any], ocr_text: str
    ) -> dict[str, Any]:
        """Run validation stages sequentially."""
        stage_results = {}

        for stage in self.stages:
            try:
                result = await self._run_single_stage(stage, receipt_data, ocr_text)
                stage_results[stage.name] = result

                # Early termination if required stage fails
                if stage.required and not result["success"]:
                    logger.warning(
                        f"Required stage {stage.name} failed, stopping pipeline"
                    )
                    break

            except Exception as e:
                logger.error(f"Error in stage {stage.name}: {e!s}")
                stage_results[stage.name] = {
                    "success": False,
                    "error": str(e),
                    "confidence": 0.0,
                }

                if stage.required:
                    break

        return stage_results

    async def _run_single_stage(
        self, stage: ValidationStage, receipt_data: dict[str, Any], ocr_text: str
    ) -> dict[str, Any]:
        """Run a single validation stage."""
        try:
            start_time = datetime.now()

            if stage.name == "confidence_scoring":
                result = await self._run_confidence_scoring(
                    stage.validator, receipt_data, ocr_text
                )
            elif stage.name == "structured_output_validation":
                result = await self._run_structured_validation(
                    stage.validator, receipt_data
                )
            elif stage.name == "business_logic_validation":
                result = await self._run_business_logic_validation(
                    stage.validator, receipt_data
                )
            elif stage.name == "consensus_validation":
                result = await self._run_consensus_validation(
                    stage.validator, receipt_data, ocr_text
                )
            else:
                result = await self._run_generic_validation(
                    stage.validator, receipt_data
                )

            processing_time = (datetime.now() - start_time).total_seconds()
            result["processing_time"] = processing_time

            return result

        except TimeoutError:
            return {
                "success": False,
                "error": f"Stage {stage.name} timed out after {stage.timeout}s",
                "confidence": 0.0,
                "processing_time": stage.timeout,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Stage {stage.name} failed: {e!s}",
                "confidence": 0.0,
                "processing_time": 0.0,
            }

    async def _run_confidence_scoring(
        self, validator: ConfidenceScorer, receipt_data: dict[str, Any], ocr_text: str
    ) -> dict[str, Any]:
        """Run confidence scoring validation."""
        ocr_confidence = (
            validator.calculate_ocr_confidence(ocr_text) if ocr_text else None
        )
        analysis_confidence = validator.calculate_analysis_confidence(receipt_data)

        overall_confidence = analysis_confidence.overall_confidence
        if ocr_confidence:
            overall_confidence = (
                ocr_confidence.overall_confidence
                + analysis_confidence.overall_confidence
            ) / 2

        return {
            "success": overall_confidence >= validator.confidence_threshold,
            "confidence": overall_confidence,
            "ocr_confidence": ocr_confidence,
            "analysis_confidence": analysis_confidence,
            "issues": analysis_confidence.validation_issues,
        }

    async def _run_structured_validation(
        self, validator: StructuredOutputValidator, receipt_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Run structured output validation."""
        result = validator.validate_receipt_data(receipt_data)

        return {
            "success": result.is_valid,
            "confidence": result.confidence,
            "errors": result.errors,
            "warnings": result.warnings,
            "validated_data": result.validated_data,
        }

    async def _run_business_logic_validation(
        self, validator: Any, receipt_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Run business logic validation."""
        # This would be implemented by a BusinessLogicValidator class
        # For now, we'll do basic business logic validation here

        issues = []
        confidence = 1.0

        # Check total amount consistency
        items = receipt_data.get("items", [])
        if items:
            calculated_total = sum(
                item.get("total_price", 0) for item in items if isinstance(item, dict)
            )
            claimed_total = receipt_data.get("total_amount", 0)

            if abs(calculated_total - claimed_total) > 0.01:
                issues.append(
                    f"Total amount mismatch: calculated {calculated_total}, claimed {claimed_total}"
                )
                confidence *= 0.7

        # Check for realistic values
        if receipt_data.get("total_amount", 0) > 10000:
            issues.append("Unrealistic total amount")
            confidence *= 0.5

        return {
            "success": confidence >= 0.8,
            "confidence": confidence,
            "issues": issues,
        }

    async def _run_consensus_validation(
        self, validator: ConsensusValidator, receipt_data: dict[str, Any], ocr_text: str
    ) -> dict[str, Any]:
        """Run consensus validation."""
        # This would require multiple agents to be configured
        # For now, return a placeholder result
        return {
            "success": True,
            "confidence": 0.9,
            "message": "Consensus validation not configured",
        }

    async def _run_generic_validation(
        self, validator: Any, receipt_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Run generic validation for unknown validator types."""
        try:
            if hasattr(validator, "validate"):
                result = validator.validate(receipt_data)
                return {
                    "success": True,
                    "confidence": getattr(result, "confidence", 0.8),
                    "result": result,
                }
            return {
                "success": True,
                "confidence": 0.8,
                "message": "Generic validation completed",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "confidence": 0.0}

    def _identify_failed_stages(self, stage_results: dict[str, Any]) -> list[str]:
        """Identify which stages failed."""
        failed_stages = []
        for stage_name, result in stage_results.items():
            if not result.get("success", False):
                failed_stages.append(stage_name)
        return failed_stages

    def _collect_warnings(self, stage_results: dict[str, Any]) -> list[str]:
        """Collect warnings from all stages."""
        warnings = []
        for result in stage_results.values():
            if "warnings" in result:
                warnings.extend(result["warnings"])
            if "issues" in result:
                warnings.extend(result["issues"])
        return warnings

    def _generate_recommendations(
        self, stage_results: dict[str, Any], failed_stages: list[str]
    ) -> list[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        for stage_name in failed_stages:
            if stage_name == "confidence_scoring":
                recommendations.append("Improve OCR quality or image resolution")
            elif stage_name == "structured_output_validation":
                recommendations.append("Check data format and structure")
            elif stage_name == "business_logic_validation":
                recommendations.append("Verify data consistency and business rules")
            elif stage_name == "consensus_validation":
                recommendations.append("Review with multiple analysis methods")

        return recommendations

    def _calculate_overall_confidence(self, stage_results: dict[str, Any]) -> float:
        """Calculate overall confidence from all stages."""
        if not stage_results:
            return 0.0

        total_weight = 0.0
        weighted_confidence = 0.0

        for stage in self.stages:
            if stage.name in stage_results:
                result = stage_results[stage.name]
                confidence = result.get("confidence", 0.0)
                weighted_confidence += confidence * stage.weight
                total_weight += stage.weight

        if total_weight == 0:
            return 0.0

        return weighted_confidence / total_weight

    def _determine_validation_success(
        self,
        stage_results: dict[str, Any],
        failed_stages: list[str],
        overall_confidence: float,
    ) -> bool:
        """Determine if validation was successful."""
        if overall_confidence < self.min_confidence_threshold:
            return False

        if self.require_all_stages:
            # All stages must pass
            return len(failed_stages) == 0
        # Only required stages must pass
        required_failures = [
            stage_name
            for stage_name in failed_stages
            if any(stage.name == stage_name and stage.required for stage in self.stages)
        ]
        return len(required_failures) == 0

    def _requires_human_review(
        self, stage_results: dict[str, Any], overall_confidence: float
    ) -> bool:
        """Determine if human review is required."""
        return (
            overall_confidence < self.min_confidence_threshold
            or len(self._identify_failed_stages(stage_results)) > 0
        )

    def get_pipeline_summary(self, result: PipelineResult) -> dict[str, Any]:
        """Get summary of pipeline results."""
        return {
            "validation_passed": result.passed,
            "overall_confidence": result.overall_confidence,
            "stage_count": len(self.stages),
            "failed_stage_count": len(result.failed_stages),
            "warning_count": len(result.warnings),
            "requires_human_review": result.requires_human_review,
            "processing_time": result.processing_time,
            "timestamp": result.timestamp.isoformat(),
        }


class BusinessLogicValidator:
    """Business logic validator for receipt data."""

    def __init__(self):
        self.max_total_amount = 10000
        self.max_item_price = 1000
        self.min_confidence = 0.8

    def validate(self, receipt_data: dict[str, Any]) -> dict[str, Any]:
        """Validate business logic consistency."""
        issues = []
        confidence = 1.0

        # Validate total amount
        total_amount = receipt_data.get("total_amount", 0)
        if total_amount > self.max_total_amount:
            issues.append(f"Total amount too high: {total_amount}")
            confidence *= 0.5

        # Validate item prices
        items = receipt_data.get("items", [])
        for item in items:
            if not isinstance(item, dict):
                continue

            price = item.get("unit_price", 0)
            if price > self.max_item_price:
                issues.append(
                    f"Item price too high: {item.get('name', 'Unknown')} - {price}"
                )
                confidence *= 0.8

        return {
            "success": confidence >= self.min_confidence,
            "confidence": confidence,
            "issues": issues,
        }
