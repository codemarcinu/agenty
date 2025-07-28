#!/usr/bin/env python3
"""
Pełny test pipeline RAG z dodaniem dokumentu, wyszukiwaniem i generowaniem odpowiedzi
"""

import asyncio
import os
import sys

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_rag_full_pipeline():
    """Pełny test pipeline RAG"""
    try:
        from backend.core.hybrid_llm_client import hybrid_llm_client
        from backend.core.rag_document_processor import rag_document_processor
        from backend.core.vector_store import vector_store


        # Wyczyść vector store
        if vector_store is not None:
            await vector_store.clear_all()

        # Test 1: Dodanie dokumentu
        test_file = "test_rag_document.txt"
        if os.path.exists(test_file):

            metadata = {
                "filename": test_file,
                "description": "Przewodnik po zdrowej żywności",
                "tags": ["zdrowie", "przepisy", "odżywianie"],
                "source": "test"
            }

            result = await rag_document_processor.process_file(test_file, metadata)

            # Sprawdź statystyki
            if vector_store is not None:
                await vector_store.get_stats()

            # Test 2: Wyszukiwanie
            try:
                if vector_store is not None:
                    search_results = await vector_store.search_text(
                        query="Jakie są podstawowe zasady zdrowego odżywiania?",
                        k=3,
                        min_similarity=0.0
                    )

                    for i, result in enumerate(search_results):
                        pass

                    # Test 3: Generowanie odpowiedzi
                    if search_results:
                        context = "\n\n".join([r["content"] for r in search_results])
                        prompt = f"""Na podstawie poniższych informacji odpowiedz na pytanie:

Kontekst:
{context}

Pytanie: Jakie są podstawowe zasady zdrowego odżywiania?

Odpowiedź:"""

                        await hybrid_llm_client.chat(
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=500,
                            temperature=0.7
                        )

                    else:
                        pass
                else:
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
    asyncio.run(test_rag_full_pipeline())
