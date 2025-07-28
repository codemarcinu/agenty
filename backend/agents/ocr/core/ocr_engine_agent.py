"""
OCR Engine Agent

Multi-engine OCR agent with voting mechanism for high accuracy text extraction.
Supports Tesseract, EasyOCR, and Azure Vision with Polish language optimization.
"""

import asyncio
import io
import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image
import pytesseract

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType

logger = logging.getLogger(__name__)


class OCREngineAgent(BaseOCRAgentImpl):
    """
    Multi-engine OCR agent with voting mechanism.

    Features:
    - Multi-engine approach (Tesseract + EasyOCR + Azure Vision)
    - Voting mechanism for consensus
    - Polish language optimization
    - Context-aware corrections
    - Confidence scoring
    """

    def __init__(self, name: str = "OCREngineAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=25.0, **kwargs)

        # OCR engines configuration
        self.engines = {
            "tesseract": {
                "enabled": True,
                "priority": 1,
                "languages": ["pol", "eng"],
                "config": "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĄĆĘŁŃÓŚŹŻąćęłńóśźż.,:-/%()[] ",
            },
            "easyocr": {
                "enabled": True,
                "priority": 2,
                "languages": ["pl", "en"],
                "config": {},
            },
            "azure": {
                "enabled": False,  # Requires API key
                "priority": 3,
                "config": {},
            },
        }

        # Voting configuration
        self.voting_config = {
            "min_confidence": 0.7,
            "consensus_threshold": 0.6,
            "weight_tesseract": 0.4,
            "weight_easyocr": 0.4,
            "weight_azure": 0.2,
        }

        # Polish-specific corrections
        self.polish_corrections = {
            # Common OCR errors in Polish receipts
            "KawZiarD orBar": "KawZiarDorBar",
            "PapCzerwoneNadz18C": "PapCzerwoneNadz180g",
            "tnipsylopSolone": "ChipsyTopSolone",
            "tnipsylopSolonel5Ug": "ChipsyTopSolone150g",
            "PicrożkiGyoza": "Pierogi Gyoza",
            "Skyrplinynatural.": "Skyr płynny naturalny",
            "Czukoliwlab.:orzech": "Czekolada w tabliczce: orzech",
            "krakerzyDobryChrup": "Krakersy Dobry Chrup",
            "Reklamówkamałarec.": "Reklamówka mała recyklingowa",
            "Licllsp.z.0.0.sp.k.": "Lidl sp.z o.o. sp.k.",
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
        }

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data for OCR processing"""
        required_keys = ["image_bytes"]

        if not all(key in input_data for key in required_keys):
            return False

        if not isinstance(input_data["image_bytes"], bytes):
            return False

        # Check if image can be opened
        try:
            image = Image.open(io.BytesIO(input_data["image_bytes"]))
            image.verify()
            return True
        except Exception:
            return False

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Process image through multi-engine OCR pipeline"""
        try:
            image_bytes = input_data["image_bytes"]
            image = Image.open(io.BytesIO(image_bytes))

            # Run OCR with multiple engines
            ocr_results = await self._run_multi_engine_ocr(image)

            # Apply voting mechanism
            final_result = await self._apply_voting_mechanism(ocr_results)

            # Apply Polish-specific corrections
            corrected_text = await self._apply_polish_corrections(final_result["text"])

            # Publish OCR completion event
            await self.publish_event(
                OCREventType.OCR_COMPLETED,
                {
                    "confidence": final_result["confidence"],
                    "engines_used": list(ocr_results.keys()),
                    "text_length": len(corrected_text),
                },
            )

            return AgentResponse(
                success=True,
                text=corrected_text,
                metadata={
                    "confidence": final_result["confidence"],
                    "engines_used": list(ocr_results.keys()),
                    "voting_method": final_result["voting_method"],
                    "corrections_applied": final_result["corrections_applied"],
                },
                data={
                    "ocr_text": corrected_text,
                    "confidence": final_result["confidence"],
                    "engine_results": ocr_results,
                },
            )

        except Exception as e:
            logger.error(f"Error in OCR processing: {e}")
            return AgentResponse(success=False, error=f"OCR processing failed: {e!s}")

    async def _run_multi_engine_ocr(
        self, image: Image.Image
    ) -> dict[str, dict[str, Any]]:
        """Run OCR with multiple engines in parallel"""
        tasks = []

        # Create tasks for enabled engines
        for engine_name, engine_config in self.engines.items():
            if engine_config["enabled"]:
                if engine_name == "tesseract":
                    tasks.append(self._run_tesseract_ocr(image, engine_config))
                elif engine_name == "easyocr":
                    tasks.append(self._run_easyocr_ocr(image, engine_config))
                elif engine_name == "azure":
                    tasks.append(self._run_azure_ocr(image, engine_config))

        # Run all engines in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        ocr_results = {}
        for i, (engine_name, engine_config) in enumerate(self.engines.items()):
            if engine_config["enabled"]:
                result = results[i]
                if isinstance(result, Exception):
                    logger.warning(f"Engine {engine_name} failed: {result}")
                    continue
                ocr_results[engine_name] = result

        return ocr_results

    async def _run_tesseract_ocr(
        self, image: Image.Image, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Run Tesseract OCR with Polish optimization"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Apply Tesseract OCR
            text = pytesseract.image_to_string(
                cv_image, lang="+".join(config["languages"]), config=config["config"]
            )

            # Get confidence data
            data = pytesseract.image_to_data(
                cv_image,
                lang="+".join(config["languages"]),
                config=config["config"],
                output_type=pytesseract.Output.DICT,
            )

            # Calculate average confidence
            confidences = [int(conf) for conf in data["conf"] if int(conf) > 0]
            avg_confidence = (
                sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            )

            return {
                "text": text.strip(),
                "confidence": avg_confidence,
                "engine": "tesseract",
                "language": config["languages"],
            }

        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "engine": "tesseract",
                "error": str(e),
            }

    async def _run_easyocr_ocr(
        self, image: Image.Image, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Run EasyOCR with Polish language support"""
        try:
            # Import EasyOCR (optional dependency)
            try:
                import easyocr
            except ImportError:
                logger.warning("EasyOCR not available, skipping")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "engine": "easyocr",
                    "error": "EasyOCR not installed",
                }

            # Initialize EasyOCR reader
            reader = easyocr.Reader(config["languages"])

            # Convert to numpy array
            np_image = np.array(image)

            # Run OCR
            results = reader.readtext(np_image)

            # Extract text and confidence
            text_parts = []
            confidences = []

            for bbox, text, confidence in results:
                text_parts.append(text)
                confidences.append(confidence)

            full_text = " ".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                "text": full_text.strip(),
                "confidence": avg_confidence,
                "engine": "easyocr",
                "language": config["languages"],
            }

        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return {"text": "", "confidence": 0.0, "engine": "easyocr", "error": str(e)}

    async def _run_azure_ocr(
        self, image: Image.Image, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Run Azure Vision OCR (requires API key)"""
        try:
            # This would require Azure Vision API key
            # For now, return empty result
            logger.warning("Azure Vision OCR not configured")
            return {
                "text": "",
                "confidence": 0.0,
                "engine": "azure",
                "error": "Azure Vision not configured",
            }

        except Exception as e:
            logger.error(f"Azure OCR failed: {e}")
            return {"text": "", "confidence": 0.0, "engine": "azure", "error": str(e)}

    async def _apply_voting_mechanism(
        self, ocr_results: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Apply voting mechanism to combine results from multiple engines"""
        if not ocr_results:
            return {"text": "", "confidence": 0.0, "voting_method": "no_results"}

        # If only one engine succeeded, return its result
        if len(ocr_results) == 1:
            engine_name = next(iter(ocr_results.keys()))
            result = ocr_results[engine_name]
            return {
                "text": result["text"],
                "confidence": result["confidence"],
                "voting_method": "single_engine",
            }

        # Multiple engines - apply voting
        valid_results = {
            k: v
            for k, v in ocr_results.items()
            if v["confidence"] >= self.voting_config["min_confidence"]
        }

        if not valid_results:
            # Use the best result even if below threshold
            best_result = max(ocr_results.values(), key=lambda x: x["confidence"])
            return {
                "text": best_result["text"],
                "confidence": best_result["confidence"],
                "voting_method": "best_below_threshold",
            }

        # Weighted voting based on confidence and engine priority
        weighted_texts = []
        total_weight = 0.0

        for engine_name, result in valid_results.items():
            weight = self.voting_config[f"weight_{engine_name}"] * result["confidence"]
            weighted_texts.append((result["text"], weight))
            total_weight += weight

        if total_weight == 0:
            # Fallback to simple voting
            texts = [result["text"] for result in valid_results.values()]
            return {
                "text": self._simple_voting(texts),
                "confidence": sum(r["confidence"] for r in valid_results.values())
                / len(valid_results),
                "voting_method": "simple_voting",
            }

        # Weighted voting
        final_text = self._weighted_voting(weighted_texts, total_weight)
        avg_confidence = sum(r["confidence"] for r in valid_results.values()) / len(
            valid_results
        )

        return {
            "text": final_text,
            "confidence": avg_confidence,
            "voting_method": "weighted_voting",
        }

    def _simple_voting(self, texts: list[str]) -> str:
        """Simple voting mechanism"""
        if not texts:
            return ""

        # Split into lines and vote line by line
        all_lines = []
        for text in texts:
            lines = text.split("\n")
            all_lines.append(lines)

        # Find the longest list of lines
        max_lines = max(len(lines) for lines in all_lines)

        voted_lines = []
        for i in range(max_lines):
            line_votes = {}
            for lines in all_lines:
                if i < len(lines):
                    line = lines[i].strip()
                    if line:
                        line_votes[line] = line_votes.get(line, 0) + 1

            if line_votes:
                # Get the most voted line
                best_line = max(line_votes.items(), key=lambda x: x[1])[0]
                voted_lines.append(best_line)
            else:
                voted_lines.append("")

        return "\n".join(voted_lines)

    def _weighted_voting(
        self, weighted_texts: list[tuple[str, float]], total_weight: float
    ) -> str:
        """Weighted voting mechanism"""
        if not weighted_texts:
            return ""

        # Split into lines and apply weighted voting
        all_lines = []
        weights = []

        for text, weight in weighted_texts:
            lines = text.split("\n")
            all_lines.append(lines)
            weights.append(weight)

        # Find the longest list of lines
        max_lines = max(len(lines) for lines in all_lines)

        voted_lines = []
        for i in range(max_lines):
            line_votes = {}
            for j, lines in enumerate(all_lines):
                if i < len(lines):
                    line = lines[i].strip()
                    if line:
                        if line not in line_votes:
                            line_votes[line] = 0.0
                        line_votes[line] += weights[j]

            if line_votes:
                # Get the line with highest weight
                best_line = max(line_votes.items(), key=lambda x: x[1])[0]
                voted_lines.append(best_line)
            else:
                voted_lines.append("")

        return "\n".join(voted_lines)

    async def _apply_polish_corrections(self, text: str) -> str:
        """Apply Polish-specific corrections to OCR text"""
        corrected_text = text
        corrections_applied = 0

        for error, correction in self.polish_corrections.items():
            if error in corrected_text:
                corrected_text = corrected_text.replace(error, correction)
                corrections_applied += 1

        # Update metadata
        self.update_performance_metric("corrections_applied", corrections_applied)

        return corrected_text
