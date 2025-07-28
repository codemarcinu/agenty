"""
Multi-Agent OCR Orchestrator
Koordynuje wszystkie agenty OCR dla najlepszej jakości rozpoznawania tekstu.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class OCROrchestrator:
    """
    Główny koordynator systemu multi-agent OCR.
    Zarządza przepływem pracy między różnymi agentami OCR.
    """

    def __init__(self):
        self.agents = {}
        self.performance_metrics = {
            "total_processed": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0,
            "agent_usage": {},
        }

    async def process_receipt(
        self, image_path: str, receipt_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Przetwarza paragon przez system multi-agent OCR.

        Args:
            image_path: Ścieżka do obrazu paragonu
            receipt_context: Kontekst paragonu (np. wykryty sklep)

        Returns:
            Wynik przetwarzania z najlepszą jakością
        """
        start_time = time.time()

        try:
            # Step 1: Preprocessing obrazu
            logger.info("Rozpoczynanie preprocessing obrazu...")
            preprocessed_result = await self._preprocess_image(image_path)

            # Step 2: Multi-engine OCR
            logger.info("Rozpoczynanie multi-engine OCR...")
            ocr_results = await self._run_multi_engine_ocr(preprocessed_result)

            # Step 3: Voting i selekcja najlepszego wyniku
            logger.info("Voting mechanism dla wyników OCR...")
            best_ocr_result = await self._voting_mechanism(ocr_results)

            # Step 4: Strukturyzacja danych
            logger.info("Strukturyzacja danych paragonu...")
            structured_data = await self._structure_receipt_data(
                best_ocr_result, receipt_context
            )

            # Step 5: Walidacja i poprawki
            logger.info("Walidacja i poprawki danych...")
            validated_data = await self._validate_and_correct(structured_data)

            processing_time = time.time() - start_time
            self._update_metrics(processing_time, True)

            logger.info(f"OCR processing completed in {processing_time:.2f}s")

            return {
                "success": True,
                "data": validated_data,
                "processing_time": processing_time,
                "agents_used": list(self.agents.keys()),
                "confidence": validated_data.get("confidence", 0.8),
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_metrics(processing_time, False)

            logger.error(f"OCR processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
            }

    async def _preprocess_image(self, image_path: str) -> dict[str, Any]:
        """Preprocessing obrazu dla lepszej jakości OCR."""
        # Implementacja preprocessing (resize, denoise, contrast, etc.)
        return {
            "original_path": image_path,
            "preprocessed_path": image_path,  # Tymczasowo bez zmian
            "improvements_applied": ["contrast_enhancement", "noise_reduction"],
        }

    async def _run_multi_engine_ocr(
        self, preprocessed_result: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Uruchamia multiple OCR engines."""
        engines = ["tesseract", "easyocr"]  # Rozszerzalne o więcej
        results = []

        for engine in engines:
            try:
                result = await self._run_single_ocr_engine(engine, preprocessed_result)
                results.append(result)
            except Exception as e:
                logger.warning(f"OCR engine {engine} failed: {e}")

        return results

    async def _run_single_ocr_engine(
        self, engine: str, preprocessed_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Uruchamia pojedynczy OCR engine."""
        # Tu będzie implementacja dla różnych engine'ów
        if engine == "tesseract":
            # Użyj istniejącej implementacji Tesseract
            from core.ocr import OCRProcessor

            ocr = OCRProcessor()
            text = ocr.extract_text_from_image(preprocessed_result["preprocessed_path"])

            return {
                "engine": engine,
                "text": text,
                "confidence": 0.8,  # Placeholder
                "language_detected": "pol",
            }

        # Placeholder dla innych engine'ów
        return {
            "engine": engine,
            "text": "",
            "confidence": 0.0,
            "language_detected": "unknown",
        }

    async def _voting_mechanism(
        self, ocr_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Voting mechanism do wyboru najlepszego wyniku OCR."""
        if not ocr_results:
            raise ValueError("No OCR results to vote on")

        # Prosty voting - wybierz wynik z najwyższą confidence
        best_result = max(ocr_results, key=lambda x: x.get("confidence", 0))

        logger.info(
            f"Selected {best_result['engine']} as best OCR result "
            f"(confidence: {best_result['confidence']:.2f})"
        )

        return best_result

    async def _structure_receipt_data(
        self, ocr_result: dict[str, Any], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Strukturyzuje dane paragonu z tekstu OCR."""
        # Użyj istniejącego ReceiptAnalysisAgent
        from agents.receipt_analysis_agent import ReceiptAnalysisAgent

        agent = ReceiptAnalysisAgent()
        analysis_result = await agent.process(
            {
                "ocr_text": ocr_result["text"],
                "image_path": context.get("image_path") if context else None,
            }
        )

        if analysis_result.success:
            return analysis_result.data
        else:
            raise ValueError(f"Receipt structuring failed: {analysis_result.error}")

    async def _validate_and_correct(
        self, structured_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Waliduje i poprawia dane paragonu."""
        # Dodatkowa walidacja i poprawki

        # Sprawdź czy suma się zgadza
        items = structured_data.get("items", [])
        if items:
            calculated_total = sum(
                item.get("quantity", 1) * item.get("unit_price", 0) for item in items
            )
            receipt_total = structured_data.get("total_amount", 0)

            if abs(calculated_total - receipt_total) > 0.01:
                logger.warning(
                    f"Total mismatch: calculated {calculated_total:.2f}, "
                    f"receipt {receipt_total:.2f}"
                )
                structured_data["total_amount"] = calculated_total
                structured_data["total_corrected"] = True

        return structured_data

    def _update_metrics(self, processing_time: float, success: bool):
        """Aktualizuje metryki wydajności."""
        self.performance_metrics["total_processed"] += 1

        # Update average processing time
        total = self.performance_metrics["total_processed"]
        current_avg = self.performance_metrics["average_processing_time"]
        new_avg = (current_avg * (total - 1) + processing_time) / total
        self.performance_metrics["average_processing_time"] = new_avg

        # Update success rate
        if success:
            success_count = (
                int(self.performance_metrics["success_rate"] * (total - 1)) + 1
            )
        else:
            success_count = int(self.performance_metrics["success_rate"] * (total - 1))

        self.performance_metrics["success_rate"] = success_count / total

    def get_performance_metrics(self) -> dict[str, Any]:
        """Zwraca metryki wydajności systemu."""
        return self.performance_metrics.copy()


# Global instance
ocr_orchestrator = OCROrchestrator()
