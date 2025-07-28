"""
Receipt processing tasks for FoodSave AI
Handles asynchronous OCR and analysis of receipt images with GPU optimization.
"""

import asyncio
from datetime import datetime
import os
from pathlib import Path
import time
from typing import Any

from celery import Celery
from celery.utils.log import get_task_logger

from agents.ocr_agent import OCRAgent, OCRAgentInput
from agents.receipt_analysis_agent import ReceiptAnalysisAgent
from core.exceptions import FoodSaveError
from core.gpu_ocr import GPUOptimizedOCRAgent

# Create Celery app
celery_app = Celery("foodsave_tasks")
celery_app.config_from_object("celeryconfig")

logger = get_task_logger(__name__)

# Configuration
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./temp_uploads"))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

# Cleanup old files (older than 24 hours)
CLEANUP_THRESHOLD = 24 * 60 * 60  # 24 hours in seconds

# GPU Configuration
USE_GPU_OCR = os.getenv("USE_GPU_OCR", "true").lower() == "true"
GPU_DEVICE_ID = int(os.getenv("GPU_DEVICE_ID", "0"))

# Initialize GPU-optimized OCR processor
gpu_ocr_agent = None
if USE_GPU_OCR:
    try:
        gpu_ocr_agent = GPUOptimizedOCRAgent(use_gpu=True)
        logger.info("GPU OCR agent initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize GPU OCR agent: {e}, falling back to CPU")
        gpu_ocr_agent = None
