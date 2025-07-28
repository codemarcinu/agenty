"""
User Profile Schemas

Pydantic schemas for user profile API endpoints
"""

from typing import Any

from pydantic import BaseModel, Field


class CookingPreferencesRequest(BaseModel):
    """Request model for cooking preferences"""

    user_id: str | None = Field(default="gui-user", description="User ID")
    session_id: str | None = Field(default="gui-session", description="Session ID")
    cooking_preferences: dict[str, Any] = Field(..., description="Cooking preferences")


class UpdateUserProfileRequest(BaseModel):
    """Request model for updating user profile"""

    user_id: str | None = Field(default="gui-user", description="User ID")
    session_id: str | None = Field(default="gui-session", description="Session ID")
    cooking_preferences: dict[str, Any] = Field(..., description="Cooking preferences")
    topics_of_interest: list[str] | None = Field(
        default=[], description="Topics of interest"
    )


class UserProfileResponse(BaseModel):
    """Response model for user profile"""

    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    preferences: dict[str, Any] = Field(..., description="User preferences")
    topics_of_interest: list[str] = Field(default=[], description="Topics of interest")


class UserProfileRAGResponse(BaseModel):
    """Response model for RAG profile setup"""

    success: bool = Field(..., description="Operation success status")
    message: str | None = Field(None, description="Success message")
    error: str | None = Field(None, description="Error message")
    document_id: str | None = Field(None, description="RAG document ID")
    profile_summary: dict[str, Any] | None = Field(None, description="Profile summary")
