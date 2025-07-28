from __future__ import annotations

"""
Authentication and authorization module for FoodSave AI
"""

import os

from auth.auth_middleware import AuthMiddleware
from auth.jwt_handler import JWTHandler
from auth.models import Role, User, UserRole
from auth.routes import auth_router
from auth.schemas import TokenResponse, UserCreate, UserLogin, UserResponse

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)

__all__ = [
    "AuthMiddleware",
    "JWTHandler",
    "Role",
    "TokenResponse",
    "User",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserRole",
    "auth_router",
]
