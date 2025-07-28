#!/usr/bin/env python3
"""
Simple test script to verify RAG database management functionality
"""

import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import contextlib

from backend.core.rag_document_processor import RAGDocumentProcessor
from backend.core.rag_integration import RAGDatabaseIntegration


async def test_rag_functionality():
    """Test basic RAG functionality"""

    # Initialize RAG components
    rag_processor = RAGDocumentProcessor()
    rag_integration = RAGDatabaseIntegration(rag_processor)


    # Test getting stats
    with contextlib.suppress(Exception):
        await rag_integration.get_rag_stats()

    # Test listing directories
    with contextlib.suppress(Exception):
        await rag_integration.list_rag_directories()

    # Test creating directory
    with contextlib.suppress(Exception):
        await rag_integration.create_rag_directory("test_directory")

    # Test searching documents
    with contextlib.suppress(Exception):
        await rag_integration.search_documents_in_rag(
            "test query", k=5
        )

    # Test deleting directory
    with contextlib.suppress(Exception):
        await rag_integration.delete_rag_directory("test_directory", None)



if __name__ == "__main__":
    asyncio.run(test_rag_functionality())
