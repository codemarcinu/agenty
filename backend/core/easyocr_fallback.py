"""
EasyOCR Fallback for Polish Receipts

This module provides EasyOCR as a fallback OCR engine when Tesseract fails
or produces poor quality results. EasyOCR is particularly good at handling
low-quality images and complex layouts.
"""

import logging
import os
import tempfile

try:
    import easyocr

    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not available. Install with: pip install easyocr")

logger = logging.getLogger(__name__)


class EasyOCRFallback:
    """
    EasyOCR fallback engine for Polish receipt OCR.

    Features:
    - Multi-language support (Polish + English)
    - Better handling of low-quality images
    - Confidence scoring
    - Automatic language detection
    """

    def __init__(self):
        self.reader = None
        self.initialized = False
        self.languages = ["pl", "en"]  # Polish and English

        if EASYOCR_AVAILABLE:
            self._initialize_reader()

    def _initialize_reader(self):
        """Initialize EasyOCR reader with Polish language support"""
        try:
            logger.info("Initializing EasyOCR reader for Polish receipts...")
            self.reader = easyocr.Reader(
                self.languages,
                gpu=False,  # Use CPU for compatibility
                model_storage_directory=None,
                download_enabled=True,
                quantize=True,  # Use quantized models for better performance
            )
            self.initialized = True
            logger.info("EasyOCR reader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.initialized = False

    def is_available(self) -> bool:
        """Check if EasyOCR is available and initialized"""
        return EASYOCR_AVAILABLE and self.initialized and self.reader is not None

    def process_image(
        self, image_bytes: bytes, confidence_threshold: float = 0.3
    ) -> dict[str, any]:
        """
        Process image with EasyOCR.

        Args:
            image_bytes: Image bytes
            confidence_threshold: Minimum confidence for text detection

        Returns:
            Dict with OCR results
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "EasyOCR not available",
                "text": "",
                "confidence": 0.0,
            }

        try:
            # Save image to temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            try:
                # Process with EasyOCR
                results = self.reader.readtext(temp_path)

                # Extract text and confidence scores
                extracted_text = []
                total_confidence = 0.0
                valid_detections = 0

                for bbox, text, confidence in results:
                    if confidence >= confidence_threshold:
                        extracted_text.append(text.strip())
                        total_confidence += confidence
                        valid_detections += 1

                # Calculate average confidence
                avg_confidence = (
                    total_confidence / valid_detections if valid_detections > 0 else 0.0
                )

                # Join text with newlines
                final_text = "\n".join(extracted_text)

                return {
                    "success": True,
                    "text": final_text,
                    "confidence": avg_confidence,
                    "detections": len(results),
                    "valid_detections": valid_detections,
                    "engine": "easyocr",
                }

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"EasyOCR processing error: {e}")
            return {"success": False, "error": str(e), "text": "", "confidence": 0.0}

    def should_use_fallback(
        self, tesseract_text: str, tesseract_confidence: float
    ) -> bool:
        """
        Determine if EasyOCR fallback should be used.

        Args:
            tesseract_text: Text from Tesseract
            tesseract_confidence: Confidence from Tesseract

        Returns:
            True if fallback should be used
        """
        if not self.is_available():
            return False

        # Use fallback if:
        # 1. Tesseract confidence is very low
        if tesseract_confidence < 0.3:
            return True

        # 2. Tesseract text is too short (likely poor OCR)
        if len(tesseract_text.strip()) < 10:
            return True

        # 3. Tesseract text contains mostly noise
        noise_ratio = self._calculate_noise_ratio(tesseract_text)
        if noise_ratio > 0.7:
            return True

        # 4. No meaningful words detected
        meaningful_words = self._count_meaningful_words(tesseract_text)
        if meaningful_words < 2:
            return True

        return False

    def _calculate_noise_ratio(self, text: str) -> float:
        """Calculate ratio of noise characters in text"""
        if not text:
            return 1.0

        # Count special characters and numbers that might be noise
        noise_chars = sum(1 for c in text if c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`")
        total_chars = len(text)

        return noise_chars / total_chars if total_chars > 0 else 1.0

    def _count_meaningful_words(self, text: str) -> int:
        """Count meaningful words (3+ characters) in text"""
        if not text:
            return 0

        words = text.split()
        meaningful_words = sum(1 for word in words if len(word) >= 3 and word.isalpha())

        return meaningful_words


# Global instance
easyocr_fallback = EasyOCRFallback()


def get_easyocr_fallback() -> EasyOCRFallback:
    """Get global EasyOCR fallback instance"""
    return easyocr_fallback


def should_use_easyocr_fallback(
    tesseract_text: str, tesseract_confidence: float
) -> bool:
    """Convenience function to check if EasyOCR fallback should be used"""
    return easyocr_fallback.should_use_fallback(tesseract_text, tesseract_confidence)


def process_with_easyocr_fallback(
    image_bytes: bytes, confidence_threshold: float = 0.3
) -> dict[str, any]:
    """Convenience function to process image with EasyOCR fallback"""
    return easyocr_fallback.process_image(image_bytes, confidence_threshold)
