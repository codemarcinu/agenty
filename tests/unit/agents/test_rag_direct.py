#!/usr/bin/env python3
"""
Bezpośredni test RAG processor
"""

import asyncio
import os
import sys

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_rag_processor():
    """Test RAG processor bezpośrednio"""
    try:
        from backend.core.rag_document_processor import rag_document_processor
        from backend.core.vector_store import vector_store


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

            # Sprawdź statystyki
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
    asyncio.run(test_rag_processor())
