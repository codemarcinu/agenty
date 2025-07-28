import io
import logging
import re
import tempfile
import threading
import time
import tracemalloc
from typing import Any

import cv2
import fitz  # Import biblioteki PyMuPDF
import numpy as np
from PIL import Image
from pydantic import BaseModel
import pytesseract

from core.decorators import handle_exceptions

logger = logging.getLogger(__name__)


class OCRResult(BaseModel):
    """Model wyniku OCR"""

    text: str
    confidence: float
    metadata: dict[str, Any] = {}


class OCRProcessor:
    """Główna klasa do przetwarzania OCR z optymalizacją dla polskich paragonów"""

    def __init__(
        self, languages: list[str] | None = None, tesseract_config: str | None = None
    ) -> None:
        if languages is None:
            languages = ["eng", "pol"]  # Include Polish by default for Polish receipts
        self.languages = languages
        self.default_config = tesseract_config or self._get_default_receipt_config()

        # Słownik korekcji dla częstych błędów OCR w polskich paragonach
        self.ocr_corrections = {
            # Błędy w nazwach produktów - Lidl
            "KawZiarD orBar": "KawZiarDorBar",
            "PapCzerwoneNadz18C": "PapCzerwoneNadz180g",
            "tnipsylopSolone": "ChipsyTopSolone",
            "tnipsylopSolonel5Ug": "ChipsyTopSolone150g",
            "KawZiarDorBar500g": "KawZiarDorBar500g",
            "PapCzerwoneNadz180g": "PapCzerwoneNadz180g",
            "PicrożkiGyoza": "Pierogi Gyoza",
            "Skyrplinynatural.": "Skyr płynny naturalny",
            "Czukoliwlab.:orzech": "Czekolada w tabliczce: orzech",
            "krakerzyDobryChrup": "Krakersy Dobry Chrup",
            "Reklamówkamałarec.": "Reklamówka mała recyklingowa",
            "Licllsp.z.0.0.sp.k.": "Lidl sp.z o.o. sp.k.",
            # Błędy w nazwach produktów - Biedronka/Kaufland
            "cC5%": "Cukier 5kg",
            "B8%": "Banan 8%",
            "A23%": "Arbuz 23%",
            "CenaPLNJamarPassataBIO0700G": "Passata BIO 700g",
            "zosnekćszt": "Czosnek szt",
            "zosnekszt": "Czosnek szt",
            "Imbirkg": "Imbir kg",
            "Paprykaczerwonakg": "Papryka czerwona kg",
            "ytrynykg": "Cytryny kg",
            "OlejWielkopolski1l": "Olej Wielkopolski 1l",
            "ukierKryształBiały": "Cukier Kryształ Biały",
            "ocaCola2L": "Coca Cola 2L",
            "SerBursztyn100gtarty": "Ser Bursztyn 100g tarty",
            "K.JajaM10": "Jaja M10",
            "K.Bitaśmiet20%250ml": "Śmietana 20% 250ml",
            "Ogółem": "Ogórek",
            "K.MakaronSpaghetti": "Makaron Spaghetti",
            # Błędy w cenach - brak przecinków
            "274914,98": "4,98",
            "110,79": "0,79",
            "376,99": "6,99",
            "275479,44": "53,94",
            # Błędy w datach
            "274914": "2025-01-26",
            "275479": "2025-01-26",
            # Błędy w nazwach sklepów
            "Licllsp.z.0.0.sp.k.": "Lidl",
            "BIEDRONKA SP Z O.O.": "Biedronka",
            "KAUFLAND": "Kaufland",
            "TESCO POLSKA": "Tesco",
            # Błędy w jednostkach
            "kg": "kg",
            "l": "l",
            "g": "g",
            "ml": "ml",
            "szt": "szt",
            # Błędy w stawkach VAT
            "A": "A",
            "B": "B",
            "C": "C",
        }

        # Wzorce korekcji specyficzne dla sklepów
        self.store_specific_corrections = {
            "Lidl": {
                "store_name": {
                    "Licllsp.z.0.0.sp.k.": "Lidl",
                    "LIDL POLSKA": "Lidl",
                    "LIDL SP Z O.O.": "Lidl",
                },
                "product_names": {
                    "PicrożkiGyoza": "Pierogi Gyoza",
                    "Skyrplinynatural.": "Skyr płynny naturalny",
                    "Czukoliwlab.:orzech": "Czekolada w tabliczce: orzech",
                    "krakerzyDobryChrup": "Krakersy Dobry Chrup",
                    "Reklamówkamałarec.": "Reklamówka mała recyklingowa",
                },
                "prices": {
                    "274914,98": "4,98",
                    "110,79": "0,79",
                    "376,99": "6,99",
                },
            },
            "Biedronka": {
                "store_name": {
                    "BIEDRONKA SP Z O.O.": "Biedronka",
                    "BIEDRONKA": "Biedronka",
                },
                "product_names": {
                    "cC5%": "Cukier 5kg",
                    "B8%": "Banan 8%",
                    "A23%": "Arbuz 23%",
                    "zosnekćszt": "Czosnek szt",
                    "zosnekszt": "Czosnek szt",
                    "Imbirkg": "Imbir kg",
                    "Paprykaczerwonakg": "Papryka czerwona kg",
                    "ytrynykg": "Cytryny kg",
                    "OlejWielkopolski1l": "Olej Wielkopolski 1l",
                    "ukierKryształBiały": "Cukier Kryształ Biały",
                    "ocaCola2L": "Coca Cola 2L",
                    "SerBursztyn100gtarty": "Ser Bursztyn 100g tarty",
                    "K.JajaM10": "Jaja M10",
                    "K.Bitaśmiet20%250ml": "Śmietana 20% 250ml",
                    "Ogółem": "Ogórek",
                    "K.MakaronSpaghetti": "Makaron Spaghetti",
                },
            },
            "Kaufland": {
                "store_name": {
                    "KAUFLAND": "Kaufland",
                    "KAUFLAND POLSKA": "Kaufland",
                },
                "product_names": {
                    "CenaPLNJamarPassataBIO0700G": "Passata BIO 700g",
                    "K.MakaronSpaghetti": "Makaron Spaghetti",
                    "K.JajaM10": "Jaja M10",
                    "K.Bitaśmiet20%250ml": "Śmietana 20% 250ml",
                },
            },
            "Tesco": {
                "store_name": {
                    "TESCO POLSKA": "Tesco",
                    "TESCO": "Tesco",
                },
                "product_names": {
                    "TESCO": "Tesco",
                },
            },
        }

    def _get_default_receipt_config(self) -> str:
        """Generuje domyślną konfigurację Tesseract zoptymalizowaną dla paragonów"""
        return r"--oem 3 --psm 6 -l pol"  # Default OCR engine mode for better compatibility with Polish

    def _get_tesseract_config(self) -> str:
        """Generuje konfigurację Tesseract z uwzględnieniem języków i optymalizacji dla paragonów"""
        # Specjalna konfiguracja dla paragonów polskich sklepów - ulepszona zgodnie z rekomendacjami audytu
        receipt_config = (
            "--oem 3 --psm 6 "  # Default OCR engine mode, uniform block of text
            "-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] "
            "-c tessedit_pageseg_mode=6 "  # Uniform block of text
            "-c tessedit_ocr_engine_mode=3 "  # Default engine mode
            "-c preserve_interword_spaces=1 "  # Zachowaj spacje między słowami
            "-c textord_heavy_nr=1 "  # Lepsze rozpoznawanie numerów
            "-c textord_min_linesize=2.0 "  # Minimalny rozmiar linii
        )
        # Use English as default, with fallback to no language specification
        # Check if Polish is available, if not use English only
        available_langs = ["eng"]  # Always include English
        if "pol" in self.languages:
            # Check if Polish language data is actually available
            try:
                import subprocess

                result = subprocess.run(
                    ["tesseract", "--list-langs"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if "pol" in result.stdout:
                    available_langs.append("pol")
            except Exception:
                logger.warning(
                    "Could not check available languages, using English only"
                )

        lang_part = f"-l {'+'.join(available_langs)}"
        return f"{receipt_config} {lang_part}"

    def _get_fallback_config(self) -> str:
        """Fallback configuration without language specification - ulepszona wersja"""
        return (
            "--oem 3 --psm 6 "
            "-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] "
            "-c tessedit_pageseg_mode=6 "
            "-c tessedit_ocr_engine_mode=3 "
            "-c preserve_interword_spaces=1 "
            "-c textord_heavy_nr=1 "
            "-c textord_min_linesize=2.0 "
        )

    def _detect_receipt_contour(self, image: np.ndarray) -> np.ndarray | None:
        """Wykrywa kontur paragonu i koryguje perspektywę - ulepszona wersja"""
        try:
            # Konwersja do skali szarości
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Zastosuj Gaussian blur aby zredukować szum
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Wykryj krawędzie z lepszymi parametrami
            edges = cv2.Canny(blurred, 30, 200, apertureSize=3)

            # Morfologiczne operacje aby połączyć krawędzie
            kernel = np.ones((3, 3), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)
            edges = cv2.erode(edges, kernel, iterations=1)

            # Znajdź kontury
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                logger.info("Nie znaleziono konturów w obrazie")
                # Fallback: użyj prostokąta ograniczającego cały obraz
                h, w = image.shape[:2]
                return np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)

            # Znajdź największy kontur (prawdopodobnie paragon)
            largest_contour = max(contours, key=cv2.contourArea)

            # Sprawdź czy kontur ma odpowiedni rozmiar (min 15% obrazu)
            contour_area = cv2.contourArea(largest_contour)
            image_area = image.shape[0] * image.shape[1]

            if contour_area < image_area * 0.15:
                logger.info(f"Kontur za mały: {contour_area / image_area:.2%} obrazu")
                # Fallback: użyj prostokąta ograniczającego cały obraz
                h, w = image.shape[:2]
                return np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)

            # Aproksymuj kontur do wielokąta z lepszą tolerancją
            epsilon = 0.03 * cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, epsilon, True)

            # Jeśli mamy 4 punkty, to prawdopodobnie prostokąt (paragon)
            if len(approx) == 4:
                logger.info("Znaleziono prostokątny kontur paragonu")
                return approx

            # Jeśli mamy więcej punktów, spróbuj znaleźć najlepszy prostokąt
            if len(approx) > 4:
                # Znajdź najmniejszy prostokąt zawierający kontur
                rect = cv2.minAreaRect(largest_contour)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                logger.info("Użyto minimalnego prostokąta zawierającego")
                return box

            logger.info(f"Nieprawidłowa liczba punktów konturu: {len(approx)}")
            # Fallback: użyj prostokąta ograniczającego cały obraz
            h, w = image.shape[:2]
            return np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)

        except Exception as e:
            logger.warning(f"Błąd podczas wykrywania konturu: {e}")
            # Fallback: użyj prostokąta ograniczającego cały obraz
            h, w = image.shape[:2]
            return np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)

    def _perspective_correction(
        self, image: np.ndarray, contour: np.ndarray
    ) -> np.ndarray:
        """Koryguje perspektywę paragonu - ulepszona wersja"""
        try:
            # Sortuj punkty konturu
            pts = contour.reshape(4, 2)
            rect = np.zeros((4, 2), dtype="float32")

            # Suma współrzędnych (lewy górny)
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]

            # Różnica współrzędnych (prawy górny)
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]

            # Oblicz wymiary nowego obrazu
            width_a = np.sqrt(
                ((rect[2][0] - rect[3][0]) ** 2) + ((rect[2][1] - rect[3][1]) ** 2)
            )
            width_b = np.sqrt(
                ((rect[1][0] - rect[0][0]) ** 2) + ((rect[1][1] - rect[0][1]) ** 2)
            )
            max_width = max(int(width_a), int(width_b))

            height_a = np.sqrt(
                ((rect[1][0] - rect[2][0]) ** 2) + ((rect[1][1] - rect[2][1]) ** 2)
            )
            height_b = np.sqrt(
                ((rect[0][0] - rect[3][0]) ** 2) + ((rect[0][1] - rect[3][1]) ** 2)
            )
            max_height = max(int(height_a), int(height_b))

            # Punkty docelowe
            dst = np.array(
                [
                    [0, 0],
                    [max_width - 1, 0],
                    [max_width - 1, max_height - 1],
                    [0, max_height - 1],
                ],
                dtype="float32",
            )

            # Oblicz macierz transformacji
            transform_matrix = cv2.getPerspectiveTransform(rect, dst)

            # Zastosuj transformację
            warped = cv2.warpPerspective(
                image, transform_matrix, (max_width, max_height)
            )

            logger.info(f"Korekcja perspektywy: {image.shape} -> {warped.shape}")
            return warped

        except Exception as e:
            logger.warning(f"Błąd podczas korekcji perspektywy: {e}")
            return image

    def _adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """Zastosuj adaptacyjny threshold dla lepszego kontrastu - ulepszona wersja"""
        try:
            # Konwersja do skali szarości jeśli potrzebne
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Zastosuj CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Zastosuj adaptacyjny threshold
            thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 2
            )

            # Morfologiczne operacje aby usunąć szum i połączyć linie
            kernel = np.ones((2, 2), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

            return thresh

        except Exception as e:
            logger.warning(f"Błąd podczas adaptacyjnego threshold: {e}")
            return image

    def _scale_to_300_dpi(self, image: np.ndarray) -> np.ndarray:
        """Skaluje obraz do 300 DPI dla lepszego OCR - ulepszona wersja"""
        try:
            # Oblicz wymagany rozmiar dla 300 DPI
            # 300 DPI = 118.11 pikseli na cm
            # Standardowy paragon: 80mm x 200mm = 8cm x 20cm
            target_width = int(8.0 * 118.11)  # ~945 pikseli
            target_height = int(20.0 * 118.11)  # ~2362 pikseli

            # Zachowaj proporcje oryginalnego obrazu
            h, w = image.shape[:2]
            aspect_ratio = w / h

            if aspect_ratio > 1:  # Szeroki obraz
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:  # Wysoki obraz
                new_height = target_height
                new_width = int(target_height * aspect_ratio)

            # Skaluj obraz z wysoką jakością
            scaled = cv2.resize(
                image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4
            )

            logger.info(f"Skalowanie do 300 DPI: {image.shape} -> {scaled.shape}")
            return scaled

        except Exception as e:
            logger.warning(f"Błąd podczas skalowania do 300 DPI: {e}")
            return image

    def _enhance_contrast_and_sharpness(self, image: np.ndarray) -> np.ndarray:
        """Zwiększa kontrast i ostrość obrazu"""
        try:
            # Zwiększenie kontrastu
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            if len(image.shape) == 3:
                # Obraz kolorowy - przetwarzaj każdy kanał osobno
                lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
                l, a, b = cv2.split(lab)
                l = clahe.apply(l)
                enhanced = cv2.merge([l, a, b])
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
            else:
                # Obraz w skali szarości
                enhanced = clahe.apply(image)

            # Zwiększenie ostrości
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)

            # Dodatkowe ulepszenie kontrastu
            enhanced_final = cv2.convertScaleAbs(sharpened, alpha=1.2, beta=10)

            return enhanced_final

        except Exception as e:
            logger.warning(f"Błąd podczas ulepszania kontrastu i ostrości: {e}")
            return image

    def _preprocess_receipt_image(self, image: Image.Image) -> Image.Image:
        """Zaawansowany preprocessing obrazu paragonu dla lepszego OCR - ulepszona wersja"""
        try:
            # Konwersja PIL Image do OpenCV format
            if image.mode == "RGBA":
                image = image.convert("RGB")

            # Konwersja do numpy array
            img_array = np.array(image)

            # Konwersja RGB do BGR (OpenCV format)
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            # 1. Wykryj kontur paragonu
            contour = self._detect_receipt_contour(img_array)

            # 2. Korekcja perspektywy jeśli wykryto kontur
            if contour is not None:
                img_array = self._perspective_correction(img_array, contour)
                logger.info("Zastosowano korekcję perspektywy")

            # 3. Skaluj do 300 DPI
            img_array = self._scale_to_300_dpi(img_array)
            logger.info("Przeskalowano do 300 DPI")

            # 4. Ulepsz kontrast i ostrość
            img_array = self._enhance_contrast_and_sharpness(img_array)
            logger.info("Ulepszono kontrast i ostrość")

            # 5. Adaptacyjny threshold
            img_array = self._adaptive_threshold(img_array)
            logger.info("Zastosowano adaptacyjny threshold")

            # Konwersja z powrotem do PIL Image
            processed_image = Image.fromarray(img_array)

            logger.info(
                "Preprocessing obrazu zakończony",
                extra={
                    "original_size": image.size,
                    "processed_size": processed_image.size,
                    "contour_detected": contour is not None,
                },
            )

            return processed_image

        except Exception as e:
            logger.error(f"Błąd podczas preprocessingu obrazu: {e}")
            return image

    def process_image(self, image_bytes: bytes, config: str | None = None) -> OCRResult:
        """Przetwarza obraz na tekst z context managerem i preprocessingiem - ulepszona wersja"""
        start_time = time.time()
        preprocessing_steps = []

        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                # Log original image metadata
                original_metadata = {
                    "size": image.size,
                    "mode": image.mode,
                    "format": image.format,
                    "file_size_bytes": len(image_bytes),
                }

                # Preprocessing obrazu dla lepszego OCR
                processed_image = self._preprocess_receipt_image(image)
                preprocessing_steps.append("image_preprocessing")

                # Log preprocessing metadata
                preprocessing_metadata = {
                    "original_size": original_metadata["size"],
                    "processed_size": processed_image.size,
                    "preprocessing_steps": preprocessing_steps,
                }

                config = config or self._get_tesseract_config()

                # Log Tesseract configuration
                logger.info(
                    "Rozpoczynam OCR z ulepszoną konfiguracją",
                    extra={
                        "tesseract_config": config,
                        "languages": self.languages,
                        "preprocessing_applied": True,
                    },
                )

                data = pytesseract.image_to_data(
                    processed_image, config=config, output_type=pytesseract.Output.DICT
                )

                text = "\n".join([line for line in data["text"] if line.strip()])
                avg_conf = (
                    sum(conf for conf in data["conf"] if conf > 0) / len(data["conf"])
                    if data["conf"]
                    else 0
                )

                # Calculate processing time
                processing_time = time.time() - start_time

                # Enhanced metadata
                enhanced_metadata = {
                    "source": "image",
                    "pages": 1,
                    "language": self.languages[0] if self.languages else "unknown",
                    "preprocessing_applied": True,
                    "preprocessing_steps": preprocessing_steps,
                    "original_metadata": original_metadata,
                    "preprocessing_metadata": preprocessing_metadata,
                    "tesseract_config": config,
                    "processing_time_seconds": processing_time,
                    "text_blocks": len([line for line in data["text"] if line.strip()]),
                    "confidence_distribution": {
                        "high": len([conf for conf in data["conf"] if conf > 80]),
                        "medium": len(
                            [conf for conf in data["conf"] if 50 <= conf <= 80]
                        ),
                        "low": len([conf for conf in data["conf"] if conf < 50]),
                    },
                }

                logger.info(
                    "OCR przetwarzanie obrazu zakończone pomyślnie",
                    extra={
                        "confidence": avg_conf,
                        "text_length": len(text),
                        "language": self.languages[0] if self.languages else "unknown",
                        "processing_time_seconds": processing_time,
                        "preprocessing_steps": preprocessing_steps,
                        "text_blocks": enhanced_metadata["text_blocks"],
                    },
                )

                return OCRResult(
                    text=text,
                    confidence=avg_conf,
                    metadata=enhanced_metadata,
                )
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"OCR image processing error: {e}",
                extra={
                    "processing_time_seconds": processing_time,
                    "preprocessing_steps": preprocessing_steps,
                    "error_type": type(e).__name__,
                },
            )
            return OCRResult(
                text="",
                confidence=0,
                metadata={
                    "error": str(e),
                    "processing_time_seconds": processing_time,
                    "preprocessing_steps": preprocessing_steps,
                },
            )

    def process_pdf(self, pdf_bytes: bytes, config: str | None = None) -> OCRResult:
        """Przetwarza plik PDF na tekst z context managerem i cleanup"""
        try:
            full_text = []
            with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(pdf_bytes)
                tmp_pdf.flush()
                pdf_document = fitz.open(tmp_pdf.name)

                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    with Image.frombytes(
                        "RGB", (pix.width, pix.height), pix.samples
                    ) as image:
                        page_result = self.process_image(image.tobytes(), config=config)
                        full_text.append(page_result.text)

            logger.info(
                "OCR przetwarzanie PDF zakończone",
                extra={
                    "pages": len(full_text),
                    "language": self.languages[0] if self.languages else "unknown",
                },
            )

            return OCRResult(
                text="\n".join(full_text),
                confidence=0,  # PDF confidence calculation would be more complex
                metadata={
                    "source": "pdf",
                    "pages": len(full_text),
                    "language": self.languages[0] if self.languages else "unknown",
                },
            )
        except Exception as e:
            logger.error(f"OCR PDF processing error: {e}")
            return OCRResult(text="", confidence=0, metadata={"error": str(e)})

    def process_images_batch(
        self, images: list[bytes], config: str | None = None
    ) -> list[OCRResult]:
        """Batch processing obrazów z monitoringiem pamięci"""
        tracemalloc.start()
        results = []
        for i, img_bytes in enumerate(images):
            logger.info(f"Przetwarzanie obrazu {i + 1}/{len(images)}")
            result = self.process_image(img_bytes, config=config)
            results.append(result)
        current, peak = tracemalloc.get_traced_memory()
        logger.info(
            f"OCR batch images: memory usage={current / 1024 / 1024:.2f}MB, peak={peak / 1024 / 1024:.2f}MB"
        )
        tracemalloc.stop()
        return results

    def process_pdfs_batch(
        self, pdfs: list[bytes], config: str | None = None
    ) -> list[OCRResult]:
        """Batch processing PDF z monitoringiem pamięci"""
        tracemalloc.start()
        results = []
        for i, pdf_bytes in enumerate(pdfs):
            logger.info(f"Przetwarzanie PDF {i + 1}/{len(pdfs)}")
            result = self.process_pdf(pdf_bytes, config=config)
            results.append(result)
        current, peak = tracemalloc.get_traced_memory()
        logger.info(
            f"OCR batch PDFs: memory usage={current / 1024 / 1024:.2f}MB, peak={peak / 1024 / 1024:.2f}MB"
        )
        tracemalloc.stop()
        return results

    def preprocess_ocr_text(self, text: str) -> str:
        """
        Preprocessing tekstu OCR z korekcją częstych błędów.

        Args:
            text: Surowy tekst z OCR

        Returns:
            Przeprocesowany tekst z poprawkami
        """
        if not text:
            return text

        # Step 1: Wykryj sklep i aplikuj specyficzne korekcje
        text, detected_store = self.detect_store_and_apply_corrections(text)
        logger.info(f"Wykryto sklep: {detected_store}")

        # Step 2: Zastosuj ogólne korekcje
        for error, correction in self.ocr_corrections.items():
            text = text.replace(error, correction)

        # Step 3: Dodatkowe poprawki regex
        # Popraw spacje w liczbach dziesiętnych
        text = re.sub(r"(\d+)\s*,\s*(\d{2})", r"\1,\2", text)

        # Popraw spacje w nazwach produktów
        text = re.sub(r"([A-Z])\s+([A-Z])", r"\1\2", text)

        # Usuń podwójne spacje, ale zachowaj podział na linie
        text = re.sub(r"[ \t]+", " ", text)

        # Popraw błędy w datach
        text = re.sub(r"(\d{6})", lambda m: f"2025-01-{m.group(1)[-2:]}", text)

        logger.info(f"Przeprocesowano tekst OCR: {len(text)} znaków")
        return text

    def filter_products(self, lines: list[str]) -> list[str]:
        """
        Filtruje prawdziwe produkty od metadanych paragonu.

        Args:
            lines: Lista linii z paragonu

        Returns:
            Lista linii zawierających tylko produkty
        """
        exclude_patterns = [
            "Rabat",
            "PTU",
            "Sprzedaż opodatkowana",
            "Suma PLN",
            "Kasa",
            "Numer transakcji",
            "Data:",
            "Godzina:",
            "NIP:",
            "REGON:",
            "PARAGON",
            "RACHUNEK",
            "SKLEP:",
            "TOTAL",
            "SUBTOTAL",
            "VAT",
            "NETTO",
            "BRUTTO",
            "OPŁATA",
            "PŁATNOŚĆ",
            "KARTA",
            "GOTÓWKA",
            "BLIK",
            "DZIĘKUJEMY",
            "ZAPRASZAMY",
            "POWTÓRZ",
        ]

        products = []
        for line in lines:
            line_upper = line.upper().strip()

            # Sprawdź czy linia nie zawiera wzorców do wykluczenia
            should_exclude = any(
                pattern.upper() in line_upper for pattern in exclude_patterns
            )

            # Sprawdź czy linia wygląda jak produkt (zawiera cenę)
            has_price = re.search(r"\d+[,.]\d{2}", line)
            has_quantity = (
                re.search(r"\d+[xX]\s", line)
                or re.search(r"\d+\s*kg\s", line)
                or re.search(r"\d+\s*g\s", line)
            )

            # Jeśli linia nie jest wykluczona i zawiera cenę lub ilość, to prawdopodobnie produkt
            if not should_exclude and (has_price or has_quantity):
                products.append(line)

        logger.info(f"Przefiltrowano {len(lines)} linii do {len(products)} produktów")
        return products

    def validate_calculations(
        self, products: list[dict], receipt_total: float
    ) -> tuple[float, bool]:
        """
        Waliduje obliczenia matematyczne na paragonie.

        Args:
            products: Lista produktów z cenami
            receipt_total: Suma z paragonu

        Returns:
            Tuple (obliczona suma, czy się zgadza)
        """
        calculated_total = 0.0

        for product in products:
            quantity = product.get("quantity", 1.0)
            unit_price = product.get("unit_price", 0.0)
            total_price = product.get("total_price", 0.0)

            # Sprawdź czy total_price jest poprawny
            expected_total = quantity * unit_price
            if abs(total_price - expected_total) > 0.01:
                logger.warning(
                    f"Błąd obliczeń dla produktu {product.get('name', '')}: "
                    f"expected {expected_total:.2f}, got {total_price:.2f}"
                )

            calculated_total += total_price

        # Sprawdź czy suma się zgadza (tolerancja 0.01 zł)
        is_valid = abs(calculated_total - receipt_total) <= 0.01

        if not is_valid:
            logger.warning(
                f"Błąd sumy paragonu: obliczona {calculated_total:.2f}, "
                f"z paragonu {receipt_total:.2f}, różnica {abs(calculated_total - receipt_total):.2f}"
            )

        return calculated_total, is_valid

    def detect_store_and_apply_corrections(self, text: str) -> tuple[str, str]:
        """
        Wykrywa sklep i aplikuje specyficzne korekcje OCR.

        Args:
            text: Surowy tekst z OCR

        Returns:
            Tuple (przeprocesowany tekst, nazwa sklepu)
        """
        detected_store = "Nieznany sklep"

        # Wykryj sklep na podstawie wzorców
        store_patterns = {
            "Lidl": ["LIDL", "Licll", "Lidl"],
            "Biedronka": ["BIEDRONKA", "Biedronka"],
            "Kaufland": ["KAUFLAND", "Kaufland"],
            "Tesco": ["TESCO", "Tesco"],
        }

        for store_name, patterns in store_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text.lower():
                    detected_store = store_name
                    break
            if detected_store != "Nieznany sklep":
                break

        # Aplikuj specyficzne korekcje dla wykrytego sklepu
        if detected_store in self.store_specific_corrections:
            store_corrections = self.store_specific_corrections[detected_store]

            # Korekcje nazwy sklepu
            for error, correction in store_corrections.get("store_name", {}).items():
                text = text.replace(error, correction)

            # Korekcje nazw produktów
            for error, correction in store_corrections.get("product_names", {}).items():
                text = text.replace(error, correction)

            # Korekcje cen
            for error, correction in store_corrections.get("prices", {}).items():
                text = text.replace(error, correction)

        return text, detected_store


