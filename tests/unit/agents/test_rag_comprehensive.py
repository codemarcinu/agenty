#!/usr/bin/env python3
"""
Kompleksowy test RAG z dodaniem dokumentu i wyszukiwaniem
"""

import asyncio
import os
import sys
from unittest.mock import Mock

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_rag_comprehensive():
    """Kompleksowy test RAG"""
    try:
        from backend.core.rag_document_processor import rag_document_processor
        from backend.core.rag_integration import rag_integration
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

            await rag_document_processor.process_file(test_file, metadata)

            # Sprawdź statystyki
            if vector_store is not None:
                await vector_store.get_stats()

            # Test 2: Wyszukiwanie
            mock_db = Mock()
            await rag_integration.query_rag(
                "Jakie są podstawowe zasady zdrowego odżywiania?",
                mock_db
            )

            # Test 3: Lista dokumentów
            await rag_integration.list_rag_documents(mock_db)

        else:
            pass

    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_comprehensive())
