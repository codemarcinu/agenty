from enum import Enum
import logging
from typing import ClassVar, TypedDict

from core.language_detector import language_detector

logger = logging.getLogger(__name__)


class ModelTask(str, Enum):
    """Typy zadań dla modeli AI"""

    TEXT_ONLY = "text_only"
    IMAGE_ANALYSIS = "image_analysis"
    CODE_GENERATION = "code_generation"
    CREATIVE = "creative"
    RAG = "rag"  # Retrieval Augmented Generation
    STRUCTURED_OUTPUT = "structured_output"


class ModelCapability(TypedDict):
    languages: dict[str, float]
    tasks: dict[ModelTask, float]
    context_length: int


class ModelSelector:
    """
    Klasa odpowiedzialna za inteligentny wybór modelu językowego
    w zależności od zadania, języka i złożoności.

    Implementuje logikę:
    - Bielik dla zapytań w języku polskim
    - Gemma dla zapytań w innych językach
    - Gemma dla zadań multimodalnych (analiza obrazów)
    - Gemma dla bardzo złożonych zadań
    """

    # Modele domyślne
    DEFAULT_POLISH_MODEL = "aya:8b"
    DEFAULT_INTERNATIONAL_MODEL = "aya:8b"

    # Moce przetwarzania poszczególnych modeli (arbitralne wartości)
    MODEL_CAPABILITIES: ClassVar[dict[str, ModelCapability]] = {
        "aya:8b": {
            "languages": {"pl": 0.95, "en": 0.85, "de": 0.75, "fr": 0.75, "es": 0.75},
            "tasks": {
                ModelTask.TEXT_ONLY: 0.95,
                ModelTask.CODE_GENERATION: 0.8,
                ModelTask.CREATIVE: 0.9,
                ModelTask.RAG: 0.9,
                ModelTask.STRUCTURED_OUTPUT: 0.8,
                ModelTask.IMAGE_ANALYSIS: 0.0,  # Nie obsługuje obrazów
            },
            "context_length": 32000,
        },
        "llama3.2:3b": {
            "languages": {"pl": 0.7, "en": 0.9, "de": 0.6, "fr": 0.6, "es": 0.6},
            "tasks": {
                ModelTask.TEXT_ONLY: 0.8,
                ModelTask.CODE_GENERATION: 0.6,
                ModelTask.CREATIVE: 0.7,
                ModelTask.RAG: 0.7,
                ModelTask.STRUCTURED_OUTPUT: 0.6,
                ModelTask.IMAGE_ANALYSIS: 0.0,
            },
            "context_length": 8192,
        },
        "llava:7b": {
            "languages": {"pl": 0.6, "en": 0.8, "de": 0.5, "fr": 0.5, "es": 0.5},
            "tasks": {
                ModelTask.TEXT_ONLY: 0.7,
                ModelTask.CODE_GENERATION: 0.5,
                ModelTask.CREATIVE: 0.6,
                ModelTask.RAG: 0.6,
                ModelTask.STRUCTURED_OUTPUT: 0.5,
                ModelTask.IMAGE_ANALYSIS: 0.9,  # Obsługuje obrazy
            },
            "context_length": 16384,
        },
    }

    DEFAULT_CAPABILITY: ClassVar[ModelCapability] = {
        "languages": {},
        "tasks": {},
        "context_length": 0,
    }

    def __init__(self) -> None:
        """Inicjalizacja selektora modeli"""
        self.language_detector = language_detector
        logger.info("ModelSelector initialized")

    def select_model(
        self,
        query: str,
        task: ModelTask = ModelTask.TEXT_ONLY,
        complexity: float = 0.5,
        contains_images: bool = False,
        context_length: int = 0,
        available_models: list[str] | None = None,
    ) -> str:
        """
        Wybiera najlepszy model dla danego zapytania i zadania.

        Args:
            query: Tekst zapytania
            task: Typ zadania do wykonania
            complexity: Złożoność zadania (0.0-1.0)
            contains_images: Czy zapytanie zawiera obrazy
            context_length: Szacowana długość kontekstu
            available_models: Lista dostępnych modeli (opcjonalnie)

        Returns:
            str: Nazwa najlepszego modelu
        """
        # Domyślna lista modeli
        if available_models is None:
            available_models = list(self.MODEL_CAPABILITIES.keys())

        # Wykryj język zapytania
        detected_language, language_confidence = self.language_detector.detect_language(
            query
        )
        logger.info(
            f"Detected language: {detected_language} (confidence: {language_confidence:.2f})"
        )

        # Przesiej modele pod kątem wymagań
        candidate_models = available_models.copy()

        # Jeśli zapytanie zawiera obrazy, wymaga modelu multimodalnego
        if contains_images:
            candidate_models = [
                model
                for model in candidate_models
                if self.MODEL_CAPABILITIES.get(model, self.DEFAULT_CAPABILITY)[
                    "tasks"
                ].get(ModelTask.IMAGE_ANALYSIS, 0)
                > 0
            ]
            logger.info(f"Filtered to multimodal models: {candidate_models}")

            # Jeśli nie ma dostępnych modeli multimodalnych
            if not candidate_models:
                logger.warning("No multimodal models available, falling back to Gemma")
                return self.DEFAULT_INTERNATIONAL_MODEL

        # Jeśli kontekst jest duży, potrzebujemy modelu z dużym kontekstem
        if context_length > 0:
            candidate_models = [
                model
                for model in candidate_models
                if self.MODEL_CAPABILITIES.get(model, self.DEFAULT_CAPABILITY)[
                    "context_length"
                ]
                >= context_length
            ]
            logger.info(f"Filtered to large context models: {candidate_models}")

            # Jeśli nie ma modeli z wystarczającym kontekstem
            if not candidate_models:
                logger.warning(
                    f"No models with sufficient context length ({context_length}), "
                    + "selecting model with largest context"
                )
                return max(
                    available_models,
                    key=lambda m: self.MODEL_CAPABILITIES.get(
                        m, self.DEFAULT_CAPABILITY
                    )["context_length"],
                )

        # Wartości do oceny modeli
        model_scores: dict[str, float] = {}

        for model in candidate_models:
            # Dodaj punkty za dopasowanie językowe
            language_score = self.MODEL_CAPABILITIES.get(
                model, self.DEFAULT_CAPABILITY
            )["languages"].get(detected_language, 0.5)

            # Dodaj punkty za obsługę zadania
            task_score = self.MODEL_CAPABILITIES.get(model, self.DEFAULT_CAPABILITY)[
                "tasks"
            ].get(task, 0.5)

            # Wynik końcowy - ważona suma
            if detected_language == "pl":
                # Dla polskich zapytań język ma większe znaczenie
                final_score = 0.6 * language_score + 0.4 * task_score
            else:
                # Dla innych języków zadanie ma większe znaczenie
                final_score = 0.4 * language_score + 0.6 * task_score

            # Preferuj Bielik-4.5B dla większości zadań (bonus)
            if model == self.DEFAULT_POLISH_MODEL:
                final_score += 0.1

            # Dla bardzo złożonych zadań i zadań wymagających obrazów preferuj Gemmę
            if (
                complexity > 0.8
                and task == ModelTask.IMAGE_ANALYSIS
                and model == self.DEFAULT_INTERNATIONAL_MODEL
            ):
                final_score += 0.3

            model_scores[model] = final_score

        # Wybierz model z najwyższym wynikiem
        if model_scores:
            best_model = max(model_scores.items(), key=lambda x: x[1])[0]
            logger.info(
                f"Selected model {best_model} with score {model_scores[best_model]:.2f} (lang: {detected_language}, task: {task}, complexity: {complexity:.2f})"
            )
            return best_model

        # Fallback - dla polskiego Bielik, dla innych Gemma
        if detected_language == "pl":
            logger.info(
                "No suitable models found, falling back to default Polish model"
            )
            return self.DEFAULT_POLISH_MODEL
        logger.info(
            "No suitable models found, falling back to default international model"
        )
        return self.DEFAULT_INTERNATIONAL_MODEL

    def is_multimodal_task(self, task: ModelTask) -> bool:
        """Sprawdza, czy zadanie wymaga modelu multimodalnego"""
        return task in [ModelTask.IMAGE_ANALYSIS]

    def is_complex_task(self, task: ModelTask) -> bool:
        """Sprawdza, czy zadanie jest złożone"""
        return task in [
            ModelTask.CODE_GENERATION,
            ModelTask.RAG,
            ModelTask.STRUCTURED_OUTPUT,
        ]


# Singleton instance
model_selector = ModelSelector()
