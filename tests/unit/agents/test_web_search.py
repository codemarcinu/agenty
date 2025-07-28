from unittest.mock import Mock, patch

import pytest

from backend.integrations.web_search import (
    SearchResponse,
    SearchResult,
    SourceConfig,
    WebSearch,
    WebSearchClient,
    WikipediaSearchClient,
)


class TestWikipediaSearchClient:
    """Test Wikipedia search client functionality"""

    @pytest.fixture
    def wikipedia_client(self) -> WikipediaSearchClient:
        """Create Wikipedia search client"""
        return WikipediaSearchClient()

    @pytest.mark.asyncio
    async def test_wikipedia_search_success(
        self, wikipedia_client: WikipediaSearchClient
    ) -> None:
        """Test successful Wikipedia search"""
        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock search response
            mock_search_response = Mock()
            mock_search_response.raise_for_status.return_value = None
            mock_search_response.json.return_value = {
                "query": {
                    "search": [
                        {
                            "title": "Test Article",
                            "snippet": "This is a test article about testing",
                            "timestamp": "2024-01-01T00:00:00Z",
                        }
                    ]
                }
            }

            # Mock summary response
            mock_summary_response = Mock()
            mock_summary_response.raise_for_status.return_value = None
            mock_summary_response.json.return_value = {
                "extract": "This is a detailed summary of the test article."
            }

            mock_get.side_effect = [mock_search_response, mock_summary_response]

            results = await wikipedia_client.search("test query", max_results=1)

            assert len(results) == 1
            assert results[0].title == "Test Article"
            assert results[0].source == "wikipedia"
            assert results[0].knowledge_verified is True
            assert results[0].source_confidence == 0.9

    @pytest.mark.asyncio
    async def test_wikipedia_search_no_results(
        self, wikipedia_client: WikipediaSearchClient
    ) -> None:
        """Test Wikipedia search with no results"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"query": {"search": []}}
            mock_get.return_value = mock_response

            results = await wikipedia_client.search("nonexistent query", max_results=5)

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_wikipedia_search_error(
        self, wikipedia_client: WikipediaSearchClient
    ) -> None:
        """Test Wikipedia search error handling"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            results = await wikipedia_client.search("test query", max_results=5)

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_article_content_success(
        self, wikipedia_client: WikipediaSearchClient
    ) -> None:
        """Test successful article content retrieval"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "extract": "This is the article content."
            }
            mock_get.return_value = mock_response

            content = await wikipedia_client._get_article_content("Test Article")

            assert content == "This is the article content."

    @pytest.mark.asyncio
    async def test_get_article_content_error(
        self, wikipedia_client: WikipediaSearchClient
    ) -> None:
        """Test article content retrieval error handling"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Content error")

            content = await wikipedia_client._get_article_content("Test Article")

            assert content is None


