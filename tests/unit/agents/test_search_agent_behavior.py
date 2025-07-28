#!/usr/bin/env python3
"""
Test zachowania SearchAgent z integracją Perplexica
"""

import asyncio
import os
import sys

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.search_agent import SearchAgent


async def test_search_agent():
    """Test zachowania SearchAgent z zapytaniem o pogodę"""


    # Inicjalizacja agenta
    try:
        agent = SearchAgent()
    except Exception:
        return

    # Test zapytania o pogodę
    query = "pogoda na dziś"

    try:
        # Wykonaj wyszukiwanie
        results = await agent.process_request(query)

        for i, result in enumerate(results, 1):
            pass

        # Test fallbacku

        # Sprawdź status Perplexica

    except Exception:
        import traceback
        traceback.print_exc()

async def test_provider_fallback():
    """Test fallbacku między providerami"""


    agent = SearchAgent()

    # Test różnych providerów
    providers = ["perplexica", "wikipedia", "duck"]

    for provider in providers:
        try:
            if provider in agent.search_providers:
                results = await agent.search_providers[provider].search("pogoda", max_results=2)
                if results:
                    pass
            else:
                pass
        except Exception:
            pass

if __name__ == "__main__":

    # Ustaw zmienne środowiskowe
    os.environ.setdefault("PERPLEXICA_BASE_URL", "http://localhost:3000/api")
    os.environ.setdefault("PERPLEXICA_ENABLED", "true")

    asyncio.run(test_search_agent())
    asyncio.run(test_provider_fallback())

