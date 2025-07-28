import logging
import os
from pathlib import Path
import tempfile
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from agents.local_enhanced_agents import LocalReceiptAnalysisAgent
from agents.ocr.specialized_ocr_llm import SpecializedOCRAgent
from agents.ocr_agent import OCRAgent, OCRAgentInput
from agents.receipt_analysis_agent import ReceiptAnalysisAgent
from core.file_validation_utils import (
    determine_file_type_with_fallback,
    validate_uploaded_file,
)
from core.local_system_optimizer import local_system_optimizer
from infrastructure.database.database import get_db
from utils.image_validator import ImageValidator

logger = logging.getLogger(__name__)

router = APIRouter()

# Temporary upload directory
TEMP_UPLOAD_DIR = Path("./temp_uploads")
TEMP_UPLOAD_DIR.mkdir(exist_ok=True, parents=True)


@router.post("/simple-upload")
async def upload_file(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Endpoint to upload files (images or PDFs) and process them with OCR and AI analysis.
    """
    logger.info(
        f"Upload endpoint called with session_id: {session_id}, filename: {file.filename}"
    )

    try:
        # Validate file using security validation
        validation_result = await validate_uploaded_file(file)
        file_bytes = validation_result["file_bytes"]
        if not file_bytes:
            raise HTTPException(status_code=400, detail="No file content received")
        file_bytes = bytes(file_bytes)  # Ensure it's bytes type
        file_type = determine_file_type_with_fallback(
            file.content_type or "application/octet-stream", file_bytes
        )

        logger.info(
            f"File validated: {file.filename}, size: {len(file_bytes) if file_bytes else 0} bytes, type: {file_type}"
        )

        # --- AUTO ENHANCE IMAGE ---
        if file_type == "image":
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

        # Save temporary file for image processing
        temp_image_path = None
        if file_type in ["image", "pdf"]:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file.filename.split('.')[-1]}"
            ) as temp_file:
                temp_file.write(file_bytes)
                temp_image_path = temp_file.name

        try:
            # Step 1: System optimization check
            logger.info("Checking system optimization...")
            if not local_system_optimizer.optimize_before_inference():
                logger.warning(
                    "System resources are critical, using fallback processing"
                )

            # Step 2: Enhanced OCR Processing with Local Models
            logger.info("Starting enhanced OCR processing with local models...")

            # Initialize OCR variables with default values
            extracted_text = ""
            ocr_confidence = 0.8  # Default confidence value
            ocr_method = "unknown"

            # Use specialized OCR agent for better vision processing
            specialized_ocr_agent = SpecializedOCRAgent()
            ocr_result = await specialized_ocr_agent.process(
                {"image_path": temp_image_path, "file_type": file_type}
            )

            if not ocr_result.success:
                logger.warning(
                    "Specialized OCR failed, falling back to traditional OCR..."
                )
                # Fallback to traditional OCR
                ocr_agent = OCRAgent()
                input_data = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)
                ocr_result = await ocr_agent.process(input_data)

                if not ocr_result.success:
                    logger.error(f"All OCR methods failed: {ocr_result.error}")
                    return {
                        "success": False,
                        "error": f"OCR processing failed: {ocr_result.error}",
                        "filename": file.filename,
                        "session_id": session_id,
                        "receipt_data": None,
                    }
                # Traditional OCRAgent returns text in the 'text' attribute of AgentResponse
                extracted_text = ocr_result.text if hasattr(ocr_result, "text") else ""
                ocr_confidence = (
                    getattr(ocr_result.metadata, "confidence", 0.5)
                    if hasattr(ocr_result, "metadata") and ocr_result.metadata
                    else 0.5
                )
                ocr_method = "traditional_fallback"
            else:
                extracted_text = (
                    ocr_result.data.get("extracted_text", "")
                    if hasattr(ocr_result, "data") and ocr_result.data
                    else ""
                )
                ocr_confidence = (
                    ocr_result.data.get("confidence", 0.8)
                    if hasattr(ocr_result, "data") and ocr_result.data
                    else 0.8
                )
                ocr_method = "specialized_local"

            logger.info(
                f"OCR completed successfully using {ocr_method}. Text length: {len(extracted_text)}"
            )

            # Validate we have OCR text before proceeding
            if not extracted_text or len(extracted_text.strip()) < 10:
                logger.error(
                    f"OCR text is empty or too short (length: {len(extracted_text)})"
                )
                return {
                    "success": False,
                    "error": "OCR failed to extract meaningful text from the file",
                    "filename": file.filename,
                    "session_id": session_id,
                    "ocr_text": extracted_text,
                    "receipt_data": None,
                }

            # Step 3: Enhanced AI Analysis with Local Models
            logger.info("Starting enhanced AI analysis with local models...")
            local_analysis_agent = LocalReceiptAnalysisAgent()
            analysis_result = await local_analysis_agent.process(
                {"ocr_text": extracted_text, "image_path": temp_image_path}
            )

            if not analysis_result.success:
                logger.warning(
                    "Local analysis failed, falling back to traditional analysis..."
                )
                # Fallback to traditional analysis
                analysis_agent = ReceiptAnalysisAgent()
                analysis_result = await analysis_agent.process(
                    {"ocr_text": extracted_text}
                )
                analysis_method = "traditional_fallback"
            else:
                analysis_method = "local_enhanced"

            if not analysis_result.success:
                logger.error(f"AI analysis failed: {analysis_result.error}")
                return {
                    "success": False,
                    "error": f"AI analysis failed: {analysis_result.error}",
                    "filename": file.filename,
                    "session_id": session_id,
                    "ocr_text": extracted_text,  # Return OCR text even if analysis failed
                    "receipt_data": None,
                }

            logger.info(f"AI analysis completed successfully using {analysis_method}")

            # Step 4: Prepare enhanced response with local processing details
            response = {
                "success": True,
                "message": f"Paragon {file.filename} został pomyślnie przetworzony z ulepszonym systemem lokalnym",
                "filename": file.filename,
                "session_id": session_id,
                "content_type": file.content_type,
                "file_size": len(file_bytes),
                "processing_details": {
                    "ocr_text": extracted_text,
                    "ocr_confidence": ocr_confidence,
                    "ocr_method": ocr_method,
                    "analysis_method": analysis_method,
                    "analysis_data": analysis_result.data,
                    "processing_time": getattr(analysis_result, "metadata", {}).get(
                        "processing_time", None
                    ),
                    "system_metrics": (
                        local_system_optimizer.monitor.get_current_metrics().__dict__
                        if hasattr(
                            local_system_optimizer.monitor, "get_current_metrics"
                        )
                        else None
                    ),
                },
                "receipt_data": {
                    "store_name": analysis_result.data.get(
                        "store_name", "Nieznany sklep"
                    ),
                    "date": analysis_result.data.get("date", "Nieznana data"),
                    "total_amount": analysis_result.data.get("total_amount", analysis_result.data.get("total", 0)),
                    "items_count": len(analysis_result.data.get("items", [])),
                    "items": analysis_result.data.get("items", []),
                    "confidence": analysis_result.data.get(
                        "confidence", ocr_confidence
                    ),
                    "processing_enhancements": {
                        "local_models_used": analysis_method == "local_enhanced",
                        "vision_ocr_used": ocr_method == "specialized_local",
                        "mathematical_validation": analysis_result.data.get(
                            "total_corrected", False
                        ),
                        "store_pattern_detection": analysis_result.data.get(
                            "store_name", ""
                        )
                        != "Nieznany sklep",
                    },
                },
            }

        finally:
            # Cleanup temporary file
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.unlink(temp_image_path)
                except Exception as cleanup_error:
                    logger.warning(
                        f"Failed to cleanup temp file {temp_image_path}: {cleanup_error}"
                    )

        logger.info(f"Processing completed successfully for {file.filename}")
        logger.info(f"Response receipt_data: {response['receipt_data']}")  # Debug log
        return response

    except HTTPException as e:
        logger.error(f"HTTP error in upload: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in upload: {e}")
        return {
            "success": False,
            "error": f"Wystąpił nieoczekiwany błąd podczas przetwarzania: {e!s}",
            "filename": file.filename,
            "session_id": session_id,
            "receipt_data": None,
        }


@router.post("/test-upload")
async def test_upload(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Simple test endpoint to debug upload issues
    """
    logger.info(f"Test upload endpoint called with session_id: {session_id}, filename: {file.filename}")

    try:
        # Read file content
        file_bytes = await file.read()
        
        logger.info(f"File read successfully: {file.filename}, size: {len(file_bytes)} bytes")
        
        # Basic validation
        if len(file_bytes) == 0:
            return {
                "success": False,
                "error": "Empty file",
                "filename": file.filename,
                "session_id": session_id,
            }
        
        # Return success response
        return {
            "success": True,
            "message": f"File {file.filename} uploaded successfully for testing",
            "filename": file.filename,
            "session_id": session_id,
            "file_size": len(file_bytes),
            "content_type": file.content_type,
        }
        
    except Exception as e:
        logger.error(f"Test upload failed: {e}")
        return {
            "success": False,
            "error": f"Test upload failed: {str(e)}",
            "filename": file.filename,
            "session_id": session_id,
        }


@router.post("/simple-upload-no-ocr")
async def simple_upload_no_ocr(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Simple upload endpoint without OCR processing for testing
    """
    logger.info(f"Simple upload no OCR called with session_id: {session_id}, filename: {file.filename}")

    try:
        # Read file content
        file_bytes = await file.read()
        
        logger.info(f"File read successfully: {file.filename}, size: {len(file_bytes)} bytes")
        
        # Basic validation
        if len(file_bytes) == 0:
            return {
                "success": False,
                "error": "Empty file",
                "filename": file.filename,
                "session_id": session_id,
            }
        
        # Return success response without OCR processing
        return {
            "success": True,
            "message": f"Plik {file.filename} został przesłany pomyślnie (bez OCR)",
            "data": {
                "filename": file.filename,
                "file_size": len(file_bytes),
                "session_id": session_id,
                "status": "uploaded_no_ocr"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in simple upload no OCR: {e}")
        return {
            "success": False,
            "error": f"Błąd przetwarzania: {str(e)}",
            "filename": file.filename,
            "session_id": session_id,
        }