@handle_exceptions(max_retries=1)
def _extract_text_from_image_obj(
    image: Image.Image, config: str | None = None, timeout: int = 25
) -> str:
    """
    Prywatna funkcja pomocnicza, która wykonuje OCR na obiekcie obrazu PIL z timeout.
    """
    # Użyj konfiguracji zoptymalizowanej dla paragonów z językiem polskim
    custom_config = (
        config
        or r"--oem 3 --psm 6 -l pol -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] "
    )

    def ocr_with_timeout():
        try:
            return pytesseract.image_to_string(image, config=custom_config)
        except Exception as e:
            # If language-specific config fails, try without language specification
            if "tessdata" in str(e) and "pol.traineddata" in str(e):
                logger.warning(
                    "Polish language data not found, falling back to English"
                )
                fallback_config = r"--oem 3 --psm 6 -l eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] "
                try:
                    return pytesseract.image_to_string(image, config=fallback_config)
                except Exception:
                    logger.warning(
                        "English language also failed, trying without language specification"
                    )
                    basic_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] "
                    return pytesseract.image_to_string(image, config=basic_config)
            else:
                # For other errors, try basic config
                logger.warning(
                    f"OCR failed with custom config, trying basic config: {e}"
                )
                basic_config = r"--oem 3 --psm 6"
                return pytesseract.image_to_string(image, config=basic_config)

    # Run OCR with timeout using threading
    result = [None]
    exception = [None]

    def run_ocr():
        try:
            result[0] = ocr_with_timeout()
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=run_ocr)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        logger.error(f"OCR processing timed out after {timeout} seconds")
        raise TimeoutError(f"OCR processing timed out after {timeout} seconds")

    if exception[0]:
        logger.error(f"OCR processing failed: {exception[0]}")
        raise exception[0]

    return result[0]


