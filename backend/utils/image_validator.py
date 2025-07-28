"""
Enhanced image validation utility for receipt processing
"""

import io
import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ImageValidator:
    """Advanced image validation and preprocessing for receipt images"""

    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.min_resolution = (300, 300)
        self.max_resolution = (4000, 4000)
        self.supported_formats = ["JPEG", "PNG", "WEBP", "TIFF"]
        self.min_brightness = 50
        self.max_brightness = 250

    def validate_image(self, image_bytes: bytes, filename: str = "") -> dict[str, Any]:
        """
        Comprehensive image validation for receipt processing

        Args:
            image_bytes: Raw image bytes
            filename: Original filename (optional)

        Returns:
            Dict with validation results and recommendations
        """
        try:
            # Basic file size check
            if len(image_bytes) > self.max_file_size:
                return {
                    "valid": False,
                    "error": "FILE_TOO_LARGE",
                    "message": f"Plik jest za duży ({len(image_bytes)/(1024*1024):.1f}MB). Maksymalny rozmiar to {self.max_file_size/(1024*1024)}MB.",
                    "suggestions": ["Skompresuj obraz", "Zmniejsz rozdzielczość"],
                }

            # Try to load image
            try:
                image = Image.open(io.BytesIO(image_bytes))
            except Exception:
                return {
                    "valid": False,
                    "error": "INVALID_IMAGE",
                    "message": "Nie można odczytać obrazu. Sprawdź czy plik nie jest uszkodzony.",
                    "suggestions": [
                        "Sprawdź format pliku",
                        "Spróbuj ponownie zrobić zdjęcie",
                    ],
                }

            # Format validation
            if image.format not in self.supported_formats:
                return {
                    "valid": False,
                    "error": "UNSUPPORTED_FORMAT",
                    "message": f'Nieobsługiwany format: {image.format}. Obsługiwane formaty: {", ".join(self.supported_formats)}',
                    "suggestions": ["Konwertuj na JPEG lub PNG"],
                }

            # Resolution validation
            width, height = image.size
            if width < self.min_resolution[0] or height < self.min_resolution[1]:
                return {
                    "valid": False,
                    "error": "RESOLUTION_TOO_LOW",
                    "message": f"Rozdzielczość za niska: {width}x{height}. Minimalna: {self.min_resolution[0]}x{self.min_resolution[1]}",
                    "suggestions": [
                        "Zrób zdjęcie z wyższą rozdzielczością",
                        "Zbliż się do paragonu",
                    ],
                }

            if width > self.max_resolution[0] or height > self.max_resolution[1]:
                return {
                    "valid": False,
                    "error": "RESOLUTION_TOO_HIGH",
                    "message": f"Rozdzielczość za wysoka: {width}x{height}. Maksymalna: {self.max_resolution[0]}x{self.max_resolution[1]}",
                    "suggestions": ["Zmniejsz rozdzielczość obrazu"],
                }

            # Image quality assessment
            quality_score = self._assess_image_quality(image)

            # Brightness check
            brightness = self._calculate_brightness(image)
            brightness_issues = []
            if brightness < self.min_brightness:
                brightness_issues.append("Obraz za ciemny")
            elif brightness > self.max_brightness:
                brightness_issues.append("Obraz za jasny")

            # Blur detection
            blur_score = self._detect_blur(image)

            # Text detection confidence
            text_confidence = self._estimate_text_confidence(image)

            # Compile results
            issues = []
            recommendations = []

            if quality_score < 0.3:
                issues.append("Niska jakość obrazu")
                recommendations.append("Popraw oświetlenie")

            if brightness_issues:
                issues.extend(brightness_issues)
                recommendations.append("Dostosuj oświetlenie")

            if blur_score > 0.7:
                issues.append("Obraz rozmyty")
                recommendations.append("Ustabilizuj telefon podczas robienia zdjęcia")

            if text_confidence < 0.4:
                issues.append("Trudno rozpoznawalny tekst")
                recommendations.append("Zrób zdjęcie z bliższej odległości")

            # Determine if image is acceptable
            is_valid = len(issues) == 0 or (
                quality_score > 0.5 and text_confidence > 0.5
            )

            return {
                "valid": is_valid,
                "quality_score": quality_score,
                "brightness": brightness,
                "blur_score": blur_score,
                "text_confidence": text_confidence,
                "resolution": (width, height),
                "file_size_mb": len(image_bytes) / (1024 * 1024),
                "format": image.format,
                "issues": issues,
                "recommendations": recommendations,
                "message": (
                    "Obraz jest dobrej jakości"
                    if is_valid
                    else "Obraz wymaga poprawy jakości"
                ),
            }

        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return {
                "valid": False,
                "error": "VALIDATION_ERROR",
                "message": f"Błąd podczas walidacji obrazu: {e!s}",
                "suggestions": ["Spróbuj ponownie", "Sprawdź format pliku"],
            }

    def _assess_image_quality(self, image: Image.Image) -> float:
        """Assess overall image quality using multiple metrics"""
        try:
            # Convert to grayscale for analysis
            gray = np.array(image.convert("L"))

            # Calculate sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000, 1.0)

            # Calculate contrast
            contrast = gray.std()
            contrast_score = min(contrast / 50, 1.0)

            # Calculate noise level (inverse of quality)
            noise_level = np.mean(cv2.bilateralFilter(gray, 9, 75, 75) - gray) ** 2
            noise_score = max(0, 1 - noise_level / 100)

            # Combine metrics
            quality_score = (
                sharpness_score * 0.4 + contrast_score * 0.3 + noise_score * 0.3
            )

            return min(max(quality_score, 0), 1)

        except Exception as e:
            logger.warning(f"Error assessing image quality: {e}")
            return 0.5

    def _calculate_brightness(self, image: Image.Image) -> float:
        """Calculate average brightness of the image"""
        try:
            gray = np.array(image.convert("L"))
            return np.mean(gray)
        except Exception:
            return 128  # Default middle brightness

    def _detect_blur(self, image: Image.Image) -> float:
        """Detect image blur using Laplacian variance"""
        try:
            gray = np.array(image.convert("L"))
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            # Lower variance indicates more blur
            # Normalize to 0-1 where 1 is very blurry
            blur_score = max(0, 1 - laplacian_var / 1000)
            return min(blur_score, 1)
        except Exception:
            return 0.5

    def _estimate_text_confidence(self, image: Image.Image) -> float:
        """Estimate how well OCR would perform on this image"""
        try:
            gray = np.array(image.convert("L"))

            # Edge detection for text-like structures
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.count_nonzero(edges) / edges.size

            # Text regions typically have specific characteristics
            # This is a simplified heuristic
            text_score = min(edge_density * 10, 1.0)

            return text_score

        except Exception:
            return 0.5

    def get_optimization_suggestions(
        self, validation_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate specific suggestions for image optimization"""
        suggestions = {"preprocessing": [], "capture_tips": [], "immediate_actions": []}

        if not validation_result.get("valid", False):
            error_code = validation_result.get("error", "")

            if error_code == "FILE_TOO_LARGE":
                suggestions["immediate_actions"].append(
                    "Kompresuj obraz do formatu JPEG z jakością 85%"
                )
                suggestions["preprocessing"].append("Automatyczna kompresja")

            elif error_code == "RESOLUTION_TOO_LOW":
                suggestions["capture_tips"].append("Trzymaj telefon bliżej paragonu")
                suggestions["capture_tips"].append("Użyj głównego aparatu, nie selfie")

            elif error_code == "RESOLUTION_TOO_HIGH":
                suggestions["preprocessing"].append(
                    "Zmniejsz rozdzielczość do 2000x2000px"
                )

            elif validation_result.get("brightness", 128) < 80:
                suggestions["capture_tips"].append(
                    "Włącz latarkę lub znajdź lepsze oświetlenie"
                )
                suggestions["preprocessing"].append("Automatyczna korekta jasności")

            elif validation_result.get("blur_score", 0) > 0.6:
                suggestions["capture_tips"].append("Trzymaj telefon stabilnie")
                suggestions["capture_tips"].append("Użyj timer lub przycisk głośności")

            elif validation_result.get("text_confidence", 0) < 0.4:
                suggestions["capture_tips"].append("Upewnij się, że tekst jest wyraźny")
                suggestions["capture_tips"].append("Zrób zdjęcie pod prostym kątem")

        return suggestions

    def auto_enhance_image(self, image_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
        """Automatically enhance image quality for better OCR"""
        try:
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Convert to numpy array for processing
            img_array = np.array(image)

            # Apply enhancements
            enhanced_array = self._apply_enhancements(img_array)

            # Convert back to PIL Image
            enhanced_image = Image.fromarray(enhanced_array)

            # Save to bytes
            output = io.BytesIO()
            enhanced_image.save(output, format="JPEG", quality=90, optimize=True)
            enhanced_bytes = output.getvalue()

            return enhanced_bytes, {
                "success": True,
                "original_size": len(image_bytes),
                "enhanced_size": len(enhanced_bytes),
                "compression_ratio": len(enhanced_bytes) / len(image_bytes),
                "enhancements_applied": [
                    "Noise reduction",
                    "Contrast enhancement",
                    "Sharpening",
                    "Compression optimization",
                ],
            }

        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image_bytes, {
                "success": False,
                "error": str(e),
                "message": "Nie udało się poprawić jakości obrazu",
            }

    def _apply_enhancements(self, img_array: np.ndarray) -> np.ndarray:
        """Apply various image enhancements"""
        try:
            # Noise reduction
            img_array = cv2.bilateralFilter(img_array, 9, 75, 75)

            # Contrast enhancement using CLAHE
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            img_array = cv2.merge([l, a, b])
            img_array = cv2.cvtColor(img_array, cv2.COLOR_LAB2RGB)

            # Slight sharpening
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(img_array, -1, kernel)
            img_array = cv2.addWeighted(img_array, 0.7, sharpened, 0.3, 0)

            # Ensure values are in valid range
            img_array = np.clip(img_array, 0, 255)

            return img_array.astype(np.uint8)

        except Exception as e:
            logger.error(f"Error applying enhancements: {e}")
            return img_array
