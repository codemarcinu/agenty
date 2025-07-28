#!/usr/bin/env python3
"""Simple API test script"""

import asyncio
import sys

import pytest

sys.path.append("src/backend")

from backend.core.llm_client import llm_client


@pytest.mark.asyncio
async def test_api(model_name="mistral:7b"):
    """Test our LLM API"""
    try:
        await llm_client.chat(
            model_name, [{"role": "user", "content": "Hello"}], stream=False
        )
        return True
    except Exception:
        return False


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "mistral:7b"
    success = asyncio.run(test_api(model))
    sys.exit(0 if success else 1)
