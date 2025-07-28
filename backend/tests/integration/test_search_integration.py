from unittest.mock import patch

import pytest

from agents.search_agent import SearchAgent


@pytest.mark.asyncio
async def test_search_integration_wikipedia_encyclopedic():
    """Test integracyjny: zapytanie encyklopedyczne → Wikipedia provider."""
    # Wyłącz cache dla testów
    agent = SearchAgent(config={"cache_enabled": False})

    # Mock odpowiedzi Wikipedii
    wiki_results = [
        {
            "title": "Albert Einstein",
            "snippet": "Albert Einstein was a German-born theoretical physicist...",
            "pageid": 736,
            "url": "https://pl.wikipedia.org/wiki/Albert_Einstein",
            "source": "wikipedia",
        }
    ]

    # Mock metody search w WikipediaSearchProvider
    with patch.object(
        agent.search_providers["wikipedia"], "search", return_value=wiki_results
    ):
        results = await agent.process_request("kto to Albert Einstein")

        assert len(results) == 1
        assert results[0]["title"] == "Albert Einstein"
        assert "theoretical physicist" in results[0]["snippet"]
        assert results[0]["pageid"] == 736


@pytest.mark.asyncio
async def test_search_integration_duckduckgo_web():
    """Test integracyjny: zapytanie webowe → DuckDuckGo provider."""
    # Wyłącz cache dla testów
    agent = SearchAgent(config={"cache_enabled": False})

    # Mock odpowiedzi DuckDuckGo
    duck_results = [
        {
            "title": "Python (programming language)",
            "snippet": "Python is a high-level programming language",
            "url": "https://python.org",
            "source": "duckduckgo",
        },
        {
            "title": "Python Tutorial",
            "snippet": "Python Tutorial",
            "url": "https://python.org/tutorial",
            "source": "duckduckgo",
        },
    ]

    # Mock metody search w DuckDuckGoSearchProvider
    with patch.object(
        agent.search_providers["duck"], "search", return_value=duck_results
    ):
        results = await agent.process_request("szukaj informacji o Pythonie")

        assert len(results) == 2
        assert results[0]["title"] == "Python (programming language)"
        assert "programming language" in results[0]["snippet"]
        assert results[0]["url"] == "https://python.org"


@pytest.mark.asyncio
async def test_search_integration_fallback_scenario():
    """Test integracyjny: Wikipedia nie ma wyników → fallback na DuckDuckGo."""
    # Wyłącz cache dla testów
    agent = SearchAgent(config={"cache_enabled": False})

    # Wikipedia zwraca pustą odpowiedź
    wiki_empty_results = []

    # DuckDuckGo zwraca wyniki
    duck_results = [
        {
            "title": "Machine Learning",
            "snippet": "Machine learning is a subset of artificial intelligence",
            "url": "https://example.com/ml",
            "source": "duckduckgo",
        }
    ]

    # Mock metody search w obu providerach
    with (
        patch.object(
            agent.search_providers["wikipedia"],
            "search",
            return_value=wiki_empty_results,
        ),
        patch.object(
            agent.search_providers["duck"], "search", return_value=duck_results
        ),
    ):
        results = await agent.process_request("wikipedia: machine learning")

        assert len(results) == 1
        assert results[0]["title"] == "Machine Learning"
        assert "artificial intelligence" in results[0]["snippet"]


@pytest.mark.asyncio
async def test_search_integration_error_recovery():
    """Test integracyjny: błąd pierwszego providera → recovery przez drugi."""
    # Wyłącz cache dla testów
    agent = SearchAgent(config={"cache_enabled": False})

    # DuckDuckGo zwraca błąd, ale Wikipedia działa
    wiki_results = [
        {
            "title": "Test Article",
            "snippet": "Test content",
            "pageid": 123,
            "url": "https://pl.wikipedia.org/wiki/Test_Article",
            "source": "wikipedia",
        }
    ]

    # Mock metody search w obu providerach
    with (
        patch.object(
            agent.search_providers["duck"],
            "search",
            side_effect=Exception("Network error"),
        ),
        patch.object(
            agent.search_providers["wikipedia"], "search", return_value=wiki_results
        ),
    ):
        results = await agent.process_request("test query")

        assert len(results) == 1
        assert results[0]["title"] == "Test Article"


@pytest.mark.asyncio
async def test_search_integration_prefix_override():
    """Test integracyjny: prefix wymusza provider niezależnie od heurystyki."""
    # Wyłącz cache dla testów
    agent = SearchAgent(config={"cache_enabled": False})

    # Zapytanie z prefixem "duck:" ale treść encyklopedyczna
    duck_results = [
        {
            "title": "Search Results",
            "snippet": "Search results for encyclopedic query",
            "url": "https://example.com",
            "source": "duckduckgo",
        }
    ]

    # Mock metody search w DuckDuckGoSearchProvider
    with patch.object(
        agent.search_providers["duck"], "search", return_value=duck_results
    ):
        results = await agent.process_request("duck: kto to Albert Einstein")

        assert len(results) == 1
        assert results[0]["title"] == "Search Results"
        # Sprawdź czy użyto DuckDuckGo (nie Wikipedii) mimo treści encyklopedycznej


@pytest.mark.asyncio
async def test_search_integration_real_world_scenarios():
    """Test integracyjny: rzeczywiste scenariusze użycia."""
    agent = SearchAgent()

    test_cases = [
        ("wikipedia: historia Polski", "wikipedia"),
        ("szukaj najlepszych restauracji w Warszawie", "duck"),
        ("co to jest blockchain", "wikipedia"),
        ("aktualności z dzisiejszego dnia", "duck"),
        ("definicja sztucznej inteligencji", "wikipedia"),
        ("search for programming tutorials", "duck"),
    ]

    for query, expected_provider in test_cases:
        provider = agent.detect_search_type(query)
        assert (
            provider == expected_provider
        ), f"Query: {query}, Expected: {expected_provider}, Got: {provider}"
