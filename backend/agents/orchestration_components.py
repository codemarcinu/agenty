from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any

from agents.interfaces import AgentResponse, IntentData, MemoryContext

logger = logging.getLogger(__name__)


class IIntentDetector(ABC):
    @abstractmethod
    async def detect_intent(self, query: str, context: MemoryContext) -> IntentData:
        """Detects user intent based on query and context."""


class IMemoryManager(ABC):
    @abstractmethod
    async def get_context(self, session_id: str) -> MemoryContext:
        """Retrieves or creates a memory context for a session."""

    @abstractmethod
    async def update_context(
        self, context: MemoryContext, new_data: dict[str, Any]
    ) -> None:
        """Updates the memory context with new data."""


class IResponseGenerator(ABC):
    @abstractmethod
    async def generate_response(
        self, context: MemoryContext, last_response: AgentResponse
    ) -> AgentResponse:
        """Generates a final response based on the conversation context."""


class SimpleIntentDetector(IIntentDetector):
    async def detect_intent(self, query: str, context: MemoryContext) -> IntentData:
        query_lower = query.lower()

        # Pantry detection - check for pantry-related queries FIRST
        pantry_keywords = [
            "spiżarnia",
            "pantry",
            "spiżarni",
            "w spiżarni",
            "co mam w spiżarni",
            "co jest w spiżarni",
            "sprawdź spiżarnię",
            "sprawdź co mam",
            "co mam w domu",
            "co jest w domu",
            "produkty w spiżarni",
            "produkty w domu",
            "jedzenie w domu",
            "jedzenie w spiżarni",
            "zapasy",
            "zapasy w domu",
            "co mam do jedzenia",
            "co mogę ugotować",
            "co mogę zjeść",
            "co mam w lodówce",
            "co jest w lodówce",
            "lodówka",
            "fridge",
            "refrigerator",
            "kuchenne zapasy",
            "domowe zapasy",
            "co kupiłem",
            "co kupiłam",
            "co mam w szafkach",
            "co jest w szafkach",
            "szafki kuchenne",
            "kuchenne szafki",
        ]

        for keyword in pantry_keywords:
            if keyword in query_lower:
                return IntentData("pantry")

        if "przepis" in query_lower:
            return IntentData("recipe_request")
        if "dodaj" in query_lower or "kup" in query_lower:
            return IntentData("add_to_list")
        return IntentData("general_query")


class BasicMemoryManager(IMemoryManager):
    def __init__(self) -> None:
        self.contexts = {}

    async def get_context(self, session_id: str) -> MemoryContext:
        if session_id not in self.contexts:
            self.contexts[session_id] = MemoryContext(session_id)
        return self.contexts[session_id]

    async def update_context(
        self, context: MemoryContext, new_data: dict[str, Any]
    ) -> None:
        if new_data:
            context.history.append(
                {"timestamp": datetime.now().isoformat(), "data": new_data}
            )


class BasicResponseGenerator(IResponseGenerator):
    async def generate_response(
        self, context: MemoryContext, agent_response: AgentResponse
    ) -> AgentResponse:
        if agent_response.text:
            return AgentResponse(success=True, text=agent_response.text)
        return AgentResponse(
            success=False,
            error="Przepraszam, wystąpił problem podczas przetwarzania żądania.",
        )
