"""
Testy dla zaawansowanego preprocessingu OCR z detekcją konturów, korekcją perspektywy i adaptacyjnym progowaniem.
"""

import io
from typing import Any
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image
import pytest

from backend.core.ocr import OCRProcessor


class TestOCRAdvancedPreprocessing:
    """Testy dla zaawansowanego preprocessingu OCR."""

    @pytest.fixture
    def ocr_processor(self) -> OCRProcessor:
        """Tworzy instancję OCRProcessor do testów."""
        return OCRProcessor()

    @pytest.fixture
    def sample_receipt_image(self) -> Image.Image:
        """Tworzy przykładowy obraz paragonu z konturami."""
        # Tworzy obraz z prostokątnym konturem paragonu
        image = Image.new("RGB", (400, 300), color="white")
        # Dodaj prostokątny kontur paragonu
        for x in range(50, 350):
            for y in range(30, 270):
                if x in {50, 349} or y in {30, 269}:
                    image.putpixel((x, y), (0, 0, 0))
        return image

    @pytest.fixture
    def sample_receipt_image_bytes(self) -> bytes:
        """Tworzy bajty przykładowego obrazu paragonu."""
        image = Image.new("RGB", (400, 300), color="white")
        # Dodaj tekst paragonu
        for x in range(100, 300):
            for y in range(100, 200):
                if x % 20 == 0 or y % 20 == 0:
                    image.putpixel((x, y), (0, 0, 0))

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()

    def test_enhanced_contour_detection(
        self, ocr_processor: OCRProcessor, sample_receipt_image: Image.Image
    ) -> None:
        """Test ulepszonej detekcji konturów paragonu."""
        # Mock OpenCV functions
        with patch("backend.core.ocr.cv2") as mock_cv2:
            # Mock contour detection
            mock_contours = [
                np.array([[50, 30], [350, 30], [350, 270], [50, 270]], dtype=np.int32)
            ]
            mock_cv2.findContours.return_value = (mock_contours, None)
            mock_cv2.contourArea.return_value = 80000  # Duży obszar
            mock_cv2.arcLength.return_value = 1000
            mock_cv2.approxPolyDP.return_value = np.array(
                [[50, 30], [350, 30], [350, 270], [50, 270]], dtype=np.int32
            )
            mock_cv2.boundingRect.return_value = (50, 30, 300, 240)

            # Mock image conversion
            mock_cv2.cvtColor.return_value = np.array(sample_receipt_image)
            mock_cv2.COLOR_RGB2GRAY = 7

            # Convert PIL Image to numpy array
            image_array = np.array(sample_receipt_image)
            result = ocr_processor._detect_receipt_contour(image_array)

            assert result is not None
            assert len(result) == 4  # 4 punkty dla prostokąta
            mock_cv2.findContours.assert_called_once()

    def test_contour_detection_fallback_to_bounding_rect(
        self, ocr_processor: OCRProcessor, sample_receipt_image: Image.Image
    ) -> None:
        """Test fallback do minimalnego prostokąta ograniczającego."""
        with patch("backend.core.ocr.cv2") as mock_cv2:
            # Mock brak konturów
            mock_cv2.findContours.return_value = ([], None)
            mock_cv2.boundingRect.return_value = (0, 0, 400, 300)

            # Mock image conversion
            mock_cv2.cvtColor.return_value = np.array(sample_receipt_image)
            mock_cv2.COLOR_RGB2GRAY = 7

            # Convert PIL Image to numpy array
            image_array = np.array(sample_receipt_image)
            result = ocr_processor._detect_receipt_contour(image_array)

            assert result is not None
            # Powinien zwrócić prostokąt ograniczający cały obraz
            assert len(result) == 4

    def test_perspective_correction(self, ocr_processor: OCRProcessor) -> None:
        """Test korekcji perspektywy."""
        # Mock OpenCV functions
        with patch("backend.core.ocr.cv2") as mock_cv2:
            # Mock perspective transform
            mock_cv2.getPerspectiveTransform.return_value = np.eye(3)
            mock_cv2.warpPerspective.return_value = np.array(
                Image.new("RGB", (400, 300), "white")
            )

            # Mock contour points
            contour_points = np.array(
                [[50, 30], [350, 30], [350, 270], [50, 270]], dtype=np.int32
            )

            result = ocr_processor._perspective_correction(
                np.array(Image.new("RGB", (400, 300), "white")), contour_points
            )

            assert result is not None
            mock_cv2.getPerspectiveTransform.assert_called_once()
            mock_cv2.warpPerspective.assert_called_once()

    def test_adaptive_thresholding_clahe(self, ocr_processor: OCRProcessor) -> None:
        """Test adaptacyjnego progowania z CLAHE."""
        with patch("backend.core.ocr.cv2") as mock_cv2:
            # Mock CLAHE
            mock_clahe = Mock()
            mock_cv2.createCLAHE.return_value = mock_clahe
            mock_clahe.apply.return_value = np.array(Image.new("L", (400, 300), 128))

            # Mock morphological operations
            mock_cv2.morphologyEx.return_value = np.array(
                Image.new("L", (400, 300), 128)
            )
            mock_cv2.MORPH_CLOSE = 3
            mock_cv2.getStructuringElement.return_value = np.ones((3, 3))
            mock_cv2.MORPH_RECT = 0

            image = Image.new("L", (400, 300), 128)
            result = ocr_processor._adaptive_threshold(np.array(image))

            assert result is not None
            mock_cv2.createCLAHE.assert_called_once_with(
                clipLimit=2.0, tileGridSize=(8, 8)
            )
            mock_clahe.apply.assert_called_once()

    def test_300_dpi_scaling(self, ocr_processor: OCRProcessor) -> None:
        """Test skalowania do 300 DPI."""
        # Tworzy mały obraz
        small_image = Image.new("RGB", (200, 150), "white")
        small_image_array = np.array(small_image)

        result = ocr_processor._scale_to_300_dpi(small_image_array)

        # Sprawdź czy obraz został powiększony (result is numpy array)
        assert result.shape[1] > small_image.size[0]  # width
        assert result.shape[0] > small_image.size[1]  # height

        # Sprawdź czy proporcje zostały zachowane
        original_ratio = small_image.size[0] / small_image.size[1]
        result_ratio = result.shape[1] / result.shape[0]  # width/height
        assert abs(original_ratio - result_ratio) < 0.1

    def test_contrast_enhancement(self, ocr_processor: OCRProcessor) -> None:
        """Test zwiększania kontrastu."""
        # Tworzy obraz o niskim kontraście
        low_contrast_image = Image.new("RGB", (100, 100), (128, 128, 128))
        low_contrast_array = np.array(low_contrast_image)

        result = ocr_processor._enhance_contrast_and_sharpness(low_contrast_array)

        assert result is not None
        assert result.shape == low_contrast_array.shape

    def test_sharpness_enhancement(self, ocr_processor: OCRProcessor) -> None:
        """Test zwiększania ostrości."""
        # Tworzy rozmyty obraz
        blurry_image = Image.new("RGB", (100, 100), "white")
        blurry_array = np.array(blurry_image)

        result = ocr_processor._enhance_contrast_and_sharpness(blurry_array)

        assert result is not None
        assert result.shape == blurry_array.shape

    def test_lstm_engine_configuration(self, ocr_processor: OCRProcessor) -> None:
        """Test konfiguracji silnika LSTM."""
        config = ocr_processor._get_default_receipt_config()

        # Sprawdź czy używa LSTM engine
        assert "--oem 3" in config  # Default engine mode
        assert "--psm 6" in config  # Uniform block of text
        assert "-l pol" in config  # Polish language

    @patch("backend.core.ocr.pytesseract")
    def test_process_image_with_advanced_preprocessing(
        self,
        mock_tesseract: Any,
        ocr_processor: OCRProcessor,
        sample_receipt_image_bytes: bytes,
    ) -> None:
        """Test przetwarzania obrazu z zaawansowanym preprocessingiem."""
        # Mock odpowiedzi Tesseract
        mock_data = {
            "text": ["Lidl", "Mleko 3.2% 1L 4,99 PLN", "RAZEM 4,99 PLN"],
            "conf": [95, 90, 85],
        }
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        # Mock OpenCV functions
        with patch("backend.core.ocr.cv2") as mock_cv2:
            mock_cv2.findContours.return_value = ([], None)
            mock_cv2.boundingRect.return_value = (0, 0, 400, 300)
            mock_cv2.cvtColor.return_value = np.array(
                Image.new("RGB", (400, 300), "white")
            )
            mock_cv2.COLOR_RGB2GRAY = 7
            mock_cv2.getPerspectiveTransform.return_value = np.eye(3)
            mock_cv2.warpPerspective.return_value = np.array(
                Image.new("RGB", (400, 300), "white")
            )
            mock_cv2.createCLAHE.return_value = Mock()
            mock_cv2.morphologyEx.return_value = np.array(
                Image.new("L", (400, 300), 128)
            )
            mock_cv2.MORPH_CLOSE = 3
            mock_cv2.getStructuringElement.return_value = np.ones((3, 3))
            mock_cv2.MORPH_RECT = 0

        result = ocr_processor.process_image(sample_receipt_image_bytes)

        assert result.text == "Lidl\nMleko 3.2% 1L 4,99 PLN\nRAZEM 4,99 PLN"
        assert result.confidence > 0
        assert result.metadata["preprocessing_applied"] is True
        assert "preprocessing_applied" in result.metadata
        assert result.metadata["preprocessing_applied"] is True

    def test_preprocessing_error_handling(self, ocr_processor: OCRProcessor) -> None:
        """Test obsługi błędów podczas preprocessingu."""
        # Symuluj błąd podczas detekcji konturów
        with patch("backend.core.ocr.cv2") as mock_cv2:
            mock_cv2.findContours.side_effect = Exception("OpenCV error")

            image = Image.new("RGB", (100, 100), "white")
            # Convert PIL Image to numpy array
            image_array = np.array(image)
            result = ocr_processor._detect_receipt_contour(image_array)

            # Powinien zwrócić fallback (prostokąt ograniczający cały obraz) w przypadku błędu
            assert result is not None
            assert len(result) == 4  # Prostokąt ma 4 punkty

    @patch("backend.core.ocr.pytesseract")
    def test_metadata_tracking(
        self, mock_tesseract: Any, ocr_processor: OCRProcessor
    ) -> None:
        """Test śledzenia metadanych preprocessingu."""
        # Mock Tesseract response
        mock_tesseract.image_to_data.return_value = {
            "text": ["Test"],
            "conf": [95],
        }
        mock_tesseract.Output.DICT = "dict"

        # Test that metadata is properly tracked in process_image
        image = Image.new("RGB", (400, 300), "white")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes = image_bytes.getvalue()
        result = ocr_processor.process_image(image_bytes)

        assert "preprocessing_applied" in result.metadata
        assert result.metadata["preprocessing_applied"] is True
        assert "preprocessing_steps" in result.metadata
        assert isinstance(result.metadata["preprocessing_steps"], list)

    @patch("backend.core.ocr.pytesseract")
    def test_confidence_distribution_calculation(
        self, mock_tesseract: Any, ocr_processor: OCRProcessor
    ) -> None:
        """Test obliczania rozkładu pewności."""
        # Mock Tesseract response
        mock_tesseract.image_to_data.return_value = {
            "text": ["Test", "Text"],
            "conf": [95, 85],
        }
        mock_tesseract.Output.DICT = "dict"

        # Test that confidence distribution is calculated in process_image
        image = Image.new("RGB", (400, 300), "white")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes = image_bytes.getvalue()
        result = ocr_processor.process_image(image_bytes)

        assert "confidence_distribution" in result.metadata
        distribution = result.metadata["confidence_distribution"]
        assert "high" in distribution
        assert "medium" in distribution
        assert "low" in distribution

    @patch("backend.core.ocr.pytesseract")
    def test_processing_time_tracking(
        self, mock_tesseract: Any, ocr_processor: OCRProcessor
    ) -> None:
        """Test śledzenia czasu przetwarzania."""
        # Mock Tesseract response
        mock_tesseract.image_to_data.return_value = {
            "text": ["Test"],
            "conf": [95],
        }
        mock_tesseract.Output.DICT = "dict"

        # Test that processing time is tracked in process_image
        image = Image.new("RGB", (400, 300), "white")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes = image_bytes.getvalue()
        result = ocr_processor.process_image(image_bytes)

        assert "processing_time_seconds" in result.metadata
        assert result.metadata["processing_time_seconds"] > 0

    @patch("backend.core.ocr.pytesseract")
    def test_polish_receipt_text_recognition(
        self,
        mock_tesseract: Any,
        ocr_processor: OCRProcessor,
        sample_receipt_image_bytes: bytes,
    ) -> None:
        """Test rozpoznawania polskiego tekstu paragonu."""
        # Mock polski tekst paragonu
        polish_text = [
            "Lidl sp. z o.o.",
            "Mleko 3,2% 1L 4,99 zł",
            "Chleb żytni 3,50 zł",
            "RAZEM: 8,49 zł",
            "NIP: 123-456-78-90",
        ]
        mock_data = {"text": polish_text, "conf": [95, 90, 88, 92, 85]}
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        # Mock OpenCV functions
        with patch("backend.core.ocr.cv2") as mock_cv2:
            mock_cv2.findContours.return_value = ([], None)
            mock_cv2.boundingRect.return_value = (0, 0, 400, 300)
            mock_cv2.cvtColor.return_value = np.array(
                Image.new("RGB", (400, 300), "white")
            )
            mock_cv2.COLOR_RGB2GRAY = 7
            mock_cv2.getPerspectiveTransform.return_value = np.eye(3)
            mock_cv2.warpPerspective.return_value = np.array(
                Image.new("RGB", (400, 300), "white")
            )
            mock_cv2.createCLAHE.return_value = Mock()
            mock_cv2.morphologyEx.return_value = np.array(
                Image.new("L", (400, 300), 128)
            )
            mock_cv2.MORPH_CLOSE = 3
            mock_cv2.getStructuringElement.return_value = np.ones((3, 3))
            mock_cv2.MORPH_RECT = 0

        result = ocr_processor.process_image(sample_receipt_image_bytes)

        # Sprawdź czy polskie znaki zostały poprawnie rozpoznane
        assert "Lidl sp. z o.o." in result.text
        assert "Mleko 3,2% 1L 4,99 zł" in result.text
        assert "Chleb żytni 3,50 zł" in result.text
        assert "RAZEM: 8,49 zł" in result.text
        assert "NIP: 123-456-78-90" in result.text
        assert result.metadata["language"] in ["eng", "pol"]

    @patch("backend.core.ocr.pytesseract")
    def test_image_quality_analysis(
        self, mock_tesseract: Any, ocr_processor: OCRProcessor
    ) -> None:
        """Test analizy jakości obrazu."""
        # Mock Tesseract response
        mock_tesseract.image_to_data.return_value = {
            "text": ["Test"],
            "conf": [95],
        }
        mock_tesseract.Output.DICT = "dict"

        # Test that image quality analysis is handled in process_image
        image = Image.new("RGB", (400, 300), "white")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes = image_bytes.getvalue()
        result = ocr_processor.process_image(image_bytes)

        # Check that preprocessing was applied
        assert result.metadata["preprocessing_applied"] is True
        assert "preprocessing_steps" in result.metadata

    def test_preprocessing_pipeline_integration(
        self, ocr_processor: OCRProcessor
    ) -> None:
        """Test integracji całego pipeline'u preprocessingu."""
        # Tworzy obraz testowy
        test_image = Image.new("RGB", (400, 300), "white")

        # Mock OpenCV functions
        with patch("backend.core.ocr.cv2") as mock_cv2:
            mock_cv2.findContours.return_value = ([], None)
            mock_cv2.boundingRect.return_value = (0, 0, 400, 300)
            mock_cv2.cvtColor.return_value = np.array(test_image)
            mock_cv2.COLOR_RGB2GRAY = 7
            mock_cv2.getPerspectiveTransform.return_value = np.eye(3)
            mock_cv2.warpPerspective.return_value = np.array(test_image)
            mock_cv2.createCLAHE.return_value = Mock()
            mock_cv2.morphologyEx.return_value = np.array(
                Image.new("L", (400, 300), 128)
            )
            mock_cv2.MORPH_CLOSE = 3
            mock_cv2.getStructuringElement.return_value = np.ones((3, 3))
            mock_cv2.MORPH_RECT = 0

        result = ocr_processor._preprocess_receipt_image(test_image)

        assert result is not None
        assert result.mode == "L"  # Skala szarości
        assert result.size[0] > 0 and result.size[1] > 0
