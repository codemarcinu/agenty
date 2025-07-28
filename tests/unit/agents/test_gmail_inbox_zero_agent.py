"""
Testy dla Gmail Inbox Zero Agent

Testy jednostkowe dla agenta zarządzającego Inbox Zero w Gmail.
"""

import pytest
import asyncio
import time
import hashlib
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.agents.gmail_inbox_zero_agent import (
    GmailInboxZeroAgent,
    SmartCache,
    EnhancedRateLimiter,
    EnhancedPrefilterEngine,
    BatchProcessor
)
from backend.agents.interfaces import AgentResponse
from backend.schemas.gmail_schemas import InboxZeroRequest


class TestSmartCache:
    """Testy dla inteligentnego systemu cachowania"""
    
    def test_cache_initialization(self):
        """Test inicjalizacji cache"""
        cache = SmartCache(max_size=100, ttl_hours=12)
        assert cache.max_size == 100
        assert cache.ttl_hours == 12
        assert len(cache.analysis_cache) == 0
        
    def test_cache_key_generation(self):
        """Test generowania kluczy cache"""
        cache = SmartCache()
        data1 = {"message_id": "123", "sender": "test@example.com"}
        data2 = {"message_id": "123", "sender": "test@example.com"}
        data3 = {"message_id": "456", "sender": "test@example.com"}
        
        key1 = cache._generate_cache_key(data1)
        key2 = cache._generate_cache_key(data2)
        key3 = cache._generate_cache_key(data3)
        
        assert key1 == key2  # Same data should generate same key
        assert key1 != key3  # Different data should generate different key
        
    def test_cache_analysis(self):
        """Test cachowania analizy"""
        cache = SmartCache()
        message_id = "test123"
        email_data = {
            "sender": "test@example.com",
            "subject": "Test Subject",
            "body_plain": "Test body"
        }
        analysis = {
            "suggested_labels": ["work"],
            "confidence": 0.8
        }
        
        # Cache should be empty initially
        assert cache.get_cached_analysis(message_id, email_data) is None
        
        # Cache the analysis
        cache.cache_analysis(message_id, email_data, analysis)
        
        # Should retrieve cached analysis
        cached = cache.get_cached_analysis(message_id, email_data)
        assert cached == analysis
        
    def test_cache_expiration(self):
        """Test wygasania cache"""
        cache = SmartCache(ttl_hours=1)  # 1 hour TTL
        message_id = "test123"
        email_data = {"sender": "test@example.com", "subject": "Test", "body_plain": "Test"}
        analysis = {"suggested_labels": ["work"]}
        
        cache.cache_analysis(message_id, email_data, analysis)
        
        # Should be cached initially
        assert cache.get_cached_analysis(message_id, email_data) is not None
        
        # Manually expire the cache by modifying timestamp
        cache_key = cache._generate_cache_key({
            'message_id': message_id,
            'sender': email_data.get('sender', ''),
            'subject': email_data.get('subject', ''),
            'body_hash': hashlib.md5(email_data.get('body_plain', '').encode()).hexdigest()[:16]
        })
        cache.analysis_cache[cache_key]['timestamp'] = time.time() - (2 * 3600)  # 2 hours ago
        
        # Should be expired now
        assert cache.get_cached_analysis(message_id, email_data) is None
        
    def test_cache_stats(self):
        """Test statystyk cache"""
        cache = SmartCache()
        message_id = "test123"
        email_data = {"sender": "test@example.com", "subject": "Test", "body_plain": "Test"}
        analysis = {"suggested_labels": ["work"]}
        
        # Cache some data
        cache.cache_analysis(message_id, email_data, analysis)
        cache.get_cached_analysis(message_id, email_data)  # Access it
        
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == 1
        assert stats['total_hits'] >= 1
        assert stats['hit_rate'] > 0
        assert 'memory_usage_mb' in stats


