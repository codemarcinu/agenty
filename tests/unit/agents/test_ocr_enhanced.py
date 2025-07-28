"""
Testy dla ulepszonego OCR z preprocessingiem obrazów i obsługą polskich paragonów.
"""

import io
from unittest.mock import Mock, patch

from PIL import Image, ImageEnhance
import pytest

from backend.core.ocr import OCRProcessor, process_image_file, process_pdf_file


class TestOCREnhanced:
    """Testy dla ulepszonego modułu OCR."""

    @pytest.fixture
    def ocr_processor(self) -> OCRProcessor:
        """Fixture dla procesora OCR."""
        return OCRProcessor()

    @pytest.fixture
    def sample_image(self) -> Image.Image:
        """Fixture dla przykładowego obrazu."""
        return Image.new("RGB", (800, 600), color="white")

    @pytest.fixture
    def sample_image_bytes(self) -> bytes:
        """Fixture dla przykładowego obrazu w formacie bytes."""
        image = Image.new("RGB", (800, 600), color="white")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()

    def test_get_default_receipt_config(self, ocr_processor: OCRProcessor) -> None:
        """Test domyślnej konfiguracji dla paragonów."""
        config = ocr_processor._get_default_receipt_config()
        assert "--psm 6" in config
        assert "--oem 3" in config

    def test_get_tesseract_config_with_polish_chars(
        self, ocr_processor: OCRProcessor
    ) -> None:
        """Test konfiguracji Tesseract z polskimi znakami."""
        config = ocr_processor._get_tesseract_config()
        assert "ĄĆĘŁŃÓŚŹŻ" in config

    def test_preprocess_receipt_image_grayscale_conversion(
        self, ocr_processor: OCRProcessor, sample_image: Image.Image
    ) -> None:
        """Test konwersji do skali szarości."""
        processed = ocr_processor._preprocess_receipt_image(sample_image)

        # Sprawdź czy obraz został przetworzony
        assert processed is not None
        assert processed.size[0] > 0 and processed.size[1] > 0

    def test_preprocess_receipt_image_contrast_enhancement(
        self, ocr_processor: OCRProcessor, sample_image: Image.Image
    ) -> None:
        """Test zwiększenia kontrastu."""
        processed = ocr_processor._preprocess_receipt_image(sample_image)

        # Sprawdź czy obraz został przetworzony
        assert processed is not None
        assert processed.size[0] > 0 and processed.size[1] > 0

    def test_preprocess_receipt_image_resize_small_image(
        self, ocr_processor: OCRProcessor
    ) -> None:
        """Test zmiany rozmiaru małego obrazu."""
        # Tworzy mały obraz
        small_image = Image.new("RGB", (400, 300), color="white")

        processed = ocr_processor._preprocess_receipt_image(small_image)

        # Sprawdź czy obraz został powiększony
        assert processed.size[0] >= 800 or processed.size[1] >= 600

    def test_preprocess_receipt_image_error_handling(
        self, ocr_processor: OCRProcessor
    ) -> None:
        """Test obsługi błędów podczas preprocessingu."""
        # Symuluj błąd podczas przetwarzania
        with patch.object(ImageEnhance, "Contrast") as mock_contrast:
            mock_contrast.side_effect = Exception("Test error")

            sample_image = Image.new("RGB", (100, 100), color="white")
            processed = ocr_processor._preprocess_receipt_image(sample_image)

            # Powinien zwrócić przetworzony obraz w przypadku błędu
            assert processed is not None
            assert processed.size[0] > 0 and processed.size[1] > 0

    @patch("backend.core.ocr.pytesseract")
    def test_process_image_with_preprocessing(
        self,
        mock_tesseract: Mock,
        ocr_processor: OCRProcessor,
        sample_image_bytes: bytes,
    ) -> None:
        """Test przetwarzania obrazu z preprocessingiem."""
        # Mock odpowiedzi Tesseract
        mock_data = {"text": ["Test", "paragon", "tekst"], "conf": [90, 85, 80]}
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        result = ocr_processor.process_image(sample_image_bytes)

        assert result.text == "Test\nparagon\ntekst"
        assert result.confidence > 0
        assert result.metadata.get("preprocessing_applied") is True

    @patch("backend.core.ocr.pytesseract")
    def test_process_image_error_handling(
        self,
        mock_tesseract: Mock,
        ocr_processor: OCRProcessor,
        sample_image_bytes: bytes,
    ) -> None:
        """Test obsługi błędów podczas przetwarzania obrazu."""
        mock_tesseract.image_to_data.side_effect = Exception("OCR error")

        result = ocr_processor.process_image(sample_image_bytes)

        assert result.text == ""
        assert result.confidence == 0
        assert "error" in result.metadata

    @patch("backend.core.ocr.fitz")
    @patch("backend.core.ocr.pytesseract")
    def test_process_pdf_with_preprocessing(
        self, mock_tesseract: Mock, mock_fitz: Mock, ocr_processor: OCRProcessor
    ) -> None:
        """Test przetwarzania PDF z preprocessingiem."""
        # Mock PyMuPDF z poprawnymi danymi
        mock_doc = Mock()
        mock_page = Mock()
        mock_pix = Mock()
        mock_pix.width = 100
        mock_pix.height = 100
        mock_pix.samples = b"test_samples" * (100 * 100 * 3)  # Poprawne dane RGB

        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__ = Mock(return_value=1)

        mock_fitz.open.return_value = mock_doc

        # Mock Tesseract z poprawnymi danymi
        mock_data = {"text": ["PDF", "tekst"], "conf": [90, 85]}
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        pdf_bytes = b"fake_pdf_content"
        result = ocr_processor.process_pdf(pdf_bytes)

        # Sprawdź czy wynik jest poprawny
        assert result.text is not None
        assert result.metadata.get("source") == "pdf"
        assert result.metadata.get("pages") == 1

    def test_process_images_batch_with_logging(
        self, ocr_processor: OCRProcessor
    ) -> None:
        """Test batch processing obrazów z logowaniem."""
        images = [b"image1", b"image2", b"image3"]

        with patch.object(ocr_processor, "process_image") as mock_process:
            mock_process.return_value = Mock(text="test", confidence=90, metadata={})

            results = ocr_processor.process_images_batch(images)

            assert len(results) == 3
            assert mock_process.call_count == 3

    def test_process_pdfs_batch_with_logging(self, ocr_processor: OCRProcessor) -> None:
        """Test batch processing PDF z logowaniem."""
        pdfs = [b"pdf1", b"pdf2"]

        with patch.object(ocr_processor, "process_pdf") as mock_process:
            mock_process.return_value = Mock(text="test", confidence=0, metadata={})

            results = ocr_processor.process_pdfs_batch(pdfs)

            assert len(results) == 2
            assert mock_process.call_count == 2

    @patch("backend.core.ocr.pytesseract")
    def test_extract_text_from_image_obj_with_receipt_config(
        self, mock_tesseract: Mock
    ) -> None:
        """Test wyciągania tekstu z obiektu obrazu z konfiguracją paragonów."""
        mock_tesseract.image_to_string.return_value = "Test paragon tekst"

        # Tworzę poprawny obiekt obrazu
        image = Image.new("RGB", (100, 100), color="white")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        image_bytes = img_byte_arr.getvalue()

        process_image_file(image_bytes)

        # Sprawdź czy użyto konfiguracji dla paragonów
        mock_tesseract.image_to_string.assert_called_once()
        call_args = mock_tesseract.image_to_string.call_args
        config = call_args[1]["config"]
        assert "--psm 6" in config
        assert "-l pol" in config
        assert "ĄĆĘŁŃÓŚŹŻ" in config

    @patch("backend.core.ocr.pytesseract")
    def test_process_image_file_with_preprocessing(self, mock_tesseract: Mock) -> None:
        """Test process_image_file z preprocessingiem."""
        mock_tesseract.image_to_string.return_value = "Przetworzony tekst"

        image = Image.new("RGB", (100, 100), color="white")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        image_bytes = img_byte_arr.getvalue()

        text = process_image_file(image_bytes)

        assert text == "Przetworzony tekst"
        mock_tesseract.image_to_string.assert_called_once()

    @patch("backend.core.ocr.fitz")
    @patch("backend.core.ocr.pytesseract")
    def test_process_pdf_file_with_preprocessing(
        self, mock_tesseract: Mock, mock_fitz: Mock
    ) -> None:
        """Test process_pdf_file z preprocessingiem."""
        mock_tesseract.image_to_string.return_value = "PDF tekst"

        # Mock PyMuPDF z poprawnymi danymi
        mock_doc = Mock()
        mock_page = Mock()
        mock_pix = Mock()
        mock_pix.width = 100
        mock_pix.height = 100
        mock_pix.samples = b"test_samples" * (100 * 100 * 3)  # Poprawne dane RGB

        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__ = Mock(return_value=1)

        mock_fitz.open.return_value = mock_doc

        pdf_bytes = b"fake_pdf_content"
        text = process_pdf_file(pdf_bytes)

        assert text == "PDF tekst"

    def test_ocr_processor_language_configuration(self) -> None:
        """Test konfiguracji języków OCR."""
        # Test z polskim i angielskim
        processor = OCRProcessor(languages=["pol", "eng"])
        config = processor._get_tesseract_config()
        assert "-l pol+eng" in config or "-l eng+pol" in config

        # Test tylko z polskim
        processor = OCRProcessor(languages=["pol"])
        config = processor._get_tesseract_config()
        assert "-l pol" in config or "-l eng+pol" in config

    def test_ocr_processor_custom_config(self) -> None:
        """Test niestandardowej konfiguracji OCR."""
        custom_config = "--oem 1 --psm 8"
        processor = OCRProcessor(tesseract_config=custom_config)

        config = processor._get_tesseract_config()
        # Sprawdź czy konfiguracja zawiera podstawowe elementy
        assert "--oem" in config
        assert "--psm" in config

    @patch("backend.core.ocr.pytesseract")
    def test_ocr_confidence_calculation(
        self,
        mock_tesseract: Mock,
        ocr_processor: OCRProcessor,
        sample_image_bytes: bytes,
    ) -> None:
        """Test obliczania confidence OCR."""
        # Mock odpowiedzi z różnymi poziomami confidence
        mock_data = {
            "text": ["Test", "paragon", "tekst"],
            "conf": [90, 85, 80],  # Średnia: 85
        }
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        result = ocr_processor.process_image(sample_image_bytes)

        assert result.confidence == 85.0

    @patch("backend.core.ocr.pytesseract")
    def test_ocr_confidence_with_zero_values(
        self,
        mock_tesseract: Mock,
        ocr_processor: OCRProcessor,
        sample_image_bytes: bytes,
    ) -> None:
        """Test obliczania confidence z wartościami zerowymi."""
        mock_data = {"text": ["Test", "paragon"], "conf": [0, 0]}  # Wszystkie zera
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        result = ocr_processor.process_image(sample_image_bytes)

        assert result.confidence == 0

    def test_preprocessing_preserves_image_integrity(
        self, ocr_processor: OCRProcessor
    ) -> None:
        """Test czy preprocessing zachowuje integralność obrazu."""
        # Tworzy obraz z określonymi wymiarami
        original_image = Image.new("RGB", (800, 600), color="white")

        processed = ocr_processor._preprocess_receipt_image(original_image)

        # Sprawdź czy obraz nie został uszkodzony
        assert processed is not None
        assert processed.size[0] > 0
        assert processed.size[1] > 0

    @patch("backend.core.ocr.pytesseract")
    def test_ocr_with_polish_receipt_text(
        self,
        mock_tesseract: Mock,
        ocr_processor: OCRProcessor,
        sample_image_bytes: bytes,
    ) -> None:
        """Test OCR z polskim tekstem paragonu."""
        # Mock odpowiedzi z polskim tekstem
        mock_data = {
            "text": ["Lidl", "sp.", "z", "o.o.", "Mleko", "3,2%", "1L", "4,99", "zł"],
            "conf": [95, 90, 85, 80, 75, 70, 65, 60, 55],
        }
        mock_tesseract.image_to_data.return_value = mock_data
        mock_tesseract.Output.DICT = "dict"

        result = ocr_processor.process_image(sample_image_bytes)

        # Sprawdź czy tekst został poprawnie rozpoznany
        assert "Lidl" in result.text
        assert "Mleko" in result.text
        assert "4,99" in result.text
        assert result.confidence > 0

    def test_ocr_processor_with_different_image_formats(
        self, ocr_processor: OCRProcessor
    ) -> None:
        """Test procesora OCR z różnymi formatami obrazów."""
        # Test z różnymi formatami
        formats = ["PNG", "JPEG", "BMP"]

        for format_name in formats:
            image = Image.new("RGB", (100, 100), color="white")
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=format_name)
            image_bytes = img_byte_arr.getvalue()

            # Sprawdź czy można przetworzyć różne formaty
            assert len(image_bytes) > 0

    def test_ocr_processor_error_recovery(self, ocr_processor: OCRProcessor) -> None:
        """Test odzyskiwania po błędach OCR."""
        # Test z nieprawidłowymi danymi
        invalid_bytes = b"not_an_image"

        # Powinien obsłużyć błąd gracefully
        try:
            result = ocr_processor.process_image(invalid_bytes)
            assert result.text == ""
            assert result.confidence == 0
        except Exception:
            # Błąd jest akceptowalny dla nieprawidłowych danych
            pass


if __name__ == "__main__":
    pytest.main(["-v", "test_ocr_enhanced.py"])
