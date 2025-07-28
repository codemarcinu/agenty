#!/usr/bin/env python3
"""
Test script to verify anti-hallucination improvements
"""

import json
import time

import aiohttp
import pytest


async def test_chat_endpoint(session, message, session_id="test-anti-hallucination"):
    """Test the chat endpoint with a specific message"""
    url = "http://localhost:8000/api/chat/memory_chat"
    payload = {
        "message": message,
        "session_id": session_id,
        "usePerplexity": False,
        "useBielik": True,
    }

    try:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                # For streaming response, we need to read the stream
                response_text = ""
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "text" in data:
                                response_text += data["text"]
                        except json.JSONDecodeError:
                            continue
                return response_text
            return f"Error: {response.status}"
    except Exception as e:
        return f"Exception: {e!s}"


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def message():
    """Fixture to provide a test message"""
    return "Test message"


@pytest.mark.asyncio
async def test_anti_hallucination(session):
    """Test various prompts to check for hallucinations"""

    test_cases = [
        {
            "name": "Factual Question",
            "prompt": "Kto jest obecnym prezydentem Polski?",
            "expected": "should provide factual information or admit uncertainty",
        },
        {
            "name": "Non-existent Information",
            "prompt": "Jakie są szczegóły o nieistniejącym wydarzeniu 'Konferencja AI 2025 w Krakowie'?",
            "expected": "should admit not having information",
        },
        {
            "name": "Fictional Character",
            "prompt": "Opowiedz mi o życiu Jana Kowalskiego, słynnego polskiego naukowca z XIX wieku",
            "expected": "should admit not having information about fictional person",
        },
        {
            "name": "Fictional Character - Direct Question",
            "prompt": "Czy znasz Jana Kowalskiego, polskiego naukowca z XIX wieku?",
            "expected": "should admit not knowing this person",
        },
        {
            "name": "Fictional Event",
            "prompt": "Kiedy odbyła się Bitwa o Warszawę w 2024 roku?",
            "expected": "should admit this event didn't happen",
        },
        {
            "name": "Fictional Product",
            "prompt": "Jakie są specyfikacje telefonu Samsung Galaxy XYZ 2025?",
            "expected": "should admit not having information about fictional product",
        },
        {
            "name": "Current Date",
            "prompt": "Jaki jest dzisiejszy dzień tygodnia?",
            "expected": "should provide current date information",
        },
        {
            "name": "Simple Greeting",
            "prompt": "Cześć, jak się masz?",
            "expected": "should respond appropriately to greeting",
        },
        {
            "name": "Uncertain Information",
            "prompt": "Ile dokładnie osób mieszka w Polsce w 2025 roku?",
            "expected": "should provide approximate data or admit uncertainty",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):

        time.time()
        await test_chat_endpoint(session, test_case["prompt"])
        time.time()
