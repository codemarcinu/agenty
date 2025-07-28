#!/usr/bin/env python3
"""
Test z rzeczywistymi zapytaniami użytkownika
"""

import asyncio
from datetime import datetime
import os
import sys

# Dodaj ścieżkę do src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from backend.agents.search_agent import SearchAgent


async def test_user_queries():
    """Test z rzeczywistymi zapytaniami użytkownika"""

    agent = SearchAgent()

    # Rzeczywiste zapytania użytkowników
    user_queries = [
        "Kim był Adam Mickiewicz?",
        "wyszukaj informacje na temat nowego prezydenta elekta Polski",
        "informacje na temat ostatnich wyborów prezydenckich w Polsce",
        "Jakie są najnowsze technologie AI?",
        "Gdzie mogę znaleźć przepisy na pierogi?",
        "Co to jest sztuczna inteligencja?",
        "Historia Warszawy - najważniejsze wydarzenia",
        "Jakie są tradycyjne polskie potrawy?",
        "Najnowsze wydarzenia w Polsce 2025",
        "Co to jest blockchain?"
    ]

    results_summary = {
        "total_queries": len(user_queries),
        "successful": 0,
        "failed": 0,
        "avg_time": 0,
        "total_time": 0.0
    }

    for i, query in enumerate(user_queries, 1):

        try:
            start_time = datetime.now()

            input_data = {
                "query": query,
                "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
                "max_results": 3
            }

            response = await agent.process(input_data)
            end_time = datetime.now()

            duration = (end_time - start_time).total_seconds()
            results_summary["total_time"] += duration


            if response.success:
                results_summary["successful"] += 1

                # Sprawdź czy są wyniki wyszukiwania
                if hasattr(response, "results") and response.results:
                    for j, result in enumerate(response.results[:2], 1):
                        pass
                else:
                    pass

                # Sprawdź odpowiedź AI
                if hasattr(response, "response") and response.response:
                    pass
                else:
                    pass

            else:
                results_summary["failed"] += 1
                response.error if hasattr(response, "error") else "Nieznany błąd"

        except Exception:
            results_summary["failed"] += 1


    # Podsumowanie

    if results_summary["successful"] > 0:
        results_summary["total_time"] / results_summary["successful"]

    if results_summary["successful"] >= results_summary["total_queries"] * 0.8 or results_summary["successful"] >= results_summary["total_queries"] * 0.6:
        pass
    else:
        pass



if __name__ == "__main__":
    asyncio.run(test_user_queries())
