"""
Receipt Import Agent - odpowiedzialny za kontakt z API OCR i wstępne clean-up
Zgodnie z rekomendacjami audytu - single responsibility principle
"""

import logging
from typing import Any

from pydantic import BaseModel, ValidationError

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.decorators import handle_exceptions
from core.ocr import process_image_file, process_pdf_file

logger = logging.getLogger(__name__)


class ReceiptImportInput(BaseModel):
    """Model wejściowy dla ReceiptImportAgent."""

    file_bytes: bytes
    file_type: str
    filename: str = "unknown"


class ReceiptImportAgent(BaseAgent):
    """
    Agent importu paragonów - odpowiedzialny wyłącznie za kontakt z API OCR +
    wstępne clean-up.

    Zgodnie z zasadą single responsibility:
    - Kontakt z API OCR
    - Wstępne clean-up tekstu
    - Zapis surowego JSON
    """

    def __init__(
        self,
        name: str = "ReceiptImportAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        """Inicjalizuje ReceiptImportAgent."""
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )
        self.TIMEOUT = kwargs.get("timeout", 30)
        self.default_language = kwargs.get("language", "eng")

    @handle_exceptions(max_retries=1, retry_delay=0.5)
    async def process(
        self, input_data: ReceiptImportInput | dict[str, Any]
    ) -> AgentResponse:
        """
        Przetwarza plik paragonu i wyciąga surowy tekst OCR.

        Args:
            input_data: Dane wejściowe z plikiem do przetworzenia

        Returns:
            AgentResponse: Odpowiedź z surowym tekstem OCR
        """
        try:
            if not isinstance(input_data, ReceiptImportInput):
                input_data = ReceiptImportInput.model_validate(input_data)
        except ValidationError as ve:
            return AgentResponse(
                success=False,
                error=f"Błąd walidacji danych wejściowych: {ve}",
            )

        file_bytes: bytes = input_data.file_bytes
        file_type: str = input_data.file_type.lower()
        filename: str = input_data.filename

        try:
            logger.info(f"Rozpoczynam import paragonu: {filename}")

            # Step 1: OCR Processing
            if file_type == "image":
                text = process_image_file(file_bytes, timeout=self.TIMEOUT)
            elif file_type == "pdf":
                text = process_pdf_file(file_bytes, timeout=self.TIMEOUT)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Nieobsługiwany typ pliku: {file_type}",
                )

            if not text:
                return AgentResponse(
                    success=False,
                    error="Nie udało się rozpoznać tekstu z pliku. Sprawdź czy plik jest czytelny.",
                )

            # Step 2: Wstępne clean-up tekstu
            cleaned_text = self._basic_text_cleanup(text)

            # Step 3: Przygotuj surowy JSON do zapisu
            raw_data = {
                "filename": filename,
                "file_type": file_type,
                "file_size": len(file_bytes),
                "ocr_text": cleaned_text,
                "original_text": text,  # Zachowaj oryginalny tekst
                "processing_timestamp": self._get_timestamp(),
                "agent_version": "1.0",
                "processing_stage": "import",
            }

            logger.info(
                f"Import paragonu zakończony: {filename}",
                extra={
                    "text_length": len(cleaned_text),
                    "file_type": file_type,
                    "file_size": len(file_bytes),
                },
            )

            return AgentResponse(
                success=True,
                text=cleaned_text,
                data=raw_data,
                message=f"Pomyślnie zaimportowano paragon: {filename}",
                metadata={
                    "file_type": file_type,
                    "filename": filename,
                    "text_length": len(cleaned_text),
                    "processing_stage": "import",
                },
            )

        except TimeoutError:
            return AgentResponse(
                success=False,
                error=f"Import przekroczył limit czasu ({self.TIMEOUT} sekund).",
            )
        except Exception as e:
            logger.error(f"Błąd podczas importu paragonu {filename}: {e!s}")
            return AgentResponse(
                success=False,
                error=f"Wystąpił błąd podczas importu: {e!s}",
            )

    def _basic_text_cleanup(self, text: str) -> str:
        """
        Wstępne clean-up tekstu OCR.

        Args:
            text: Surowy tekst z OCR

        Returns:
            str: Wyczyczony tekst
        """
        if not text:
            return text

        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Usuń puste linie
            if not line.strip():
                continue

            # Usuń znaki kontrolne
            cleaned_line = "".join(
                char for char in line if ord(char) >= 32 or char == "\t"
            )

            # Usuń nadmiarowe spacje
            cleaned_line = " ".join(cleaned_line.split())

            if cleaned_line:
                cleaned_lines.append(cleaned_line)

        return "\n".join(cleaned_lines)

    def _get_timestamp(self) -> str:
        """Zwraca aktualny timestamp w formacie ISO."""
        from datetime import datetime

        return datetime.now().isoformat()

    def get_metadata(self) -> dict[str, Any]:
        """Zwraca metadane agenta."""
        return {
            "name": self.name,
            "type": "ReceiptImportAgent",
            "capabilities": ["OCR processing", "text cleanup", "raw data export"],
            "version": "1.0",
            "processing_stage": "import",
        }

    def get_dependencies(self) -> list:
        """Lista zależności agenta."""
        return []

    def is_healthy(self) -> bool:
        """Sprawdza czy agent jest zdrowy."""
        return True
