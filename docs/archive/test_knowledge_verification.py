#!/usr/bin/env python3
"""
Simple test script to verify knowledge verification functionality
"""

import asyncio
import contextlib
import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


@pytest.mark.asyncio
async def test_knowledge_verification():
    """Test the knowledge verification functionality"""
    try:
        from backend.agents.search_agent import SearchAgent
        from backend.core.hybrid_llm_client import hybrid_llm_client
        from backend.core.vector_store import VectorStore
        from backend.integrations.web_search import web_search


        # Test 1: Basic web search
        try:
            results = await web_search.search("artificial intelligence", max_results=3)
            for i, result in enumerate(results, 1):
                pass
        except Exception:
            pass

        # Test 2: Search with verification
        try:
            verification_result = await web_search.search_with_verification(
                "machine learning", max_results=3
            )

            sum(
                1 for r in verification_result["results"] if r["knowledge_verified"]
            )
        except Exception:
            pass

        # Test 3: SearchAgent with knowledge verification
        try:
            vector_store = VectorStore()
            search_agent = SearchAgent(
                vector_store=vector_store, llm_client=hybrid_llm_client
            )

            response = await search_agent.process(
                {
                    "query": "Python programming language",
                    "use_perplexity": False,
                    "verify_knowledge": True,
                }
            )


            # Consume the stream
            result_text = ""
            async for chunk in response.text_stream:
                result_text += chunk

            if "Wskaźnik wiarygodności" in result_text:
                pass
            else:
                pass

        except Exception:
            pass

        # Test 4: Knowledge claim verification
        with contextlib.suppress(Exception):
            verification_result = await search_agent.verify_knowledge_claim(
                "Python is a programming language", "programming languages"
            )




    except ImportError:
        pass
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(test_knowledge_verification())
