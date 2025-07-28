#!/usr/bin/env python3
import asyncio
import os
import sys

# Dodaj ścieżkę do src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.search_agent import SearchAgent


async def test_current_events():

    # Tworzę SearchAgent
    agent = SearchAgent()

    queries = [
        "ostatnie wybory prezydenckie w Polsce",
        "nowy prezydent Polski",
        "aktualne wydarzenia w Polsce 2025"
    ]

    for query in queries:
        try:
            input_data = {
                "query": query,
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

    # Zamykam klienta HTTP
    if hasattr(agent, "http_client"):
        await agent.http_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_current_events())