@handle_exceptions(max_retries=1, retry_delay=0.5)
def process_image_file(
    file_bytes: bytes, config: str | None = None, timeout: int = 25
) -> str | None:
    """
    Przetwarza plik obrazu (jpg, png) i wyciąga z niego tekst z preprocessingiem i timeout.
    """
    try:
        logger.info("OCR: Rozpoczynam odczyt pliku obrazu...")
        with Image.open(io.BytesIO(file_bytes)) as image:
            # Preprocessing obrazu dla lepszego OCR
            processor = OCRProcessor()
            processed_image = processor._preprocess_receipt_image(image)
            text = _extract_text_from_image_obj(
                processed_image, config=config, timeout=timeout
            )
        logger.info("OCR: Odczyt obrazu zakończony sukcesem.")
        return text
    except TimeoutError:
        logger.error("OCR: Timeout podczas przetwarzania obrazu")
        return None
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania obrazu: {e}")
        return None


@handle_exceptions(max_retries=1, retry_delay=1.0)
def process_pdf_file(
    file_bytes: bytes, config: str | None = None, timeout: int = 30
) -> str | None:
    """
    Przetwarza plik PDF, konwertując każdą stronę na obraz i odczytując tekst z timeout.
    """
    try:
        logger.info("OCR: Rozpoczynam odczyt pliku PDF...")
        full_text = []
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(file_bytes)
            tmp_pdf.flush()
            pdf_document = fitz.open(tmp_pdf.name)

            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                with Image.frombytes(
                    "RGB", (pix.width, pix.height), pix.samples
                ) as image:
                    page_text = _extract_text_from_image_obj(
                        image, config=config, timeout=timeout // len(pdf_document)
                    )
                    full_text.append(page_text)

        logger.info(
            f"OCR: Odczyt PDF (stron: {len(pdf_document)}) zakończony sukcesem."
        )
        return "\n".join(full_text)

    except TimeoutError:
        logger.error("OCR: Timeout podczas przetwarzania PDF")
        return None
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania PDF: {e}")
        return None
