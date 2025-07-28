"""
Specialized OCR LLM Integration
Dedicated vision and text models for enhanced OCR processing of Polish receipts.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import re
import time
from typing import Any

import cv2
import numpy as np

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.easyocr_fallback import (
    process_with_easyocr_fallback,
    should_use_easyocr_fallback,
)
from core.llm_client import EnhancedLLMClient
from core.ocr_text_postprocessing import postprocess_ocr_text

logger = logging.getLogger(__name__)


class OCRModelType(str, Enum):
    """Specialized OCR models for different use cases"""

    VISION_PRIMARY = (
        "llava:7b"  # Primary vision model for direct image processing (available)
    )
    VISION_FAST = "llava:7b"  # Faster vision model for simple cases (available)
    TEXT_CORRECTOR = "llama3.2:3b"  # Text correction and enhancement (available)
    STRUCTURE_PARSER = "llama3.2:3b"  # Fast structural parsing (available)
    POLISH_SPECIALIST = "aya:8b"  # Polish language specialist (available)


@dataclass
class OCRProcessingConfig:
    """Configuration for specialized OCR processing"""

    vision_model_timeout: int = 60  # Increased timeout for reliable processing
    text_model_timeout: int = 30    # Increased timeout for reliable processing
    max_image_size: tuple[int, int] = (2048, 2048)
    image_quality: int = 95
    enable_preprocessing: bool = True
    enable_postprocessing: bool = True
    confidence_threshold: float = 0.7
    use_ensemble: bool = True


class ImagePreprocessor:
    """Advanced image preprocessing for better OCR results"""

    def __init__(self, config: OCRProcessingConfig):
        self.config = config

    def preprocess_receipt_image(self, image_path: str) -> dict[str, Any]:
        """
        Comprehensive preprocessing of receipt image for optimal OCR.
        Returns processed image path and metadata.
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot load image: {image_path}")

            original_shape = image.shape

            # Step 1: Resize if too large
            image = self._resize_image(image)

            # Step 2: Deskew correction
            image = self._deskew_image(image)

            # Step 3: Noise reduction
            image = self._reduce_noise(image)

            # Step 4: Contrast enhancement
            image = self._enhance_contrast(image)

            # Step 5: Text region enhancement
            image = self._enhance_text_regions(image)

            # Save processed image
            processed_path = self._save_processed_image(image, image_path)

            return {
                "processed_path": processed_path,
                "original_shape": original_shape,
                "final_shape": image.shape,
                "preprocessing_applied": [
                    "resize",
                    "deskew",
                    "noise_reduction",
                    "contrast_enhancement",
                    "text_enhancement",
                ],
            }

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return {
                "processed_path": image_path,  # Fallback to original
                "preprocessing_applied": [],
                "error": str(e),
            }

    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        """Resize image to optimal size for OCR"""
        height, width = image.shape[:2]
        max_width, max_height = self.config.max_image_size

        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(
                image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4
            )

        return image

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Correct skewed receipt images"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Find edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Find lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

        if lines is not None:
            # Calculate average angle
            angles = []
            for line in lines[:10]:  # Use top 10 lines
                rho, theta = line[0]
                angle = theta * 180 / np.pi
                if angle < 45:
                    angles.append(angle)
                elif angle > 135:
                    angles.append(angle - 180)

            if angles:
                avg_angle = np.median(angles)
                if abs(avg_angle) > 0.5:  # Only correct if angle is significant
                    # Rotate image
                    center = (image.shape[1] // 2, image.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                    image = cv2.warpAffine(
                        image, rotation_matrix, (image.shape[1], image.shape[0])
                    )

        return image

    def _reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """Remove noise while preserving text"""
        # Bilateral filter to reduce noise while keeping edges sharp
        image = cv2.bilateralFilter(image, 9, 75, 75)
        return image

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast for better text visibility"""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])

        # Convert back to BGR
        image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        return image

    def _enhance_text_regions(self, image: np.ndarray) -> np.ndarray:
        """Enhance text regions specifically"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Morphological operations to enhance text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

        # Opening to remove noise
        gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)

        # Convert back to BGR
        image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return image

    def _save_processed_image(self, image: np.ndarray, original_path: str) -> str:
        """Save processed image with proper cleanup tracking"""
        path = Path(original_path)
        processed_path = path.parent / f"{path.stem}_processed{path.suffix}"

        try:
            cv2.imwrite(
                str(processed_path),
                image,
                [cv2.IMWRITE_JPEG_QUALITY, self.config.image_quality],
            )
            logger.info(f"Processed image saved: {processed_path}")
            return str(processed_path)
        except Exception as e:
            logger.error(f"Failed to save processed image: {e}")
            return original_path  # Return original if save fails


