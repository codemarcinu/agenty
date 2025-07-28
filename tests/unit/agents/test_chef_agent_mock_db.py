#!/usr/bin/env python3
"""
Test script for ChefAgent with mock database
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.chef_agent import ChefAgent
from backend.core.anti_hallucination_system import ValidationLevel


async def test_chef_agent_with_mock_db():
    """Test ChefAgent with mock database"""


    # Create ChefAgent instance
    chef_agent = ChefAgent()

    # Mock database session
    mock_db = AsyncMock()

    # Mock available products in database
    mock_products = [
        MagicMock(name="kurczak", is_consumed=0),
        MagicMock(name="ryż", is_consumed=0),
        MagicMock(name="brokuły", is_consumed=0),
        MagicMock(name="indyk", is_consumed=0),
        MagicMock(name="wołowina", is_consumed=0),
    ]

    # Mock database query results
    mock_db.execute.return_value.scalars.return_value.all.return_value = mock_products

    # Test data
    test_input = {
        "available_ingredients": ["kurczak", "ryż", "brokuły"],
        "dietary_restrictions": None,
        "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        "validation_level": ValidationLevel.STRICT,
        "max_ingredients_allowed": 3,
        "db": mock_db
    }

    try:
        # Test ingredient verification
        await chef_agent._check_ingredient_availability(
            mock_db,
            ["kurczak", "ryż", "brokuły"]
        )


        # Test full process
        await chef_agent.process(test_input)


        # Test with missing ingredients
        test_input_missing = {
            "available_ingredients": ["kurczak", "makaron", "pomidory"],
            "dietary_restrictions": None,
            "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
            "validation_level": ValidationLevel.STRICT,
            "max_ingredients_allowed": 3,
            "db": mock_db
        }

        await chef_agent.process(test_input_missing)


    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chef_agent_with_mock_db())
