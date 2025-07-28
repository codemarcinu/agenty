from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.vector_store import VectorStore


class AgentContainer:
    """Dependency Injection container for agent dependencies"""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a service in the container"""
        self._services[name] = service

    def get(self, name: str) -> Any | None:
        """Get a registered service"""
        return self._services.get(name)

    def register_core_services(self, db: AsyncSession) -> None:
        """Register core services used by agents"""
        from agents.adapters.alert_service import AlertService
        from agents.adapters.error_handler import ErrorHandler
        from agents.adapters.fallback_manager import FallbackManager
        from agents.interfaces import (
            IAlertService,
            IErrorHandler,
            IFallbackProvider,
        )
        from core.hybrid_llm_client import hybrid_llm_client
        from core.profile_manager import ProfileManager

        self.register("db", db)
        self.register("profile_manager", ProfileManager(db))
        self.register("llm_client", hybrid_llm_client)
        self.register("vector_store", VectorStore())

        # Register interface implementations
        self.register(IErrorHandler.__name__, ErrorHandler("global"))
        self.register(IAlertService.__name__, AlertService("global"))
        self.register(IFallbackProvider.__name__, FallbackManager())
