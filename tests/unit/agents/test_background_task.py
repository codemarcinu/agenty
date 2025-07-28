#!/usr/bin/env python3
"""
Test bezpośredni background task
"""

import asyncio
import os
import sys
import tempfile

# Dodaj src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_background_task():
    """Test bezpośredni background task"""
    try:
        from backend.api.v2.endpoints.rag import process_document_background


        # Utwórz tymczasowy plik
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        temp_file.write("Test dokument dla background task")
        temp_file.close()


        # Wywołaj background task
        await process_document_background(
            file_path=temp_file.name,
            filename="test_background.txt",
            description="Test background task",
            tags=["test", "background"],
            directory_path=None
        )


        # Wyczyść plik tymczasowy
        os.unlink(temp_file.name)

    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_background_task())