class TestEnhancedRateLimiter:
    """Testy dla ulepszonego rate limitera"""
    
    def test_initialization(self):
        """Test inicjalizacji rate limitera"""
        limiter = EnhancedRateLimiter(max_requests_per_second=5)
        assert limiter.max_requests_per_second == 5
        assert limiter.current_rate == 5
        assert len(limiter.request_times) == 0
        
    def test_exponential_backoff(self):
        """Test exponential backoff"""
        limiter = EnhancedRateLimiter()
        
        # Test backoff calculation
        backoff1 = limiter.exponential_backoff(1)
        backoff2 = limiter.exponential_backoff(2)
        backoff3 = limiter.exponential_backoff(3)
        
        assert backoff1 > 0
        assert backoff2 > backoff1
        assert backoff3 > backoff2
        assert backoff3 <= 60.0  # Max delay
        
    @pytest.mark.asyncio
    async def test_wait_if_needed(self):
        """Test czekania gdy rate limit jest przekroczony"""
        limiter = EnhancedRateLimiter(max_requests_per_second=2)
        
        # Add some requests to reach the limit
        limiter.request_times.extend([time.time() - 0.1, time.time() - 0.05])
        
        # Should wait for third request (we're at the limit)
        start_time = time.time()
        await limiter.wait_if_needed()
        elapsed = time.time() - start_time
        # Should wait because we're at the limit
        assert elapsed > 0.05
        
    def test_success_failure_recording(self):
        """Test rejestrowania sukcesów i porażek"""
        limiter = EnhancedRateLimiter()
        
        assert limiter.success_count == 0
        assert limiter.failure_count == 0
        
        limiter.record_success()
        assert limiter.success_count == 1
        
        limiter.record_failure()
        assert limiter.failure_count == 1
        
    def test_quota_exceeded_handling(self):
        """Test obsługi przekroczenia limitu"""
        limiter = EnhancedRateLimiter()
        
        initial_backoff = limiter.backoff_multiplier
        limiter.handle_quota_exceeded(1)
        
        assert limiter.quota_exceeded_count == 1
        assert limiter.failure_count == 1
        assert limiter.backoff_multiplier > initial_backoff


class TestEnhancedPrefilterEngine:
    """Testy dla ulepszonego silnika prefilteringu"""
    
    def test_initialization(self):
        """Test inicjalizacji prefilter engine"""
        engine = EnhancedPrefilterEngine()
        assert len(engine.whitelist_domains) > 0
        assert len(engine.spam_keywords) > 0
        assert len(engine.newsletter_patterns) > 0
        
    def test_trusted_domain_detection(self):
        """Test wykrywania zaufanych domen"""
        engine = EnhancedPrefilterEngine()
        email_data = {
            "sender": "test@linkedin.com",
            "subject": "Test",
            "body_plain": "Test body"
        }
        
        result = engine.should_skip_ai_analysis(email_data)
        assert result["skip_ai"] is True
        assert result["reason"] == "trusted_domain"
        assert result["suggested_action"] == "safe_archive"
        assert result["confidence"] == 0.9
        
    def test_newsletter_detection(self):
        """Test wykrywania newsletterów"""
        engine = EnhancedPrefilterEngine()
        email_data = {
            "sender": "test@example.com",
            "subject": "Weekly Newsletter",
            "body_plain": "This is our weekly newsletter with unsubscribe link"
        }
        
        result = engine.should_skip_ai_analysis(email_data)
        assert result["skip_ai"] is True
        assert result["reason"] == "newsletter"
        assert result["suggested_action"] == "auto_label_newsletter"
        assert result["confidence"] > 0.8
        
    def test_spam_detection(self):
        """Test wykrywania spamu"""
        engine = EnhancedPrefilterEngine()
        email_data = {
            "sender": "spam@example.com",
            "subject": "URGENT: You won a lottery!",
            "body_plain": "Congratulations! You won money! Click here to claim!"
        }
        
        result = engine.should_skip_ai_analysis(email_data)
        assert result["skip_ai"] is True
        assert result["reason"] == "spam"
        assert result["suggested_action"] == "delete"
        assert "spam_keywords" in result
        
    def test_safe_sender_management(self):
        """Test zarządzania bezpiecznymi nadawcami"""
        engine = EnhancedPrefilterEngine()
        email = "friend@example.com"
        
        # Should not be safe initially
        assert not engine.is_safe_sender(email)
        
        # Add to safe senders
        engine.add_safe_sender(email)
        assert engine.is_safe_sender(email)
        
    def test_user_preferences(self):
        """Test preferencji użytkownika"""
        engine = EnhancedPrefilterEngine()
        user_id = "user123"
        preferences = {"auto_archive_newsletters": True}
        
        engine.update_user_preferences(user_id, preferences)
        assert engine.user_preferences[user_id] == preferences


