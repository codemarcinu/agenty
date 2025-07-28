from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Any

# from typing import TYPE_CHECKING  # Uncomment when TYPE_CHECKING block is re-enabled
from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from agents.ocr_agent import OCRAgent, OCRAgentInput
from agents.receipt_analysis_agent import ReceiptAnalysisAgent
from api.v2.exceptions import (
    BadRequestError,
    InternalServerError,
    UnprocessableEntityError,
)
from config.celery_config import celery_app
from core.file_security import file_security_validator
from core.file_validation_utils import (
    determine_file_type_with_fallback,
    validate_uploaded_file,
)
from core.receipt_exceptions import (
    FileSecurityError,
    FileValidationError,
    ReceiptProcessingError,
)
from tasks.receipt_tasks import process_receipt_task
from utils.image_validator import ImageValidator

logger = logging.getLogger(__name__)

# Note: AsyncSession and shopping_schemas are used in commented code below
# Uncomment when /save endpoint is re-enabled
# if TYPE_CHECKING:
#     from sqlalchemy.ext.asyncio import AsyncSession
#     from schemas import shopping_schemas

router = APIRouter(prefix="/receipts", tags=["Receipts"])

# Lista dozwolonych typów plików
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_PDF_TYPES

TEMP_UPLOAD_DIR = Path("./temp_uploads")
TEMP_UPLOAD_DIR.mkdir(exist_ok=True, parents=True)


@router.post("/upload", response_model=None)
async def upload_receipt(file: UploadFile = File(...)):  # type: ignore[reportCallInDefaultInitializer]
    """Endpoint for uploading and processing receipt images with enhanced OCR.

    Returns:
        JSONResponse: Standardized success or error response
    """
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

        # --- AUTO ENHANCE IMAGE ---
        if file_type == "image":
            validator = ImageValidator()
            enhanced_bytes, enhancement_result = validator.auto_enhance_image(
                file_bytes
            )
            if enhancement_result.get("success", False):
                logger.info(
                    f"Image auto-enhanced for {file.filename if hasattr(file, 'filename') else file}"
                )
                file_bytes = enhanced_bytes
            else:
                logger.warning(
                    f"Image auto-enhancement failed for {file.filename if hasattr(file, 'filename') else file}, using original"
                )

        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)
        result = await agent.process(input_data)

        if not result.success:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Failed to process receipt",
                    "details": {
                        "error": result.error,
                        "error_code": "RECEIPT_PROCESSING_ERROR",
                    },
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Receipt processed successfully",
                "data": {
                    "text": result.text,
                    "message": result.message,
                    "metadata": result.metadata,
                },
            },
        )

    except (FileSecurityError, FileValidationError) as e:
        logger.warning(
            f"File validation failed in upload endpoint: {file.filename}",
            extra={"error_code": e.error_code, "correlation_id": e.correlation_id},
        )
        return JSONResponse(
            status_code=400,
            content={
                "status_code": 400,
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details,
                "correlation_id": e.correlation_id,
            },
        )
    except HTTPException as he:
        # Re-raise HTTPException to preserve the status code and detail
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {e!s}")
        # For other exceptions, return a 500 error with standardized format
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error processing receipt",
                "details": {"error": str(e)},
            },
        )


@router.post("/analyze", response_model=None)
async def analyze_receipt(ocr_text: str = Form(...)):  # type: ignore[reportCallInDefaultInitializer]
    """Analyze OCR text from receipt and extract structured data with enhanced parsing.

    Returns:
        JSONResponse: Structured receipt data
    """
    try:
        # Validate OCR text
        if not ocr_text or not ocr_text.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "OCR text is required and cannot be empty",
                    "error_code": "BAD_REQUEST",
                },
            )

        # Process OCR text with enhanced ReceiptAnalysisAgent
        analysis_agent = ReceiptAnalysisAgent()
        analysis_result = await analysis_agent.process({"ocr_text": ocr_text})

        if not analysis_result.success:
            raise UnprocessableEntityError(
                message="Failed to analyze receipt data",
                details={
                    "error": analysis_result.error,
                    "error_code": "RECEIPT_ANALYSIS_ERROR",
                },
            )

        # Return structured receipt data
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Receipt analyzed successfully",
                "data": analysis_result.data,
            },
        )

    except HTTPException as he:
        raise he
    except ReceiptProcessingError as e:
        logger.warning(
            "Receipt processing error in analyze endpoint",
            extra={"error_code": e.error_code, "correlation_id": e.correlation_id},
        )
        return JSONResponse(
            status_code=422,
            content={
                "status_code": 422,
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details,
                "correlation_id": e.correlation_id,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error in analyze endpoint: {e!s}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error analyzing receipt",
                "details": {"error": str(e)},
            },
        )