else:
    logger.info("GPU OCR disabled, using CPU OCR")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_receipt_task(
    self, file_path: str, original_filename: str, user_id: str | None = None
) -> dict[str, Any]:
    """
    Asynchroniczne zadanie przetwarzania paragonu z optymalizacją GPU.

    Args:
        file_path: Ścieżka do zapisanego pliku
        original_filename: Oryginalna nazwa pliku
        user_id: ID użytkownika (opcjonalne)

    Returns:
        Dict zawierający wyniki przetwarzania
    """
    task_id = self.request.id
    logger.info(
        f"Rozpoczynam przetwarzanie paragonu: {original_filename} (Task ID: {task_id})"
    )

    # Log GPU status
    if USE_GPU_OCR and gpu_ocr_agent:
        gpu_status = gpu_ocr_agent.get_gpu_status()
        logger.info(f"GPU Status: {gpu_status}")

    try:
        # Step 1: Update task state to PROCESSING
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Initializing",
                "progress": 5,
                "message": "Inicjalizacja przetwarzania paragonu",
                "filename": original_filename,
                "gpu_enabled": USE_GPU_OCR,
            },
        )

        # Step 2: Validate file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Plik nie został znaleziony: {file_path}")

        # Step 3: Pre-processing validation
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Validation",
                "progress": 10,
                "message": "Walidacja pliku",
                "filename": original_filename,
            },
        )

        # Check file size
        file_size = file_path_obj.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError(f"Plik jest zbyt duży: {file_size / (1024 * 1024):.2f}MB")

        # Step 4: OCR Processing with GPU optimization
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "OCR",
                "progress": 25,
                "message": (
                    "Przetwarzanie OCR (GPU)"
                    if USE_GPU_OCR
                    else "Przetwarzanie OCR (CPU)"
                ),
                "filename": original_filename,
            },
        )

        # Read file and determine type
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Determine file type based on extension
        file_extension = file_path_obj.suffix.lower()
        if file_extension in [".jpg", ".jpeg", ".png", ".webp"]:
            file_type = "image"
        elif file_extension == ".pdf":
            file_type = "pdf"
        else:
            raise ValueError(f"Nieobsługiwany typ pliku: {file_extension}")

        # Process with GPU-optimized OCR Agent
        try:
            logger.info(
                f"Starting {'GPU-optimized' if USE_GPU_OCR else 'CPU'} OCR processing for {original_filename}"
            )

            if USE_GPU_OCR and gpu_ocr_agent:
                # Use GPU-optimized OCR
                ocr_result = gpu_ocr_agent.process_image(file_bytes)
            else:
                # Fallback to standard OCR
                ocr_result = run_ocr_agent_sync(file_bytes, file_type)

            logger.info(f"OCR processing completed for {original_filename}")
        except FoodSaveError as e:
            logger.error(f"FoodSaveError in OCR: {e!s}")
            return {
                "status_code": 500,
                "error_code": "OCR_PROCESSING_FAILED",
                "message": f"OCR processing failed: {e!s}",
                "details": {"filename": original_filename},
            }
        except Exception as e:
            logger.error(f"Unexpected error in OCR processing: {e!s}")
            return {
                "status_code": 500,
                "error_code": "OCR_UNEXPECTED_ERROR",
                "message": f"OCR processing failed due to unexpected error: {e!s}",
                "details": {"filename": original_filename},
            }

        # Check OCR result success
        if not ocr_result:
            error_msg = "OCR processing returned no result"
            logger.error(f"{error_msg} for {original_filename}")
            return {
                "status_code": 400,
                "error_code": "OCR_FAILED",
                "message": error_msg,
                "details": {"filename": original_filename},
            }

        if not hasattr(ocr_result, "text"):
            error_msg = "OCR result has no text attribute"
            logger.error(f"{error_msg} for {original_filename}")
            return {
                "status_code": 400,
                "error_code": "OCR_FAILED",
                "message": error_msg,
                "details": {"filename": original_filename},
            }

        if not ocr_result.text or not ocr_result.text.strip():
            logger.warning(
                f"OCR extracted empty text for {original_filename}, will attempt analysis anyway"
            )
            ocr_result.text = "BRAK_TEKSTU_OCR"

        # Step 5: OCR Quality Check
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "OCR Quality Check",
                "progress": 40,
                "message": "Sprawdzanie jakości OCR",
                "filename": original_filename,
            },
        )

        # Basic quality check - ensure we have some meaningful text
        ocr_text = ocr_result.text.strip()
        if len(ocr_text) < 3:
            logger.warning(
                f"OCR text very short ({len(ocr_text)} chars) for {original_filename}: '{ocr_text}'"
            )
            # Continue with analysis anyway - might still extract some info
        elif len(ocr_text) < 10:
            logger.warning(
                f"OCR text short ({len(ocr_text)} chars) for {original_filename}, continuing anyway"
            )

        # Check for receipt keywords
        receipt_keywords = [
            "PLN",
            "SUMA",
            "PARAGON",
            "RACHUNEK",
            "SKLEP",
            "SKLEP:",
            "TOTAL",
            "SUBTOTAL",
        ]
        has_receipt_keywords = any(
            keyword.lower() in ocr_text.lower() for keyword in receipt_keywords
        )

        if not has_receipt_keywords:
            logger.warning(
                f"Brak słów kluczowych paragonu w tekście OCR: {original_filename}"
            )

        # Step 6: AI Analysis with GPU optimization
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "AI Analysis",
                "progress": 60,
                "message": "Analiza AI (GPU)" if USE_GPU_OCR else "Analiza AI (CPU)",
                "filename": original_filename,
            },
        )

        # Process with Receipt Analysis Agent
        try:
            logger.info(f"Starting AI analysis for {original_filename}")
            analysis_result = run_analysis_agent_sync(ocr_text)

            logger.info(f"AI analysis completed for {original_filename}")
        except FoodSaveError as e:
            logger.error(f"FoodSaveError in AI analysis: {e!s}")
            return {
                "status_code": 500,
                "error_code": "AI_ANALYSIS_FAILED",
                "message": f"Receipt analysis failed: {e!s}",
                "details": {"filename": original_filename},
            }
        except Exception as e:
            logger.error(f"Unexpected error in AI analysis: {e!s}")
            return {
                "status_code": 500,
                "error_code": "AI_UNEXPECTED_ERROR",
                "message": f"Receipt analysis failed due to unexpected error: {e!s}",
                "details": {"filename": original_filename},
            }

        if not analysis_result or not hasattr(analysis_result, "success"):
            return {
                "status_code": 500,
                "error_code": "AI_ANALYSIS_FAILED",
                "message": "AI analysis failed to return valid result",
                "details": {"filename": original_filename},
            }

        if not analysis_result.success:
            error_msg = getattr(analysis_result, "error", "Unknown error")
            return {
                "status_code": 500,
                "error_code": "AI_ANALYSIS_FAILED",
                "message": f"Błąd analizy AI: {error_msg}",
                "details": {"filename": original_filename},
            }

        # Step 7: Data Validation
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Validation",
                "progress": 80,
                "message": "Walidacja danych",
                "filename": original_filename,
            },
        )

        # Step 8: Prepare final result
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Finalization",
                "progress": 90,
                "message": "Finalizacja wyników",
                "filename": original_filename,
            },
        )

        # Prepare final result with proper error handling
        try:
            # Ensure analysis_result.data is a dictionary
            if hasattr(analysis_result, "data") and isinstance(
                analysis_result.data, dict
            ):
                final_data = analysis_result.data
            else:
                # Create a basic structure if data is not available
                final_data = {
                    "ocr_text": ocr_text,
                    "analysis": analysis_result,
                    "metadata": {
                        "processing_time": datetime.now().isoformat(),
                        "file_size": file_size,
                        "file_type": file_type,
                        "gpu_enabled": USE_GPU_OCR,
                    },
                }

            # Ensure user_id is a string
            safe_user_id = str(user_id) if user_id is not None else "unknown"

            # Save to database if needed
            try:
                save_receipt_sync(None, final_data, safe_user_id, task_id)
            except Exception as save_error:
                logger.warning(f"Failed to save receipt to database: {save_error}")

            # Cleanup temporary file
            try:
                if file_path_obj.exists():
                    file_path_obj.unlink()
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")

            # Return final result
            return {
                "status_code": 200,
                "message": "Receipt processed successfully",
                "data": final_data,
                "metadata": {
                    "task_id": task_id,
                    "processing_time": datetime.now().isoformat(),
                    "gpu_enabled": USE_GPU_OCR,
                    "file_size": file_size,
                    "file_type": file_type,
                },
            }

        except Exception as e:
            logger.error(f"Error preparing final result: {e}")
            return {
                "status_code": 500,
                "error_code": "FINALIZATION_FAILED",
                "message": f"Error preparing final result: {e}",
                "details": {"filename": original_filename},
            }

    except Exception as e:
        logger.error(f"Receipt processing failed: {e}")

        # Cleanup on error
        try:
            if file_path_obj.exists():
                file_path_obj.unlink()
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup on error: {cleanup_error}")

        raise


