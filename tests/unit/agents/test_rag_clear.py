#!/usr/bin/env python3
"""
Test wyczyszczenia vector store i ponownego przetestowania RAG
"""

import asyncio
import os
import sys

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_rag_clear_and_process():
    """Test wyczyszczenia vector store i ponownego przetestowania"""
    try:
        from backend.core.rag_document_processor import rag_document_processor
        from backend.core.vector_store import vector_store


        # Wyczyść vector store
        if vector_store is not None:
            await vector_store.clear_all()

            # Sprawdź statystyki po wyczyszczeniu
            await vector_store.get_stats()

        # Test przetwarzania pliku
        test_file = "test_rag_document.txt"
        if os.path.exists(test_file):

            metadata = {
                "filename": test_file,
                "description": "Test dokument RAG",
                "tags": ["test", "rag", "zdrowie"],
                "source": "test"
            }

            await rag_document_processor.process_file(test_file, metadata)

            # Sprawdź statystyki po przetwarzaniu
            if vector_store is not None:
                await vector_store.get_stats()
            else:
                pass

        else:
            pass

    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_clear_and_process())
