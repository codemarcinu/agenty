"""
OCR (Optical Character Recognition) agents package.
Contains specialized agents for text extraction from images and documents.
"""

# Import the new specialized OCR components
try:
    from .specialized_ocr_llm import OCRModelOrchestrator, SpecializedOCRAgent

    SPECIALIZED_OCR_AVAILABLE = True
except ImportError:
    SPECIALIZED_OCR_AVAILABLE = False

# Import legacy components if they exist
try:
    from .orchestrator import OCROrchestrator as LegacyOCROrchestrator

    LEGACY_OCR_AVAILABLE = True
except ImportError:
    LEGACY_OCR_AVAILABLE = False

# Export available components
__all__ = []

if SPECIALIZED_OCR_AVAILABLE:
    __all__.extend(["SpecializedOCRAgent", "OCRModelOrchestrator"])

if LEGACY_OCR_AVAILABLE:
    __all__.append("LegacyOCROrchestrator")

__version__ = "1.0.0"
