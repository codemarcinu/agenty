"""
Enhanced Local LLM-based Agents for Receipt Processing
Optimized for offline operation with local models and specialized OCR capabilities.
"""

from dataclasses import dataclass
from enum import Enum
import json
import logging
from pathlib import Path
import re
import time
from typing import Any

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.llm_client import ollama_client

logger = logging.getLogger(__name__)


class LocalModelType(str, Enum):
    """Types of local models optimized for different tasks"""

    GENERAL = "llama3.2:3b"  # Szybki model do ogólnych zadań
    REASONING = "llama3.2:8b"  # Model do złożonego rozumowania
    OCR_SPECIALIZED = "llava:7b"  # Model z obsługą vision dla OCR
    POLISH_OPTIMIZED = "aya:8b"  # Model zoptymalizowany dla języka polskiego


@dataclass
class LocalProcessingConfig:
    """Configuration for local processing optimization"""

    max_context_length: int = 4096
    temperature: float = 0.1  # Niska temperatura dla deterministic results
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    timeout_seconds: int = 30
    enable_caching: bool = True
    batch_size: int = 1  # Dla local processing zazwyczaj 1
    gpu_acceleration: bool = True


class LocalReceiptAnalysisAgent(BaseAgent):
    """
    Enhanced Receipt Analysis Agent optimized for local LLM processing.
    Focuses on Polish receipts with offline capabilities.
    """

    def __init__(self, name: str = "LocalReceiptAnalysisAgent", **kwargs):
        super().__init__(name=name, **kwargs)
        self.config = LocalProcessingConfig()
        self.model_type = LocalModelType.REASONING
        self.polish_store_patterns = self._load_polish_store_patterns()
        self.local_cache = {}

    def _load_polish_store_patterns(self) -> dict[str, dict[str, Any]]:
        """Load Polish store-specific patterns for better recognition"""
        return {
            "lidl": {
                "indicators": ["lidl", "neckermann", "schwarz"],
                "product_patterns": ["k."],
                "price_format": r"\d+,\d{2}",
                "typical_products": ["pestogustobel", "freeway", "pilos"],
            },
            "biedronka": {
                "indicators": ["biedronka", "jeronimo martins"],
                "product_patterns": ["bio", "dobre i tanie"],
                "price_format": r"\d+,\d{2}",
                "typical_products": ["bio jajka", "dobre i tanie"],
            },
            "kaufland": {
                "indicators": ["kaufland", "schwarz gruppe"],
                "product_patterns": ["k&h", "jeden dzień"],
                "price_format": r"\d+,\d{2}",
                "typical_products": ["k&h", "jeden dzień"],
            },
            "żabka": {
                "indicators": ["żabka", "zabka"],
                "product_patterns": ["żabka"],
                "price_format": r"\d+,\d{2}",
                "typical_products": ["hot dog", "kawa żabka"],
            },
        }

    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Process receipt using local LLM with Polish-optimized prompts.
        """
        try:
            ocr_text = input_data.get("ocr_text", "")
            if not ocr_text:
                return AgentResponse(success=False, error="Brak tekstu OCR do analizy")

            logger.info(
                f"Processing receipt with local LLM, text length: {len(ocr_text)}"
            )

            # Step 1: Pre-analysis with local patterns
            store_hints = self._detect_store_locally(ocr_text)

            # Step 2: Enhanced prompt for local LLM
            enhanced_prompt = self._create_enhanced_polish_prompt(ocr_text, store_hints)

            # Step 3: Process with local LLM
            analysis_result = await self._process_with_local_llm(enhanced_prompt)

            # Step 4: Post-process and validate
            validated_result = self._validate_and_enhance_locally(
                analysis_result, ocr_text
            )

            return AgentResponse(
                success=True,
                data=validated_result,
                metadata={
                    "processing_time": validated_result.get("processing_time"),
                    "model_used": self.model_type.value,
                    "store_detected": validated_result.get("store_name"),
                    "confidence": validated_result.get("confidence", 0.8),
                },
            )

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            return AgentResponse(
                success=False, error=f"Błąd podczas analizy paragonu: {e!s}"
            )

    def _detect_store_locally(self, text: str) -> dict[str, Any]:
        """Fast local pattern-based store detection"""
        text_lower = text.lower()
        detected_stores = []

        for store_name, patterns in self.polish_store_patterns.items():
            for indicator in patterns["indicators"]:
                if indicator in text_lower:
                    detected_stores.append(
                        {"name": store_name, "confidence": 0.9, "indicator": indicator}
                    )
                    break

        return {
            "detected_stores": detected_stores,
            "primary_store": (
                detected_stores[0]["name"] if detected_stores else "nieznany"
            ),
        }

    def _create_enhanced_polish_prompt(
        self, ocr_text: str, store_hints: dict[str, Any]
    ) -> str:
        """Create optimized prompt for local Polish LLM"""
        primary_store = store_hints.get("primary_store", "nieznany")

        prompt = f"""
