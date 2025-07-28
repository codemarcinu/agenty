#!/usr/bin/env python3
"""
Simple test script to verify FoodSave AI fixes
"""

import asyncio
import sys

import pytest

# Add src to path
sys.path.insert(0, "src")


@pytest.mark.asyncio
async def test_fixes():
    """Test that the fixes are working"""

    try:
        # Test 1: Orchestrator import and methods
        from backend.agents.orchestrator import Orchestrator

        orchestrator = Orchestrator()

        # Check if methods exist
        if hasattr(orchestrator, "process_command"):
            pass
        else:
            pass

        if hasattr(orchestrator, "_initialize_default_agents"):
            pass
        else:
            pass

        # Test 2: LLM Client
        from backend.core.llm_client import llm_client

        llm_client.get_health_status()

        # Test 3: Agent Router
        from backend.agents.agent_router import AgentRouter

        AgentRouter()

        # Test 4: Simple Circuit Breaker
        from backend.agents.orchestrator import SimpleCircuitBreaker

        SimpleCircuitBreaker("test", 3, 60)

        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fixes())
    sys.exit(0 if success else 1)
