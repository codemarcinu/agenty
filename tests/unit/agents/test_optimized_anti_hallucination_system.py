"""
Tests for optimized anti-hallucination system
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from backend.core.anti_hallucination_system_optimized import (
    OptimizedAntiHallucinationSystem,
    OptimizedValidationCache,
)
from backend.core.anti_hallucination_system import ValidationLevel, HallucinationType
from backend.core.agent_specific_config import get_agent_config


class TestOptimizedValidationCache:
    """Test OptimizedValidationCache functionality"""

    @pytest.fixture
    def cache(self):
        return OptimizedValidationCache(max_size=10, default_ttl_minutes=30)

    def test_generate_key(self, cache):
        """Test cache key generation"""
        response = "Test response"
        context = "Test context"
        agent_name = "TestAgent"
        
        key1 = cache._generate_key(response, context, agent_name)
        key2 = cache._generate_key(response, context, agent_name)
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length

    def test_set_and_get(self, cache):
        """Test setting and getting cache entries"""
        response = "Test response"
        context = "Test context"
        agent_name = "TestAgent"
        
        # Mock validation result
        mock_result = MagicMock()
        mock_result.confidence = 0.8
        mock_result.hallucination_score = 0.2
        
        # Set cache entry
        cache.set(response, context, agent_name, mock_result)
        
        # Get cache entry
        cached_result = cache.get(response, context, agent_name)
        
        assert cached_result is not None
        assert cached_result.confidence == 0.8
        assert cached_result.hallucination_score == 0.2

    def test_cache_expiration(self, cache):
        """Test cache entry expiration"""
        response = "Test response"
        context = "Test context"
        agent_name = "TestAgent"
        
        # Mock validation result
        mock_result = MagicMock()
        
        # Set cache entry with short TTL
        cache.set(response, context, agent_name, mock_result, ttl_minutes=0)
        
        # Try to get expired entry
        cached_result = cache.get(response, context, agent_name)
        
        assert cached_result is None

    def test_cache_size_limit(self, cache):
        """Test cache size limit enforcement"""
        # Add more entries than max_size
        for i in range(15):
            response = f"Response {i}"
            context = f"Context {i}"
            agent_name = f"Agent{i}"
            
            mock_result = MagicMock()
            cache.set(response, context, agent_name, mock_result)
        
        # Check that cache size doesn't exceed max_size
        assert len(cache.cache) <= 10


class TestOptimizedAntiHallucinationSystem:
    """Test OptimizedAntiHallucinationSystem functionality"""

    @pytest.fixture
    def system(self):
        return OptimizedAntiHallucinationSystem()

    @pytest.mark.asyncio
    async def test_validate_response_chef_agent(self, system):
        """Test validation for chef agent"""
        response = "Dodaj 300g makaronu i 2 pomidory"
        context = "Przepis na spaghetti"
        agent_name = "ChefAgent"
        
        result = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="bielik-11b",
            available_ingredients=["makaron", "pomidory", "cebula"],
            agent_type="chef"
        )
        
        assert result is not None
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'hallucination_score')
        assert result.agent_name == "ChefAgent"

    @pytest.mark.asyncio
    async def test_validate_response_receipt_agent(self, system):
        """Test validation for receipt analysis agent"""
        response = "Paragon z 15.01.2024, kwota 45.67 zł"
        context = "Analiza paragonu"
        agent_name = "ReceiptAnalysisAgent"
        
        result = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="bielik-11b",
            agent_type="receipt_analysis"
        )
        
        assert result is not None
        assert result.agent_name == "ReceiptAnalysisAgent"

    @pytest.mark.asyncio
    async def test_validate_response_weather_agent(self, system):
        """Test validation for weather agent"""
        response = "Temperatura 22°C, wilgotność 65%"
        context = "Pogoda w Warszawie"
        agent_name = "WeatherAgent"
        
        result = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="bielik-11b",
            agent_type="weather"
        )
        
        assert result is not None
        assert result.agent_name == "WeatherAgent"

    @pytest.mark.asyncio
    async def test_validate_response_search_agent(self, system):
        """Test validation for search agent"""
        response = "Według źródeł z 2024 roku..."
        context = "Wyszukiwanie informacji"
        agent_name = "SearchAgent"
        
        result = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="bielik-11b",
            agent_type="search"
        )
        
        assert result is not None
        assert result.agent_name == "SearchAgent"

    @pytest.mark.asyncio
    async def test_cache_hit(self, system):
        """Test cache hit scenario"""
        response = "Test response"
        context = "Test context"
        agent_name = "TestAgent"
        
        # First validation (cache miss)
        result1 = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="test-model"
        )
        
        # Second validation (cache hit)
        result2 = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="test-model"
        )
        
        assert result1.confidence == result2.confidence
        assert result1.hallucination_score == result2.hallucination_score

    @pytest.mark.asyncio
    async def test_agent_type_detection(self, system):
        """Test automatic agent type detection"""
        # Test chef agent detection
        result = await system.validate_response(
            response="Test response",
            context="Test context",
            agent_name="ChefAgent",
            model_used="test-model"
        )
        
        assert result.agent_name == "ChefAgent"

    @pytest.mark.asyncio
    async def test_validation_level_override(self, system):
        """Test validation level override"""
        response = "Test response"
        context = "Test context"
        agent_name = "ChefAgent"
        
        # Use LENIENT instead of default STRICT for chef
        result = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="test-model",
            validation_level=ValidationLevel.LENIENT,
            agent_type="chef"
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, system):
        """Test error handling in validation"""
        response = "Test response"
        context = "Test context"
        agent_name = "TestAgent"
        
        # Mock validator to raise exception
        with patch.object(system.validator_factory, 'get_validator') as mock_get_validator:
            mock_validator = AsyncMock()
            mock_validator.validate.side_effect = Exception("Validation error")
            mock_get_validator.return_value = mock_validator
            
            result = await system.validate_response(
                response=response,
                context=context,
                agent_name=agent_name,
                model_used="test-model"
            )
            
            # Should return fallback result
            assert result.is_valid is False
            assert result.confidence == 0.0
            assert result.hallucination_score == 1.0

    def test_detect_agent_type(self, system):
        """Test agent type detection"""
        # Test various agent name patterns
        test_cases = [
            ("ChefAgent", "chef"),
            ("ReceiptAnalysisAgent", "receipt_analysis"),
            ("WeatherAgent", "weather"),
            ("SearchAgent", "search"),
            ("UnknownAgent", "general_conversation"),
        ]
        
        for agent_name, expected_type in test_cases:
            detected_type = system._detect_agent_type(agent_name)
            assert detected_type == expected_type

    def test_apply_agent_thresholds(self, system):
        """Test agent-specific threshold application"""
        from backend.core.anti_hallucination_system import ValidationResult
        
        # Create mock validation result
        mock_result = ValidationResult(
            is_valid=True,
            confidence=0.9,
            hallucination_score=0.1,
            detected_hallucinations=[],
            suspicious_phrases=[],
            validation_errors=[],
            recommendation="Test",
            timestamp=datetime.now(),
            agent_name="TestAgent",
            model_used="test-model"
        )
        
        # Get chef config
        chef_config = get_agent_config("chef")
        
        # Apply thresholds
        updated_result = system._apply_agent_thresholds(mock_result, chef_config)
        
        assert updated_result.is_valid is True  # Should still be valid with high confidence
        assert updated_result.confidence == 0.9
        assert updated_result.hallucination_score == 0.1

    def test_get_metrics(self, system):
        """Test metrics collection"""
        metrics = system.get_metrics()
        
        assert "total_validations" in metrics
        assert "cache_hits" in metrics
        assert "cache_misses" in metrics
        assert "validation_times" in metrics
        assert "agent_metrics" in metrics

    def test_clear_cache(self, system):
        """Test cache clearing"""
        # Add some entries to cache
        system.cache.set("test", "context", "agent", MagicMock())
        
        # Clear cache
        system.clear_cache()
        
        # Check that cache is empty
        assert len(system.cache.cache) == 0

    def test_get_cache_stats(self, system):
        """Test cache statistics"""
        stats = system.get_cache_stats()
        
        assert "cache_size" in stats
        assert "max_size" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats


class TestAgentSpecificConfig:
    """Test agent-specific configuration functionality"""

    def test_get_chef_config(self):
        """Test getting chef agent configuration"""
        config = get_agent_config("chef")
        
        assert config.validation_level == ValidationLevel.STRICT
        assert config.confidence_threshold == 0.7
        assert config.hallucination_threshold == 0.3
        assert "ingredient" in config.enabled_patterns
        assert "measurement" in config.enabled_patterns

    def test_get_receipt_config(self):
        """Test getting receipt analysis configuration"""
        config = get_agent_config("receipt_analysis")
        
        assert config.validation_level == ValidationLevel.STRICT
        assert config.confidence_threshold == 0.8
        assert config.hallucination_threshold == 0.2
        assert "factual" in config.enabled_patterns
        assert "price" in config.enabled_patterns

    def test_get_weather_config(self):
        """Test getting weather agent configuration"""
        config = get_agent_config("weather")
        
        assert config.validation_level == ValidationLevel.LENIENT
        assert config.confidence_threshold == 0.5
        assert config.hallucination_threshold == 0.4
        assert "measurement" in config.enabled_patterns

    def test_get_search_config(self):
        """Test getting search agent configuration"""
        config = get_agent_config("search")
        
        assert config.validation_level == ValidationLevel.MODERATE
        assert config.confidence_threshold == 0.7
        assert config.hallucination_threshold == 0.3
        assert "factual" in config.enabled_patterns
        assert "unverifiable" in config.enabled_patterns

    def test_get_unknown_agent_config(self):
        """Test getting configuration for unknown agent type"""
        config = get_agent_config("unknown_agent")
        
        # Should return default configuration
        assert config.validation_level == ValidationLevel.MODERATE
        assert config.confidence_threshold == 0.6
        assert config.hallucination_threshold == 0.4


class TestPerformanceOptimizations:
    """Test performance optimizations"""

    @pytest.mark.asyncio
    async def test_parallel_validation(self):
        """Test that validations can run in parallel"""
        import asyncio
        
        system = OptimizedAntiHallucinationSystem()
        
        # Create multiple validation tasks
        tasks = []
        for i in range(5):
            task = system.validate_response(
                response=f"Test response {i}",
                context=f"Test context {i}",
                agent_name=f"TestAgent{i}",
                model_used="test-model"
            )
            tasks.append(task)
        
        # Run all validations in parallel
        start_time = datetime.now()
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        # All validations should complete
        assert len(results) == 5
        for result in results:
            assert result is not None
        
        # Should complete quickly (parallel execution)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test cache performance benefits"""
        system = OptimizedAntiHallucinationSystem()
        
        response = "Test response for caching"
        context = "Test context"
        agent_name = "TestAgent"
        
        # First call (cache miss)
        start_time = datetime.now()
        result1 = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="test-model"
        )
        first_call_time = (datetime.now() - start_time).total_seconds()
        
        # Second call (cache hit)
        start_time = datetime.now()
        result2 = await system.validate_response(
            response=response,
            context=context,
            agent_name=agent_name,
            model_used="test-model"
        )
        second_call_time = (datetime.now() - start_time).total_seconds()
        
        # Cache hit should be faster
        assert second_call_time < first_call_time
        assert result1.confidence == result2.confidence

    def test_agent_specific_ttl(self):
        """Test agent-specific TTL configuration"""
        from backend.core.agent_specific_config import get_agent_config
        
        # Chef agent has longer TTL
        chef_config = get_agent_config("chef")
        chef_ttl = chef_config.timeout_seconds / 60  # Convert to minutes
        assert chef_ttl == 15.0  # 15 minutes
        
        # Weather agent has shorter TTL
        weather_config = get_agent_config("weather")
        weather_ttl = weather_config.timeout_seconds / 60
        assert weather_ttl == 8.0  # 8 minutes


