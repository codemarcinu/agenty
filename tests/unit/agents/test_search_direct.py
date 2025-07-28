#!/usr/bin/env python3
"""
Test bezpośredniego wyszukiwania w vector store
"""

import asyncio
import os
import sys

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_search_direct():
    """Test bezpośredniego wyszukiwania"""
    try:
        from backend.core.vector_store import vector_store


        if vector_store is not None:
            # Sprawdź statystyki
            await vector_store.get_stats()

            # Test wyszukiwania
            try:
                results = await vector_store.search_text(
                    query="zdrowe odżywianie",
                    k=5,
                    min_similarity=0.0
                )

                for i, result in enumerate(results):
                    pass

            except Exception:
                import traceback
                traceback.print_exc()
        else:
            pass

    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_direct())
