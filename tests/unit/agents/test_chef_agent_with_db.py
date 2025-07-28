#!/usr/bin/env python3
"""
Test script for ChefAgent with real database
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.chef_agent import ChefAgent
from backend.core.anti_hallucination_system import ValidationLevel
from backend.infrastructure.database.database import get_db_session


async def test_chef_agent_with_db():
    """Test ChefAgent with real database"""


    # Create ChefAgent instance
    chef_agent = ChefAgent()

    # Get database session
    async with get_db_session() as db:
        # Test data
        test_input = {
            "available_ingredients": ["kurczak", "ryż", "brokuły"],
            "dietary_restrictions": None,
            "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
            "validation_level": ValidationLevel.STRICT,
            "max_ingredients_allowed": 3,
            "session_id": "test_session",
            "db": db
        }


        try:
            # Test ingredient availability check
            await chef_agent._check_ingredient_availability(db, ["kurczak", "ryż", "brokuły"])

            # Test recipe generation with database
            response = await chef_agent.process(test_input)

            if response.data:
                pass

        except Exception:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chef_agent_with_db())
