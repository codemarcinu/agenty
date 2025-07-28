from __future__ import annotations

"""
Tests for updated Agent Factory with new agent types

Tests the enhanced agent factory that supports:
- GeneralConversationAgent
- Updated agent creation with model selection
"""

from unittest.mock import Mock

import pytest

from agents.agent_factory import (
    AgentConfig,
    AgentFactory,
    AnalyticsAgent,
    CategorizationAgent,
    ChefAgent,
    EnhancedOCRAgent,
    GeneralConversationAgent,
    MealPlannerAgent,
    PromoScrapingAgent,
    RAGAgent,
    SearchAgent,
    WeatherAgent,
)
from agents.agent_registry import AgentRegistry
from agents.base_agent import BaseAgent


class TestAgentFactoryNew:
    """Test cases for the new AgentFactory implementation"""

    @pytest.fixture
    def agent_factory(self):
        """Create a fresh AgentFactory instance for each test"""
        return AgentFactory()

    @pytest.fixture
    def agent_registry(self):
        """Create a fresh AgentRegistry instance for each test"""
        return AgentRegistry()

    def test_agent_factory_initialization(self, agent_factory):
        """Test that AgentFactory initializes correctly"""
        assert agent_factory is not None
        assert hasattr(agent_factory, "AGENT_REGISTRY")
        assert isinstance(agent_factory.AGENT_REGISTRY, dict)

    def test_agent_registry_contains_expected_agents(self, agent_factory):
        """Test that all expected agent types are registered"""
        expected_agents = [
            "general_conversation",
            "cooking",
            "Chef",
            "search",
            "Search",
            "weather",
            "Weather",
            "rag",
            "RAG",
            "categorization",
            "Categorization",
            "meal_planning",
            "MealPlanner",
            "ocr",
            "OCR",
            "receipt_analysis",
            "ReceiptAnalysis",
            "analytics",
            "Analytics",
            "promo_scraping",
            "PromoScraping",
            "default",
        ]

        for agent_type in expected_agents:
            assert (
                agent_type in agent_factory.AGENT_REGISTRY
            ), f"Agent type '{agent_type}' not found in registry"

    def test_create_general_conversation_agent(self, agent_factory):
        """Test creating a GeneralConversationAgent"""
        agent = agent_factory.create_agent("general_conversation")
        assert isinstance(agent, GeneralConversationAgent)

    def test_create_chef_agent(self, agent_factory):
        """Test creating a ChefAgent"""
        agent = agent_factory.create_agent("cooking")
        assert isinstance(agent, ChefAgent)

    def test_create_search_agent(self, agent_factory):
        """Test creating a SearchAgent"""
        agent = agent_factory.create_agent("search")
        assert isinstance(agent, SearchAgent)

    def test_create_weather_agent(self, agent_factory):
        """Test creating a WeatherAgent"""
        agent = agent_factory.create_agent("weather")
        assert isinstance(agent, WeatherAgent)

    def test_create_rag_agent(self, agent_factory):
        """Test creating a RAGAgent"""
        agent = agent_factory.create_agent("rag")
        assert isinstance(agent, RAGAgent)

    def test_create_ocr_agent(self, agent_factory):
        """Test creating an EnhancedOCRAgent"""
        agent = agent_factory.create_agent("ocr")
        assert isinstance(agent, EnhancedOCRAgent)

    def test_create_categorization_agent(self, agent_factory):
        """Test creating a CategorizationAgent"""
        agent = agent_factory.create_agent("categorization")
        assert isinstance(agent, CategorizationAgent)

    def test_create_meal_planner_agent(self, agent_factory):
        """Test creating a MealPlannerAgent"""
        agent = agent_factory.create_agent("meal_planning")
        assert isinstance(agent, MealPlannerAgent)

    def test_create_analytics_agent(self, agent_factory):
        """Test creating an AnalyticsAgent"""
        agent = agent_factory.create_agent("analytics")
        assert isinstance(agent, AnalyticsAgent)

    def test_create_promo_scraping_agent(self, agent_factory):
        """Test creating a PromoScrapingAgent"""
        agent = agent_factory.create_agent("promo_scraping")
        assert isinstance(agent, PromoScrapingAgent)

    def test_create_agent_with_alias(self, agent_factory):
        """Test creating agents using aliases (capitalized names)"""
        # Test Chef alias
        chef_agent = agent_factory.create_agent("Chef")
        assert isinstance(chef_agent, ChefAgent)

        # Test Search alias
        search_agent = agent_factory.create_agent("Search")
        assert isinstance(search_agent, SearchAgent)

        # Test Weather alias
        weather_agent = agent_factory.create_agent("Weather")
        assert isinstance(weather_agent, WeatherAgent)

    def test_create_agent_with_fallback(self, agent_factory):
        """Test that unknown agent types fall back to default"""
        agent = agent_factory.create_agent("unknown_agent_type")
        assert isinstance(agent, GeneralConversationAgent)  # Default fallback

    def test_create_agent_with_config(self, agent_factory):
        """Test creating an agent with configuration"""
        config = {"model": "test-model", "temperature": 0.7}
        agent = agent_factory.create_agent("general_conversation", config=config)
        assert isinstance(agent, GeneralConversationAgent)

    def test_create_agent_with_kwargs(self, agent_factory):
        """Test creating an agent with additional keyword arguments"""
        agent = agent_factory.create_agent(
            "general_conversation",
            name="TestAgent",
            error_handler=Mock(),
            fallback_manager=Mock(),
        )
        assert isinstance(agent, GeneralConversationAgent)
        assert agent.name == "TestAgent"

    def test_agent_caching(self, agent_factory):
        """Test that agents are cached when use_cache=True"""
        # Create first agent
        agent1 = agent_factory.create_agent("general_conversation", use_cache=True)
        # Create second agent with same type
        agent2 = agent_factory.create_agent("general_conversation", use_cache=True)

        # Should be the same instance due to caching
        assert agent1 is agent2

    def test_agent_no_caching(self, agent_factory):
        """Test that agents are not cached when use_cache=False"""
        # Create first agent
        agent1 = agent_factory.create_agent("general_conversation", use_cache=False)
        # Create second agent with same type
        agent2 = agent_factory.create_agent("general_conversation", use_cache=False)

        # Should be different instances due to no caching
        assert agent1 is not agent2

    def test_agent_registry_integration(self, agent_factory, agent_registry):
        """Test integration with AgentRegistry"""

        # Register a custom agent class
        class CustomAgent(BaseAgent):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.custom_property = "test"

        agent_registry.register_agent_class("Custom", CustomAgent)

        # Create agent factory with custom registry
        custom_factory = AgentFactory(agent_registry=agent_registry)

        # Test creating custom agent
        agent = custom_factory.create_agent("Custom")
        assert isinstance(agent, CustomAgent)
        assert agent.custom_property == "test"

    def test_get_available_agents(self, agent_factory):
        """Test getting list of available agents"""
        available_agents = agent_factory.get_available_agents()
        assert isinstance(available_agents, dict)
        assert len(available_agents) > 0

        # Check that all registered agents are in the list
        for agent_type in agent_factory.AGENT_REGISTRY:
            assert agent_type in available_agents

    def test_cleanup(self, agent_factory):
        """Test agent factory cleanup"""
        # Create some agents to populate cache
        agent_factory.create_agent("general_conversation", use_cache=True)
        agent_factory.create_agent("cooking", use_cache=True)

        # Verify cache has entries
        assert len(agent_factory._agent_cache) > 0

        # Cleanup
        agent_factory.cleanup()

        # Verify cache is cleared
        assert len(agent_factory._agent_cache) == 0

    def test_reset(self, agent_factory):
        """Test agent factory reset"""
        # Create some agents to populate cache
        agent_factory.create_agent("general_conversation", use_cache=True)

        # Reset
        agent_factory.reset()

        # Verify cache is cleared
        assert len(agent_factory._agent_cache) == 0

    def test_thread_safety(self, agent_factory):
        """Test that agent factory is thread-safe"""
        import threading
        import time

        def create_agents():
            for i in range(10):
                agent_factory.create_agent(
                    "general_conversation", use_cache=True
                )
                time.sleep(0.01)  # Small delay to increase chance of race conditions

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_agents)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should not raise any exceptions due to thread safety

    def test_agent_config_model(self, agent_factory):
        """Test AgentConfig model"""
        config = AgentConfig(
            agent_type="test_agent",
            dependencies={"llm": "llm_client"},
            settings={"temperature": 0.7},
            cache_enabled=True,
        )

        assert config.agent_type == "test_agent"
        assert config.dependencies == {"llm": "llm_client"}
        assert config.settings == {"temperature": 0.7}
        assert config.cache_enabled is True

    def test_error_handling(self, agent_factory):
        """Test error handling in agent creation"""
        # Test with invalid agent type (should fall back to default)
        agent = agent_factory.create_agent("invalid_type")
        assert isinstance(agent, GeneralConversationAgent)  # Default fallback

    def test_agent_factory_with_container(self, agent_factory):
        """Test AgentFactory with container dependency injection"""
        from agents.agent_container import AgentContainer

        container = AgentContainer()
        factory_with_container = AgentFactory(container=container)

        # Should still work normally
        agent = factory_with_container.create_agent("general_conversation")
        assert isinstance(agent, GeneralConversationAgent)