@router.post("/process", response_model=None)
async def process_receipt_complete(file: UploadFile = File(...)):  # type: ignore[reportCallInDefaultInitializer]
    """Complete receipt processing workflow: OCR + Analysis in one endpoint with optimizations.

    Returns:
        JSONResponse: Complete structured receipt data
    """
    # Cache dla wyników analizy paragonów (w pamięci)
    _receipt_cache = {}
    _cache_ttl = 3600  # 1 godzina

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

        # --- AUTO ENHANCE IMAGE ---
        if file_type == "image":
            validator = ImageValidator()
            enhanced_bytes, enhancement_result = validator.auto_enhance_image(
                file_bytes
            )
            if enhancement_result.get("success", False):
                logger.info(
                    f"Image auto-enhanced for {file.filename if hasattr(file, 'filename') else file}"
                )
                file_bytes = enhanced_bytes
            else:
                logger.warning(
                    f"Image auto-enhancement failed for {file.filename if hasattr(file, 'filename') else file}, using original"
                )

        # Generuj hash pliku dla cache
        file_hash = file_security_validator.calculate_file_hash(file_bytes)

        # Sprawdź cache
        if file_hash in _receipt_cache:
            cache_entry = _receipt_cache[file_hash]
            if datetime.now() - cache_entry["timestamp"] < timedelta(
                seconds=_cache_ttl
            ):
                return JSONResponse(
                    status_code=200,
                    content={
                        "status_code": 200,
                        "message": "Receipt processed successfully (cached)",
                        "data": cache_entry["data"],
                        "cached": True,
                    },
                )

        # File type już został określony przez determine_file_type()

        # OCR Processing z timeout
        try:
            ocr_agent = OCRAgent()
            input_data = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)
            # Timeout dla OCR: 180 sekund (3 minuty)
            # ZWIĘKSZONY timeout dla OCR: 360 sekund (6 minut)
            # Jeśli przetwarzanie dużych lub trudnych paragonów, rozważ użycie endpointu /process_async
            ocr_result = await asyncio.wait_for(
                ocr_agent.process(input_data), timeout=360.0
            )
            if not ocr_result.success:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "message": "Failed to extract text from receipt",
                        "details": {
                            "error": ocr_result.error,
                            "error_code": "OCR_PROCESSING_ERROR",
                        },
                    },
                )
        except TimeoutError:
            raise HTTPException(
                status_code=408,
                detail={
                    "message": "OCR processing timeout",
                    "details": {
                        "error": "OCR processing took too long",
                        "error_code": "OCR_TIMEOUT",
                    },
                },
            )

        # Receipt Analysis z timeout
        try:
            analysis_agent = ReceiptAnalysisAgent()
            # Timeout dla analizy: 120 sekund (2 minuty)
            # ZWIĘKSZONY timeout dla analizy: 240 sekund (4 minuty)
            # Jeśli przetwarzanie dużych lub trudnych paragonów, rozważ użycie endpointu /process_async
            analysis_result = await asyncio.wait_for(
                analysis_agent.process({"ocr_text": ocr_result.text, "skip_llm": True}),
                timeout=240.0,
            )
            if not analysis_result.success:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "message": "Failed to analyze receipt data",
                        "details": {
                            "error": analysis_result.error,
                            "error_code": "RECEIPT_ANALYSIS_ERROR",
                        },
                    },
                )
        except TimeoutError:
            raise HTTPException(
                status_code=408,
                detail={
                    "message": "Receipt analysis timeout",
                    "details": {
                        "error": "Receipt analysis took too long",
                        "error_code": "ANALYSIS_TIMEOUT",
                    },
                },
            )

        # Przygotuj kompletny wynik
        complete_result = {
            "ocr_text": ocr_result.text,
            "analysis": analysis_result.data,
            "metadata": {
                "processing_time": datetime.now().isoformat(),
                "file_size": len(file_bytes),
                "file_type": file_type,
                "cached": False,
            },
        }

        # Zapisz w cache
        _receipt_cache[file_hash] = {
            "data": complete_result,
            "timestamp": datetime.now(),
        }

        # Wyczyść stary cache (zachowaj tylko ostatnie 100 wpisów)
        if len(_receipt_cache) > 100:
            # Usuń najstarsze wpisy
            sorted_cache = sorted(
                _receipt_cache.items(), key=lambda x: x[1]["timestamp"]
            )
            for key, _ in sorted_cache[:-100]:
                del _receipt_cache[key]

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Receipt processed successfully",
                "data": complete_result,
            },
        )

    except (FileSecurityError, FileValidationError) as e:
        logger.warning(
            "File validation failed in process endpoint",
            extra={"error_code": e.error_code, "correlation_id": e.correlation_id},
        )
        return JSONResponse(
            status_code=400,
            content={
                "status_code": 400,
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details,
                "correlation_id": e.correlation_id,
            },
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in process endpoint: {e!s}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error processing receipt",
                "details": {"error": str(e)},
            },
        )


