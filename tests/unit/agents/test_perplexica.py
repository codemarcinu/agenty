#!/usr/bin/env python3
import asyncio
import os
import sys

# Dodaj ścieżkę do src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.tools.search_providers import PerplexicaSearchProvider


async def test_perplexica():

    provider = PerplexicaSearchProvider()

    try:
        results = await provider.search("Adam Mickiewicz", 3)

        for i, result in enumerate(results, 1):
            pass

    except Exception:
        pass

    finally:
        await provider.close()

if __name__ == "__main__":
    asyncio.run(test_perplexica())
