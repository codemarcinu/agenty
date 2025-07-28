"""
Feedback API endpoints for collecting user corrections and failed extraction cases.

This module provides REST API endpoints for the feedback loop system,
allowing users to submit corrections and the system to log failed cases.
"""

from datetime import datetime
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.feedback_loop import (
    feedback_manager,
    log_failed_extraction,
    log_user_feedback,
)

router = APIRouter(prefix="/feedback", tags=["Feedback"])
logger = logging.getLogger(__name__)


class UserFeedbackRequest(BaseModel):
    """Request model for user feedback submission"""

    original_ocr_text: str
    original_analysis: dict[str, Any]
    user_corrections: dict[str, Any]
    confidence_score: float
    feedback_type: str = "correction"  # "correction", "improvement", "error"
    user_notes: str | None = None
    processing_time: float | None = None


class FailedExtractionRequest(BaseModel):
    """Request model for logging failed extraction cases"""

    file_path: str
    ocr_text: str
    analysis_result: dict[str, Any]
    error_type: str
    error_details: str
    confidence_score: float
    suggested_improvements: list[str] | None = None


@router.post("/user-feedback")
async def submit_user_feedback(request: UserFeedbackRequest) -> JSONResponse:
    """
    Submit user feedback for OCR/analysis improvements.

    This endpoint allows users to submit corrections to OCR results
    and analysis data, which are used to improve the AI models.
    """
    try:
        feedback_id = log_user_feedback(
            original_ocr_text=request.original_ocr_text,
            original_analysis=request.original_analysis,
            user_corrections=request.user_corrections,
            confidence_score=request.confidence_score,
            feedback_type=request.feedback_type,
            user_notes=request.user_notes,
            processing_time=request.processing_time,
        )

        if feedback_id:
            logger.info(f"User feedback logged successfully: {feedback_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Feedback submitted successfully",
                    "feedback_id": feedback_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to log user feedback")

    except Exception as e:
        logger.error(f"Error submitting user feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {e!s}")


@router.post("/failed-extraction")
async def log_failed_extraction_case(request: FailedExtractionRequest) -> JSONResponse:
    """
    Log a failed extraction case for training data.

    This endpoint allows the system to log cases where OCR or analysis
    failed, providing data for improving the AI models.
    """
    try:
        case_id = log_failed_extraction(
            file_path=request.file_path,
            ocr_text=request.ocr_text,
            analysis_result=request.analysis_result,
            error_type=request.error_type,
            error_details=request.error_details,
            confidence_score=request.confidence_score,
            suggested_improvements=request.suggested_improvements,
        )

        if case_id:
            logger.info(f"Failed extraction case logged successfully: {case_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Failed extraction case logged successfully",
                    "case_id": case_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        else:
            raise HTTPException(
                status_code=500, detail="Failed to log failed extraction case"
            )

    except Exception as e:
        logger.error(f"Error logging failed extraction case: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to log failed extraction case: {e!s}"
        )


@router.get("/statistics")
async def get_feedback_statistics() -> JSONResponse:
    """
    Get feedback system statistics.

    Returns comprehensive statistics about the feedback system,
    including total entries, average confidence, and error patterns.
    """
    try:
        stats = feedback_manager.get_feedback_statistics()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Feedback statistics retrieved successfully",
                "data": stats,
                "timestamp": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error getting feedback statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get feedback statistics: {e!s}"
        )


@router.get("/training-data")
async def get_training_data(limit: int = 100) -> JSONResponse:
    """
    Get training data from feedback and failed cases.

    This endpoint provides access to the collected feedback data
    for training and improving AI models.
    """
    try:
        training_data = feedback_manager.get_training_data(limit=limit)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Training data retrieved successfully",
                "data": training_data,
                "timestamp": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error getting training data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get training data: {e!s}"
        )


@router.get("/improvement-suggestions")
async def get_improvement_suggestions() -> JSONResponse:
    """
    Get improvement suggestions based on feedback data.

    This endpoint provides AI-generated suggestions for improving
    the system based on collected feedback and error patterns.
    """
    try:
        suggestions = feedback_manager.generate_improvement_suggestions()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Improvement suggestions retrieved successfully",
                "data": {"suggestions": suggestions, "count": len(suggestions)},
                "timestamp": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error getting improvement suggestions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get improvement suggestions: {e!s}"
        )


@router.post("/cleanup")
async def cleanup_old_data(days_to_keep: int = 90) -> JSONResponse:
    """
    Clean up old feedback and failed case data.

    This endpoint removes old feedback entries and failed cases
    to manage storage and maintain data quality.
    """
    try:
        feedback_manager.cleanup_old_data(days_to_keep=days_to_keep)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Old data cleaned up successfully (keeping {days_to_keep} days)",
                "timestamp": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup old data: {e!s}"
        )
