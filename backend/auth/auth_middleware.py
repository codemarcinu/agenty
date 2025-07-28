"""
Authentication middleware for FastAPI
"""

from collections.abc import Callable
from functools import wraps
import logging
import os
from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from auth.jwt_handler import jwt_handler

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware with development mode support"""

    def __init__(self, app, exclude_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/health",
            "/ready",
            "/metrics",
            "/ws/dashboard",
            "/ws/status",
            "/ws/test",
            "/api/ws/dashboard",
            "/api/ws/status",
            "/api/v2/weather",
            "/api/v2/weather/",
            "weather",
            "/weather",
            "/weather/",
            "/monitoring",
            "/monitoring/",
            "/api/monitoring",
            "/api/monitoring/",
            "/api/analytics/expenses",
            "/api/analytics/budget",
            "/api/analytics/insights",
            # Add wildcard patterns for analytics
            "/api/analytics",
            "/api/analytics/",
            # Add v2 receipts endpoints
            "/api/v2/receipts",
            "/api/v2/receipts/",
            "/api/v2/receipts/process_async",
            "/api/v2/receipts/upload",
            "/api/v2/receipts/analyze",
            "/api/v2/receipts/save",
            "/api/v2/receipts/process",
            # Add v2 inventory endpoints
            "/api/v2/inventory",
            "/api/v2/inventory/",
            # Add v2 chat endpoints
            "/api/v2/chat",
            # Add v1 chat endpoints
            "/api/chat",
            "/api/memory_chat",
            "/api/test_simple_chat",
            "/api/test_chat_simple",
            # Add v1 chat endpoints for frontend
            "/api/v1/chat",
            "/api/v1/chat/",
            # Add agents endpoints
            "/api/v1/agents",
            "/api/v1/agents/",
            "/api/agents/agents",
            "/api/agents/agents/",
            # Add v2 RAG endpoints
            "/api/v2/rag",
            "/api/v2/rag/",
            "/api/v2/rag/upload",
            "/api/v2/rag/documents",
            "/api/v2/rag/query",
            "/api/v2/rag/stats",
            "/api/v2/rag/sync-database",
            "/api/v2/rag/directories",
            "/api/v2/rag/search",
            # Add v2 feedback endpoints
            "/api/v2/feedback",
            "/api/v2/feedback/",
            "/api/v2/feedback/user-feedback",
            "/api/v2/feedback/failed-extraction",
            "/api/v2/feedback/statistics",
            "/api/v2/feedback/training-data",
            "/api/v2/feedback/improvement-suggestions",
            "/api/v2/feedback/cleanup",
            # Add monitoring endpoints
            "/monitoring/status",
            # Add wildcard patterns for v2 API
            "/api/v2",
            "/api/v2/",
            # Add agents endpoints for GUI integration
            "/api/agents/execute",
            "/api/agents",
            "/api/agents/",
            # Add pantry endpoints for development
            "/api/pantry",
            "/api/pantry/",
            # Add v1 receipts endpoints
            "/api/v1/receipts",
            "/api/v1/receipts/",
            "/api/v1/receipts/validate",
            "/api/v1/receipts/upload",
            # Add v1 upload endpoints
            "/api/v1/upload",
            "/api/v1/simple-upload",
            "/api/v1/test-upload",
            "/api/v1/simple-upload-no-ocr",
            # Add v3 receipts endpoints for async processing
            "/api/v3/receipts",
            "/api/v3/receipts/",
            "/api/v3/receipts/process",
            "/api/v3/receipts/status",
            "/api/v3/receipts/health",
            "/api/v3/receipts/cancel",
            # Add v3 RAG endpoints
            "/api/v3/rag",
            "/api/v3/rag/",
            "/api/v3/rag/documents",
            "/api/v3/rag/stats",
            "/api/v3/rag/clear",
            # Add test endpoints
            "/api/chat/test_simple_chat",
            # Settings endpoints
            "/api/settings",
            "/api/settings/",
            "/api/settings/llm-models",
            "/api/settings/llm-model/selected",
        ]

        # Authentication configuration
        logger.info("🔒 Authentication enabled")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with authentication"""
        path = request.url.path
        logger.info(f"🔒 AuthMiddleware dispatch called for path: {path}")

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            logger.debug(f"Skipping auth for OPTIONS request: {path}")
            return await call_next(request)

        # Skip authentication for excluded paths - improved matching logic
        is_excluded = False
        for exclude_path in self.exclude_paths:
            # Exact match
            if (
                path == exclude_path
                or exclude_path.endswith("/")
                and path.startswith(exclude_path)
                or exclude_path in path
            ):
                is_excluded = True
                break

        logger.info(
            f"🔒 Path {path} excluded: {is_excluded} (checking against {len(self.exclude_paths)} exclude paths)"
        )
        logger.info(
            f"🔒 Exclude paths: {self.exclude_paths[:5]}..."
        )  # Show first 5 paths

        if is_excluded:
            logger.info(f"✅ Skipping auth for excluded path: {path}")
            return await call_next(request)

        # Skip authentication in testing mode
        if os.getenv("TESTING_MODE") == "true":
            logger.debug("TESTING_MODE active: setting mock user in request.state")
            request.state.user = {
                "sub": "1",
                "email": "test@example.com",
                "roles": ["user"],
            }
            request.state.user_id = "1"
            request.state.user_roles = ["user"]
            return await call_next(request)

        # 🔒 PRODUCTION MODE: Normal authentication
        # Extract token from Authorization header
        token = self._extract_token(request)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token
        payload = jwt_handler.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Add user info to request state
        request.state.user = payload
        request.state.user_id = payload.get("sub")
        request.state.user_roles = payload.get("roles", [])

        logger.debug(f"Authenticated user {payload.get('sub')} for {request.url.path}")

        return await call_next(request)

    def _extract_token(self, request: Request) -> str | None:
        """Extract JWT token from request"""
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        return auth_header.split(" ")[1]


def get_current_user(request: Request) -> dict[str, Any]:
    """Get current user from request state"""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return request.state.user


def get_current_user_id(request: Request) -> int:
    """Get current user ID from request state"""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return request.state.user_id


def require_roles(required_roles: list[str]) -> Callable[..., Any]:
    """Decorator to require specific roles"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            user_roles = getattr(request.state, "user_roles", [])

            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str) -> Callable[..., Any]:
    """Decorator to require specific permission"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            user_permissions = getattr(request.state, "user_permissions", [])

            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