class TestIntegration:
    """Integration tests for the optimized system"""

    @pytest.mark.asyncio
    async def test_full_validation_workflow(self):
        """Test complete validation workflow"""
        system = OptimizedAntiHallucinationSystem()
        
        # Test chef agent with ingredients
        chef_result = await system.validate_response(
            response="Dodaj 300g makaronu i 2 pomidory",
            context="Przepis na spaghetti",
            agent_name="ChefAgent",
            model_used="bielik-11b",
            available_ingredients=["makaron", "pomidory", "cebula"],
            agent_type="chef"
        )
        
        assert chef_result is not None
        assert chef_result.agent_name == "ChefAgent"
        
        # Test receipt analysis
        receipt_result = await system.validate_response(
            response="Paragon z 15.01.2024, kwota 45.67 zł",
            context="Analiza paragonu",
            agent_name="ReceiptAnalysisAgent",
            model_used="bielik-11b",
            agent_type="receipt_analysis"
        )
        
        assert receipt_result is not None
        assert receipt_result.agent_name == "ReceiptAnalysisAgent"
        
        # Check metrics
        metrics = system.get_metrics()
        assert metrics["total_validations"] >= 2
        assert "ChefAgent" in metrics["agent_metrics"]
        assert "ReceiptAnalysisAgent" in metrics["agent_metrics"]

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test system recovery from validation errors"""
        system = OptimizedAntiHallucinationSystem()
        
        # This should not crash the system
        result = await system.validate_response(
            response="Test response",
            context="Test context",
            agent_name="TestAgent",
            model_used="test-model",
            agent_type="invalid_agent_type"
        )
        
        # Should return fallback result
        assert result is not None
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'hallucination_score') 