Analizujesz paragon ze sklepu w Polsce.
Wykryty sklep: {primary_store}

TEKST PARAGONU:
{ocr_text}

ZADANIE: Wyodrębnij strukturalne dane w formacie JSON:

{{
    "store_name": "nazwa sklepu (Lidl/Biedronka/Kaufland/Żabka/inny)",
    "date": "data w formacie DD.MM.YYYY",
    "time": "godzina w formacie HH:MM",
    "total_amount": kwota_całkowita_jako_liczba,
    "items": [
        {{
            "name": "znormalizowana nazwa produktu",
            "quantity": ilość_jako_liczba,
            "unit_price": cena_jednostkowa_jako_liczba,
            "total_price": cena_całkowita_jako_liczba,
            "category": "kategoria produktu"
        }}
    ],
    "payment_method": "metoda płatności",
    "confidence": ocena_pewności_od_0_do_1
}}

WAŻNE ZASADY:
1. Używaj polskich nazw kategorii: "Napoje", "Pieczywo", "Mięso", "Nabiał", "Owoce i warzywa"
2. Normalizuj nazwy produktów (bez błędów OCR)
3. Wszystkie ceny jako liczby (nie stringi)
4. Usuń duplikaty i pozycje niebędące produktami
5. Jeśli suma się nie zgadza, użyj sumy produktów
6. Odpowiedz TYLKO w JSON, bez dodatkowych komentarzy
"""
        return prompt

    async def _process_with_local_llm(self, prompt: str) -> dict[str, Any]:
        """Process with local Ollama model optimized for structured output"""
        try:
            start_time = time.time()

            # Use optimized parameters for local processing
            response = await ollama_client.chat(
                model=self.model_type.value,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                    "repeat_penalty": self.config.repeat_penalty,
                    "num_ctx": self.config.max_context_length,
                },
            )

            processing_time = time.time() - start_time

            # Extract JSON from response
            response_text = response["message"]["content"]
            json_result = self._extract_json_from_response(response_text)
            json_result["processing_time"] = processing_time

            return json_result

        except Exception as e:
            logger.error(f"Error in local LLM processing: {e}")
            raise

    def _extract_json_from_response(self, response_text: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling various formats"""
        # Try to find JSON block
        json_pattern = r"\{.*\}"
        json_match = re.search(json_pattern, response_text, re.DOTALL)

        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from LLM response")

        # Fallback: create basic structure
        return {
            "store_name": "Nieznany sklep",
            "date": "Nieznana data",
            "total_amount": 0,
            "items": [],
            "confidence": 0.3,
        }

    def _validate_and_enhance_locally(
        self, result: dict[str, Any], original_text: str
    ) -> dict[str, Any]:
        """Local validation and enhancement of results"""
        # Mathematical validation
        items = result.get("items", [])
        if items:
            calculated_total = sum(
                item.get("quantity", 1) * item.get("unit_price", 0) for item in items
            )
            receipt_total = result.get("total_amount", 0)

            if abs(calculated_total - receipt_total) > 0.01:
                logger.info(f"Correcting total: {receipt_total} → {calculated_total}")
                result["total_amount"] = calculated_total
                result["total_corrected"] = True

        # Store name enhancement
        if result.get("store_name") == "Nieznany sklep":
            store_hints = self._detect_store_locally(original_text)
            if store_hints["primary_store"] != "nieznany":
                result["store_name"] = store_hints["primary_store"].title()

        # Category normalization
        for item in result.get("items", []):
            if "category" in item:
                item["category"] = self._normalize_category(item["category"])

        return result

    def _normalize_category(self, category: str) -> str:
        """Normalize product categories to Polish standards"""
        category_mapping = {
            "beverages": "Napoje",
            "bread": "Pieczywo",
            "meat": "Mięso i wędliny",
            "dairy": "Nabiał",
            "fruits": "Owoce i warzywa",
            "vegetables": "Owoce i warzywa",
            "snacks": "Przekąski",
            "frozen": "Mrożonki",
            "coffee": "Napoje > Kawa i herbata",
            "tea": "Napoje > Kawa i herbata",
        }

        category_lower = category.lower()
        for eng, pol in category_mapping.items():
            if eng in category_lower:
                return pol

        return category  # Return original if no mapping found


