"""
OCR-RAG Integration API Endpoints

This module provides API endpoints for integrating OCR processing with RAG system.
"""

from datetime import datetime
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from agents.ocr_rag_integration_agent import OCRRAGIntegrationAgent
from core.database import get_db
from core.file_validation_utils import validate_uploaded_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr-rag", tags=["OCR-RAG Integration"])


@router.post("/process-receipt")
async def process_receipt_with_rag(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    store_name: str = Form(None),
    store_address: str = Form(None),
    receipt_date: str = Form(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Process receipt with OCR and add to RAG knowledge base

    This endpoint:
    1. Validates and processes the uploaded file
    2. Extracts text using OCR
    3. Adds the extracted content to RAG knowledge base
    4. Returns processing results
    """
    try:
        # Validate file
        validation_result = await validate_uploaded_file(file)
        file_bytes = validation_result["file_bytes"]

        if not file_bytes:
            raise HTTPException(status_code=400, detail="No file content received")

        # Prepare store information
        store_info = {}
        if store_name:
            store_info["name"] = store_name
        if store_address:
            store_info["address"] = store_address

        # Initialize OCR-RAG integration agent
        ocr_rag_agent = OCRRAGIntegrationAgent()

        # Process with OCR-RAG integration
        result = await ocr_rag_agent.process(
            {
                "file_bytes": file_bytes,
                "file_type": (
                    "image"
                    if file.content_type and file.content_type.startswith("image/")
                    else "pdf"
                ),
                "filename": file.filename or "unknown",
                "session_id": session_id,
                "store_info": store_info,
                "receipt_date": receipt_date,
            }
        )

        if not result.success:
            raise HTTPException(
                status_code=400, detail=f"OCR-RAG processing failed: {result.error}"
            )

        return {
            "success": True,
            "message": result.text,
            "data": result.data,
            "metadata": result.metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OCR-RAG processing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/query-history")
async def query_receipt_history(
    query: str = Form(...),
    session_id: str = Form(None),
    limit: int = Form(5),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Query receipt history using RAG

    This endpoint allows searching through processed receipts
    using natural language queries.
    """
    try:
        # Initialize OCR-RAG integration agent
        ocr_rag_agent = OCRRAGIntegrationAgent()

        # Query receipt history
        result = await ocr_rag_agent.query_receipt_history(
            query=query, session_id=session_id, limit=limit
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=f"Query failed: {result.error}")

        return {"success": True, "message": result.text, "data": result.data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in receipt history query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/statistics")
async def get_receipt_statistics(
    session_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get statistics about processed receipts

    This endpoint provides statistics about OCR-processed receipts
    in the RAG knowledge base.
    """
    try:
        # Initialize OCR-RAG integration agent
        ocr_rag_agent = OCRRAGIntegrationAgent()

        # Get statistics
        result = await ocr_rag_agent.get_receipt_statistics(
            session_id=session_id, date_from=date_from, date_to=date_to
        )

        if not result.success:
            raise HTTPException(
                status_code=400, detail=f"Statistics retrieval failed: {result.error}"
            )

        return {"success": True, "message": result.text, "data": result.data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in receipt statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/demo-upload")
async def demo_ocr_rag_upload(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Demo endpoint for OCR-RAG integration

    This endpoint demonstrates the complete OCR-RAG workflow:
    1. File upload and validation
    2. OCR text extraction
    3. RAG knowledge base integration
    4. Future query capability
    """
    try:
        logger.info(f"Demo OCR-RAG upload for {file.filename}")

        # Validate file
        validation_result = await validate_uploaded_file(file)
        file_bytes = validation_result["file_bytes"]

        if not file_bytes:
            raise HTTPException(status_code=400, detail="No file content received")

        # Initialize OCR-RAG integration agent
        ocr_rag_agent = OCRRAGIntegrationAgent()

        # Process with OCR-RAG integration
        result = await ocr_rag_agent.process(
            {
                "file_bytes": file_bytes,
                "file_type": (
                    "image"
                    if file.content_type and file.content_type.startswith("image/")
                    else "pdf"
                ),
                "filename": file.filename or "unknown",
                "session_id": session_id,
                "store_info": {"name": "Demo Store", "address": "Demo Address"},
                "receipt_date": datetime.now().strftime("%Y-%m-%d"),
            }
        )

        if not result.success:
            raise HTTPException(
                status_code=400, detail=f"Demo processing failed: {result.error}"
            )

        # Return comprehensive demo response
        return {
            "success": True,
            "message": "Demo OCR-RAG processing completed successfully",
            "demo_info": {
                "workflow": [
                    "1. File uploaded and validated",
                    "2. OCR text extraction completed",
                    "3. Content added to RAG knowledge base",
                    "4. Future queries enabled",
                ],
                "ocr_results": {
                    "extracted_text": (
                        result.data.get("ocr_text", "")[:200] + "..."
                        if len(result.data.get("ocr_text", "")) > 200
                        else result.data.get("ocr_text", "")
                    ),
                    "confidence": result.data.get("ocr_confidence", 0.0),
                    "chunks_added": result.data.get("rag_chunks_added", 0),
                },
                "rag_integration": {
                    "source_id": result.data.get("rag_source_id", ""),
                    "metadata": {
                        "filename": result.data.get("filename", ""),
                        "session_id": result.data.get("session_id", ""),
                        "store_info": result.data.get("store_info", {}),
                        "receipt_date": result.data.get("receipt_date", ""),
                    },
                },
                "next_steps": [
                    "Query the receipt history using /ocr-rag/query-history",
                    "Get statistics using /ocr-rag/statistics",
                    "Upload more receipts to build knowledge base",
                ],
            },
            "data": result.data,
            "metadata": result.metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in demo OCR-RAG upload: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")
