from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from agents.ocr_agent import OCRAgent, OCRAgentInput
from core.feedback_loop import log_failed_extraction
from utils.image_validator import ImageValidator

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.post("/validate")
async def validate_receipt_image(
    file: UploadFile = File(...),
    auto_enhance: bool = Query(False, description="Auto-enhance image quality"),
):
    """Validate receipt image quality and provide optimization suggestions."""
    try:
        # Read file content
        file_bytes = await file.read()

        # Validate image
        validator = ImageValidator()
        validation_result = validator.validate_image(file_bytes, file.filename or "")

        # Get optimization suggestions
        suggestions = validator.get_optimization_suggestions(validation_result)

        # Auto-enhance if requested and image needs improvement
        enhanced_bytes = None
        enhancement_result = None

        if auto_enhance and not validation_result.get("valid", False):
            enhanced_bytes, enhancement_result = validator.auto_enhance_image(
                file_bytes
            )

            # Re-validate enhanced image
            if enhancement_result.get("success", False):
                enhanced_validation = validator.validate_image(
                    enhanced_bytes, file.filename or ""
                )
                validation_result["enhanced"] = enhanced_validation
                validation_result["enhancement"] = enhancement_result

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "validation": validation_result,
                "suggestions": suggestions,
                "filename": file.filename,
                "can_process": validation_result.get("valid", False)
                or (validation_result.get("enhanced", {}).get("valid", False)),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating receipt image: {e!s}",
        )


@router.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    auto_enhance: bool = Query(
        False, description="Auto-enhance image quality before processing"
    ),
):
    """Endpoint for uploading and processing receipt images with OCR."""
    import logging

    from core.file_validation_utils import (
        determine_file_type_with_fallback,
        validate_uploaded_file,
    )
    from utils.image_validator import ImageValidator

    logger = logging.getLogger(__name__)
    try:
        # Validate file using new security validation
        validation_result = await validate_uploaded_file(file)
        file_bytes = validation_result["file_bytes"]
        if not file_bytes:
            raise HTTPException(status_code=400, detail="No file content received")
        file_bytes = bytes(file_bytes)  # Ensure it's bytes type
        file_type = determine_file_type_with_fallback(
            file.content_type or "application/octet-stream", file_bytes
        )
        logger.info(
            f"[v1/upload] File validated: {file.filename}, size: {len(file_bytes)}, content_type: {file.content_type}, detected_type: {validation_result.get('detected_type')}, file_type: {file_type}"
        )

        # --- AUTO ENHANCE IMAGE ---
        if auto_enhance and file_type == "image":
            validator = ImageValidator()
            enhanced_bytes, enhancement_result = validator.auto_enhance_image(
                file_bytes
            )
            if enhancement_result.get("success", False):
                logger.info(f"Image auto-enhanced for {file.filename}")
                file_bytes = enhanced_bytes
            else:
                logger.warning(
                    f"Image auto-enhancement failed for {file.filename}, using original"
                )

        # Process with OCRAgent
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)
        result = await agent.process(input_data)

        if not result.success:
            # Log failed OCR
            log_failed_extraction(
                file_path=file.filename or "unknown",
                ocr_text="",
                analysis_result={"error": result.error},
                error_type="ocr_failure",
                error_details=result.error or "Unknown OCR error",
                confidence_score=0.0,
                suggested_improvements=[
                    "Improve image quality",
                    "Enhance OCR preprocessing",
                ],
            )

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "OCR_FAILED",
                    "message": result.error,
                    "validation": validation_result,
                },
            )

        # Log low confidence OCR results
        if hasattr(result, "confidence") and result.confidence < 0.5:
            log_failed_extraction(
                file_path=file.filename or "unknown",
                ocr_text=result.text or "",
                analysis_result={"confidence": result.confidence},
                error_type="low_ocr_confidence",
                error_details=f"OCR confidence too low: {result.confidence}",
                confidence_score=result.confidence or 0.0,
                suggested_improvements=[
                    "Improve image preprocessing",
                    "Use EasyOCR fallback",
                ],
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "text": result.text,
                "message": result.message,
                "validation": validation_result,
                "processing_info": {
                    "auto_enhanced": auto_enhance,
                    "file_size": len(file_bytes),
                    "format": file_type,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PROCESSING_ERROR",
                "message": f"Błąd podczas przetwarzania paragonu: {e!s}",
            },
        )
