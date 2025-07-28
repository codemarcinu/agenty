from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from datetime import datetime

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
import structlog

from agents.orchestrator_factory import create_orchestrator
from api import (
    agents,
    analytics,
    chat,
    health,
    monitoring,
    pantry,
    settings as settings_router,  # food,  # Temporarily disabled
    upload,
)
from api.openapi import setup_openapi_docs
from api.v1.endpoints import devops, receipts
from api.v2.api import api_router as api_v2_router
from api.v2.exceptions import APIException
from auth.auth_middleware import AuthMiddleware
from auth.routes import auth_router
from core.cache_manager import CacheManager
from core.database import AsyncSessionLocal, Base, engine, get_db
from core.exceptions import FoodSaveError
from core.middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from core.migrations import run_migrations
from core.seed_data import seed_database
from core.telemetry import setup_telemetry

# Import custom logger to configure logging
from logger import configure_root_logger
from orchestrator_management.orchestrator_pool import orchestrator_pool
from settings import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Configure logging before creating the app
configure_root_logger()
logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)

# Testowy log WARNING po starcie aplikacji
import logging
logging.getLogger().warning('[WARNING] Testowy warning z app_factory.py - root logger działa!')


# Exception Handlers
async def custom_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler dla FoodSaveError - zwraca spójny format błędów"""
    if isinstance(exc, FoodSaveError):
        logger.error(f"FoodSaveError: {exc}")
        return JSONResponse(
            status_code=500,  # FoodSaveError doesn't have status_code, use default
            content={
                "error": "foodsave_error",
                "message": exc.message,
                "details": exc.details,
            },
        )
    # Fallback for other exceptions
    logger.error(f"Unexpected exception in custom handler: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "Internal server error"},
    )


async def api_v2_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler dla APIException - zwraca format zgodny z API v2"""
    if isinstance(exc, APIException):
        logger.error(f"APIException: {exc}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )
    # Fallback for other exceptions
    logger.error(f"Unexpected exception in API v2 handler: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "Internal server error"},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler dla HTTPException - zachowuje domyślny format FastAPI"""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    # Fallback for other exceptions
    logger.error(f"Unexpected exception in HTTP handler: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found."},
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup logic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Skip migrations for SQLite (they use PostgreSQL-specific queries)
    if not settings.DATABASE_URL.startswith("sqlite"):
        await run_migrations()
    else:
        logger.info("Skipping migrations for SQLite database")

    logger.info("database.seeding.start")
    async with AsyncSessionLocal() as db:
        try:
            await seed_database(db)
        except Exception as e:
            logger.error("database.seeding.error", error=str(e))
            raise
    logger.info("database.seeding.complete")

    # Initialize cache
    cache_manager = CacheManager()
    await cache_manager.connect()

    # Initialize MMLW embeddings if enabled
    if settings.USE_MMLW_EMBEDDINGS:
        try:
            from core.mmlw_embedding_client import mmlw_client

            logger.info("Initializing MMLW embeddings...")
            await mmlw_client.initialize()
            if mmlw_client.is_available():
                logger.info("MMLW embeddings initialized successfully")
            else:
                logger.warning("MMLW embeddings initialization failed")
        except Exception as e:
            logger.error(f"Failed to initialize MMLW embeddings: {e}")
    else:
        logger.info("MMLW embeddings disabled in settings.")

    # --- Refaktoryzacja Orchestrator Pool ---
    # Zabezpiecz inicjalizację agentów na wypadek błędów DB i loguj szczegóły
    logger.info("Initializing orchestrator pool and request queue...")
    try:
        async for db in get_db():
            default_orchestrator = create_orchestrator(db)
            await orchestrator_pool.add_instance("default", default_orchestrator)
            await orchestrator_pool.start_health_checks()
            logger.info("Orchestrator pool initialized with default instance")
            break
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator pool: {e}")
        raise

    # --- Rejestracja agentów na starcie ---
    try:
        from agents.agent_registry import AgentRegistry
        from agents.analytics_agent import AnalyticsAgent
        from agents.categorization_agent import CategorizationAgent
        from agents.chef_agent import ChefAgent
        from agents.meal_planner_agent import MealPlannerAgent
        from agents.ocr_agent import OCRAgent
        from agents.rag_agent import RAGAgent
        from agents.search_agent import SearchAgent
        from agents.weather_agent import WeatherAgent

        agent_registry = AgentRegistry()

        # Rejestruj klasy agentów jeśli nie są zarejestrowane
        if "Chef" not in agent_registry.get_all_registered_agent_types():
            agent_registry.register_agent_class("Chef", ChefAgent)
        if "Weather" not in agent_registry.get_all_registered_agent_types():
            agent_registry.register_agent_class("Weather", WeatherAgent)
        if "RAG" not in agent_registry.get_all_registered_agent_types():
            agent_registry.register_agent_class("RAG", RAGAgent)
        if "OCR" not in agent_registry.get_all_registered_agent_types():
            agent_registry.register_agent_class("OCR", OCRAgent)
        if "Categorization" not in agent_registry.get_all_registered_agent_types():
            agent_registry.register_agent_class("Categorization", CategorizationAgent)
        if "MealPlanner" not in agent_registry.get_all_registered_agent_types():
            agent_registry.register_agent_class("MealPlanner", MealPlannerAgent)
        if "Search" not in agent_registry.get_all_registered_agent_types():
            agent_registry.register_agent_class("Search", SearchAgent)
        if "Analytics" not in agent_registry.get_all_registered_agent_types():
            agent_registry.register_agent_class("Analytics", AnalyticsAgent)

        logger.info(
            f"Agent types registered at startup: {agent_registry.get_all_registered_agent_types()}"
        )
    except Exception as e:
        logger.error(f"Agent registration at startup failed: {e}")

    yield

    # Shutdown logic
    await cache_manager.disconnect()
    logger.info("Application shutdown.")


def create_app() -> FastAPI:
    """Creates and configures a FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.include_router(health.router)
    
    # Add health endpoint at /api/health for frontend compatibility
    @app.get("/api/health", tags=["Monitoring"])
    async def api_health_check():
        return {"status": "ok", "service": "backend", "timestamp": datetime.now().isoformat()}

    # --- Optymalizacja kolejności middleware ---
    # CORS musi być pierwszy, potem bezpieczeństwo, logowanie, throttling, obsługa błędów
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3002",
            "http://localhost:3003",
            "http://127.0.0.1:3003",
            "http://localhost:3004",
            "http://127.0.0.1:3004",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:4321",
            "http://127.0.0.1:4321",
            "http://localhost:1420",
            "http://127.0.0.1:1420",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:8085",
            "http://127.0.0.1:8085",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    # app.add_middleware(PerformanceMonitoringMiddleware) # Can be noisy

    # Add exception handlers
    app.add_exception_handler(FoodSaveError, custom_exception_handler)
    app.add_exception_handler(APIException, api_v2_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(404, not_found_handler)

    # Setup telemetry if enabled
    if settings.TELEMETRY_ENABLED:
        setup_telemetry("foodsave-ai-backend")

    # Include routers
    api_router = APIRouter()
    api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
    # api_router.include_router(food.router, prefix="/food", tags=["Food"])  # Temporarily disabled
    api_router.include_router(pantry.router, prefix="/pantry", tags=["Pantry"])
    api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
    api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
    api_router.include_router(
        settings_router.router, prefix="/settings", tags=["Settings"]
    )

    # Include WebSocket routers
    from api.chat_websocket import router as chat_websocket_router
    from api.websocket import router as websocket_router

    app.include_router(websocket_router, tags=["WebSocket"])
    app.include_router(chat_websocket_router, tags=["Chat WebSocket"])

    # Versioned API routers
    api_v1_router = APIRouter()
    api_v1_router.include_router(receipts.router, tags=["Receipts V1"])
    api_v1_router.include_router(upload.router, tags=["Upload"])
    api_v1_router.include_router(devops.router, tags=["DevOps"])
    
    # Import and add v1 routers
    from api import agents_v1, chat_v1
    api_v1_router.include_router(agents_v1.router, tags=["Agents V1"])
    api_v1_router.include_router(chat_v1.router, tags=["Chat V1"])

    app.include_router(monitoring.router)
    app.include_router(auth_router)
    app.include_router(api_router, prefix="/api")
    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(api_v2_router, prefix="/api/v2")

    # Limiter state needs to be attached to the app
    app.state.limiter = limiter

    # Setup enhanced OpenAPI documentation
    setup_openapi_docs(app)

    return app


app = create_app()
