from unittest.mock import AsyncMock, patch

import pytest

from agents.tools.search_providers import (
    DuckDuckGoSearchProvider,
    WikipediaSearchProvider,
)


@pytest.fixture
def wikipedia_provider():
    return WikipediaSearchProvider()


@pytest.fixture
def duckduckgo_provider():
    return DuckDuckGoSearchProvider()


@pytest.mark.asyncio
async def test_wikipedia_search_success(wikipedia_provider):
    """Test udanego wyszukiwania w Wikipedii."""
    mock_response = {
        "query": {
            "search": [
                {
                    "title": "Albert Einstein",
                    "snippet": "Albert Einstein was a German-born theoretical physicist...",
                    "pageid": 736,
                },
                {
                    "title": "Einstein (disambiguation)",
                    "snippet": "Einstein may refer to...",
                    "pageid": 12345,
                },
            ]
        }
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response_obj = type(
            "Response",
            (),
            {"raise_for_status": lambda self: None, "json": lambda self: mock_response},
        )()
        mock_get.return_value = mock_response_obj

        results = await wikipedia_provider.search("Albert Einstein")

        assert len(results) == 2
        assert results[0]["title"] == "Albert Einstein"
        assert (
            results[0]["snippet"]
            == "Albert Einstein was a German-born theoretical physicist..."
        )
        assert results[0]["pageid"] == 736


@pytest.mark.asyncio
async def test_wikipedia_search_no_results(wikipedia_provider):
    """Test wyszukiwania w Wikipedii bez wyników."""
    mock_response = {"query": {"search": []}}

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        results = await wikipedia_provider.search("xyz123nonexistent")

        assert results == []


@pytest.mark.asyncio
async def test_wikipedia_search_api_error(wikipedia_provider):
    """Test obsługi błędu API Wikipedii."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("API Error")

        # Wikipedia provider returns empty list on error, doesn't raise
        results = await wikipedia_provider.search("test")
        assert results == []


@pytest.mark.asyncio
async def test_duckduckgo_search_with_abstract(duckduckgo_provider):
    """Test wyszukiwania DuckDuckGo z abstraktem."""
    mock_response = {
        "Abstract": "Python is a programming language",  # Poprawiony klucz
        "Heading": "Python (programming language)",
        "AbstractURL": "https://python.org",
        "RelatedTopics": [
            {"Text": "Python Tutorial", "FirstURL": "https://python.org/tutorial"}
        ],
    }

    with patch.object(duckduckgo_provider.client, "get") as mock_get:
        mock_response_obj = type(
            "Response",
            (),
            {"raise_for_status": lambda self: None, "json": lambda self: mock_response},
        )()
        mock_get.return_value = mock_response_obj

        results = await duckduckgo_provider.search("Python programming")

        assert len(results) == 2
        assert results[0]["title"] == "Python (programming language)"
        assert results[0]["snippet"] == "Python is a programming language"
        assert results[0]["url"] == "https://python.org"
        assert results[1]["title"] == "Python Tutorial"
        assert results[1]["url"] == "https://python.org/tutorial"


@pytest.mark.asyncio
async def test_duckduckgo_search_no_abstract(duckduckgo_provider):
    """Test wyszukiwania DuckDuckGo bez abstraktu."""
    mock_response = {
        "Abstract": "",  # Poprawiony klucz
        "Heading": "",
        "AbstractURL": "",
        "RelatedTopics": [
            {"Text": "Python Tutorial", "FirstURL": "https://python.org/tutorial"},
            {"Text": "Python Documentation", "FirstURL": "https://python.org/docs"},
        ],
    }

    with patch.object(duckduckgo_provider.client, "get") as mock_get:
        mock_response_obj = type(
            "Response",
            (),
            {"raise_for_status": lambda self: None, "json": lambda self: mock_response},
        )()
        mock_get.return_value = mock_response_obj

        results = await duckduckgo_provider.search("Python")

        assert len(results) == 2
        assert results[0]["title"] == "Python Tutorial"
        assert results[0]["url"] == "https://python.org/tutorial"
        assert results[1]["title"] == "Python Documentation"
        assert results[1]["url"] == "https://python.org/docs"


@pytest.mark.asyncio
async def test_duckduckgo_search_empty_response(duckduckgo_provider):
    """Test wyszukiwania DuckDuckGo z pustą odpowiedzią."""
    mock_response = {}

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        results = await duckduckgo_provider.search("xyz123")

        assert results == []


@pytest.mark.asyncio
async def test_duckduckgo_search_api_error(duckduckgo_provider):
    """Test obsługi błędu API DuckDuckGo."""
    with patch.object(duckduckgo_provider.client, "get") as mock_get:
        mock_get.side_effect = Exception("API Error")

        # DuckDuckGo provider returns empty list on error, doesn't raise
        results = await duckduckgo_provider.search("test")
        assert results == []


@pytest.mark.asyncio
async def test_wikipedia_search_params(wikipedia_provider):
    """Test parametrów wyszukiwania Wikipedia."""
    with patch.object(wikipedia_provider.client, "get") as mock_get:
        mock_response_obj = type(
            "Response",
            (),
            {
                "raise_for_status": lambda self: None,
                "json": lambda self: {"query": {"search": []}},
            },
        )()
        mock_get.return_value = mock_response_obj

        await wikipedia_provider.search("test query", max_results=3)

        # Sprawdź czy wywołanie miało odpowiednie parametry
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "srsearch" in call_args[1]["params"]
        assert call_args[1]["params"]["srlimit"] == 3


@pytest.mark.asyncio
async def test_duckduckgo_search_params(duckduckgo_provider):
    """Test parametrów wyszukiwania DuckDuckGo."""
    with patch.object(duckduckgo_provider.client, "get") as mock_get:
        mock_response_obj = type(
            "Response",
            (),
            {
                "raise_for_status": lambda self: None,
                "json": lambda self: {"RelatedTopics": []},
            },
        )()
        mock_get.return_value = mock_response_obj

        await duckduckgo_provider.search("test query", max_results=3)

        # Sprawdź czy wywołanie miało odpowiednie parametry
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "q" in call_args[1]["params"]
        assert call_args[1]["params"]["q"] == "test query"
