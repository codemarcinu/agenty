from unittest.mock import AsyncMock, patch

import pytest

from agents.interfaces import AgentResponse
from agents.search_agent import SearchAgent


@pytest.fixture
def search_agent():
    return SearchAgent()


@pytest.mark.asyncio
async def test_detect_search_type_prefix():
    """Test wyboru providera na podstawie prefixu."""
    agent = SearchAgent()
    assert agent.detect_search_type("wikipedia: Albert Einstein") == "wikipedia"
    assert agent.detect_search_type("duck: najlepsze restauracje") == "duck"
    assert agent.detect_search_type("duckduckgo: aktualności") == "duck"


@pytest.mark.asyncio
async def test_detect_search_type_heuristics():
    """Test wyboru providera na podstawie heurystyki."""
    agent = SearchAgent()
    # Heurystyka encyklopedyczna
    assert agent.detect_search_type("kto to Albert Einstein") == "wikipedia"
    assert agent.detect_search_type("co to jest sztuczna inteligencja") == "wikipedia"
    assert agent.detect_search_type("definicja blockchain") == "wikipedia"
    assert agent.detect_search_type("biografia Marii Curie") == "wikipedia"
    # Heurystyka webowa
    assert agent.detect_search_type("szukaj najlepszych restauracji") == "duck"
    assert agent.detect_search_type("search for programming tutorials") == "duck"
    assert agent.detect_search_type("find weather information") == "duck"
    assert agent.detect_search_type("aktualności z Polski") == "duck"


@pytest.mark.asyncio
async def test_detect_search_type_default():
    """Test domyślnego wyboru providera."""
    agent = SearchAgent()
    assert agent.detect_search_type("jakieś zwykłe zapytanie") == "duck"


