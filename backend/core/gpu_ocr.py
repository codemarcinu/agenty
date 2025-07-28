"""
GPU-accelerated OCR processing
Provides optimized OCR processing using GPU acceleration
"""

import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image

from core.exceptions import FoodSaveError
from core.ocr import OCRResult

logger = logging.getLogger(__name__)


class GPUOCRProcessor:
    """GPU-accelerated OCR processor with optimizations"""

    def __init__(self, use_gpu: bool = True, gpu_device: int = 0):
        """
        Initialize GPU OCR processor

        Args:
            use_gpu: Whether to use GPU acceleration
            gpu_device: GPU device ID
        """
        self.use_gpu = use_gpu and self._check_gpu_availability()
        self.gpu_device = gpu_device
        self.initialized = False

        if self.use_gpu:
            self._initialize_gpu()

    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available for processing"""
        try:
            # Check CUDA availability
            if hasattr(cv2, "cuda") and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                logger.info("CUDA GPU detected and available")
                return True

            # Check OpenCL availability
            if hasattr(cv2, "ocl") and cv2.ocl.useOpenCL():
                logger.info("OpenCL GPU detected and available")
                return True

            logger.warning("No GPU acceleration available, falling back to CPU")
            return False

        except Exception as e:
            logger.warning(f"GPU detection failed: {e}, falling back to CPU")
            return False

    def _initialize_gpu(self) -> None:
        """Initialize GPU for processing"""
        try:
            if hasattr(cv2, "cuda"):
                # Set CUDA device
                cv2.cuda.setDevice(self.gpu_device)
                logger.info(f"Initialized CUDA GPU device {self.gpu_device}")
            elif hasattr(cv2, "ocl"):
                # Enable OpenCL
                cv2.ocl.setUseOpenCL(True)
                logger.info("Initialized OpenCL GPU acceleration")

            self.initialized = True

        except Exception as e:
            logger.error(f"GPU initialization failed: {e}")
            self.use_gpu = False
            self.initialized = False

    def process_image_gpu(
        self, image_bytes: bytes, config: str | None = None
    ) -> OCRResult:
        """
        Process image with GPU acceleration

        Args:
            image_bytes: Image data
            config: Tesseract configuration

        Returns:
            OCRResult with extracted text
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise FoodSaveError("Failed to decode image")

            # GPU-accelerated preprocessing
            processed_image = self._preprocess_image_gpu(image)

            # Convert back to PIL for Tesseract
            pil_image = Image.fromarray(
                cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
            )

            # Use standard OCR with preprocessed image
            import pytesseract

            config = config or "--oem 1 --psm 6"

            # Extract text with GPU-optimized image
            text = pytesseract.image_to_string(pil_image, config=config)

            # Get confidence data
            data = pytesseract.image_to_data(
                pil_image, config=config, output_type=pytesseract.Output.DICT
            )
            avg_conf = (
                sum(conf for conf in data["conf"] if conf > 0) / len(data["conf"])
                if data["conf"]
                else 0
            )

            return OCRResult(
                text=text.strip(),
                confidence=avg_conf,
                metadata={
                    "gpu_accelerated": self.use_gpu,
                    "gpu_device": self.gpu_device if self.use_gpu else None,
                    "preprocessing_method": "gpu_optimized" if self.use_gpu else "cpu",
                },
            )

        except Exception as e:
            logger.error(f"GPU OCR processing failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                metadata={
                    "gpu_accelerated": self.use_gpu,
                    "error": f"GPU OCR processing failed: {e}",
                },
            )

    def _preprocess_image_gpu(self, image: np.ndarray) -> np.ndarray:
        """
        GPU-accelerated image preprocessing

        Args:
            image: Input image as numpy array

        Returns:
            Preprocessed image
        """
        try:
            if not self.use_gpu or not self.initialized:
                # Fallback to CPU preprocessing
                return self._preprocess_image_cpu(image)

            # GPU-accelerated preprocessing pipeline
            processed = image.copy()

            # 1. GPU-accelerated resize to 300 DPI
            if hasattr(cv2, "cuda"):
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(processed)

                # Calculate target size for 300 DPI
                height, width = processed.shape[:2]
                target_dpi = 300
                scale_factor = target_dpi / 96  # Assuming 96 DPI base
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)

                # GPU resize
                gpu_resized = cv2.cuda.resize(gpu_image, (new_width, new_height))
                processed = gpu_resized.download()
            else:
                # CPU resize
                height, width = processed.shape[:2]
                target_dpi = 300
                scale_factor = target_dpi / 96
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                processed = cv2.resize(processed, (new_width, new_height))

            # 2. GPU-accelerated grayscale conversion
            if hasattr(cv2, "cuda"):
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(processed)
                gpu_gray = cv2.cuda.cvtColor(gpu_image, cv2.COLOR_BGR2GRAY)
                processed = gpu_gray.download()
            else:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

            # 3. GPU-accelerated adaptive threshold
            if hasattr(cv2, "cuda"):
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(processed)

                # GPU adaptive threshold
                gpu_thresh = cv2.cuda.adaptiveThreshold(
                    gpu_image,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2,
                )
                processed = gpu_thresh.download()
            else:
                processed = cv2.adaptiveThreshold(
                    processed,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2,
                )

            # 4. GPU-accelerated noise reduction
            if hasattr(cv2, "cuda"):
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(processed)

                # GPU morphological operations
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                gpu_kernel = cv2.cuda_GpuMat()
                gpu_kernel.upload(kernel)

                gpu_denoised = cv2.cuda.morphologyEx(
                    gpu_image, cv2.MORPH_CLOSE, gpu_kernel
                )
                processed = gpu_denoised.download()
            else:
                # CPU noise reduction
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

            return processed

        except Exception as e:
            logger.warning(f"GPU preprocessing failed: {e}, falling back to CPU")
            return self._preprocess_image_cpu(image)

    def _preprocess_image_cpu(self, image: np.ndarray) -> np.ndarray:
        """
        CPU fallback for image preprocessing

        Args:
            image: Input image as numpy array

        Returns:
            Preprocessed image
        """
        processed = image.copy()

        # 1. Resize to 300 DPI
        height, width = processed.shape[:2]
        target_dpi = 300
        scale_factor = target_dpi / 96
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        processed = cv2.resize(processed, (new_width, new_height))

        # 2. Grayscale conversion
        processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # 3. Adaptive threshold
        processed = cv2.adaptiveThreshold(
            processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # 4. Noise reduction
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

        return processed

    def process_images_batch_gpu(
        self, images: list[bytes], config: str | None = None
    ) -> list[OCRResult]:
        """
        Process multiple images with GPU acceleration

        Args:
            images: List of image data
            config: Tesseract configuration

        Returns:
            List of OCR results
        """
        results = []

        for i, image_bytes in enumerate(images):
            logger.info(f"Processing image {i+1}/{len(images)} with GPU acceleration")
            result = self.process_image_gpu(image_bytes, config)
            results.append(result)

        return results

    def get_gpu_info(self) -> dict[str, Any]:
        """Get GPU information and status"""
        info = {
            "gpu_available": self.use_gpu,
            "gpu_initialized": self.initialized,
            "gpu_device": self.gpu_device if self.use_gpu else None,
        }

        if self.use_gpu:
            try:
                if hasattr(cv2, "cuda"):
                    device_count = cv2.cuda.getCudaEnabledDeviceCount()
                    info.update(
                        {
                            "cuda_devices": device_count,
                            "cuda_version": cv2.cuda.getCudaVersion(),
                        }
                    )
                elif hasattr(cv2, "ocl"):
                    info.update(
                        {
                            "opencl_available": True,
                            "opencl_version": cv2.ocl.getOpenCLVersion(),
                        }
                    )
            except Exception as e:
                info["gpu_error"] = str(e)

        return info


# Global GPU OCR processor instance
gpu_ocr_processor = GPUOCRProcessor()


class GPUOptimizedOCRAgent:
    """GPU-optimized OCR agent wrapper"""

    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu
        self.processor = GPUOCRProcessor(use_gpu=use_gpu)

    def process_image(self, image_bytes: bytes, config: str | None = None) -> OCRResult:
        """
        Process image with GPU optimization

        Args:
            image_bytes: Image data
            config: Tesseract configuration

        Returns:
            OCR result
        """
        return self.processor.process_image_gpu(image_bytes, config)

    def process_batch(
        self, images: list[bytes], config: str | None = None
    ) -> list[OCRResult]:
        """
        Process batch of images with GPU optimization

        Args:
            images: List of image data
            config: Tesseract configuration

        Returns:
            List of OCR results
        """
        return self.processor.process_images_batch_gpu(images, config)

    def get_gpu_status(self) -> dict[str, Any]:
        """Get GPU status and information"""
        return self.processor.get_gpu_info()