# Temporarily disabled due to OpenAPI schema issues
@router.post("/save", response_model=None)
async def save_receipt_data(receipt_data: dict):
    """Save analyzed receipt data to database.

    Returns:
        JSONResponse: Result of saving receipt data
    """
    try:
        from core.receipt_database import ReceiptDatabaseManager

        # Create database manager
        db_manager = ReceiptDatabaseManager()

        # Generate correlation ID for tracing
        correlation_id = f"save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(
            "Saving receipt data to database",
            extra={
                "correlation_id": correlation_id,
                "store_name": receipt_data.get("store_name"),
                "total_amount": receipt_data.get("total_amount"),
            },
        )

        # Save to database
        save_result = await db_manager.save_receipt_to_database(
            receipt_data,
            user_id=None,  # TODO: Add user authentication
            correlation_id=correlation_id,
        )

        if save_result.get("success"):
            logger.info(
                "Successfully saved receipt to database",
                extra={
                    "correlation_id": correlation_id,
                    "trip_id": save_result.get("trip_id"),
                    "products_count": save_result.get("products_count"),
                },
            )

            return JSONResponse(
                status_code=200,
                content={
                    "status_code": 200,
                    "message": "Receipt data saved successfully",
                    "data": {
                        "trip_id": save_result.get("trip_id"),
                        "products_count": save_result.get("products_count"),
                        "store_name": save_result.get("store_name"),
                        "trip_date": save_result.get("trip_date"),
                        "total_amount": save_result.get("total_amount"),
                        "created_at": save_result.get("created_at"),
                    },
                },
            )
        else:
            logger.error(
                "Failed to save receipt to database",
                extra={
                    "correlation_id": correlation_id,
                    "error": save_result.get("error"),
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "status_code": 500,
                    "error_code": "DATABASE_SAVE_ERROR",
                    "message": "Failed to save receipt data",
                    "details": {"error": save_result.get("error")},
                },
            )

    except Exception as e:
        logger.error(f"Unexpected error saving receipt data: {e!s}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error saving receipt data",
                "details": {"error": str(e)},
            },
        )