class LocalOCREnhancementAgent(BaseAgent):
    """
    Specialized agent for OCR enhancement using vision-capable local models.
    Uses LLaVA or similar vision models for direct image-to-text processing.
    """

    def __init__(self, name: str = "LocalOCREnhancementAgent", **kwargs):
        super().__init__(name=name, **kwargs)
        self.model_type = LocalModelType.OCR_SPECIALIZED
        self.config = LocalProcessingConfig()

    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Process receipt image directly with vision model for enhanced OCR.
        """
        try:
            image_path = input_data.get("image_path")
            fallback_text = input_data.get("fallback_ocr_text", "")

            if not image_path and not fallback_text:
                return AgentResponse(success=False, error="Brak obrazu ani tekstu OCR")

            # Try vision model first if image available
            if image_path and Path(image_path).exists():
                vision_result = await self._process_with_vision_model(image_path)
                if vision_result["success"]:
                    return AgentResponse(
                        success=True,
                        data=vision_result["data"],
                        metadata={
                            "method": "vision_model",
                            "model": self.model_type.value,
                        },
                    )

            # Fallback to text enhancement
            if fallback_text:
                enhanced_result = await self._enhance_existing_ocr(fallback_text)
                return AgentResponse(
                    success=True,
                    data=enhanced_result,
                    metadata={"method": "text_enhancement"},
                )

            return AgentResponse(
                success=False, error="Nie udało się przetworzyć obrazu ani tekstu"
            )

        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            return AgentResponse(
                success=False, error=f"Błąd podczas ulepszania OCR: {e!s}"
            )

    async def _process_with_vision_model(self, image_path: str) -> dict[str, Any]:
        """Process receipt image with local vision model (LLaVA)"""
        try:
            prompt = """
Przeanalizuj ten paragon i wyodrębnij tekst w sposób strukturalny.
Skoncentruj się na:
1. Nazwie sklepu
2. Dacie i godzinie
3. Produktach z cenami
4. Sumie końcowej

Zwróć czysty tekst paragonu, poprawiając błędy OCR.
"""

            response = await ollama_client.chat(
                model=self.model_type.value,
                messages=[{"role": "user", "content": prompt, "images": [image_path]}],
                options={"temperature": 0.1, "top_p": 0.9},
            )

            extracted_text = response["message"]["content"]

            return {
                "success": True,
                "data": {
                    "enhanced_text": extracted_text,
                    "method": "vision_model",
                    "confidence": 0.85,
                },
            }

        except Exception as e:
            logger.error(f"Vision model processing failed: {e}")
            return {"success": False, "error": str(e)}

    async def _enhance_existing_ocr(self, ocr_text: str) -> dict[str, Any]:
        """Enhance existing OCR text using local LLM"""
        prompt = f"""
