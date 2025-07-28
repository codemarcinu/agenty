#!/usr/bin/env python3
"""
Test script for Tesseract OCR installation and functionality
"""

from pathlib import Path
import subprocess
import sys


def test_tesseract_installation():
    """Test if Tesseract is properly installed"""

    try:
        # Test 1: Check if tesseract command exists
        result = subprocess.run(
            ["tesseract", "--version"], capture_output=True, text=True, timeout=10, check=False
        )

        if result.returncode == 0:
            pass
        else:
            return False

    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

    return True


def test_tesseract_languages():
    """Test available Tesseract languages"""

    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"], capture_output=True, text=True, timeout=10, check=False
        )

        if result.returncode == 0:
            languages = result.stdout.strip().split("\n")[1:]  # Skip header

            # Check for Polish language
            if any("pol" in lang.lower() for lang in languages):
                pass
            else:
                pass

            # Check for English language
            if any("eng" in lang.lower() for lang in languages):
                pass
            else:
                pass

            for lang in languages:
                if lang.strip():
                    pass

        else:
            return False

    except Exception:
        return False

    return True


def test_pytesseract_import():
    """Test if pytesseract Python package is available"""

    try:
        # Test basic OCR functionality
        import io

        from PIL import Image
        import pytesseract

        # Create a simple test image
        test_image = Image.new("RGB", (100, 50), color="white")

        # Test OCR on the image
        pytesseract.image_to_string(test_image)

        return True

    except ImportError:
        return False
    except Exception:
        return False


def test_ocr_with_polish():
    """Test OCR with Polish language"""

    try:
        from PIL import Image, ImageDraw, ImageFont
        import pytesseract

        # Create a test image with Polish text
        img = Image.new("RGB", (400, 200), color="white")
        draw = ImageDraw.Draw(img)

        # Try to use a default font
        try:
            font = ImageFont.load_default()
        except:
            font = None

        # Draw Polish text
        text_lines = [
            "PARAGON",
            "Data: 2024-01-15",
            "Sklep: Test Market",
            "Produkty:",
            "- Chleb 5.99 zł",
            "- Mleko 3.50 zł",
            "SUMA: 11.49 zł",
        ]

        y_position = 20
        for line in text_lines:
            draw.text((20, y_position), line, fill="black", font=font)
            y_position += 25

        # Test OCR with Polish language
        try:
            pytesseract.image_to_string(img, lang="pol")
            return True
        except Exception:

            # Try with English as fallback
            try:
                pytesseract.image_to_string(img, lang="eng")
                return True
            except Exception:
                return False

    except Exception:
        return False


def test_backend_ocr_integration():
    """Test backend OCR integration"""

    try:
        # Add src to Python path
        src_path = Path(__file__).parent.parent / "src"
        sys.path.insert(0, str(src_path))

        # Test importing OCR modules
        from backend.core.ocr import OCRProcessor, process_image_file


        # Test OCRProcessor initialization
        processor = OCRProcessor()

        # Test configuration
        processor._get_tesseract_config()

        return True

    except ImportError:
        return False
    except Exception:
        return False


def main():
    """Run all Tesseract tests"""

    tests = [
        ("Tesseract Installation", test_tesseract_installation),
        ("Available Languages", test_tesseract_languages),
        ("Python pytesseract", test_pytesseract_import),
        ("OCR with Polish", test_ocr_with_polish),
        ("Backend Integration", test_backend_ocr_integration),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception:
            results.append((test_name, False))

    # Summary

    passed = 0
    total = len(results)

    for test_name, result in results:
        if result:
            passed += 1


    if passed == total:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
