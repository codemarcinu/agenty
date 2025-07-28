"""
Tests for PerplexicaSearchProvider
"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.tools.search_providers import PerplexicaSearchProvider


class TestPerplexicaSearchProvider:
    @pytest.fixture
    def provider(self):
        return PerplexicaSearchProvider()

    def test_weather_query_detection(self, provider):
        """Test weather query detection"""
        # Test weather keywords
        weather_queries = ["pogoda w warszawie", "weather today", "temperatura"]
        for query in weather_queries:
            assert provider._is_weather_query(query) is True

        # Test non-weather queries
        non_weather_queries = ["najlepsze przepisy", "wikipedia", "search"]
        for query in non_weather_queries:
            assert provider._is_weather_query(query) is False

    def test_location_extraction(self, provider):
        """Test location extraction from weather queries"""
        # Test Polish cities - use ASCII versions for consistency
        assert provider._extract_location_from_query("pogoda w warszawie") == "Warszawa"
        assert provider._extract_location_from_query("weather in krakow") == "Krakow"
        assert (
            provider._extract_location_from_query("temperatura w wroclaw") == "Wroclaw"
        )

        # Test default location
        assert provider._extract_location_from_query("pogoda") == "Warszawa"

    def test_validate_result(self, provider):
        """Test result validation"""
        valid_result = {
            "title": "Test",
            "url": "https://example.com",
            "snippet": "Test content",
        }
        assert provider._validate_result(valid_result) is True

        invalid_result = {
            "title": "Test"
            # Missing url and snippet
        }
        assert provider._validate_result(invalid_result) is False

    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.base_url is not None
        assert hasattr(provider, "weather_keywords")
        assert len(provider.weather_keywords) > 0

    @pytest.mark.asyncio
    async def test_search_integration_with_search_agent(self, provider):
        """Test integration with SearchAgent"""
        # This test verifies that the provider can be used with SearchAgent
        from backend.agents.search_agent import SearchAgent

        agent = SearchAgent()
        assert "perplexica" in agent.search_providers
        assert isinstance(
            agent.search_providers["perplexica"], PerplexicaSearchProvider
        )

    @pytest.mark.asyncio
    async def test_weather_query_handling_simple(self, provider):
        """Test weather query handling with simplified mocking"""
        # Test that weather query detection works
        query = "pogoda w warszawie"
        assert provider._is_weather_query(query) is True

        # Test location extraction
        location = provider._extract_location_from_query(query)
        assert location == "Warszawa"

    @pytest.mark.asyncio
    async def test_search_error_handling(self, provider):
        """Test error handling when Perplexica fails"""
        with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("API Error")

            results = await provider.search("test query")

            assert results == []