@router.post("/process_async", response_model=None)
async def process_receipt_async(file: UploadFile = File(...)):  # type: ignore[reportCallInDefaultInitializer]
    """
    Asynchronous receipt processing: saves file, starts Celery task, returns task_id.
    """
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

        # --- AUTO ENHANCE IMAGE ---
        if file_type == "image":
            validator = ImageValidator()
            enhanced_bytes, enhancement_result = validator.auto_enhance_image(
                file_bytes
            )
            if enhancement_result.get("success", False):
                logger.info(
                    f"Image auto-enhanced for {file.filename if hasattr(file, 'filename') else file}"
                )
                file_bytes = enhanced_bytes
            else:
                logger.warning(
                    f"Image auto-enhancement failed for {file.filename if hasattr(file, 'filename') else file}, using original"
                )

        # Generate safe filename for temporary storage
        safe_filename = file_security_validator.generate_safe_filename(
            file.filename, file.content_type or "application/octet-stream"
        )
        temp_path = TEMP_UPLOAD_DIR / safe_filename
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
        # Start Celery task
        task = process_receipt_task.apply_async(
            args=[str(temp_path), file.filename if file.filename else "unknown", None]
        )
        return JSONResponse(
            status_code=202,
            content={
                "status_code": 202,
                "message": "Receipt processing started",
                "task_id": task.id,
            },
        )
    except (FileSecurityError, FileValidationError) as e:
        logger.warning(
            f"File validation failed in async processing: {file.filename}",
            extra={"error_code": e.error_code, "correlation_id": e.correlation_id},
        )
        raise BadRequestError(
            message=e.message,
            details=e.details,
        )
    except BadRequestError as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in async receipt processing: {e!s}")
        raise InternalServerError(
            message="Failed to start async receipt processing",
            details={"error": str(e)},
        )