class SpecializedOCRAgent(BaseAgent):
    """
    Specialized OCR agent using dedicated vision models for Polish receipts.
    Combines multiple approaches for maximum accuracy.
    """

    def __init__(self, name: str = "SpecializedOCRAgent", **kwargs):
        super().__init__(name=name, **kwargs)
        self.config = OCRProcessingConfig()
        self.preprocessor = ImagePreprocessor(self.config)
        self.model_performance: dict[str, float] = {}

    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Advanced OCR processing with multiple specialized models.
        """
        try:
            image_path = input_data.get("image_path")
            file_type = input_data.get("file_type", "image")

            if not image_path or not Path(image_path).exists():
                return AgentResponse(
                    success=False, error="Nieprawidłowa ścieżka do obrazu"
                )

            logger.info(
                f"Starting specialized OCR processing for: {image_path} (type: {file_type})"
            )
            start_time = time.time()

            # Check if file type is supported for vision models BEFORE preprocessing
            if file_type == "pdf":
                logger.info(
                    "PDF detected - vision models not supported, falling back to traditional OCR directly"
                )
                # For PDFs, use traditional OCR directly
                try:
                    from core.ocr import process_image_file
                    
                    with open(image_path, "rb") as f:
                        file_bytes = f.read()
                    
                    extracted_text = process_image_file(file_bytes) or ""
                    confidence = 0.7  # Default confidence for PDF OCR
                    
                    if extracted_text and len(extracted_text.strip()) >= 10:
                        return AgentResponse(
                            success=True,
                            data={
                                "extracted_text": extracted_text,
                                "confidence": confidence,
                                "preprocessing": {"applied": False, "reason": "pdf_direct_processing"},
                                "models_used": ["traditional_ocr_pdf"],
                                "processing_time": time.time() - start_time,
                            },
                            metadata={
                                "method": "specialized_ocr_pdf_fallback",
                                "processing_time": time.time() - start_time,
                                "confidence": confidence,
                            },
                        )
                except Exception as pdf_error:
                    logger.error(f"PDF OCR processing failed: {pdf_error}")
                
                # If PDF processing fails, return error
                return AgentResponse(
                    success=False,
                    error="PDF processing failed. Please try with an image file.",
                    metadata={
                        "method": "specialized_ocr",
                        "file_type": file_type,
                        "reason": "pdf_processing_failed",
                    },
                )

            # Step 1: Image preprocessing (only for image files)
            preprocessing_result = {}
            if self.config.enable_preprocessing:
                preprocessing_result = self.preprocessor.preprocess_receipt_image(
                    image_path
                )
                processed_image_path = preprocessing_result.get(
                    "processed_path", image_path
                )
            else:
                processed_image_path = image_path

            # Step 2: Multi-model OCR processing
            ocr_results = await self._run_multi_model_ocr(processed_image_path)

            # Step 3: Result fusion and enhancement
            final_result = await self._fuse_and_enhance_results(ocr_results)

            # Step 4: Post-processing
            if self.config.enable_postprocessing:
                final_result = await self._post_process_result(final_result)

            processing_time = time.time() - start_time

            # Step 5: Cleanup processed image if it was created
            if (preprocessing_result.get("processed_path") and 
                preprocessing_result["processed_path"] != image_path and
                Path(preprocessing_result["processed_path"]).exists()):
                try:
                    Path(preprocessing_result["processed_path"]).unlink()
                    logger.info("Cleaned up processed image file")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup processed image: {cleanup_error}")

            return AgentResponse(
                success=True,
                data={
                    "extracted_text": final_result["text"],
                    "confidence": final_result["confidence"],
                    "preprocessing": preprocessing_result,
                    "models_used": final_result["models_used"],
                    "processing_time": processing_time,
                },
                metadata={
                    "method": "specialized_ocr",
                    "processing_time": processing_time,
                    "confidence": final_result["confidence"],
                },
            )

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas przetwarzania OCR: {e!s}",
                data={"confidence": 0.0},
            )

    async def _run_multi_model_ocr(self, image_path: str) -> list[dict[str, Any]]:
        """Run OCR with multiple specialized models - optimized for speed"""
        ocr_tasks = []

        # Start with traditional OCR for speed
        ocr_tasks.append(
            self._run_traditional_ocr(image_path)
        )

        # Use vision model if explicitly requested and available
        if self.config.use_ensemble:
            ocr_tasks.append(
                self._run_vision_model_ocr(image_path, OCRModelType.VISION_PRIMARY)
            )

        # Run all models concurrently
        results = await asyncio.gather(*ocr_tasks, return_exceptions=True)

        # Filter successful results
        successful_results = []
        for result in results:
            if isinstance(result, dict) and result.get("success", False):
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"OCR model failed: {result}")

        return successful_results

    async def _run_traditional_ocr(self, image_path: str) -> dict[str, Any]:
        """Run traditional OCR for speed"""
        try:
            from core.ocr import process_image_file
            
            with open(image_path, "rb") as f:
                file_bytes = f.read()
            
            extracted_text = process_image_file(file_bytes) or ""
            confidence = 0.8  # Default confidence for traditional OCR
            
            return {
                "success": True,
                "text": extracted_text,
                "confidence": confidence,
                "model": "traditional_ocr",
                "engine_used": "tesseract",
            }
        except Exception as e:
            logger.error(f"Traditional OCR failed: {e}")
            return {"success": False, "error": str(e), "model": "traditional_ocr"}

    async def _run_vision_model_ocr(
        self, image_path: str, model_type: OCRModelType
    ) -> dict[str, Any]:
        """Run OCR with specific vision model"""
        try:
            start_time = time.time()

            # Initialize variables with default values
            engine_used = "tesseract"  # Default engine
            confidence = 0.0  # Default confidence

            # Optimized prompt for Polish receipts with image processing
            prompt = f"""
{self._get_polish_receipt_prompt()}

