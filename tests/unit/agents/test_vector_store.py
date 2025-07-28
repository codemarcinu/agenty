#!/usr/bin/env python3
"""
Test script to check if vector store is working correctly
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_vector_store():
    """Test vector store functionality"""
    try:
        from backend.core.rag_document_processor import rag_document_processor
        from backend.core.vector_store import vector_store


        # Check if vector store is available
        if vector_store is None:
            return False


        # Test adding a document
        test_content = "To jest testowy dokument do sprawdzenia RAG systemu."
        test_metadata = {
            "filename": "test.txt",
            "description": "Test document",
            "tags": ["test", "rag"],
            "source": "test"
        }

        await rag_document_processor.process_document(
            content=test_content,
            source_id="test_doc_1",
            metadata=test_metadata
        )


        # Check if document was added
        await vector_store.get_stats()

        # Test search
        await vector_store.search_text("testowy dokument", k=5)

        # Save index
        await vector_store.save_index_async()

        return True

    except Exception:
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""

    success = await test_vector_store()

    if success:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
