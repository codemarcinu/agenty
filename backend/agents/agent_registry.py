import json
import logging
from pathlib import Path

from agents.interfaces import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self, config_file: str | None = None) -> None:
        self._agents: dict[str, type[BaseAgent]] = {}
        self._intent_mappings: dict[str, str] = {}

        # Load intent mappings from config file or use defaults
        self.intent_to_agent_mapping = self._load_intent_mappings(config_file)

    def _load_intent_mappings(self, config_file: str | None = None) -> dict[str, str]:
        """Load intent mappings from config file or return defaults"""
        default_mappings = {
            "general_conversation": "GeneralConversation",
            "food_conversation": "GeneralConversation",
            "shopping_conversation": "Categorization",
            "information_query": "Search",
            "cooking": "Chef",
            # Weather queries are now handled by PerplexicaSearchProvider in SearchAgent
            "search": "Search",
            "rag": "RAG",
            "ocr": "OCR",
            "categorization": "Categorization",
            "meal_planning": "MealPlanner",
            "analytics": "Analytics",
            "general": "GeneralConversation",  # Default mapping
            "date": "GeneralConversation",  # Date/time queries
            "receipt_processing": "OCR",  # Receipt processing
            "pantry": "Pantry",  # Pantry queries - handled by PantryAgent
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("intent_mappings", default_mappings)
            except Exception as e:
                logger.error(f"Error loading agent config: {e}, using defaults")
                return default_mappings

        return default_mappings

    def register_agent_class(
        self, agent_type: str, agent_class: type[BaseAgent]
    ) -> None:
        """Rejestruje klasę agenta pod danym typem."""
        self._agents[agent_type] = agent_class

    def register_intent_to_agent_mapping(self, intent: str, agent_type: str) -> None:
        """Mapuje intencję do zarejestrowanego typu agenta."""
        if agent_type not in self._agents:
            raise ValueError(
                f"Agent type '{agent_type}' must be registered before mapping an intent to it."
            )
        self._intent_mappings[intent] = agent_type

    def get_agent_class(self, agent_type: str) -> type[BaseAgent] | None:
        """Zwraca klasę agenta na podstawie jego typu."""
        return self._agents.get(agent_type)

    def get_agent_type_for_intent(
        self, intent: str, default_agent_type: str = "GeneralConversation"
    ) -> str:
        """Zwraca typ agenta dla danej intencji, z domyślnym fallbackiem."""
        return self._intent_mappings.get(intent, default_agent_type)

    def get_all_registered_agent_types(self) -> list[str]:
        """Zwraca listę wszystkich zarejestrowanych typów agentów."""
        return list(self._agents.keys())


agent_registry = AgentRegistry()
