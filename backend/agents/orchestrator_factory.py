import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

from agents.agent_factory import AgentFactory
from agents.agent_registry import AgentRegistry
from agents.intent_detector import SimpleIntentDetector
from agents.memory_manager import MemoryManager
from agents.orchestrator import Orchestrator
from agents.response_generator import ResponseGenerator
from agents.router_service import AgentRouter
from core.profile_manager import ProfileManager


def create_orchestrator(db: AsyncSession) -> Orchestrator:
    """
    Fabryka tworząca instancję Orchestrator z wymaganymi zależnościami.

    Args:
        db: Sesja bazy danych (AsyncSession)

    Returns:
        Instancja Orchestrator
    """
    logger = logging.getLogger(__name__)

    # Utwórz menedżer profilów
    profile_manager = ProfileManager(db)
    logger.debug("ProfileManager created")

    # Utwórz detektor intencji
    intent_detector = SimpleIntentDetector()
    logger.debug("SimpleIntentDetector created")

    # Utwórz rejestr agentów i fabrykę
    config_file = os.path.join(
        os.path.dirname(__file__), "../data/config/agent_config.json"
    )
    agent_registry = AgentRegistry(config_file=config_file)
    agent_factory = AgentFactory(agent_registry=agent_registry)

    # Rejestruj agenty w registry
    try:
        from agents.analytics_agent import AnalyticsAgent
        from agents.categorization_agent import CategorizationAgent
        from agents.chef_agent import ChefAgent
        from agents.meal_planner_agent import MealPlannerAgent
        from agents.ocr_agent import OCRAgent
        from agents.rag_agent import RAGAgent
        from agents.search_agent import SearchAgent
        from agents.weather_agent import WeatherAgent

        # Rejestruj klasy agentów
        agent_registry.register_agent_class("Chef", ChefAgent)
        agent_registry.register_agent_class("Weather", WeatherAgent)
        agent_registry.register_agent_class("RAG", RAGAgent)
        agent_registry.register_agent_class("OCR", OCRAgent)
        agent_registry.register_agent_class("Categorization", CategorizationAgent)
        agent_registry.register_agent_class("MealPlanner", MealPlannerAgent)
        agent_registry.register_agent_class("Search", SearchAgent)
        agent_registry.register_agent_class("Analytics", AnalyticsAgent)

        # Try to import PantryAgent separately
        try:
            from agents.pantry_agent import PantryAgent

            agent_registry.register_agent_class("Pantry", PantryAgent)
            logger.info("PantryAgent successfully registered")
        except Exception as pantry_error:
            logger.error(f"Failed to import PantryAgent: {pantry_error}")

        logger.info(
            f"Agent types registered in factory: {agent_registry.get_all_registered_agent_types()}"
        )
    except Exception as e:
        logger.error(f"Agent registration in factory failed: {e}")

    logger.debug("AgentRegistry and AgentFactory created")

    # Utwórz router agentów z fabryką
    agent_router = AgentRouter(agent_factory, agent_registry)
    logger.debug("AgentRouter created with factory")

    # Utwórz menedżera pamięci
    memory_manager = MemoryManager()
    logger.debug("MemoryManager created")

    # Utwórz generator odpowiedzi
    response_generator = ResponseGenerator()
    logger.debug("ResponseGenerator created")

    # Utwórz i zwróć orchestrator
    orchestrator = Orchestrator(
        db_session=db,
        profile_manager=profile_manager,
        intent_detector=intent_detector,
        agent_router=agent_router,
        memory_manager=memory_manager,
        response_generator=response_generator,
    )
    logger.debug("Orchestrator created successfully")

    return orchestrator
