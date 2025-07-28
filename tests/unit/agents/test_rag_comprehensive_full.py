#!/usr/bin/env python3
"""
Kompleksowy test RAG - pełny pipeline od uploadu do wykorzystania przez modele
"""

import asyncio
import contextlib
import os
import sys
import time
from unittest.mock import Mock

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_rag_full_pipeline():
    """Kompleksowy test całego pipeline RAG"""

    try:
        # Import komponentów
        from backend.core.rag_document_processor import rag_document_processor
        from backend.core.rag_integration import rag_integration
        from backend.core.vector_store import vector_store


        # Test 1: Sprawdzenie stanu początkowego
        if vector_store is not None:
            await vector_store.get_stats()
        else:
            return None

        # Test 2: Czyszczenie vector store
        await vector_store.clear_all()
        await vector_store.get_stats()

        # Test 3: Przygotowanie dokumentu testowego
        test_file = "test_rag_document.txt"
        if not os.path.exists(test_file):
            return None

        os.path.getsize(test_file)

        # Test 4: Przetwarzanie dokumentu
        metadata = {
            "filename": test_file,
            "description": "Przewodnik po zdrowej żywności i przepisach",
            "tags": ["zdrowie", "przepisy", "odżywianie", "dieta"],
            "source": "test_comprehensive",
            "category": "nutrition_guide"
        }

        start_time = time.time()
        result = await rag_document_processor.process_file(test_file, metadata)
        time.time() - start_time


        # Test 5: Sprawdzenie statystyk po przetworzeniu
        await vector_store.get_stats()

        # Test 6: Wyszukiwanie semantyczne
        test_queries = [
            "Jakie są podstawowe zasady zdrowego odżywiania?",
            "Przepis na owsiankę z owocami",
            "Jak przechowywać żywność?",
            "Wskazówki dla diabetyków",
            "Dieta wegetariańska"
        ]

        for i, query in enumerate(test_queries, 1):
            try:
                search_results = await vector_store.search_text(
                    query=query,
                    k=3,
                    min_similarity=0.5
                )
                for j, result in enumerate(search_results[:2], 1):
                    pass
            except Exception:
                pass

        # Test 7: Test RAG Integration
        mock_db = Mock()
        with contextlib.suppress(Exception):
            await rag_integration.query_rag(
                "Jakie są podstawowe zasady zdrowego odżywiania?",
                mock_db
            )

        # Test 8: Test listowania dokumentów
        try:
            documents = await rag_integration.list_rag_documents(mock_db)
            for doc in documents[:3]:
                pass
        except Exception:
            pass

        # Test 9: Test różnych typów zapytań
        complex_queries = [
            ("Przepisy", "Znajdź przepisy na zdrowe śniadania"),
            ("Przechowywanie", "Jak przechowywać mięso i warzywa?"),
            ("Witaminy", "Jakie witaminy są ważne dla zdrowia?"),
            ("Aktywność", "Co jeść przed i po treningu?"),
            ("Diabetycy", "Wskazówki żywieniowe dla diabetyków")
        ]

        for category, query in complex_queries:
            try:
                results = await vector_store.search_text(
                    query=query,
                    k=2,
                    min_similarity=0.6
                )
                if results:
                    best_match = results[0]
                    best_match.get("similarity", 0)
                else:
                    pass
            except Exception:
                pass

        # Test 10: Test wydajności
        performance_queries = [
            "zdrowe odżywianie",
            "przepisy",
            "witaminy",
            "przechowywanie",
            "aktywność fizyczna"
        ]

        total_time = 0
        successful_queries = 0

        for query in performance_queries:
            start_time = time.time()
            try:
                results = await vector_store.search_text(
                    query=query,
                    k=3,
                    min_similarity=0.5
                )
                query_time = time.time() - start_time
                total_time += query_time
                successful_queries += 1
            except Exception:
                pass

        if successful_queries > 0:
            total_time / successful_queries

        # Test 11: Sprawdzenie końcowych statystyk
        await vector_store.get_stats()

        # Podsumowanie

        return True

    except Exception:
        import traceback
        traceback.print_exc()
        return False

async def test_rag_api_endpoints():
    """Test endpointów API RAG"""


    import requests

    base_url = "http://localhost:8003"  # Używamy portu 8003

    # Test 1: Sprawdzenie statystyk
    try:
        response = requests.get(f"{base_url}/api/v2/rag/stats")
        if response.status_code == 200:
            response.json()
        else:
            pass
    except Exception:
        pass

    # Test 2: Upload dokumentu przez API
    try:
        with open("test_rag_document.txt", "rb") as f:
            files = {"file": ("test_rag_document.txt", f, "text/plain")}
            data = {
                "description": "Test dokument przez API",
                "tags": ["test", "api", "rag"],
                "directory_path": "test"
            }
            response = requests.post(
                f"{base_url}/api/v2/rag/upload",
                files=files,
                data=data
            )

            if response.status_code == 200:
                response.json()
            else:
                pass
    except Exception:
        pass

    # Test 3: Wyszukiwanie przez API
    try:
        response = requests.get(
            f"{base_url}/api/v2/rag/search",
            params={
                "query": "zdrowe odżywianie",
                "k": 3,
                "min_similarity": 0.5
            }
        )

        if response.status_code == 200:
            response.json()
        else:
            pass
    except Exception:
        pass

if __name__ == "__main__":

    # Test głównego pipeline
    success = asyncio.run(test_rag_full_pipeline())

    if success:
        # Test API endpointów
        asyncio.run(test_rag_api_endpoints())

