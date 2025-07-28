"""
Image Preprocessing Agent

Specialized agent for preprocessing receipt images to improve OCR accuracy.
Implements advanced image processing techniques optimized for Polish receipts.
"""

import io
import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageEnhance

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType

logger = logging.getLogger(__name__)


class ImagePreprocessingAgent(BaseOCRAgentImpl):
    """
    Advanced image preprocessing agent for receipt OCR.

    Implements sophisticated image processing techniques:
    - Deskewing (perspective correction)
    - Noise removal and denoising
    - Resolution enhancement
    - Contrast and brightness adjustment
    - Adaptive thresholding
    - Receipt-specific optimizations
    """

    def __init__(self, name: str = "ImagePreprocessingAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=15.0, **kwargs)

        # Preprocessing configuration
        self.config = {
            "deskew_enabled": True,
            "noise_removal_enabled": True,
            "contrast_enhancement": True,
            "sharpening_enabled": True,
            "adaptive_threshold": True,
            "receipt_optimization": True,
            "max_image_size": (1920, 1080),
            "min_confidence": 0.7,
        }

        # Polish receipt-specific settings
        self.polish_receipt_config = {
            "expected_aspect_ratio": (2.5, 4.0),  # Typical receipt aspect ratios
            "text_region_margin": 0.05,  # 5% margin for text regions
            "min_text_height": 8,  # Minimum text height in pixels
            "max_text_height": 50,  # Maximum text height in pixels
        }

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data for image preprocessing"""
        required_keys = ["image_bytes"]

        if not all(key in input_data for key in required_keys):
            return False

        if not isinstance(input_data["image_bytes"], bytes):
            return False

        # Check if image can be opened
        try:
            image = Image.open(io.BytesIO(input_data["image_bytes"]))
            image.verify()
            return True
        except Exception:
            return False

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Process image through preprocessing pipeline"""
        try:
            image_bytes = input_data["image_bytes"]

            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Apply preprocessing pipeline
            processed_image = await self._apply_preprocessing_pipeline(image)

            # Convert back to bytes
            output_buffer = io.BytesIO()
            processed_image.save(output_buffer, format="PNG")
            processed_bytes = output_buffer.getvalue()

            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(
                image, processed_image
            )

            # Publish preprocessing event
            await self.publish_event(
                OCREventType.IMAGE_PREPROCESSED,
                {
                    "original_size": image.size,
                    "processed_size": processed_image.size,
                    "quality_metrics": quality_metrics,
                },
            )

            return AgentResponse(
                success=True,
                text="Image preprocessing completed successfully",
                metadata={
                    "original_size": image.size,
                    "processed_size": processed_image.size,
                    "quality_metrics": quality_metrics,
                    "preprocessing_steps": list(self.config.keys()),
                },
                data={
                    "processed_image_bytes": processed_bytes,
                    "quality_metrics": quality_metrics,
                },
            )

        except Exception as e:
            logger.error(f"Error in image preprocessing: {e}")
            return AgentResponse(
                success=False, error=f"Image preprocessing failed: {e!s}"
            )

    async def _apply_preprocessing_pipeline(self, image: Image.Image) -> Image.Image:
        """Apply complete preprocessing pipeline"""
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 1. Deskewing (perspective correction)
        if self.config["deskew_enabled"]:
            image = await self._deskew_image(image)

        # 2. Noise removal
        if self.config["noise_removal_enabled"]:
            image = await self._remove_noise(image)

        # 3. Contrast enhancement
        if self.config["contrast_enhancement"]:
            image = await self._enhance_contrast(image)

        # 4. Sharpening
        if self.config["sharpening_enabled"]:
            image = await self._sharpen_image(image)

        # 5. Adaptive thresholding
        if self.config["adaptive_threshold"]:
            image = await self._apply_adaptive_threshold(image)

        # 6. Receipt-specific optimizations
        if self.config["receipt_optimization"]:
            image = await self._optimize_for_receipt(image)

        # 7. Resize if needed
        image = await self._resize_if_needed(image)

        return image

    async def _deskew_image(self, image: Image.Image) -> Image.Image:
        """Apply deskewing to correct perspective distortion"""
        try:
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Find contours
            _, binary = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                # Find the largest contour (assumed to be the receipt)
                largest_contour = max(contours, key=cv2.contourArea)

                # Get bounding rectangle
                rect = cv2.minAreaRect(largest_contour)
                box = cv2.boxPoints(rect)
                box = box.astype(np.int32)

                # Get width and height of the detected rectangle
                width = int(rect[1][0])
                height = int(rect[1][1])

                # Order points for perspective transform
                src_pts = box.astype("float32")
                dst_pts = np.array(
                    [[0, height - 1], [0, 0], [width - 1, 0], [width - 1, height - 1]],
                    dtype="float32",
                )

                # Calculate perspective transform matrix
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

                # Apply perspective transform
                warped = cv2.warpPerspective(cv_image, matrix, (width, height))

                # Convert back to PIL
                warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                return Image.fromarray(warped_rgb)

            return image

        except Exception as e:
            logger.warning(f"Deskewing failed: {e}, returning original image")
            return image

    async def _remove_noise(self, image: Image.Image) -> Image.Image:
        """Remove noise from image"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Apply bilateral filter for noise removal while preserving edges
            denoised = cv2.bilateralFilter(cv_image, 9, 75, 75)

            # Convert back to PIL
            denoised_rgb = cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)
            return Image.fromarray(denoised_rgb)

        except Exception as e:
            logger.warning(f"Noise removal failed: {e}, returning original image")
            return image

    async def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance contrast and brightness"""
        try:
            # Convert to grayscale for contrast enhancement
            gray = image.convert("L")

            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            cv_gray = np.array(gray)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(cv_gray)

            # Convert back to PIL
            return Image.fromarray(enhanced)

        except Exception as e:
            logger.warning(
                f"Contrast enhancement failed: {e}, returning original image"
            )
            return image

    async def _sharpen_image(self, image: Image.Image) -> Image.Image:
        """Sharpen image for better text clarity"""
        try:
            # Apply unsharp mask
            enhancer = ImageEnhance.Sharpness(image)
            sharpened = enhancer.enhance(1.5)

            return sharpened

        except Exception as e:
            logger.warning(f"Sharpening failed: {e}, returning original image")
            return image

    async def _apply_adaptive_threshold(self, image: Image.Image) -> Image.Image:
        """Apply adaptive thresholding for better text extraction"""
        try:
            # Convert to grayscale
            gray = image.convert("L")
            cv_gray = np.array(gray)

            # Apply adaptive threshold
            adaptive_thresh = cv2.adaptiveThreshold(
                cv_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            return Image.fromarray(adaptive_thresh)

        except Exception as e:
            logger.warning(
                f"Adaptive thresholding failed: {e}, returning original image"
            )
            return image

    async def _optimize_for_receipt(self, image: Image.Image) -> Image.Image:
        """Apply receipt-specific optimizations"""
        try:
            # Detect receipt boundaries
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Apply morphological operations to clean up text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # Convert back to PIL
            cleaned_rgb = cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB)
            return Image.fromarray(cleaned_rgb)

        except Exception as e:
            logger.warning(
                f"Receipt optimization failed: {e}, returning original image"
            )
            return image

    async def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """Resize image if it exceeds maximum dimensions"""
        max_width, max_height = self.config["max_image_size"]

        if image.width > max_width or image.height > max_height:
            # Calculate new size maintaining aspect ratio
            ratio = min(max_width / image.width, max_height / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))

            # Resize with high quality
            resized = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {image.size} to {resized.size}")
            return resized

        return image

    async def _calculate_quality_metrics(
        self, original: Image.Image, processed: Image.Image
    ) -> dict[str, float]:
        """Calculate quality metrics for preprocessing"""
        try:
            # Convert to grayscale for analysis
            orig_gray = np.array(original.convert("L"))
            proc_gray = np.array(processed.convert("L"))

            # Calculate metrics
            metrics = {
                "contrast_improvement": self._calculate_contrast_improvement(
                    orig_gray, proc_gray
                ),
                "sharpness_improvement": self._calculate_sharpness_improvement(
                    orig_gray, proc_gray
                ),
                "noise_reduction": self._calculate_noise_reduction(
                    orig_gray, proc_gray
                ),
                "overall_quality_score": 0.0,
            }

            # Calculate overall quality score
            metrics["overall_quality_score"] = (
                metrics["contrast_improvement"] * 0.4
                + metrics["sharpness_improvement"] * 0.3
                + metrics["noise_reduction"] * 0.3
            )

            return metrics

        except Exception as e:
            logger.warning(f"Quality metrics calculation failed: {e}")
            return {
                "contrast_improvement": 0.0,
                "sharpness_improvement": 0.0,
                "noise_reduction": 0.0,
                "overall_quality_score": 0.0,
            }

    def _calculate_contrast_improvement(
        self, original: np.ndarray, processed: np.ndarray
    ) -> float:
        """Calculate contrast improvement"""
        try:
            orig_std = np.std(original)
            proc_std = np.std(processed)

            if orig_std == 0:
                return 0.0

            improvement = (proc_std - orig_std) / orig_std
            return float(max(0.0, min(1.0, improvement)))
        except:
            return 0.0

    def _calculate_sharpness_improvement(
        self, original: np.ndarray, processed: np.ndarray
    ) -> float:
        """Calculate sharpness improvement using Laplacian variance"""
        try:
            orig_laplacian = cv2.Laplacian(original, cv2.CV_64F).var()
            proc_laplacian = cv2.Laplacian(processed, cv2.CV_64F).var()

            if orig_laplacian == 0:
                return 0.0

            improvement = (proc_laplacian - orig_laplacian) / orig_laplacian
            return float(max(0.0, min(1.0, improvement)))
        except:
            return 0.0

    def _calculate_noise_reduction(
        self, original: np.ndarray, processed: np.ndarray
    ) -> float:
        """Calculate noise reduction using FFT"""
        try:
            # Calculate FFT
            orig_fft = np.fft.fft2(original)
            proc_fft = np.fft.fft2(processed)

            # Calculate magnitude spectrum
            orig_magnitude = np.abs(orig_fft)
            proc_magnitude = np.abs(proc_fft)

            # Calculate noise reduction (simplified)
            orig_noise = np.std(orig_magnitude)
            proc_noise = np.std(proc_magnitude)

            if orig_noise == 0:
                return 0.0

            reduction = (orig_noise - proc_noise) / orig_noise
            return max(0.0, min(1.0, reduction))
        except:
            return 0.0
