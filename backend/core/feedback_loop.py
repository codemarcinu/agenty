"""
Feedback Loop System for OCR and Receipt Analysis

This module provides a comprehensive feedback loop system for collecting
user corrections and logging failed extraction cases for AI training.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any
import uuid

logger = logging.getLogger(__name__)


@dataclass
class FeedbackEntry:
    """Single feedback entry with user corrections"""

    id: str
    timestamp: str
    original_ocr_text: str
    original_analysis: dict[str, Any]
    user_corrections: dict[str, Any]
    confidence_score: float
    feedback_type: str  # "correction", "improvement", "error"
    user_notes: str | None = None
    processing_time: float | None = None


@dataclass
class FailedExtractionCase:
    """Case of failed extraction for training data"""

    id: str
    timestamp: str
    file_path: str
    ocr_text: str
    analysis_result: dict[str, Any]
    error_type: str  # "ocr_failure", "analysis_failure", "validation_failure"
    error_details: str
    confidence_score: float
    suggested_improvements: list[str]


class FeedbackLoopManager:
    """
    Manages feedback collection and failed extraction logging.

    Features:
    - User correction collection
    - Failed extraction logging
    - Training data generation
    - Performance metrics tracking
    - Automatic improvement suggestions
    """

    def __init__(self, data_dir: str = "data/feedback"):
        self.data_dir = Path(data_dir)
        self.feedback_file = self.data_dir / "feedback_entries.jsonl"
        self.failed_cases_file = self.data_dir / "failed_extractions.jsonl"
        self.metrics_file = self.data_dir / "feedback_metrics.json"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize metrics
        self.metrics = {
            "total_feedback_entries": 0,
            "total_failed_cases": 0,
            "average_confidence": 0.0,
            "most_common_errors": {},
            "improvement_suggestions": [],
            "last_updated": datetime.now().isoformat(),
        }

        # Load existing metrics
        self._load_metrics()

    def _load_metrics(self):
        """Load existing metrics from file"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, encoding="utf-8") as f:
                    self.metrics.update(json.load(f))
        except Exception as e:
            logger.warning(f"Could not load metrics: {e}")

    def _save_metrics(self):
        """Save current metrics to file"""
        try:
            self.metrics["last_updated"] = datetime.now().isoformat()
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save metrics: {e}")

    def log_user_feedback(
        self,
        original_ocr_text: str,
        original_analysis: dict[str, Any],
        user_corrections: dict[str, Any],
        confidence_score: float,
        feedback_type: str = "correction",
        user_notes: str | None = None,
        processing_time: float | None = None,
    ) -> str:
        """
        Log user feedback for OCR/analysis improvements.

        Args:
            original_ocr_text: Original OCR text
            original_analysis: Original analysis result
            user_corrections: User's corrections
            confidence_score: Confidence score of original result
            feedback_type: Type of feedback
            user_notes: Optional user notes
            processing_time: Processing time in seconds

        Returns:
            Feedback entry ID
        """
        entry = FeedbackEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            original_ocr_text=original_ocr_text,
            original_analysis=original_analysis,
            user_corrections=user_corrections,
            confidence_score=confidence_score,
            feedback_type=feedback_type,
            user_notes=user_notes,
            processing_time=processing_time,
        )

        # Save to file
        try:
            with open(self.feedback_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

            # Update metrics
            self.metrics["total_feedback_entries"] += 1
            self._update_confidence_metrics(confidence_score)
            self._save_metrics()

            logger.info(f"Logged user feedback: {entry.id}")
            return entry.id

        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
            return ""

    def log_failed_extraction(
        self,
        file_path: str,
        ocr_text: str,
        analysis_result: dict[str, Any],
        error_type: str,
        error_details: str,
        confidence_score: float,
        suggested_improvements: list[str] | None = None,
    ) -> str:
        """
        Log failed extraction case for training data.

        Args:
            file_path: Path to the file
            ocr_text: OCR text (even if poor quality)
            analysis_result: Analysis result (even if failed)
            error_type: Type of error
            error_details: Detailed error description
            confidence_score: Confidence score
            suggested_improvements: List of suggested improvements

        Returns:
            Failed case ID
        """
        case = FailedExtractionCase(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            file_path=file_path,
            ocr_text=ocr_text,
            analysis_result=analysis_result,
            error_type=error_type,
            error_details=error_details,
            confidence_score=confidence_score,
            suggested_improvements=suggested_improvements or [],
        )

        # Save to file
        try:
            with open(self.failed_cases_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(case), ensure_ascii=False) + "\n")

            # Update metrics
            self.metrics["total_failed_cases"] += 1
            self._update_error_metrics(error_type)
            self._save_metrics()

            logger.info(f"Logged failed extraction: {case.id}")
            return case.id

        except Exception as e:
            logger.error(f"Failed to log failed extraction: {e}")
            return ""

    def _update_confidence_metrics(self, confidence_score: float):
        """Update confidence-related metrics"""
        current_avg = self.metrics["average_confidence"]
        total_entries = self.metrics["total_feedback_entries"]

        if total_entries > 0:
            self.metrics["average_confidence"] = (
                current_avg * (total_entries - 1) + confidence_score
            ) / total_entries

    def _update_error_metrics(self, error_type: str):
        """Update error-related metrics"""
        if error_type not in self.metrics["most_common_errors"]:
            self.metrics["most_common_errors"][error_type] = 0
        self.metrics["most_common_errors"][error_type] += 1

    def get_feedback_statistics(self) -> dict[str, Any]:
        """Get feedback statistics"""
        feedback_size = 0
        failed_size = 0

        if self.feedback_file.exists():
            feedback_size = self.feedback_file.stat().st_size

        if self.failed_cases_file.exists():
            failed_size = self.failed_cases_file.stat().st_size

        return {
            **self.metrics,
            "feedback_file_size": feedback_size,
            "failed_cases_file_size": failed_size,
        }

    def get_training_data(self, limit: int = 100) -> dict[str, Any]:
        """
        Get training data from feedback and failed cases.

        Args:
            limit: Maximum number of entries to return

        Returns:
            Dictionary with feedback and failed cases for training
        """
        feedback_data = []
        failed_data = []

        # Load feedback entries
        if self.feedback_file.exists():
            with open(self.feedback_file, encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    try:
                        entry = json.loads(line.strip())
                        feedback_data.append(entry)
                    except json.JSONDecodeError:
                        continue

        # Load failed cases
        if self.failed_cases_file.exists():
            with open(self.failed_cases_file, encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    try:
                        case = json.loads(line.strip())
                        failed_data.append(case)
                    except json.JSONDecodeError:
                        continue

        return {
            "feedback_entries": feedback_data,
            "failed_cases": failed_data,
            "total_feedback": len(feedback_data),
            "total_failed": len(failed_data),
        }

    def generate_improvement_suggestions(self) -> list[str]:
        """Generate improvement suggestions based on feedback data"""
        suggestions = []

        # Analyze feedback patterns
        training_data = self.get_training_data(limit=50)
        total_feedback = training_data.get("total_feedback", 0)
        total_failed = training_data.get("total_failed", 0)

        if total_feedback > 0:
            suggestions.append(
                "Consider improving OCR preprocessing for low-confidence cases"
            )

        if total_failed > 0:
            suggestions.append(
                "Review failed extraction patterns for model improvements"
            )

        # Add specific suggestions based on error types
        error_types = self.metrics.get("most_common_errors", {})
        for error_type, count in error_types.items():
            if isinstance(count, int) and count > 5:
                suggestions.append(f"Focus on improving {error_type} handling")

        return suggestions

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old feedback and failed case data"""
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

        # Clean feedback entries
        if self.feedback_file.exists():
            cleaned_entries = []
            with open(self.feedback_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_timestamp = datetime.fromisoformat(
                            entry["timestamp"]
                        ).timestamp()
                        if entry_timestamp > cutoff_date:
                            cleaned_entries.append(line)
                    except (json.JSONDecodeError, ValueError):
                        continue

            with open(self.feedback_file, "w", encoding="utf-8") as f:
                f.writelines(cleaned_entries)

        # Clean failed cases
        if self.failed_cases_file.exists():
            cleaned_cases = []
            with open(self.failed_cases_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        case = json.loads(line.strip())
                        case_timestamp = datetime.fromisoformat(
                            case["timestamp"]
                        ).timestamp()
                        if case_timestamp > cutoff_date:
                            cleaned_cases.append(line)
                    except (json.JSONDecodeError, ValueError):
                        continue

            with open(self.failed_cases_file, "w", encoding="utf-8") as f:
                f.writelines(cleaned_cases)


# Global instance
feedback_manager = FeedbackLoopManager()


def log_user_feedback(
    original_ocr_text: str,
    original_analysis: dict[str, Any],
    user_corrections: dict[str, Any],
    confidence_score: float,
    feedback_type: str = "correction",
    user_notes: str | None = None,
    processing_time: float | None = None,
) -> str:
    """Convenience function to log user feedback"""
    return feedback_manager.log_user_feedback(
        original_ocr_text,
        original_analysis,
        user_corrections,
        confidence_score,
        feedback_type,
        user_notes,
        processing_time,
    )


def log_failed_extraction(
    file_path: str,
    ocr_text: str,
    analysis_result: dict[str, Any],
    error_type: str,
    error_details: str,
    confidence_score: float,
    suggested_improvements: list[str] | None = None,
) -> str:
    """Convenience function to log failed extraction"""
    return feedback_manager.log_failed_extraction(
        file_path,
        ocr_text,
        analysis_result,
        error_type,
        error_details,
        confidence_score,
        suggested_improvements,
    )