@router.get("/status/{task_id}", response_model=None)
async def get_receipt_task_status(task_id: str):
    """
    Get status and result of async receipt processing task.
    """
    try:
        if not task_id:
            raise BadRequestError(message="Missing task_id")
        result = AsyncResult(str(task_id), app=celery_app)
        if result.status == "PENDING":
            return JSONResponse(
                status_code=200,
                content={
                    "status": "pending",
                    "task_id": task_id,
                    "progress": 0,
                },
            )
        if result.status == "PROGRESS":
            meta = result.info or {}
            return JSONResponse(
                status_code=200,
                content={
                    "status": "processing",
                    "task_id": task_id,
                    "progress": meta.get("progress", 0),
                    "step": meta.get("step"),
                    "message": meta.get("message"),
                },
            )
        if result.status == "SUCCESS":
            data = result.result
            return JSONResponse(
                status_code=200,
                content={
                    "status": "completed",
                    "task_id": task_id,
                    "result": data,
                },
            )
        if result.status == "FAILURE":
            error = str(result.result)
            return JSONResponse(
                status_code=200,
                content={
                    "status": "failed",
                    "task_id": task_id,
                    "error": error,
                },
            )
        return JSONResponse(
            status_code=200,
            content={
                "status": result.status.lower(),
                "task_id": task_id,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error getting task status: {e!s}")
        raise InternalServerError(
            message="Failed to get task status", details={"error": str(e)}
        )


@router.post("/batch_upload", response_model=None)
async def batch_upload_receipts(files: list[UploadFile] = File(...)):  # type: ignore[reportCallInDefaultInitializer]
    """Batch upload and process multiple receipt files with optimizations.

    Features:
    - Parallel processing with asyncio
    - Memory-efficient batch processing
    - Progress tracking
    - Error handling per file
    - Caching for duplicate files

    Returns:
        JSONResponse: Batch processing results with individual file results
    """
    try:
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "No files provided",
                    "error_code": "NO_FILES_PROVIDED",
                },
            )

        if len(files) > 50:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Too many files. Maximum 50 files per batch.",
                    "error_code": "BATCH_SIZE_LIMIT_EXCEEDED",
                },
            )

        logger.info(f"Starting batch processing of {len(files)} files")

        # Process files in parallel with progress tracking
        results = []
        successful = 0
        failed = 0

        async def process_single_file(file: UploadFile, index: int) -> dict[str, Any]:
            """Process a single file with error handling"""
            try:
                # Validate file
                validation_result = await validate_uploaded_file(file)
                file_bytes = validation_result["file_bytes"]
                if not file_bytes:
                    return {
                        "filename": file.filename,
                        "success": False,
                        "error": "No file content received",
                        "error_code": "BAD_REQUEST",
                        "index": index,
                    }
                file_bytes = bytes(file_bytes)  # Ensure it's bytes type
                file_type = determine_file_type_with_fallback(
                    file.content_type or "application/octet-stream", file_bytes
                )

                # --- AUTO ENHANCE IMAGE ---
                if file_type == "image":
                    validator = ImageValidator()
                    enhanced_bytes, enhancement_result = validator.auto_enhance_image(
                        file_bytes
                    )
                    if enhancement_result.get("success", False):
                        logger.info(
                            f"Image auto-enhanced for {file.filename if hasattr(file, 'filename') else file}"
                        )
                        file_bytes = enhanced_bytes
                    else:
                        logger.warning(
                            f"Image auto-enhancement failed for {file.filename if hasattr(file, 'filename') else file}, using original"
                        )

                # Check cache first
                file_security_validator.calculate_file_hash(file_bytes)

                # Process with OCR
                ocr_agent = OCRAgent()
                input_data = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)
                ocr_result = await asyncio.wait_for(
                    ocr_agent.process(input_data), timeout=180.0
                )

                if not ocr_result.success:
                    return {
                        "filename": file.filename,
                        "success": False,
                        "error": ocr_result.error,
                        "error_code": "OCR_PROCESSING_ERROR",
                        "index": index,
                    }

                # Process with analysis
                analysis_agent = ReceiptAnalysisAgent()
                analysis_result = await asyncio.wait_for(
                    analysis_agent.process(
                        {"ocr_text": ocr_result.text, "skip_llm": True}
                    ),
                    timeout=120.0,
                )

                if not analysis_result.success:
                    return {
                        "filename": file.filename,
                        "success": False,
                        "error": analysis_result.error,
                        "error_code": "ANALYSIS_ERROR",
                        "index": index,
                    }

                return {
                    "filename": file.filename,
                    "success": True,
                    "ocr_text": ocr_result.text,
                    "analysis": analysis_result.data,
                    "file_size": len(file_bytes),
                    "file_type": file_type,
                    "index": index,
                    "cached": False,
                }

            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e!s}")
                return {
                    "filename": file.filename,
                    "success": False,
                    "error": str(e),
                    "error_code": "PROCESSING_ERROR",
                    "index": index,
                }

        # Process files in parallel with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent files

        async def process_with_semaphore(
            file: UploadFile, index: int
        ) -> dict[str, Any]:
            async with semaphore:
                return await process_single_file(file, index)

        # Create tasks for all files
        tasks = [process_with_semaphore(file, i) for i, file in enumerate(files)]

        # Execute all tasks concurrently
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                failed += 1
                results.append(
                    {
                        "filename": "unknown",
                        "success": False,
                        "error": str(result),
                        "error_code": "EXCEPTION",
                    }
                )
            else:
                if isinstance(result, dict) and result.get("success"):
                    successful += 1
                else:
                    failed += 1
                results.append(result)

        # Calculate summary
        total_files = len(files)
        processing_summary = {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_files) * 100 if total_files > 0 else 0,
        }

        logger.info(
            f"Batch processing completed: {successful}/{total_files} successful",
            extra=processing_summary,
        )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": f"Batch processing completed: {successful}/{total_files} successful",
                "summary": processing_summary,
                "results": results,
            },
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in batch processing: {e!s}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error in batch processing",
                "details": {"error": str(e)},
            },
        )


@router.get("", response_model=dict)
async def list_receipts():
    """Stub: Zwraca przykładową listę paragonów zgodną ze schematem kontraktowym"""
    receipts_data = [
        {
            "id": "1",
            "filename": "receipt1.jpg",
            "upload_date": "2024-06-25",
            "status": "processed",
        },
        {
            "id": "2",
            "filename": "receipt2.jpg",
            "upload_date": "2024-06-24",
            "status": "processed",
        },
    ]

    return {
        "receipts": receipts_data,
        "total": len(receipts_data),
        "page": 1,
        "per_page": 10,
    }