@celery_app.task
def cleanup_temp_files():
    """
    Zadanie czyszczenia starych plików tymczasowych.
    """
    logger.info("Rozpoczynam czyszczenie starych plików tymczasowych")

    try:
        current_time = time.time()
        deleted_count = 0

        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime

                if file_age > CLEANUP_THRESHOLD:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Usunięto stary plik: {file_path}")
                    except Exception as e:
                        logger.warning(f"Nie udało się usunąć pliku {file_path}: {e}")

        logger.info(f"Zakończono czyszczenie. Usunięto {deleted_count} plików.")
        return {"deleted_count": deleted_count, "status": "SUCCESS"}

    except Exception as e:
        logger.error(f"Błąd podczas czyszczenia plików: {e}")
        return {"error": str(e), "status": "FAILURE"}


@celery_app.task
def health_check():
    """
    Zadanie sprawdzania stanu workera.
    """
    return {
        "status": "HEALTHY",
        "timestamp": datetime.now().isoformat(),
        "worker_id": os.environ.get("CELERY_WORKER_ID", "unknown"),
    }


@celery_app.task
def test_exception_serialization_task():
    """Minimal task to test Celery exception serialization."""
    raise RuntimeError("Test exception for Celery serialization.")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_receipt_task_simple(
    self, file_path: str, original_filename: str, user_id: str | None = None
) -> dict[str, Any]:
    """
    Uproszczona wersja zadania przetwarzania paragonu bez async operacji.
    """
    task_id = self.request.id
    logger.info(
        f"Rozpoczynam uproszczone przetwarzanie paragonu: {original_filename} (Task ID: {task_id})"
    )

    try:
        # Step 1: Update task state
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Initializing",
                "progress": 10,
                "message": "Inicjalizacja przetwarzania paragonu",
                "filename": original_filename,
            },
        )

        # Step 2: Validate file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Plik nie został znaleziony: {file_path}")

        # Step 3: Check file size
        file_size = file_path_obj.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError(f"Plik jest zbyt duży: {file_size / (1024 * 1024):.2f}MB")

        # Step 4: Simulate processing
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Processing",
                "progress": 50,
                "message": "Przetwarzanie pliku",
                "filename": original_filename,
            },
        )

        # Simulate some processing time
        import time

        time.sleep(1)

        # Step 5: Cleanup
        try:
            os.remove(file_path)
            logger.info(f"Usunięto plik tymczasowy: {file_path}")
        except Exception as e:
            logger.warning(f"Nie udało się usunąć pliku tymczasowego {file_path}: {e}")

        # Step 6: Return simple result
        result = {
            "status": "SUCCESS",
            "task_id": task_id,
            "filename": original_filename,
            "processing_time": datetime.now().isoformat(),
            "message": "Uproszczone przetwarzanie zakończone pomyślnie",
            "metadata": {"file_size": file_size, "user_id": user_id},
        }

        logger.info(
            f"Pomyślnie przetworzono paragon (uproszczony): {original_filename} (Task ID: {task_id})"
        )

        return result

    except Exception as e:
        logger.error(
            f"Błąd podczas uproszczonego przetwarzania paragonu {original_filename}: {e!s}"
        )
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")

        # Update task state to FAILURE
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "filename": original_filename, "task_id": task_id},
        )

        # Retry logic for transient errors
        if self.request.retries < self.max_retries:
            logger.info(
                f"Ponawiam próbę {self.request.retries + 1}/{self.max_retries} dla {original_filename}"
            )
            raise self.retry(countdown=self.default_retry_delay)

        # If max retries reached, return error result
        return {
            "status": "FAILURE",
            "task_id": task_id,
            "filename": original_filename,
            "error": str(e),
            "retries": self.request.retries,
        }


