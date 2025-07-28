"""
Base classes and interfaces for OCR agents.
"""

from .base_ocr_agent import BaseOCRAgent
from .ocr_agent_interface import OCREventType, OCRMessageBus

__all__ = [
    "BaseOCRAgent",
    "OCREventType",
    "OCRMessageBus",
]
