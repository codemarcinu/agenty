"""
Common file validation utilities for receipt processing endpoints
"""

import logging
from typing import Any

from fastapi import HTTPException, UploadFile
import magic

from core.file_security import file_security_validator
from core.receipt_exceptions import FileSecurityError, FileValidationError

logger = logging.getLogger(__name__)


async def validate_uploaded_file(file: UploadFile) -> dict[str, Any]:
    """
    Common file validation function for all receipt endpoints

    Args:
        file: FastAPI UploadFile object

    Returns:
        Dict with validation results and file_bytes

    Raises:
        HTTPException: If validation fails
    """

    # Read file content first
    file_bytes = await file.read()

    # If content_type is missing or application/octet-stream, try to detect it
    content_type = file.content_type
    if not content_type or content_type == "application/octet-stream":
        try:
            detected_type = magic.from_buffer(file_bytes, mime=True)
            logger.info(f"Detected file type for {file.filename}: {detected_type}")
            content_type = detected_type
        except Exception as e:
            logger.warning(f"Could not detect file type for {file.filename}: {e}")
            # Keep original content_type if detection fails

    # Validate content type header
    if not content_type:
        raise HTTPException(
            status_code=400,
            detail={
                "status_code": 400,
                "error_code": "BAD_REQUEST",
                "message": "Missing content type header",
                "details": {
                    "field": "file",
                    "error": "Content-Type header is required",
                },
            },
        )

    # Comprehensive file security validation
    try:
        validation_result = file_security_validator.validate_file_comprehensive(
            file_bytes, content_type, file.filename
        )

        logger.info(
            f"File validation passed: {file.filename}",
            extra={
                "file_size": validation_result["file_size"],
                "detected_type": validation_result["detected_type"],
                "security_checks": validation_result["security_checks"],
            },
        )

        # Add file_bytes to result
        validation_result["file_bytes"] = file_bytes
        validation_result["filename"] = file.filename
        validation_result["content_type"] = content_type

        return validation_result

    except (FileSecurityError, FileValidationError) as e:
        logger.warning(
            f"File validation failed: {file.filename}",
            extra={
                "error_code": e.error_code,
                "error_message": e.message,
                "correlation_id": e.correlation_id,
            },
        )
        raise HTTPException(
            status_code=400,
            detail={
                "status_code": 400,
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details,
                "correlation_id": e.correlation_id,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error during file validation: {e!s}")
        raise HTTPException(
            status_code=500,
            detail={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error during file validation",
                "details": {"error": str(e)},
            },
        )


def determine_file_type(content_type: str) -> str:
    """
    Determine file type for OCR processing

    Args:
        content_type: MIME content type

    Returns:
        String: 'image' or 'pdf'

    Raises:
        HTTPException: If content type is not supported
    """

    image_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    pdf_types = ["application/pdf"]

    if content_type in image_types:
        return "image"
    elif content_type in pdf_types:
        return "pdf"
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported file type",
                "details": {
                    "content_type": content_type,
                    "supported_types": image_types + pdf_types,
                },
            },
        )


def determine_file_type_with_fallback(
    content_type: str, file_bytes: bytes | None = None
) -> str:
    """
    Determine file type for OCR processing with magic number fallback

    Args:
        content_type: MIME content type
        file_bytes: File content for magic number detection

    Returns:
        String: 'image' or 'pdf'

    Raises:
        HTTPException: If content type is not supported
    """

    image_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    pdf_types = ["application/pdf"]

    # If content_type is in allowed types, use it
    if content_type in image_types:
        return "image"
    elif content_type in pdf_types:
        return "pdf"

    # If content_type is application/octet-stream or missing, try magic number detection
    if content_type == "application/octet-stream" or not content_type:
        if file_bytes:
            try:
                detected_type = magic.from_buffer(file_bytes, mime=True)
                logger.info(f"Magic number detection: {detected_type}")

                if detected_type in image_types:
                    return "image"
                elif detected_type in pdf_types:
                    return "pdf"
                else:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": "Unsupported file type",
                            "details": {
                                "detected_type": detected_type,
                                "supported_types": image_types + pdf_types,
                            },
                        },
                    )
            except Exception as e:
                logger.warning(f"Magic number detection failed: {e}")

    # If we get here, the content_type is not supported
    raise HTTPException(
        status_code=400,
        detail={
            "message": "Unsupported file type",
            "details": {
                "content_type": content_type,
                "supported_types": image_types + pdf_types,
            },
        },
    )
