#!/usr/bin/env python3
import asyncio
import os
import sys

# Dodaj ścieżkę do src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.search_agent import SearchAgent


async def test_search_integration():

    # Tworzę SearchAgent
    agent = SearchAgent()

    try:
        # Test wyszukiwania
        input_data = {
            "query": "Adam Mickiewicz",
            "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
            "max_results": 3
        }

        response = await agent.process(input_data)

        if response.success:
            pass
        else:
            pass

    except Exception:
        pass

    finally:
        # Zamykam klienta HTTP
        if hasattr(agent, "http_client"):
            await agent.http_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_search_integration())