Przeanalizuj dokładnie obraz paragonu i wyodrębnij CAŁY tekst w dokładnej kolejności.
ZWRÓĆ TYLKO TEKST PARAGONU - bez komentarzy, bez dodatkowych opisów.
"""

            # Try vision model first, with proper error handling
            extracted_text = ""
            try:
                import ollama
                from settings import settings
                
                # Create raw ollama client for vision models
                raw_ollama_client = ollama.Client(host=settings.OLLAMA_URL)
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        raw_ollama_client.chat,
                        model=model_type.value,
                        messages=[
                            {"role": "user", "content": prompt, "images": [image_path]}
                        ],
                        options={"temperature": 0.1, "top_p": 0.9, "num_ctx": 4096},
                    ),
                    timeout=self.config.vision_model_timeout,
                )

                # Handle response
                if isinstance(response, dict) and "message" in response:
                    extracted_text = response["message"]["content"]
                    logger.info(f"Vision model {model_type.value} succeeded")
                else:
                    logger.warning(f"Vision model {model_type.value} returned empty response")
                    extracted_text = ""
                    
            except ImportError:
                logger.error("Ollama client not available, falling back to traditional OCR")
                extracted_text = ""
            except Exception as e:
                logger.error(f"Vision model {model_type.value} failed: {e}")
                extracted_text = ""

            # Always fallback to traditional OCR if vision model fails or returns empty
            if not extracted_text or len(extracted_text.strip()) < 10:
                logger.info("Vision model failed or returned insufficient text, using traditional OCR fallback")
                try:
                    from core.ocr import process_image_file
                    with open(image_path, "rb") as f:
                        file_bytes = f.read()
                    fallback_text = process_image_file(file_bytes) or ""
                    if len(fallback_text.strip()) > len(extracted_text.strip()):
                        extracted_text = fallback_text
                        logger.info("Traditional OCR fallback provided better results")
                except Exception as fallback_error:
                    logger.error(f"Traditional OCR fallback also failed: {fallback_error}")
                    if not extracted_text:
                        extracted_text = ""

            # Calculate confidence based on text quality
            confidence = self._calculate_text_confidence(extracted_text)

            # Check if EasyOCR fallback should be used
            if should_use_easyocr_fallback(extracted_text, confidence):
                logger.info("Tesseract OCR quality poor, trying EasyOCR fallback...")
                # Read image bytes for EasyOCR fallback
                with open(image_path, "rb") as f:
                    file_bytes = f.read()
                easyocr_result = process_with_easyocr_fallback(file_bytes)

                if (
                    easyocr_result.get("success", False)
                    and easyocr_result.get("confidence", 0.0) > confidence
                ):
                    logger.info(
                        f"EasyOCR fallback successful: confidence {easyocr_result.get('confidence', 0.0):.2f} vs {confidence:.2f}"
                    )
                    extracted_text = easyocr_result.get("text", "")
                    confidence = easyocr_result.get("confidence", 0.0)
                    engine_used = "easyocr_fallback"
                else:
                    logger.info(
                        "EasyOCR fallback failed or no improvement, using Tesseract result"
                    )
                    engine_used = "tesseract"
            else:
                engine_used = "tesseract"

            # Apply OCR text postprocessing
            postprocessing_result = postprocess_ocr_text(extracted_text, confidence)

            if postprocessing_result["success"]:
                processed_text = postprocessing_result["processed_text"]
                improvements = postprocessing_result["improvements"]
                logger.info(f"OCR postprocessing applied: {improvements}")
            else:
                processed_text = extracted_text
                logger.warning(
                    f"OCR postprocessing failed: {postprocessing_result.get('errors', [])}"
                )

            return {
                "success": True,
                "text": processed_text,
                "confidence": confidence,
                "model": model_type.value,
                "engine_used": engine_used,
                "postprocessing": {
                    "applied": postprocessing_result["success"],
                    "improvements": postprocessing_result.get("improvements", []),
                    "text_length_change": postprocessing_result.get(
                        "text_length_change", 0
                    ),
                },
            }

        except TimeoutError:
            logger.error(f"Timeout in vision model {model_type.value}")
            return {"success": False, "error": "timeout", "model": model_type.value}
        except Exception as e:
            logger.error(f"Error in vision model {model_type.value}: {e}")
            return {"success": False, "error": str(e), "model": model_type.value}

    def _get_polish_receipt_prompt(self) -> str:
        """Optimized prompt for Polish receipt OCR"""
        return """
