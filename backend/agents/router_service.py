import logging
from typing import Any

from agents.agent_factory import AgentFactory
from agents.agent_registry import AgentRegistry
from agents.error_types import AgentError
from agents.interfaces import (
    AgentResponse,
    IAgentRouter,
    IntentData,
    MemoryContext,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AgentRouter(IAgentRouter):
    def __init__(
        self, agent_factory: AgentFactory, agent_registry: AgentRegistry
    ) -> None:
        self.agent_factory = agent_factory
        self.agent_registry = agent_registry

        # Check if agent classes are registered
        registered_types = self.agent_registry.get_all_registered_agent_types()
        logger.info(f"Registered agent types: {registered_types}")

        # Register intent mappings with the registry - only if agents are registered
        self._register_intent_mappings()

    def _register_intent_mappings(self) -> None:
        """Register intent mappings only if corresponding agents are registered"""
        registered_types = self.agent_registry.get_all_registered_agent_types()

        # Define mappings with fallback checks
        mappings = [
            ("cooking", "Chef"),
            ("weather", "Weather"),
            ("document", "RAG"),
            ("image", "OCR"),
            ("shopping", "Categorization"),
            ("meal_plan", "MealPlanner"),
            ("search", "Search"),
            ("analytics", "Analytics"),
            ("pantry", "Pantry"),
            ("general", "GeneralConversation"),
            ("general_conversation", "GeneralConversation"),
        ]

        for intent, agent_type in mappings:
            if agent_type in registered_types:
                try:
                    self.agent_registry.register_intent_to_agent_mapping(
                        intent, agent_type
                    )
                    logger.debug(f"Registered intent mapping: {intent} -> {agent_type}")
                except Exception as e:
                    logger.warning(
                        f"Failed to register intent mapping {intent} -> {agent_type}: {e}"
                    )
            else:
                logger.warning(
                    f"Agent type '{agent_type}' not registered, skipping intent mapping for '{intent}'"
                )

    def register_agent(self, agent_type: str, agent: Any) -> None:
        """Register an agent implementation for a specific type"""
        # This method is required by the orchestrator but not used in this
        # implementation as agents are created dynamically by the factory
        logger.info(f"Agent registration requested for type: {agent_type}")

    def get_agent(self, agent_type: str) -> None:
        """Get registered agent by type"""
        # This method is required by the orchestrator but not used in this implementation
        # as agents are created dynamically by the factory
        logger.info(f"Agent retrieval requested for type: {agent_type}")

    def set_fallback_agent(self, agent: Any) -> None:
        """Set fallback agent for unknown intents"""
        # This method is required by the orchestrator but not used in this implementation
        # as agents are created dynamically by the factory
        logger.info("Fallback agent set")

    async def route_to_agent(
        self,
        intent: IntentData,
        context: MemoryContext,
        user_command: str = "",
        db_session=None,
    ) -> AgentResponse:
        intent_type = intent.type
        agent_type = self.agent_registry.get_agent_type_for_intent(intent_type)

        try:
            # Walidacja przed utworzeniem agenta
            if agent_type not in self.agent_registry.get_all_registered_agent_types():
                logger.warning(
                    f"Agent type '{agent_type}' not found in factory registry for intent '{intent_type}'. "
                    f"Falling back to default agent 'GeneralConversation'."
                )
                agent_type = "GeneralConversation"  # Fallback na czat ogólny

            logger.debug(f"Creating agent: {agent_type}")
            agent = self.agent_factory.create_agent(agent_type)

            if agent is None:
                logger.error(f"Agent factory returned None for type: {agent_type}")
                return AgentResponse(
                    success=False,
                    error="Agent creation failed",
                    text="Przepraszam, wystąpił problem podczas tworzenia agenta.",
                )

            logger.debug(f"Agent created successfully: {type(agent)}")

            # Przygotuj dane wejściowe dla agenta
            input_data = {
                "query": user_command,
                "intent": intent.type,
                "entities": intent.entities,
                "confidence": intent.confidence,
                "session_id": context.session_id,
                "context": context.history[-10:] if context.history else [],
            }

            logger.debug(f"Processing with agent: {agent_type}")
            response = await agent.process(input_data, db=db_session)

            logger.debug(f"Agent response: {type(response)} - {response}")

            # Upewnij się, że AgentResponse jest właściwie obsługiwany
            if isinstance(response, AgentResponse):
                return response
            # Jeśli agent zwróci inny typ, opakuj w AgentResponse
            return AgentResponse(
                success=True,
                text=str(response) if response else "Brak odpowiedzi",
                data={"original_response": response},
            )

        except AgentError as e:
            logger.error(
                f"AgentError during processing with agent {agent_type}: {e!s}",
                exc_info=True,
            )
            return AgentResponse(
                success=False,
                error=f"Error processing request: {e!s}",
                text="Przepraszam, wystąpił błąd podczas przetwarzania żądania.",
            )
        except Exception as e:
            logger.error(
                f"Unexpected error processing request with agent {agent_type}: {e!s}",
                exc_info=True,
            )
            return AgentResponse(
                success=False,
                error="Przepraszam, wystąpił nieoczekiwany błąd podczas przetwarzania żądania.",
                text="Przepraszam, wystąpił nieoczekiwany błąd podczas przetwarzania żądania.",
            )