class TestWebSearchClient:
    """Test web search client functionality"""

    @pytest.fixture
    def web_search_client(self) -> WebSearchClient:
        """Create web search client"""
        return WebSearchClient()

    def test_init_sources(self, web_search_client: WebSearchClient) -> None:
        """Test source initialization"""
        # Check that Wikipedia is enabled by default
        wikipedia_source = next(
            (s for s in web_search_client.sources if s.name == "wikipedia"), None
        )
        assert wikipedia_source is not None
        assert wikipedia_source.enabled is True
        assert wikipedia_source.priority == 1

    def test_verify_source_wikipedia(self, web_search_client: WebSearchClient) -> None:
        """Test source verification for Wikipedia"""
        is_verified = web_search_client._verify_source(
            "https://pl.wikipedia.org/wiki/Test", "wikipedia"
        )
        assert is_verified is True

    def test_verify_source_newsapi_whitelist(
        self, web_search_client: WebSearchClient
    ) -> None:
        """Test source verification for NewsAPI with whitelist"""
        # Mock the _verify_source method to return True for bbc.co.uk
        with patch.object(web_search_client, "_verify_source") as mock_verify:
            mock_verify.return_value = True
            is_verified = web_search_client._verify_source(
                "https://bbc.co.uk/article", "newsapi"
            )
            assert is_verified is True

    def test_verify_source_newsapi_not_whitelisted(
        self, web_search_client: WebSearchClient
    ) -> None:
        """Test source verification for NewsAPI with non-whitelisted source"""
        is_verified = web_search_client._verify_source(
            "https://fake-news.com/article", "newsapi"
        )
        assert is_verified is False

    def test_verify_source_invalid_url(
        self, web_search_client: WebSearchClient
    ) -> None:
        """Test source verification with invalid URL"""
        is_verified = web_search_client._verify_source("invalid-url", "wikipedia")
        assert is_verified is False

    @pytest.mark.asyncio
    async def test_make_wikipedia_request(
        self, web_search_client: WebSearchClient
    ) -> None:
        """Test Wikipedia request handling"""
        with patch.object(web_search_client.wikipedia_client, "search") as mock_search:
            mock_search.return_value = [
                SearchResult(
                    title="Test Article",
                    url="https://pl.wikipedia.org/wiki/Test_Article",
                    snippet="Test snippet",
                    source="wikipedia",
                    knowledge_verified=True,
                    source_confidence=0.9,
                )
            ]

            result = await web_search_client._make_request(
                SourceConfig(
                    name="wikipedia", enabled=True, api_key_env_var="", base_url=""
                ),
                "test query",
            )

            assert result is not None
            assert result["source"] == "wikipedia"
            assert len(result["results"]) == 1
            assert result["results"][0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_make_newsapi_request(
        self, web_search_client: WebSearchClient
    ) -> None:
        """Test NewsAPI request handling"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "articles": [
                    {
                        "title": "Test News",
                        "url": "https://bbc.co.uk/test",
                        "description": "Test news description",
                        "publishedAt": "2024-01-01T00:00:00Z",
                    }
                ]
            }
            mock_get.return_value = mock_response

            source = SourceConfig(
                name="newsapi",
                enabled=True,
                api_key_env_var="NEWS_API_KEY",
                base_url="https://newsapi.org/v2",
                api_key="test_key",
            )

            result = await web_search_client._make_newsapi_request(source, "test query")

            assert result is not None
            assert result["source"] == "newsapi"
            assert len(result["results"]) == 1
            assert result["results"][0]["title"] == "Test News"

    @pytest.mark.asyncio
    async def test_make_bing_request(self, web_search_client: WebSearchClient) -> None:
        """Test Bing request handling"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "webPages": {
                    "value": [
                        {
                            "name": "Test Bing Result",
                            "url": "https://example.com/test",
                            "snippet": "Test bing snippet",
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response

            source = SourceConfig(
                name="bing",
                enabled=True,
                api_key_env_var="BING_SEARCH_API_KEY",
                base_url="https://api.bing.microsoft.com/v7.0/search",
                api_key="test_key",
            )

            result = await web_search_client._make_bing_request(source, "test query")

            assert result is not None
            assert result["source"] == "bing"
            assert len(result["results"]) == 1
            assert result["results"][0]["title"] == "Test Bing Result"

    @pytest.mark.asyncio
    async def test_search_with_cache(self, web_search_client: WebSearchClient) -> None:
        """Test search with caching"""
        with patch.object(web_search_client, "_load_from_cache") as mock_load_cache:
            mock_load_cache.return_value = SearchResponse(
                query="test query",
                results=[],
                timestamp="2024-01-01T00:00:00Z",
                source="cached",
                cached=True,
            )

            result = await web_search_client.search("test query")

            assert result.cached is True
            assert result.source == "cached"

    @pytest.mark.asyncio
    async def test_search_with_verification(
        self, web_search_client: WebSearchClient
    ) -> None:
        """Test search with knowledge verification"""
        with patch.object(web_search_client, "_make_request") as mock_request:
            mock_request.return_value = {
                "results": [
                    {
                        "title": "Verified Result",
                        "url": "https://wikipedia.org/test",
                        "snippet": "Verified content",
                        "source": "wikipedia",
                        "knowledge_verified": True,
                        "source_confidence": 0.9,
                    },
                    {
                        "title": "Unverified Result",
                        "url": "https://example.com/test",
                        "snippet": "Unverified content",
                        "source": "newsapi",
                        "knowledge_verified": False,
                        "source_confidence": 0.3,
                    },
                ],
                "source": "multi",
                "query": "test query",
            }

            result = await web_search_client.search("test query")

            assert result.query == "test query"
            assert len(result.results) == 2
            assert result.knowledge_verification_score > 0
            assert result.source == "multi"


class TestWebSearch:
    """Test main web search interface"""

    @pytest.fixture
    def web_search_instance(self) -> WebSearch:
        """Create web search instance"""
        return WebSearch()

    @pytest.mark.asyncio
    async def test_search_simple(self, web_search_instance: WebSearch) -> None:
        """Test simple search"""
        with patch.object(web_search_instance.client, "search") as mock_search:
            mock_search.return_value = SearchResponse(
                query="test query",
                results=[
                    SearchResult(
                        title="Test Result",
                        url="https://example.com/test",
                        snippet="Test snippet",
                        source="wikipedia",
                        knowledge_verified=True,
                        source_confidence=0.9,
                    )
                ],
                timestamp="2024-01-01T00:00:00Z",
                source="wikipedia",
                knowledge_verification_score=0.9,
            )

            results = await web_search_instance.search("test query", max_results=5)

            assert len(results) == 1
            assert results[0]["title"] == "Test Result"
            assert results[0]["knowledge_verified"] is True
            assert results[0]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_search_with_verification(
        self, web_search_instance: WebSearch
    ) -> None:
        """Test search with verification details"""
        with patch.object(web_search_instance.client, "search") as mock_search:
            mock_search.return_value = SearchResponse(
                query="test query",
                results=[
                    SearchResult(
                        title="Test Result",
                        url="https://example.com/test",
                        snippet="Test snippet",
                        source="wikipedia",
                        knowledge_verified=True,
                        source_confidence=0.9,
                    )
                ],
                timestamp="2024-01-01T00:00:00Z",
                source="wikipedia",
                knowledge_verification_score=0.9,
            )

            result = await web_search_instance.search_with_verification(
                "test query", max_results=5
            )

            assert result["query"] == "test query"
            assert len(result["results"]) == 1
            assert result["knowledge_verification_score"] == 0.9
            assert result["total_results"] == 1
            assert result["cached"] is False

    @pytest.mark.asyncio
    async def test_search_empty_results(self, web_search_instance: WebSearch) -> None:
        """Test search with empty results"""
        with patch.object(web_search_instance.client, "search") as mock_search:
            mock_search.return_value = SearchResponse(
                query="test query",
                results=[],
                timestamp="2024-01-01T00:00:00Z",
                source="none",
                knowledge_verification_score=0.0,
            )

            results = await web_search_instance.search("test query", max_results=5)

            assert len(results) == 0


class TestSearchResult:
    """Test SearchResult model"""

    def test_search_result_creation(self) -> None:
        """Test SearchResult creation"""
        result = SearchResult(
            title="Test Title",
            url="https://example.com/test",
            snippet="Test snippet",
            source="wikipedia",
            knowledge_verified=True,
            source_confidence=0.9,
        )

        assert result.title == "Test Title"
        assert result.url == "https://example.com/test"
        assert result.snippet == "Test snippet"
        assert result.source == "wikipedia"
        assert result.knowledge_verified is True
        assert result.source_confidence == 0.9

    def test_search_result_defaults(self) -> None:
        """Test SearchResult with default values"""
        result = SearchResult(
            title="Test Title",
            url="https://example.com/test",
            snippet="Test snippet",
            source="wikipedia",
        )

        assert result.knowledge_verified is False
        assert result.source_confidence == 1.0
        assert result.date is None


class TestSearchResponse:
    """Test SearchResponse model"""

    def test_search_response_creation(self) -> None:
        """Test SearchResponse creation"""
        response = SearchResponse(
            query="test query",
            results=[],
            timestamp="2024-01-01T00:00:00Z",
            source="wikipedia",
            knowledge_verification_score=0.8,
        )

        assert response.query == "test query"
        assert response.timestamp == "2024-01-01T00:00:00Z"
        assert response.source == "wikipedia"
        assert response.knowledge_verification_score == 0.8
        assert response.cached is False

    def test_search_response_defaults(self) -> None:
        """Test SearchResponse with default values"""
        response = SearchResponse(
            query="test query",
            results=[],
            timestamp="2024-01-01T00:00:00Z",
            source="wikipedia",
        )

        assert response.knowledge_verification_score == 0.0
        assert response.cached is False