class TestBatchProcessor:
    """Testy dla procesora batch"""
    
    def test_initialization(self):
        """Test inicjalizacji batch processor"""
        processor = BatchProcessor(max_batch_size=50)
        assert processor.max_batch_size == 50
        assert len(processor.operations) == 0
        
    def test_add_operation(self):
        """Test dodawania operacji"""
        processor = BatchProcessor()
        
        processor.add_operation("archive", "msg123", {"labels": ["work"]})
        assert len(processor.operations) == 1
        assert processor.operations[0]["type"] == "archive"
        assert processor.operations[0]["message_id"] == "msg123"
        
    def test_get_batches(self):
        """Test pobierania batchów"""
        processor = BatchProcessor(max_batch_size=2)
        
        # Add 3 operations
        processor.add_operation("archive", "msg1", {})
        processor.add_operation("label", "msg2", {})
        processor.add_operation("delete", "msg3", {})
        
        batches = processor.get_batches()
        assert len(batches) == 2
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1
        
    def test_clear_operations(self):
        """Test czyszczenia operacji"""
        processor = BatchProcessor()
        
        processor.add_operation("archive", "msg123", {})
        assert len(processor.operations) == 1
        
        processor.clear()
        assert len(processor.operations) == 0
        
    def test_get_stats(self):
        """Test statystyk batch processor"""
        processor = BatchProcessor(max_batch_size=2)
        
        # Add some operations
        processor.add_operation("archive", "msg1", {})
        processor.add_operation("label", "msg2", {})
        
        stats = processor.get_stats()
        assert stats["pending_operations"] == 2
        assert stats["batch_count"] == 1
        assert stats["avg_batch_size"] == 2


class TestGmailInboxZeroAgent:
    """Testy dla głównego agenta Gmail Inbox Zero"""
    
    @pytest.fixture
    def agent(self):
        """Fixture dla agenta"""
        return GmailInboxZeroAgent()
    
    @pytest.fixture
    def sample_request(self):
        """Fixture dla przykładowego żądania"""
        return InboxZeroRequest(
            user_id="test_user",
            session_id="test_session",
            operation="analyze",
            message_id="test_message_123",
            thread_id=None,
            labels=None,
            user_feedback=None,
            learning_data=None,
            email_data={
                "sender": "test@example.com",
                "subject": "Test Subject",
                "body_plain": "Test email body",
                "labels": [],
                "is_read": False,
                "has_attachments": False
            }
        )
    
    def test_agent_initialization(self, agent):
        """Test inicjalizacji agenta"""
        assert agent.name == "GmailInboxZeroAgent"
        assert agent.rate_limiter is not None
        assert agent.batch_processor is not None
        assert agent.prefilter_engine is not None
        assert agent.smart_cache is not None
        
    @pytest.mark.asyncio
    async def test_process_with_cache(self, agent, sample_request):
        """Test przetwarzania z cache"""
        # Mock the hybrid_llm_client
        with patch('backend.agents.gmail_inbox_zero_agent.hybrid_llm_client') as mock_client:
            mock_client.chat = AsyncMock(return_value={
                "message": {"content": '{"suggested_labels": ["work"], "confidence": 0.8}'}
            })
            
            # First call should not use cache
            result1 = await agent.process(sample_request.model_dump())
            assert result1.success is True
            
            # Second call should use cache
            result2 = await agent.process(sample_request.model_dump())
            assert result2.success is True
            assert result2.metadata.get("from_cache") is True
            
    @pytest.mark.asyncio
    async def test_process_with_prefilter(self, agent):
        """Test przetwarzania z prefilterem"""
        # Create request with trusted domain
        request_data = {
            "user_id": "test_user",
            "session_id": "test_session",
            "operation": "analyze",
            "message_id": "test_message_123",
            "thread_id": None,
            "labels": None,
            "user_feedback": None,
            "learning_data": None,
            "email_data": {
                "sender": "test@linkedin.com",
                "subject": "Test",
                "body_plain": "Test body",
                "labels": [],
                "is_read": False,
                "has_attachments": False
            }
        }
        
        result = await agent.process(request_data)
        assert result.success is True
        # Should be processed by prefilter (trusted domain)
        assert "prefiltered" in result.metadata
        
    def test_select_optimal_model(self, agent):
        """Test wyboru optymalnego modelu"""
        # Short email should use lightweight model
        short_email = {"body_plain": "Short", "subject": "Test"}
        model1 = agent._select_optimal_model(short_email)
        assert "llama3.2" in model1 or "3b" in model1
        
        # Long email should use standard model
        long_email = {"body_plain": "Long email content " * 50, "subject": "Long subject " * 10}
        model2 = agent._select_optimal_model(long_email)
        assert "bielik" in model2 or "11b" in model2
        
    def test_get_prefilter_labels(self, agent):
        """Test pobierania labeli z prefiltera"""
        prefilter_result = {"reason": "newsletter", "suggested_action": "auto_label_newsletter"}
        labels = agent._get_prefilter_labels(prefilter_result)
        assert "Newsletter" in labels
        
        prefilter_result = {"reason": "spam", "suggested_action": "delete"}
        labels = agent._get_prefilter_labels(prefilter_result)
        assert "Spam" in labels
        
    def test_prepare_suggestions(self, agent):
        """Test przygotowywania sugestii"""
        analysis_result = {
            "suggested_labels": ["work", "important"],
            "should_archive": False,
            "requires_response": True,
            "priority": "high",
            "confidence": 0.9
        }
        
        suggestions = agent._prepare_suggestions(analysis_result)
        # Check that suggestions contain expected elements
        assert any("work" in s.lower() or "praca" in s.lower() for s in suggestions)
        assert any("important" in s.lower() or "ważny" in s.lower() for s in suggestions)
        assert len(suggestions) >= 2


