"""
Security utilities for FoodSave AI
"""

from auth.jwt_handler import jwt_handler


def create_access_token(data: dict) -> str:
    """Create access token using JWT handler"""
    return jwt_handler.create_access_token(data=data)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using JWT handler"""
    return jwt_handler.verify_password(plain_password, hashed_password)
