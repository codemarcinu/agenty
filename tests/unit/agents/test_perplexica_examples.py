#!/usr/bin/env python3
"""
Przykładowe wyszukiwania dla testowania hybrydowej integracji Perplexica
"""

import asyncio
from datetime import datetime
import os
import sys

# Dodaj ścieżkę do src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.search_agent import SearchAgent
from backend.agents.tools.search_providers import PerplexicaSearchProvider


async def test_perplexica_search_provider():
    """Test PerplexicaSearchProvider bezpośrednio"""

    provider = PerplexicaSearchProvider()

    test_queries = [
        "Adam Mickiewicz",
        "ostatnie wybory prezydenckie w Polsce",
        "najnowsze technologie AI 2025",
        "przepisy na pierogi",
        "historia Warszawy"
    ]

    for i, query in enumerate(test_queries, 1):

        try:
            start_time = datetime.now()
            results = await provider.search(query, max_results=3)
            end_time = datetime.now()

            (end_time - start_time).total_seconds()


            if results:
                for j, result in enumerate(results, 1):
                    pass
            else:
                pass

        except Exception:
            pass



async def test_search_agent_integration():
    """Test integracji z SearchAgent"""

    agent = SearchAgent()

    test_queries = [
        "Kim był Adam Mickiewicz?",
        "Jakie są najnowsze wydarzenia w Polsce?",
        "Co to jest sztuczna inteligencja?",
        "Jakie są tradycyjne polskie potrawy?",
        "Historia i zabytki Krakowa"
    ]

    for i, query in enumerate(test_queries, 1):

        try:
            start_time = datetime.now()

            input_data = {
                "query": query,
                "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
                "max_results": 3
            }

            response = await agent.process(input_data)
            end_time = datetime.now()

            (end_time - start_time).total_seconds()


            if response.success:
                pass
            else:
                pass

        except Exception:
            pass



async def test_fallback_scenarios():
    """Test scenariuszy fallback"""

    provider = PerplexicaSearchProvider()

    # Test z bardzo specyficznym zapytaniem
    specific_queries = [
        "najnowsze wydarzenia w Polsce 2025",
        "aktualny prezydent Polski",
        "ostatnie wybory parlamentarne",
        "najnowsze technologie AI",
        "przyszłe wydarzenia kulturalne w Warszawie"
    ]

    for i, query in enumerate(specific_queries, 1):

        try:
            results = await provider.search(query, max_results=2)


            if results:
                [result.get("source", "unknown") for result in results]

                for j, result in enumerate(results, 1):
                    pass
            else:
                pass

        except Exception:
            pass



async def test_performance_comparison():
    """Porównanie wydajności różnych providerów"""

    from backend.agents.tools.search_providers import (
        DuckDuckGoSearchProvider,
        WikipediaSearchProvider,
    )

    providers = {
        "Perplexica": PerplexicaSearchProvider(),
        "Wikipedia": WikipediaSearchProvider(),
        "DuckDuckGo": DuckDuckGoSearchProvider()
    }

    test_query = "Adam Mickiewicz"

    for provider in providers.values():

        try:
            start_time = datetime.now()
            results = await provider.search(test_query, max_results=2)
            end_time = datetime.now()

            (end_time - start_time).total_seconds()


            if results:
                for i, result in enumerate(results, 1):
                    pass

        except Exception:
            pass



async def main():
    """Główna funkcja testowa"""

    # Test 1: PerplexicaSearchProvider
    await test_perplexica_search_provider()

    # Test 2: Integracja z SearchAgent
    await test_search_agent_integration()

    # Test 3: Scenariusze fallback
    await test_fallback_scenarios()

    # Test 4: Porównanie wydajności
    await test_performance_comparison()



if __name__ == "__main__":
    asyncio.run(main())