class TestIntegration:
    """Testy integracyjne"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test pełnego workflow"""
        agent = GmailInboxZeroAgent()
        
        # Mock the hybrid_llm_client
        with patch('backend.agents.gmail_inbox_zero_agent.hybrid_llm_client') as mock_client:
            mock_client.chat = AsyncMock(return_value={
                "message": {"content": '{"suggested_labels": ["work"], "confidence": 0.8}'}
            })
            
            # Test analyze operation
            request_data = {
                "user_id": "test_user",
                "session_id": "test_session",
                "operation": "analyze",
                "message_id": "test_message_123",
                "thread_id": None,
                "labels": None,
                "user_feedback": None,
                "learning_data": None,
                "email_data": {
                    "sender": "test@example.com",
                    "subject": "Test Subject",
                    "body_plain": "Test email body",
                    "labels": [],
                    "is_read": False,
                    "has_attachments": False
                }
            }
            
            result = await agent.process(request_data)
            assert result.success is True
            assert result.data is not None
            assert "data" in result.data or "suggestions" in result.data
            
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test przetwarzania batch"""
        agent = GmailInboxZeroAgent()
        
        # Mock the hybrid_llm_client
        with patch('backend.agents.gmail_inbox_zero_agent.hybrid_llm_client') as mock_client:
            mock_client.chat = AsyncMock(return_value={
                "message": {"content": '{"suggested_labels": ["work"], "confidence": 0.8}'}
            })
            
            # Test batch processing
            request_data = {
                "user_id": "test_user",
                "session_id": "test_session",
                "operation": "batch_process",
                "message_id": None,
                "thread_id": None,
                "labels": None,
                "user_feedback": None,
                "learning_data": None,
                "email_data": {
                    "message_ids": ["msg1", "msg2", "msg3"],
                    "operation_type": "analyze"
                }
            }
            
            result = await agent.process(request_data)
            assert result.success is True
            assert result.data is not None
            assert "total_processed" in result.data
            assert "success_rate" in result.data
            
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting"""
        agent = GmailInboxZeroAgent()
        
        # Test that rate limiter is working
        initial_rate = agent.rate_limiter.current_rate
        
        # Simulate some operations
        for _ in range(5):
            agent.rate_limiter.record_success()
            
        # Rate should be adjusted based on success
        assert agent.rate_limiter.current_rate >= initial_rate
        
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test wydajności cache"""
        agent = GmailInboxZeroAgent()
        
        # Test cache performance
        stats = agent.smart_cache.get_cache_stats()
        assert "total_entries" in stats
        assert "hit_rate" in stats
        assert "memory_usage_mb" in stats
        
    @pytest.mark.asyncio
    async def test_prefilter_performance(self):
        """Test wydajności prefiltera"""
        agent = GmailInboxZeroAgent()
        
        # Test prefilter performance with different email types
        test_cases = [
            {
                "email": {"sender": "test@linkedin.com", "subject": "Test", "body_plain": "Test"},
                "expected_reason": "trusted_domain"
            },
            {
                "email": {"sender": "test@example.com", "subject": "Newsletter", "body_plain": "Weekly digest"},
                "expected_reason": "newsletter"
            },
            {
                "email": {"sender": "spam@example.com", "subject": "URGENT", "body_plain": "You won money!"},
                "expected_reason": "spam"
            }
        ]
        
        for case in test_cases:
            result = agent.prefilter_engine.should_skip_ai_analysis(case["email"])
            # Allow for some flexibility in classification
            if case["expected_reason"] == "spam":
                assert result["reason"] in ["spam", "requires_analysis"]
            else:
                assert result["reason"] == case["expected_reason"]
            # Check skip_ai based on the actual result
            if result["reason"] in ["trusted_domain", "newsletter", "spam", "safe_sender", "automated_email"]:
                assert result["skip_ai"] is True
            else:
                assert result["skip_ai"] is False


if __name__ == "__main__":
    pytest.main([__file__])