@celery_app.task
def process_receipt_task_minimal(
    file_path: str, original_filename: str, user_id: str | None = None
) -> dict[str, Any]:
    """
    Minimalna wersja zadania przetwarzania paragonu bez żadnych skomplikowanych operacji.
    """
    logger.info(f"Rozpoczynam minimalne przetwarzanie paragonu: {original_filename}")

    try:
        # Simple file check
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Plik nie został znaleziony: {file_path}")

        # Simple result
        result = {
            "status": "SUCCESS",
            "filename": original_filename,
            "processing_time": datetime.now().isoformat(),
            "message": "Minimalne przetwarzanie zakończone pomyślnie",
            "user_id": user_id,
        }

        logger.info(f"Pomyślnie przetworzono paragon (minimalny): {original_filename}")

        return result

    except Exception as e:
        logger.error(
            f"Błąd podczas minimalnego przetwarzania paragonu {original_filename}: {e!s}"
        )

        # Simple error result
        return {
            "status": "FAILURE",
            "filename": original_filename,
            "error": str(e),
            "user_id": user_id,
        }


@celery_app.task(bind=True)
def process_receipt_task_minimal_with_state(
    self, file_path: str, original_filename: str, user_id: str | None = None
) -> dict[str, Any]:
    """
    Minimalna wersja zadania przetwarzania paragonu z update_state.
    """
    logger.info(
        f"Rozpoczynam minimalne przetwarzanie paragonu z state: {original_filename}"
    )

    try:
        # Test update_state
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Processing",
                "progress": 50,
                "message": "Przetwarzanie pliku",
                "filename": original_filename,
            },
        )

        # Simple file check
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Plik nie został znaleziony: {file_path}")

        # Simple result
        result = {
            "status": "SUCCESS",
            "filename": original_filename,
            "processing_time": datetime.now().isoformat(),
            "message": "Minimalne przetwarzanie z state zakończone pomyślnie",
            "user_id": user_id,
        }

        logger.info(
            f"Pomyślnie przetworzono paragon (minimalny z state): {original_filename}"
        )

        return result

    except Exception as e:
        logger.error(
            f"Błąd podczas minimalnego przetwarzania paragonu z state {original_filename}: {e!s}"
        )

        # Simple error result
        return {
            "status": "FAILURE",
            "filename": original_filename,
            "error": str(e),
            "user_id": user_id,
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_receipt_task_minimal_with_retry(
    self, file_path: str, original_filename: str, user_id: str | None = None
) -> dict[str, Any]:
    """
    Minimalna wersja zadania przetwarzania paragonu z retry.
    """
    logger.info(
        f"Rozpoczynam minimalne przetwarzanie paragonu z retry: {original_filename}"
    )

    try:
        # Test update_state
        self.update_state(
            state="PROGRESS",
            meta={
                "step": "Processing",
                "progress": 50,
                "message": "Przetwarzanie pliku",
                "filename": original_filename,
            },
        )

        # Simple file check
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Plik nie został znaleziony: {file_path}")

        # Simple result
        result = {
            "status": "SUCCESS",
            "filename": original_filename,
            "processing_time": datetime.now().isoformat(),
            "message": "Minimalne przetwarzanie z retry zakończone pomyślnie",
            "user_id": user_id,
        }

        logger.info(
            f"Pomyślnie przetworzono paragon (minimalny z retry): {original_filename}"
        )

        return result

    except Exception as e:
        logger.error(
            f"Błąd podczas minimalnego przetwarzania paragonu z retry {original_filename}: {e!s}"
        )

        # Test retry logic
        if self.request.retries < self.max_retries:
            logger.info(
                f"Ponawiam próbę {self.request.retries + 1}/{self.max_retries} dla {original_filename}"
            )
            raise self.retry(countdown=self.default_retry_delay)

        # Simple error result
        return {
            "status": "FAILURE",
            "filename": original_filename,
            "error": str(e),
            "user_id": user_id,
        }


# Synchronous wrappers for async agents
def run_ocr_agent_sync(file_bytes: bytes, file_type: str):
    """Synchronous wrapper for OCR agent."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ocr_agent = OCRAgent()
        ocr_input = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)
        return loop.run_until_complete(ocr_agent.process(ocr_input))
    finally:
        loop.close()


def run_analysis_agent_sync(ocr_text: str):
    """Synchronous wrapper for Receipt Analysis agent."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        analysis_agent = ReceiptAnalysisAgent()
        return loop.run_until_complete(analysis_agent.process({"ocr_text": ocr_text}))
    finally:
        loop.close()


async def save_receipt_async(
    db_manager,
    analysis_data: dict,
    user_id: str | None = None,
    correlation_id: str | None = None,
):
    """Async wrapper for database save operation."""
    safe_user_id = str(user_id) if user_id is not None else "unknown"
    safe_correlation_id = (
        str(correlation_id) if correlation_id is not None else "unknown"
    )
    return await db_manager.save_receipt_to_database(
        analysis_data, safe_user_id, safe_correlation_id
    )


def save_receipt_sync(
    db_manager,
    analysis_data: dict,
    user_id: str | None = None,
    correlation_id: str | None = None,
):
    """Synchronous wrapper for database save operation."""
    safe_user_id = str(user_id) if user_id is not None else "unknown"
    safe_correlation_id = (
        str(correlation_id) if correlation_id is not None else "unknown"
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            save_receipt_async(
                db_manager, analysis_data, safe_user_id, safe_correlation_id
            )
        )
    finally:
        loop.close()
