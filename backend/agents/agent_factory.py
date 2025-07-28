import logging
import threading
from typing import Any, ClassVar

from pydantic import BaseModel

from agents.agent_container import AgentContainer
from agents.agent_registry import AgentRegistry
from agents.analytics_agent import AnalyticsAgent
from agents.anti_hallucination.enhanced_ocr_agent import EnhancedOCRAgent
from agents.anti_hallucination.enhanced_receipt_analysis_agent import (
    EnhancedReceiptAnalysisAgent,
)
from agents.base_agent import BaseAgent
from agents.categorization_agent import CategorizationAgent
from agents.chef_agent import ChefAgent
from agents.general_conversation_agent import GeneralConversationAgent
from agents.gmail_inbox_zero_agent import GmailInboxZeroAgent
from agents.meal_planner_agent import MealPlannerAgent
from agents.pantry_agent import PantryAgent
from agents.promo_scraping_agent import PromoScrapingAgent
from agents.rag_agent import RAGAgent
from agents.search_agent import SearchAgent
from agents.weather_agent import WeatherAgent
from core.decorators import handle_exceptions

# Module-level configuration
config: dict[str, Any] = {}
llm_client: Any | None = None

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Basic configuration model for agents"""

    agent_type: str
    dependencies: dict[str, str] = {}
    settings: dict[str, Any] = {}
    cache_enabled: bool = True


class AgentFactory:
    """Factory for creating agent instances with DI support."""

    # ✅ ALWAYS: Proper agent registration with fallback
    AGENT_REGISTRY: ClassVar[dict[str, type[BaseAgent]]] = {
        "general_conversation": GeneralConversationAgent,
        "shopping_conversation": GeneralConversationAgent,
        "food_conversation": GeneralConversationAgent,
        "information_query": SearchAgent,
        "cooking": ChefAgent,  # Poprawka: ChefAgent zamiast CookingAgent
        "Chef": ChefAgent,  # Dodaj alias z wielką literą
        "search": SearchAgent,
        "Search": SearchAgent,  # Alias z wielką literą
        "weather": WeatherAgent,
        "Weather": WeatherAgent,  # Alias z wielką literą
        # Weather queries can also be handled by PerplexicaSearchProvider in SearchAgent
        "rag": RAGAgent,
        "RAG": RAGAgent,  # Alias z wielką literą
        "categorization": CategorizationAgent,
        "Categorization": CategorizationAgent,  # Alias z wielką literą
        "meal_planning": MealPlannerAgent,
        "MealPlanner": MealPlannerAgent,  # Alias z wielką literą
        "ocr": EnhancedOCRAgent,
        "OCR": EnhancedOCRAgent,  # Alias z wielką literą
        "receipt_analysis": EnhancedReceiptAnalysisAgent,
        "ReceiptAnalysis": EnhancedReceiptAnalysisAgent,  # Alias z wielką literą
        "analytics": AnalyticsAgent,
        "Analytics": AnalyticsAgent,  # Alias z wielką literą
        "promo_scraping": PromoScrapingAgent,
        "PromoScraping": PromoScrapingAgent,  # Alias z wielką literą
        "pantry": PantryAgent,
        "Pantry": PantryAgent,  # Alias z wielką literą
        "gmail_inbox_zero": GmailInboxZeroAgent,
        "GmailInboxZero": GmailInboxZeroAgent,  # Alias z wielką literą
        "inbox_zero": GmailInboxZeroAgent,  # Krótki alias
        # ✅ ALWAYS include fallback
        "default": GeneralConversationAgent,
    }

    def __init__(
        self,
        container: AgentContainer | None = None,
        agent_registry: AgentRegistry | None = None,
    ) -> None:
        self.container = container or AgentContainer()
        self.config: dict[str, Any] = {}
        self._agent_cache: dict[str, Any] = {}  # Cache dla agentów (dowolny typ)
        self._cache_lock = threading.Lock()  # Thread-safe lock dla cache
        self._registry: dict[str, BaseAgent] = {}  # Registry dla agentów (dla testów)
        self.agent_config = {
            "ocr": {"module": "ocr_agent"},
            "weather": {"module": "weather_agent"},
            "search": {"module": "search_agent"},
            "chef": {"module": "chef_agent"},
            "meal_planner": {"module": "meal_planner_agent"},
            "categorization": {"module": "categorization_agent"},
            "analytics": {"module": "analytics_agent"},
            "rag": {"module": "rag_agent"},
            "orchestrator": {"module": "orchestrator"},
        }
        self.agent_registry = agent_registry or AgentRegistry()

        # Register core services in container
        if hasattr(self.container, "register_core_services"):
            # We need a db session, but we don't have one here
            # This will be handled when creating agents
            pass

        # Register agent classes with the registry
        self._register_agent_classes()

    def _register_agent_classes(self) -> None:
        """Register all agent classes with the registry in a safe way"""
        try:
            # Rejestruj wszystkie klasy agentów
            agent_classes = {
                "GeneralConversation": GeneralConversationAgent,
                "Chef": ChefAgent,
                "Weather": WeatherAgent,
                "Search": SearchAgent,
                "RAG": RAGAgent,
                "OCR": EnhancedOCRAgent,
                "ReceiptAnalysis": EnhancedReceiptAnalysisAgent,
                "Categorization": CategorizationAgent,
                "MealPlanner": MealPlannerAgent,
                "Analytics": AnalyticsAgent,
                "PromoScraping": PromoScrapingAgent,
                "Pantry": PantryAgent,
                "GmailInboxZero": GmailInboxZeroAgent,
            }

            for agent_type, agent_class in agent_classes.items():
                self.agent_registry.register_agent_class(agent_type, agent_class)
                logger.debug(
                    f"Registered agent class: {agent_type} -> {agent_class.__name__}"
                )

        except Exception as e:
            logger.error(f"Error registering agent classes: {e}")
            # Continue with basic registration

    def register_agent(self, agent_type: str, agent_class: type[BaseAgent]) -> None:
        """
        Register an agent class with the factory and registry.

        Args:
            agent_type (str): Type of agent (e.g., 'orchestrator')
            agent_class (Type[BaseAgent]): Agent class to register
        """
        self.agent_registry.register_agent_class(agent_type, agent_class)

    @handle_exceptions(max_retries=1)
    def create_agent(
        self,
        agent_type: str,
        config: dict | None = None,
        use_cache: bool = True,
        **kwargs,
    ) -> BaseAgent | Any:
        """
        Creates and configures an agent instance using the new registry.
        """
        # Thread-safe cache check
        if use_cache and not config and not kwargs:
            with self._cache_lock:
                cache_key = agent_type
                if cache_key in self._agent_cache:
                    return self._agent_cache[cache_key]

        # Najpierw sprawdź agent_registry (customowy), potem AGENT_REGISTRY
        agent_class = None
        if self.agent_registry:
            agent_class = self.agent_registry.get_agent_class(agent_type)
        if agent_class is None:
            agent_class = self.AGENT_REGISTRY.get(agent_type)
        if agent_class is None:
            logger.warning(
                f"Unknown agent type: {agent_type}, using default agent as fallback"
            )
            agent_class = self.AGENT_REGISTRY["default"]

        agent = agent_class(**kwargs)

        if use_cache and not config and not kwargs:
            with self._cache_lock:
                cache_key = agent_type
                self._agent_cache[cache_key] = agent

        return agent

    @handle_exceptions(max_retries=1, retry_delay=0.5)
    def _get_agent_class(self, class_name: str) -> type[BaseAgent]:
        """Dynamically import agent class to avoid circular imports"""
        import importlib
        import os
        from pathlib import Path
        import sys

        # Get the project root path (relative to this file)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Map class names to actual module files (relative imports)
        module_map = {
            "GeneralConversationAgent": "general_conversation_agent",
            "EnhancedOCRAgent": "anti_hallucination.enhanced_ocr_agent",
            "WeatherAgent": "weather_agent",
            "SearchAgent": "search_agent",
            "ChefAgent": "chef_agent",
            "MealPlannerAgent": "meal_planner_agent",
            "CategorizationAgent": "categorization_agent",
            "AnalyticsAgent": "analytics_agent",
            "RAGAgent": "rag_agent",
            "PantryAgent": "pantry_agent",
            "Orchestrator": "orchestrator",
            "BaseAgent": "base_agent",
            "EnhancedReceiptAnalysisAgent": "anti_hallucination.enhanced_receipt_analysis_agent",
        }

        if class_name not in module_map:
            raise ValueError(f"No module mapping for agent class: {class_name}")

        module_name = module_map[class_name]
        full_module_path = f"backend.agents.{module_name}"

        try:
            module = importlib.import_module(full_module_path)
            return getattr(module, class_name)
        except ImportError as e:
            # Check if file actually exists
            file_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
            if not Path(file_path).exists():
                raise FileNotFoundError(
                    f"Agent module file not found: {file_path}"
                ) from e
            raise ImportError(
                f"Failed to import {class_name} from {full_module_path}: {e!s}\n"
                f"Current sys.path: {sys.path}"
            ) from e

    def get_available_agents(self) -> dict[str, str]:
        """Return a dictionary of all registered agents and their descriptions."""
        return {
            agent_type: agent_class.__doc__ or "No description provided"
            for agent_type, agent_class in self.AGENT_REGISTRY.items()
        }

    def cleanup(self) -> None:
        """Perform any necessary cleanup for the factory, such as clearing caches."""
        with self._cache_lock:
            self._agent_cache.clear()
        logger.info("AgentFactory cache cleared.")

    def reset(self) -> None:
        """Resets the factory state, clearing caches and re-initializing the registry
        if needed."""
        self.cleanup()
        # If there are any other states that need to be reset, add them here
        logger.info("AgentFactory state reset.")