@pytest.mark.asyncio
async def test_process_request_success():
    """Test przetwarzania zapytania z udanym wyszukiwaniem."""
    agent = SearchAgent()
    mock_results = [{"title": "Test", "snippet": "Test snippet"}]

    with patch.object(
        agent.search_providers["duck"], "search", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_results
        response = await agent.process({"query": "test query"})
        assert response.success is True
        assert response.text is not None and "Test" in response.text
        assert response.data["search_results"] == mock_results
        mock_search.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_process_request_fallback_no_results():
    """Test fallbacku gdy pierwszy provider nie zwraca wyników."""
    agent = SearchAgent(config={"cache_enabled": False})  # Wyłącz cache
    fallback_results = [{"title": "Fallback", "snippet": "Fallback snippet"}]

    with (
        patch.object(
            agent.search_providers["duck"], "search", new_callable=AsyncMock
        ) as mock_duck,
        patch.object(
            agent.search_providers["wikipedia"], "search", new_callable=AsyncMock
        ) as mock_wiki,
    ):
        mock_duck.return_value = []  # Brak wyników
        mock_wiki.return_value = fallback_results
        response = await agent.process({"query": "test query"})
        assert response.success is True
        assert response.data["search_results"] == fallback_results
        mock_duck.assert_called_once()
        mock_wiki.assert_called_once()


@pytest.mark.asyncio
async def test_process_request_fallback_error():
    """Test fallbacku gdy pierwszy provider zwraca błąd."""
    agent = SearchAgent(config={"cache_enabled": False})  # Wyłącz cache
    fallback_results = [{"title": "Fallback", "snippet": "Fallback snippet"}]

    with (
        patch.object(
            agent.search_providers["duck"], "search", new_callable=AsyncMock
        ) as mock_duck,
        patch.object(
            agent.search_providers["wikipedia"], "search", new_callable=AsyncMock
        ) as mock_wiki,
    ):
        mock_duck.side_effect = Exception("Network error")
        mock_wiki.return_value = fallback_results
        response = await agent.process({"query": "test query"})
        assert response.success is True
        assert response.data["search_results"] == fallback_results
        mock_duck.assert_called_once()
        mock_wiki.assert_called_once()


@pytest.mark.asyncio
async def test_process_request_both_providers_fail():
    """Test gdy oba providery zwracają błąd."""
    agent = SearchAgent(config={"cache_enabled": False})  # Wyłącz cache

    with (
        patch.object(
            agent.search_providers["duck"], "search", new_callable=AsyncMock
        ) as mock_duck,
        patch.object(
            agent.search_providers["wikipedia"], "search", new_callable=AsyncMock
        ) as mock_wiki,
    ):
        mock_duck.side_effect = Exception("Network error")
        mock_wiki.side_effect = Exception("API error")
        response = await agent.process({"query": "test query"})
        assert response.success is True
        assert response.data["search_results"] == []
        mock_duck.assert_called_once()
        mock_wiki.assert_called_once()


@pytest.mark.asyncio
async def test_process_request_wikipedia_provider():
    """Test przetwarzania zapytania przez Wikipedia provider."""
    agent = SearchAgent()
    wiki_results = [
        {"title": "Wikipedia Article", "snippet": "Wikipedia snippet", "pageid": 123}
    ]

    with patch.object(
        agent.search_providers["wikipedia"], "search", new_callable=AsyncMock
    ) as mock_wiki:
        mock_wiki.return_value = wiki_results
        response = await agent.process({"query": "wikipedia: Albert Einstein"})
        assert response.success is True
        assert response.text is not None and "Wikipedia Article" in response.text
        assert response.data["search_results"] == wiki_results
        mock_wiki.assert_called_once_with("wikipedia: Albert Einstein")


@pytest.mark.asyncio
async def test_process_request_empty_query():
    """Test obsługi pustego zapytania."""
    agent = SearchAgent()
    response = await agent.process({"query": ""})
    assert response.success is False
    assert (
        response.error is not None and "Brak zapytania wyszukiwania" in response.error
    )
    assert response.text is not None and "Proszę podać zapytanie" in response.text


@pytest.mark.asyncio
async def test_process_request_none_context():
    """Test obsługi None context."""
    agent = SearchAgent()
    mock_results = [{"title": "Test", "snippet": "Test snippet"}]

    with patch.object(
        agent.search_providers["duck"], "search", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_results
        response = await agent.process({"query": "test query", "context": None})
        assert response.success is True
        assert response.text is not None and "Test" in response.text
        assert response.data["search_results"] == mock_results


@pytest.mark.asyncio
async def test_process_method_success():
    """Test metody process() z udanym wyszukiwaniem."""
    agent = SearchAgent()
    mock_results = [{"title": "Test Article", "snippet": "Test snippet", "pageid": 123}]

    with patch.object(agent, "process_request", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = mock_results
        response = await agent.process({"query": "test query"})

        assert response.success is True
        assert response.text is not None and "Test Article" in response.text
        assert response.data["search_results"] == mock_results
        assert response.data["provider_used"] == "duck"
        assert response.metadata["agent_type"] == "search"
        assert response.metadata["results_count"] == 1


@pytest.mark.asyncio
async def test_process_method_empty_query():
    """Test metody process() z pustym zapytaniem."""
    agent = SearchAgent()
    response = await agent.process({"query": ""})

    assert response.success is False
    assert (
        response.error is not None and "Brak zapytania wyszukiwania" in response.error
    )
    assert response.text is not None and "Proszę podać zapytanie" in response.text


@pytest.mark.asyncio
async def test_process_method_with_context():
    """Test metody process() z kontekstem i ResponseGenerator."""
    agent = SearchAgent()
    mock_results = [{"title": "Test", "snippet": "Test snippet"}]

    with patch.object(agent, "process_request", new_callable=AsyncMock) as mock_process:
        with patch.object(
            agent.response_generator, "generate_response", new_callable=AsyncMock
        ) as mock_generate:
            mock_process.return_value = mock_results
            mock_generate.return_value = AgentResponse(
                success=True, text="Formatted response", metadata={"formatted": True}
            )

            context = {"session_id": "test_session"}
            response = await agent.process({"query": "test", "context": context})

            assert response.success is True
            assert response.text == "Formatted response"
            mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_format_search_results_wikipedia():
    """Test formatowania wyników Wikipedii."""
    agent = SearchAgent()
    results = [
        {"title": "Albert Einstein", "snippet": "German physicist", "pageid": 736}
    ]

    formatted = agent.format_search_results(results, "wikipedia")
    assert "Albert Einstein" in formatted
    assert "German physicist" in formatted
    assert "(ID: 736)" in formatted


@pytest.mark.asyncio
async def test_format_search_results_duckduckgo():
    """Test formatowania wyników DuckDuckGo."""
    agent = SearchAgent()
    results = [
        {
            "title": "Python",
            "snippet": "Programming language",
            "url": "https://python.org",
        }
    ]

    formatted = agent.format_search_results(results, "duck")
    assert "Python" in formatted
    assert "Programming language" in formatted
    assert "https://python.org" in formatted


@pytest.mark.asyncio
async def test_format_search_results_empty():
    """Test formatowania pustych wyników."""
    agent = SearchAgent()
    formatted = agent.format_search_results([], "wikipedia")
    assert "Nie znaleziono wyników" in formatted


@pytest.mark.asyncio
async def test_format_search_results_limit():
    """Test limitu wyników (maksymalnie 5)."""
    agent = SearchAgent()
    results = [{"title": f"Article {i}", "snippet": f"Snippet {i}"} for i in range(10)]

    formatted = agent.format_search_results(results, "duck")
    # Sprawdź czy tylko pierwsze 5 wyników zostało sformatowane
    assert "Article 0" in formatted
    assert "Article 4" in formatted
    assert "Article 5" not in formatted  # Powinno być pominięte


@pytest.mark.asyncio
async def test_get_metadata():
    """Test metadanych agenta."""
    agent = SearchAgent()
    metadata = agent.get_metadata()

    assert metadata["agent_type"] == "search"
    assert "web_search" in metadata["capabilities"]
    assert "wikipedia" in metadata["providers"]
    assert "duck" in metadata["providers"]


@pytest.mark.asyncio
async def test_get_dependencies():
    """Test zależności agenta."""
    agent = SearchAgent()
    dependencies = agent.get_dependencies()

    assert "ResponseGenerator" in dependencies


@pytest.mark.asyncio
async def test_is_healthy():
    """Test sprawdzania zdrowia agenta."""
    agent = SearchAgent()
    assert agent.is_healthy() is True