Popraw błędy OCR w tekście paragonu. Tekst zawiera błędy rozpoznawania.

ORYGINALNY TEKST OCR:
{ocr_text}

ZADANIE:
1. Popraw błędy literowe (np. "PESTOGUSTOBEL" → "Pesto Gusto Bel")
2. Usuń duplikaty linii
3. Popraw błędnie rozpoznane ceny
4. Zachowaj strukturę paragonu
5. Zwróć tylko poprawiony tekst

POPRAWIONY TEKST:
"""

        try:
            response = await ollama_client.chat(
                model=LocalModelType.REASONING.value,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1},
            )

            enhanced_text = response["message"]["content"]

            return {
                "enhanced_text": enhanced_text,
                "original_text": ocr_text,
                "method": "text_enhancement",
                "confidence": 0.75,
            }

        except Exception as e:
            logger.error(f"Text enhancement failed: {e}")
            return {
                "enhanced_text": ocr_text,  # Fallback to original
                "method": "fallback",
                "confidence": 0.5,
            }


class LocalModelManager:
    """
    Manager for local model lifecycle and optimization.
    Handles model loading, caching, and performance monitoring.
    """

    def __init__(self):
        self.loaded_models: dict[str, bool] = {}
        self.model_performance: dict[str, dict[str, float]] = {}
        self.warmup_completed: dict[str, bool] = {}

    async def ensure_model_loaded(self, model_name: str) -> bool:
        """Ensure model is loaded and ready for inference"""
        try:
            if model_name not in self.loaded_models:
                logger.info(f"Loading model: {model_name}")

                # Try to pull model if not available
                try:
                    await ollama_client.pull(model_name)
                    self.loaded_models[model_name] = True
                    logger.info(f"Model {model_name} loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load model {model_name}: {e}")
                    return False

            # Warmup model with small request
            if not self.warmup_completed.get(model_name, False):
                await self._warmup_model(model_name)
                self.warmup_completed[model_name] = True

            return True

        except Exception as e:
            logger.error(f"Error ensuring model {model_name} is loaded: {e}")
            return False

    async def _warmup_model(self, model_name: str):
        """Warmup model with small request to improve first-call performance"""
        try:
            await ollama_client.chat(
                model=model_name,
                messages=[{"role": "user", "content": "Test"}],
                options={"num_predict": 1},
            )
            logger.info(f"Model {model_name} warmed up successfully")
        except Exception as e:
            logger.warning(f"Model warmup failed for {model_name}: {e}")

    def get_optimal_model_for_task(self, task_type: str) -> str:
        """Get optimal model based on task type and performance metrics"""
        task_model_mapping = {
            "ocr_analysis": LocalModelType.REASONING.value,
            "vision_ocr": LocalModelType.OCR_SPECIALIZED.value,
            "text_enhancement": LocalModelType.REASONING.value,
            "general_processing": LocalModelType.GENERAL.value,
        }

        return task_model_mapping.get(task_type, LocalModelType.GENERAL.value)

    def record_performance(
        self, model_name: str, task_type: str, duration: float, success: bool
    ):
        """Record model performance metrics"""
        if model_name not in self.model_performance:
            self.model_performance[model_name] = {
                "total_requests": 0,
                "total_duration": 0.0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
            }

        metrics = self.model_performance[model_name]
        metrics["total_requests"] += 1
        metrics["total_duration"] += duration
        metrics["avg_duration"] = metrics["total_duration"] / metrics["total_requests"]

        # Update success rate
        success_count = metrics["success_rate"] * (metrics["total_requests"] - 1)
        if success:
            success_count += 1
        metrics["success_rate"] = success_count / metrics["total_requests"]


# Global instance
local_model_manager = LocalModelManager()
