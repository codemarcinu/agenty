"""
Enhanced OCR processor with memory management, confidence scoring, and progressive timeouts.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import logging
import threading
import time
from typing import Any

import cv2
import numpy as np
from PIL import Image
from pydantic import BaseModel
import pytesseract

from core.memory_manager import (
    memory_context,
    memory_manager,
    with_ocr_memory_limit,
)
from core.timeout_manager import TimeoutConfig, timeout_manager

logger = logging.getLogger(__name__)


class OCRResult(BaseModel):
    """Enhanced OCR result with confidence and metadata"""

    text: str
    confidence: float
    metadata: dict[str, Any] = {}
    processing_time: float = 0.0
    memory_used: float = 0.0
    fallback_used: bool = False


class OCRStrategy:
    """OCR processing strategy with different configurations"""

    def __init__(self, name: str, config: str, timeout: float, description: str):
        self.name = name
        self.config = config
        self.timeout = timeout
        self.description = description


class EnhancedOCRProcessor:
    """Enhanced OCR processor with progressive strategies and memory management"""

    def __init__(self, languages: list[str] | None = None):
        self.languages = languages or ["pol", "eng"]
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.result_cache = {}
        self.cache_lock = threading.Lock()

        # Define OCR strategies (from fast to comprehensive)
        self.strategies = [
            OCRStrategy(
                name="quick",
                config="--oem 3 --psm 6 -l pol+eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] ",
                timeout=TimeoutConfig.OCR_QUICK_TIMEOUT,
                description="Quick OCR with essential preprocessing and character filtering",
            ),
            OCRStrategy(
                name="standard",
                config="--oem 3 --psm 6 -l pol+eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] ",
                timeout=TimeoutConfig.OCR_STANDARD_TIMEOUT,
                description="Standard OCR with character filtering",
            ),
            OCRStrategy(
                name="comprehensive",
                config="--oem 3 --psm 6 -l pol+eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] -c preserve_interword_spaces=1 -c textord_heavy_nr=1",
                timeout=TimeoutConfig.OCR_FALLBACK_TIMEOUT,
                description="Comprehensive OCR with advanced preprocessing",
            ),
        ]

    async def process_image_async(self, image_bytes: bytes) -> OCRResult:
        """Process image with progressive OCR strategies"""
        start_time = time.time()
        start_memory = memory_manager.get_memory_usage()

        # Check cache first
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        with self.cache_lock:
            if image_hash in self.result_cache:
                logger.info(f"OCR cache hit for {image_hash[:8]}")
                cached_result = self.result_cache[image_hash]
                cached_result.metadata["cache_hit"] = True
                return cached_result

        # Progressive OCR strategies
        operations = []
        for strategy in self.strategies:
            operations.append(
                (
                    lambda s=strategy: self._process_with_strategy(image_bytes, s),
                    strategy.timeout,
                    strategy.description,
                )
            )

        try:
            result = await timeout_manager.progressive_timeout(
                operations, "ocr_processing"
            )

            # Cache the result
            with self.cache_lock:
                self.result_cache[image_hash] = result

                # Keep cache size reasonable
                if len(self.result_cache) > 100:
                    # Remove oldest entries
                    oldest_key = next(iter(self.result_cache))
                    del self.result_cache[oldest_key]

            # Update result metadata
            result.processing_time = time.time() - start_time
            result.memory_used = memory_manager.get_memory_usage() - start_memory
            result.metadata["image_hash"] = image_hash[:8]

            return result

        except Exception as e:
            logger.error(f"All OCR strategies failed: {e}")

            # Return fallback result
            return OCRResult(
                text="",
                confidence=0.0,
                metadata={"error": str(e), "fallback": True},
                processing_time=time.time() - start_time,
                memory_used=memory_manager.get_memory_usage() - start_memory,
                fallback_used=True,
            )

    async def _process_with_strategy(
        self, image_bytes: bytes, strategy: OCRStrategy
    ) -> OCRResult:
        """Process image with a specific OCR strategy"""
        logger.info(f"Attempting OCR with strategy: {strategy.name}")

        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                self.executor, self._process_image_sync, image_bytes, strategy
            )

            logger.info(
                f"OCR strategy {strategy.name} succeeded with confidence {result.confidence:.2f}"
            )
            return result

        except Exception as e:
            logger.warning(f"OCR strategy {strategy.name} failed: {e}")
            raise

    @with_ocr_memory_limit
    def _process_image_sync(
        self, image_bytes: bytes, strategy: OCRStrategy
    ) -> OCRResult:
        """Synchronous image processing with memory management"""
        try:
            with memory_context("ocr_processing", 128):  # 128MB limit
                # Load image
                image = Image.open(io.BytesIO(image_bytes))

                # Apply preprocessing based on strategy
                if strategy.name == "quick":
                    processed_image = self._quick_preprocessing(image)
                elif strategy.name == "standard":
                    processed_image = self._standard_preprocessing(image)
                else:  # comprehensive
                    processed_image = self._comprehensive_preprocessing(image)

                # Perform OCR with confidence scoring
                text, confidence = self._ocr_with_confidence(
                    processed_image, strategy.config
                )

                # Clean up
                del processed_image

                return OCRResult(
                    text=text,
                    confidence=confidence,
                    metadata={
                        "strategy": strategy.name,
                        "config": strategy.config,
                        "original_size": image.size,
                    },
                )

        except Exception as e:
            logger.error(f"OCR processing error with strategy {strategy.name}: {e}")
            raise

    def _quick_preprocessing(self, image: Image.Image) -> Image.Image:
        """Quick preprocessing for fast OCR - improved for better quality"""
        try:
            # Convert to RGB if needed
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            # Convert to numpy for processing
            img_array = np.array(image)

            # Basic enhancement for better OCR
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            # Scale to optimal size (more important for receipts)
            img_array = self._scale_to_optimal_size(img_array)

            # Basic contrast enhancement for receipts
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array.copy()

            # Simple contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Convert back to PIL
            processed_image = Image.fromarray(enhanced, mode="L")

            # Clean up
            del img_array, enhanced

            return processed_image

        except Exception as e:
            logger.warning(f"Quick preprocessing failed: {e}")
            # Fallback to original simple scaling
            if max(image.size) > 2000:
                ratio = 2000 / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            return image

    def _standard_preprocessing(self, image: Image.Image) -> Image.Image:
        """Standard preprocessing with basic enhancements"""
        try:
            # Convert to RGB if needed
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            # Convert to numpy array
            img_array = np.array(image)

            # Basic enhancement
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            # Scale to optimal size
            img_array = self._scale_to_optimal_size(img_array)

            # Convert back to PIL
            processed_image = Image.fromarray(
                cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            )

            # Clean up
            del img_array

            return processed_image

        except Exception as e:
            logger.warning(f"Standard preprocessing failed: {e}")
            return image

    def _comprehensive_preprocessing(self, image: Image.Image) -> Image.Image:
        """Comprehensive preprocessing with advanced techniques"""
        try:
            # Convert to RGB if needed
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            # Convert to numpy array
            img_array = np.array(image)

            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            # Advanced preprocessing
            img_array = self._detect_and_correct_skew(img_array)
            img_array = self._enhance_contrast_adaptive(img_array)
            img_array = self._scale_to_optimal_size(img_array)
            img_array = self._apply_denoising(img_array)

            # Convert back to PIL
            if len(img_array.shape) == 2:
                processed_image = Image.fromarray(img_array, mode="L")
            else:
                processed_image = Image.fromarray(
                    cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                )

            # Clean up
            del img_array

            return processed_image

        except Exception as e:
            logger.warning(f"Comprehensive preprocessing failed: {e}")
            return image

    def _ocr_with_confidence(
        self, image: Image.Image, config: str
    ) -> tuple[str, float]:
        """Perform OCR with confidence scoring"""
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                image, config=config, output_type=pytesseract.Output.DICT
            )

            # Extract text and calculate confidence
            words = []
            confidences = []

            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                conf = int(data["conf"][i])

                if text and conf > 0:
                    words.append(text)
                    confidences.append(conf)

            # Calculate average confidence
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                text = " ".join(words)
            else:
                avg_confidence = 0.0
                text = ""

            # Additional confidence boost for receipt-like patterns
            if self._looks_like_receipt(text):
                avg_confidence = min(100, avg_confidence * 1.1)

            return text, avg_confidence / 100.0  # Normalize to 0-1

        except Exception as e:
            logger.error(f"OCR with confidence failed: {e}")
            # Fallback to simple OCR
            try:
                text = pytesseract.image_to_string(image, config=config)
                return text, 0.5  # Default confidence
            except Exception as e2:
                logger.error(f"Fallback OCR failed: {e2}")
                return "", 0.0

    def _looks_like_receipt(self, text: str) -> bool:
        """Check if text looks like a receipt"""
        receipt_indicators = [
            "paragon",
            "faktura",
            "suma",
            "razem",
            "total",
            "pln",
            "zł",
            "lidl",
            "biedronka",
            "kaufland",
            "tesco",
            "auchan",
            "carrefour",
            "data",
            "nip",
            "kasa",
            "sprzedawca",
        ]

        text_lower = text.lower()
        matches = sum(1 for indicator in receipt_indicators if indicator in text_lower)

        return matches >= 2

    def _scale_to_optimal_size(self, img_array: np.ndarray) -> np.ndarray:
        """Scale image to optimal size for OCR"""
        try:
            height, width = img_array.shape[:2]

            # Target height around 1000-1500 pixels for optimal OCR
            target_height = 1200

            if height < target_height * 0.8:
                # Upscale small images
                scale_factor = target_height / height
                new_width = int(width * scale_factor)
                new_height = target_height
            elif height > target_height * 1.5:
                # Downscale large images
                scale_factor = target_height / height
                new_width = int(width * scale_factor)
                new_height = target_height
            else:
                # Size is optimal
                return img_array

            scaled = cv2.resize(
                img_array, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4
            )
            logger.debug(f"Scaled image: {img_array.shape} -> {scaled.shape}")

            return scaled

        except Exception as e:
            logger.warning(f"Scaling failed: {e}")
            return img_array

    def _detect_and_correct_skew(self, img_array: np.ndarray) -> np.ndarray:
        """Detect and correct skew in the image"""
        try:
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array.copy()

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

            if lines is not None:
                # Calculate skew angle
                angles = []
                for line in lines:
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi
                    if angle < 45:
                        angles.append(angle)
                    elif angle > 135:
                        angles.append(angle - 180)

                if angles:
                    # Use median angle to avoid outliers
                    skew_angle = np.median(angles)

                    # Only correct if skew is significant
                    if abs(skew_angle) > 0.5:
                        # Rotate image
                        (h, w) = img_array.shape[:2]
                        center = (w // 2, h // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(
                            center, skew_angle, 1.0
                        )
                        corrected = cv2.warpAffine(
                            img_array,
                            rotation_matrix,
                            (w, h),
                            flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REPLICATE,
                        )

                        logger.debug(f"Corrected skew: {skew_angle:.2f} degrees")
                        return corrected

            return img_array

        except Exception as e:
            logger.warning(f"Skew correction failed: {e}")
            return img_array

    def _enhance_contrast_adaptive(self, img_array: np.ndarray) -> np.ndarray:
        """Enhance contrast using adaptive histogram equalization"""
        try:
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array.copy()

            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Convert back to original format
            if len(img_array.shape) == 3:
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

            return enhanced

        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {e}")
            return img_array

    def _apply_denoising(self, img_array: np.ndarray) -> np.ndarray:
        """Apply denoising to improve OCR accuracy"""
        try:
            if len(img_array.shape) == 3:
                denoised = cv2.fastNlMeansDenoisingColored(
                    img_array, None, 10, 10, 7, 21
                )
            else:
                denoised = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)

            return denoised

        except Exception as e:
            logger.warning(f"Denoising failed: {e}")
            return img_array

    def clear_cache(self):
        """Clear the OCR result cache"""
        with self.cache_lock:
            self.result_cache.clear()
            logger.info("OCR cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        with self.cache_lock:
            return {
                "cache_size": len(self.result_cache),
                "cache_keys": list(self.result_cache.keys()),
            }

    def shutdown(self):
        """Shutdown the OCR processor"""
        self.executor.shutdown(wait=True)
        self.clear_cache()
        logger.info("OCR processor shutdown complete")


# Global enhanced OCR processor instance
enhanced_ocr_processor = EnhancedOCRProcessor()


# Convenience functions
async def process_image_with_confidence(image_bytes: bytes) -> OCRResult:
    """Process image with confidence scoring and progressive strategies"""
    return await enhanced_ocr_processor.process_image_async(image_bytes)


def clear_ocr_cache():
    """Clear the OCR result cache"""
    enhanced_ocr_processor.clear_cache()


def get_ocr_cache_stats() -> dict[str, Any]:
    """Get OCR cache statistics"""
    return enhanced_ocr_processor.get_cache_stats()
