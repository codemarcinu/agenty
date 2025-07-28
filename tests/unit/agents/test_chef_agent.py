#!/usr/bin/env python3
"""
Test script for ChefAgent with ingredient verification
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.chef_agent import ChefAgent
from backend.core.anti_hallucination_system import ValidationLevel


async def test_chef_agent():
    """Test ChefAgent with ingredient verification"""


    # Create ChefAgent instance
    chef_agent = ChefAgent()

    # Test data
    test_input = {
        "available_ingredients": ["kurczak", "ryż", "brokuły"],
        "dietary_restrictions": None,
        "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        "validation_level": ValidationLevel.STRICT,
        "max_ingredients_allowed": 3,
        "session_id": "test_session"
    }


    try:
        # Test ingredient extraction from query
        query = "Mam kurczaka, ryż i brokuły. Co mogę z tego zrobić?"
        chef_agent._extract_ingredients_from_query(query)

        # Test ingredient similarity
        chef_agent._ingredients_similar("kurczak", "chicken")

        # Test similar ingredients finding
        available_products = ["indyk", "wołowina", "makaron", "kasza"]
        chef_agent._find_similar_ingredients("kurczak", available_products)

        # Test recipe generation (without database for now)
        response = await chef_agent.process(test_input)

        if response.data:
            pass

    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chef_agent())