Przeanalizuj dokładnie ten polski paragon i wyodrębnij CAŁY tekst w dokładnej kolejności.

INSTRUKCJE:
1. Przeczytaj każdą linię paragonu od góry do dołu
2. Zachowaj oryginalną strukturę i kolejność
3. Popraw oczywiste błędy OCR (np. "0" zamiast "O")
4. Dla nazw produktów: zachowaj oryginalną pisownię, ale popraw czytelność
5. Dla cen: używaj formatu "XX,XX PLN" lub "XX,XX"
6. Dla dat: używaj formatu "DD.MM.YYYY" lub "DD.MM.YY"
7. Uwzględnij WSZYSTKIE informacje: nagłówek, produkty, ceny, rabaty, sumę, stopkę

ZWRÓĆ TYLKO TEKST PARAGONU - bez komentarzy, bez dodatkowych opisów.

Przykład formatu:
LIDL
ul. Przykładowa 123
00-000 Warszawa

PARAGON FISKALNY
Data: 15.12.2024  Godz: 14:30

Chleb codzienny         3,99
Mleko 3,2% 1L          4,59
Masło extra 200g       8,99
------------------------
SUMA PLN              17,57

Dziękujemy za zakupy!
"""

    def _calculate_text_confidence(self, text: str) -> float:
        """Calculate confidence score based on text quality indicators"""
        if not text:
            return 0.0

        confidence = 0.5  # Base confidence

        # Check for Polish receipt indicators
        polish_indicators = [
            "paragon",
            "fiskalny",
            "suma",
            "pln",
            "nip",
            "regon",
            "data",
            "godz",
            "dziękujemy",
            "zakupy",
        ]

        text_lower = text.lower()
        indicator_count = sum(
            1 for indicator in polish_indicators if indicator in text_lower
        )
        confidence += (indicator_count / len(polish_indicators)) * 0.3

        # Check for price patterns
        price_patterns = [
            r"\d+,\d{2}",  # Format XX,XX
            r"\d+\.\d{2}",  # Format XX.XX
            r"pln",  # PLN currency
        ]

        for pattern in price_patterns:
            if len(list(re.finditer(pattern, text_lower))) > 0:
                confidence += 0.1

        # Check for store names
        store_names = ["lidl", "biedronka", "kaufland", "żabka", "tesco", "carrefour"]
        if any(store in text_lower for store in store_names):
            confidence += 0.1

        # Penalize for obvious OCR errors
        error_indicators = ["###", "???", "|||"]
        error_count = sum(text.count(indicator) for indicator in error_indicators)
        confidence -= min(error_count * 0.05, 0.2)

        return max(0.0, min(1.0, confidence))

    async def _fuse_and_enhance_results(
        self, ocr_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Fuse results from multiple models and enhance with text correction"""
        if not ocr_results:
            return {
                "text": "",
                "confidence": 0.0,
                "models_used": [],
                "fusion_method": "none",
            }

        if len(ocr_results) == 1:
            result = ocr_results[0]
            enhanced_text = await self._enhance_text_with_llm(result["text"])
            return {
                "text": enhanced_text,
                "confidence": result.get("confidence", 0.0),
                "models_used": [result.get("model", "unknown")],
                "fusion_method": "single_model_enhanced",
            }

        # Multi-model fusion - ensure all results have confidence
        valid_results = [r for r in ocr_results if r.get("confidence", 0.0) > 0.0]

        if not valid_results:
            # If no valid results, use the first one with default confidence
            best_result = (
                ocr_results[0]
                if ocr_results
                else {"text": "", "confidence": 0.0, "model": "unknown"}
            )
        else:
            best_result = max(valid_results, key=lambda x: x.get("confidence", 0.0))

        # Enhance the best result
        enhanced_text = await self._enhance_text_with_llm(best_result.get("text", ""))

        return {
            "text": enhanced_text,
            "confidence": best_result.get("confidence", 0.0),
            "models_used": [r.get("model", "unknown") for r in ocr_results],
            "fusion_method": "confidence_based",
        }

    async def _enhance_text_with_llm(self, raw_text: str) -> str:
        """Enhance OCR text using specialized text correction model"""
        try:
            prompt = f"""
Popraw błędy OCR w tekście polskiego paragonu. Zachowaj strukturę i wszystkie informacje.

ZASADY KOREKTY:
1. Popraw błędy literowe zachowując sens
2. Popraw błędnie rozpoznane cyfry w cenach
3. Usuń duplikaty linii
4. Zachowaj nazwy produktów (mogą być skrócone)
5. Popraw format dat i godzin
6. Zachowaj wszystkie ceny i sumy

ORYGINALNY TEKST OCR:
{raw_text}

POPRAWIONY TEKST:
"""

            llm_client = EnhancedLLMClient()
            response = await asyncio.wait_for(
                llm_client.chat(
                    model=OCRModelType.TEXT_CORRECTOR.value,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.1, "top_p": 0.9, "num_ctx": 4096},
                ),
                timeout=self.config.text_model_timeout,
            )

            # Handle response properly
            if isinstance(response, dict) and "message" in response:
                enhanced_text = response["message"]["content"].strip()
            else:
                enhanced_text = raw_text.strip()

            # Validate enhancement (should not be dramatically different)
            if len(enhanced_text) < len(raw_text) * 0.5:
                logger.warning("Enhanced text too short, using original")
                return raw_text

            return enhanced_text

        except Exception as e:
            logger.error(f"Text enhancement failed: {e}")
            return raw_text  # Fallback to original

    async def _post_process_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Post-process the final OCR result"""
        text = result.get("text", "")

        # Basic text cleaning
        text = self._clean_ocr_text(text)

        # Structure validation
        confidence_adjustment = self._validate_receipt_structure(text)
        current_confidence = result.get("confidence", 0.0)
        result["confidence"] = max(
            0.0, min(1.0, current_confidence + confidence_adjustment)
        )

        result["text"] = text
        return result

    def _clean_ocr_text(self, text: str) -> str:
        """Basic cleaning of OCR text"""
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]  # Remove empty lines

        # Remove duplicate lines
        seen_lines = set()
        cleaned_lines = []
        for line in lines:
            if line not in seen_lines:
                cleaned_lines.append(line)
                seen_lines.add(line)

        return "\n".join(cleaned_lines)

    def _validate_receipt_structure(self, text: str) -> float:
        """Validate receipt structure and return confidence adjustment"""
        adjustment = 0.0

        # Check for required sections
        has_header = any(
            word in text.lower() for word in ["paragon", "fiskalny", "sklep"]
        )
        has_products = (
            len([line for line in text.split("\n") if "," in line or "." in line]) > 0
        )
        has_total = any(word in text.lower() for word in ["suma", "razem", "total"])

        if has_header:
            adjustment += 0.05
        if has_products:
            adjustment += 0.05
        if has_total:
            adjustment += 0.05

        return adjustment


class OCRModelOrchestrator:
    """
    Orchestrates multiple OCR models for optimal results.
    Manages model lifecycle and performance optimization.
    """

    def __init__(self):
        self.available_models = {
            OCRModelType.VISION_PRIMARY: {"loaded": False, "performance": 0.0},
            OCRModelType.VISION_FAST: {"loaded": False, "performance": 0.0},
            OCRModelType.TEXT_CORRECTOR: {"loaded": False, "performance": 0.0},
            OCRModelType.POLISH_SPECIALIST: {"loaded": False, "performance": 0.0},
        }
        self.model_stats = {}

    async def ensure_models_ready(self) -> bool:
        """Ensure all required models are loaded and ready"""
        success = True

        # Use available models: llava:7b, llama3.2:3b, aya:8b
        for model_type in [
            OCRModelType.VISION_PRIMARY,
            OCRModelType.TEXT_CORRECTOR,
            OCRModelType.POLISH_SPECIALIST,
        ]:
            if not await self._ensure_model_loaded(model_type.value):
                success = False

        return success

    async def _ensure_model_loaded(self, model_name: str) -> bool:
        """Ensure specific model is loaded"""
        try:
            # Try a simple request to check if model is available
            llm_client = EnhancedLLMClient()
            await llm_client.chat(
                model=model_name,
                messages=[{"role": "user", "content": "test"}],
                options={"num_predict": 1},
            )
            return True
        except Exception as e:
            logger.warning(f"Model {model_name} not available: {e}")
            try:
                # Try to pull the model - this would need a different approach
                # since EnhancedLLMClient doesn't have pull method
                logger.info(f"Model {model_name} not available, skipping pull")
                return False
            except Exception as pull_error:
                logger.error(f"Failed to check model {model_name}: {pull_error}")
                return False

    def get_model_recommendations(
        self, image_complexity: str = "medium"
    ) -> list[OCRModelType]:
        """Get recommended models based on image complexity"""
        if image_complexity == "simple":
            return [OCRModelType.VISION_FAST]
        elif image_complexity == "complex":
            return [OCRModelType.VISION_PRIMARY, OCRModelType.VISION_FAST]
        else:  # medium
            return [OCRModelType.VISION_PRIMARY]


# Global orchestrator instance
ocr_model_orchestrator = OCRModelOrchestrator()
