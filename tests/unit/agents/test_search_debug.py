#!/usr/bin/env python3
"""
Test wyszukiwania z debugowaniem
"""

import asyncio
import os
import sys

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_search_debug():
    """Test wyszukiwania z debugowaniem"""
    try:
        from backend.core.hybrid_llm_client import hybrid_llm_client
        from backend.core.vector_store import vector_store


        if vector_store is not None:
            # Sprawdź statystyki
            await vector_store.get_stats()

            # Sprawdź czy indeks ma wektory
            if hasattr(vector_store.index, "ntotal"):
                pass
            else:
                pass

            # Test generowania embedding dla zapytania
            try:
                embedding_response = await hybrid_llm_client.embed(text="zdrowe odżywianie")

                # Test wyszukiwania bezpośrednio
                query_embedding = vector_store._adjust_dimension_if_needed(
                    vector_store.normalize_embedding(embedding_response)
                )

                # Test search
                results = await vector_store.search(query_embedding, k=3)

                for i, (doc, similarity) in enumerate(results):
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
    asyncio.run(test_search_debug())
