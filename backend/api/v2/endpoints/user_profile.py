"""
User Profile API Endpoints

This module provides API endpoints for managing user profiles:
- Get user profile
- Update user profile
- Setup user profile in RAG
- Get cooking preferences
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.rag_integration import rag_integration
from core.user_profile_rag import setup_user_profile_in_rag
from infrastructure.database.database import get_db
from models.user_profile import CookingPreferences, UserPreferences, UserProfile
from schemas.user_profile_schemas import (
    CookingPreferencesRequest,
    UpdateUserProfileRequest,
    UserProfileRAGResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/user-profile", tags=["User Profile"])
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserProfileResponse)
async def get_user_profile(db: AsyncSession = Depends(get_db)) -> UserProfileResponse:
    """
    Get current user profile
    """
    try:
        # For now, return a default profile
        # In a full implementation, this would fetch from database
        default_profile = {
            "user_id": "gui-user",
            "session_id": "gui-session",
            "preferences": {
                "cooking": {
                    "name": "Użytkownik",
                    "age": None,
                    "occupation": "",
                    "favorite_cuisines": [],
                    "dietary_restrictions": [],
                    "allergies": [],
                    "spice_tolerance": "medium",
                    "cooking_style": [],
                    "preferred_meal_types": [],
                    "cooking_time_preference": "quick",
                    "available_appliances": [],
                    "cooking_methods": [],
                    "budget_conscious": True,
                    "healthy_eating_focus": True,
                    "environmental_conscious": False,
                    "loves_trying_new_things": True,
                },
                "formality": "neutral",
            },
            "topics_of_interest": [],
        }

        return UserProfileResponse(**default_profile)

    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/me", response_model=UserProfileResponse)
async def update_user_profile(
    request: dict[str, Any], db: AsyncSession = Depends(get_db)
) -> UserProfileResponse:
    """
    Update user profile and sync with RAG
    
    Accepts both formats:
    1. Old format: {cooking_preferences: {...}, topics_of_interest: [...]}
    2. New format: {user_id: "...", session_id: "...", preferences: {...}, topics_of_interest: [...]}
    """
    try:
        # Handle both request formats
        if "cooking_preferences" in request:
            # Old format - cooking_preferences at top level
            cooking_prefs = CookingPreferences.model_validate(request["cooking_preferences"])
            user_id = request.get("user_id", "gui-user")
            session_id = request.get("session_id", "gui-session")
            topics_of_interest = request.get("topics_of_interest", [])
        else:
            # New format - UserProfile structure
            user_id = request.get("user_id", "gui-user")
            session_id = request.get("session_id", "gui-session")
            topics_of_interest = request.get("topics_of_interest", [])
            
            # Extract cooking preferences from the nested structure
            preferences = request.get("preferences", {})
            cooking_data = preferences.get("cooking", {})
            cooking_prefs = CookingPreferences.model_validate(cooking_data)

        # Create user preferences
        user_prefs = UserPreferences(cooking=cooking_prefs)

        user_profile = UserProfile(
            user_id=user_id,
            session_id=session_id,
            preferences=user_prefs.model_dump(),
            topics_of_interest=topics_of_interest,
        )

        # Update in RAG system
        rag_result = await setup_user_profile_in_rag(
            user_id=user_profile.user_id,
            session_id=user_profile.session_id,
            cooking_preferences=cooking_prefs.model_dump(),
            rag_integration=rag_integration,
        )

        if not rag_result["success"]:
            logger.error(f"Failed to update profile in RAG: {rag_result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update profile in RAG: {rag_result.get('error')}",
            )

        logger.info(f"Successfully updated user profile for {user_profile.user_id}")

        return UserProfileResponse(
            user_id=user_profile.user_id,
            session_id=user_profile.session_id,
            preferences=user_prefs.model_dump(),
            topics_of_interest=user_profile.topics_of_interest,
        )

    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-rag", response_model=UserProfileRAGResponse)
async def setup_user_profile_rag(
    cooking_preferences: dict[str, Any], db: AsyncSession = Depends(get_db)
) -> UserProfileRAGResponse:
    """
    Setup user profile in RAG system
    """
    try:
        # Setup in RAG system
        rag_result = await setup_user_profile_in_rag(
            user_id="gui-user",
            session_id="gui-session",
            cooking_preferences=cooking_preferences,
            rag_integration=rag_integration,
        )

        return UserProfileRAGResponse(
            success=rag_result["success"],
            message=rag_result.get("message"),
            error=rag_result.get("error"),
            document_id=rag_result.get("document_id"),
            profile_summary=rag_result.get("profile_summary"),
        )

    except Exception as e:
        logger.error(f"Error setting up user profile in RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cooking-preferences", response_model=dict[str, Any])
async def get_cooking_preferences(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Get cooking preferences for current user
    """
    try:
        # For now, return default preferences
        # In a full implementation, this would fetch from database
        default_preferences = {
            "name": "Użytkownik",
            "age": None,
            "occupation": "",
            "favorite_cuisines": ["polska", "włoska"],
            "dietary_restrictions": [],
            "allergies": [],
            "spice_tolerance": "medium",
            "cooking_style": ["szybko", "praktycznie"],
            "preferred_meal_types": ["jednogarnkowe", "dania główne"],
            "cooking_time_preference": "quick",
            "available_appliances": ["piekarnik", "mikrofala", "patelnia"],
            "cooking_methods": ["smażenie", "pieczenie", "gotowanie"],
            "budget_conscious": True,
            "healthy_eating_focus": True,
            "environmental_conscious": False,
            "loves_trying_new_things": True,
        }

        return default_preferences

    except Exception as e:
        logger.error(f"Error getting cooking preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))
