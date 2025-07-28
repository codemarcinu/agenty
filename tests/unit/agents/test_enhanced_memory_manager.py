"""
Unit tests for enhanced memory management system
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from backend.agents.memory_manager import (
    ContextWindow,
    ConversationSummary,
    MemoryContext,
    MemoryManager,
)


class TestConversationSummary:
    """Test ConversationSummary class"""

    def test_conversation_summary_creation(self):
        """Test creating conversation summary"""
        summary = ConversationSummary(
            key_points=["User likes cooking", "Prefers Italian food"],
            topics_discussed=["cooking", "recipes"],
            user_preferences={"cuisine": "italian"},
            conversation_style="friendly",
        )

        assert summary.key_points == ["User likes cooking", "Prefers Italian food"]
        assert summary.topics_discussed == ["cooking", "recipes"]
        assert summary.user_preferences == {"cuisine": "italian"}
        assert summary.conversation_style == "friendly"
        assert isinstance(summary.created_at, datetime)
        assert isinstance(summary.updated_at, datetime)

    def test_format_for_llm(self):
        """Test formatting summary for LLM"""
        summary = ConversationSummary(
            key_points=["User likes cooking"],
            topics_discussed=["cooking", "recipes"],
            user_preferences={},
            conversation_style="friendly",
        )

        formatted = summary.format_for_llm()
        assert "Wcześniej rozmawialiśmy o: cooking, recipes" in formatted
        assert "Styl rozmowy: friendly" in formatted
        assert "Kluczowe punkty: User likes cooking" in formatted


class TestContextWindow:
    """Test ContextWindow class"""

    def test_context_window_creation(self):
        """Test creating context window"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        window = ContextWindow(recent_messages=messages, summary=None, token_count=50)

        assert window.recent_messages == messages
        assert window.summary is None
        assert window.token_count == 50
        assert isinstance(window.last_optimized, datetime)

    def test_get_optimized_messages_with_summary(self):
        """Test getting optimized messages with summary"""
        messages = [{"role": "user", "content": "Hello"}]
        summary = ConversationSummary(
            key_points=["Previous topic"],
            topics_discussed=["general"],
            user_preferences={},
            conversation_style="friendly",
        )

        window = ContextWindow(
            recent_messages=messages, summary=summary, token_count=100
        )

        optimized = window.get_optimized_messages()
        assert len(optimized) == 2  # Summary + recent message
        assert optimized[0]["role"] == "system"
        assert "Wcześniej rozmawialiśmy o: general" in optimized[0]["content"]
        assert optimized[1] == messages[0]

    def test_get_optimized_messages_without_summary(self):
        """Test getting optimized messages without summary"""
        messages = [{"role": "user", "content": "Hello"}]

        window = ContextWindow(recent_messages=messages, summary=None, token_count=50)

        optimized = window.get_optimized_messages()
        assert optimized == messages


class TestMemoryContext:
    """Test MemoryContext class"""

    def test_memory_context_creation(self):
        """Test creating memory context"""
        context = MemoryContext("test_session_123")

        assert context.session_id == "test_session_123"
        assert context.history == []
        assert context.active_agents == {}
        assert context.last_response is None
        assert context.last_command is None
        assert context.request_id is None
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.last_updated, datetime)
        assert context.conversation_summary is None
        assert context.context_window is None
        assert context.persistent_id is None
        assert context.semantic_hash is None

    def test_add_message(self):
        """Test adding message to context"""
        context = MemoryContext("test_session")
        context.add_message("user", "Hello", {"metadata": "test"})

        assert len(context.history) == 1
        message = context.history[0]
        assert message["role"] == "user"
        assert message["content"] == "Hello"
        assert message["metadata"] == {"metadata": "test"}
        assert "timestamp" in message

    def test_set_last_command(self):
        """Test setting last command"""
        context = MemoryContext("test_session")
        context.set_last_command("test_command")
        assert context.last_command == "test_command"

    def test_estimate_tokens(self):
        """Test token estimation"""
        context = MemoryContext("test_session")
        messages = [
            {"content": "Hello world"},  # ~3 tokens
            {"content": "This is a longer message"},  # ~6 tokens
        ]

        tokens = context._estimate_tokens(messages)
        assert tokens > 0
        assert tokens <= 10  # Rough estimation

    def test_create_conversation_summary(self):
        """Test creating conversation summary"""
        context = MemoryContext("test_session")
        messages = [
            {"role": "user", "content": "I like cooking pasta"},
            {"role": "assistant", "content": "Great! What kind of pasta?"},
            {"role": "user", "content": "I prefer Italian recipes"},
        ]

        summary = context._create_conversation_summary(messages)
        assert isinstance(summary, ConversationSummary)
        assert "cooking" in summary.topics_discussed
        assert summary.conversation_style == "friendly"

    def test_optimize_context_window_short_conversation(self):
        """Test optimizing context window for short conversation"""
        context = MemoryContext("test_session")
        for i in range(5):
            context.add_message("user", f"Message {i}")

        context._optimize_context_window(max_tokens=4000)

        assert context.context_window is not None
        assert len(context.context_window.recent_messages) == 5
        assert context.context_window.summary is None

    def test_optimize_context_window_long_conversation(self):
        """Test optimizing context window for long conversation"""
        context = MemoryContext("test_session")
        for i in range(20):
            context.add_message("user", f"Message {i}")

        context._optimize_context_window(max_tokens=4000)

        assert context.context_window is not None
        assert len(context.context_window.recent_messages) == 10  # Last 10
        assert context.context_window.summary is not None

    def test_get_optimized_context(self):
        """Test getting optimized context"""
        context = MemoryContext("test_session")
        for i in range(15):
            context.add_message("user", f"Message {i}")

        optimized = context.get_optimized_context(max_tokens=4000)

        assert len(optimized) > 0
        # Should include summary and recent messages
        assert any(msg.get("role") == "system" for msg in optimized)


class TestMemoryManager:
    """Test MemoryManager class"""

    @pytest.fixture
    def memory_manager(self):
        """Create memory manager for testing"""
        return MemoryManager(
            max_contexts=10,
            cleanup_threshold_ratio=0.8,
            enable_persistence=False,  # Disable for unit tests
            enable_semantic_cache=True,
        )

    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self, memory_manager):
        """Test memory manager initialization"""
        assert memory_manager._max_contexts == 10
        assert memory_manager._cleanup_threshold == 8
        assert memory_manager._enable_persistence is False
        assert memory_manager._enable_semantic_cache is True
        assert len(memory_manager._contexts) == 0

    @pytest.mark.asyncio
    async def test_store_and_retrieve_context(self, memory_manager):
        """Test storing and retrieving context"""
        context = MemoryContext("test_session")
        await memory_manager.store_context(context)

        retrieved = await memory_manager.retrieve_context("test_session")
        assert retrieved is not None
        assert retrieved.session_id == "test_session"

    @pytest.mark.asyncio
    async def test_get_context_creates_new(self, memory_manager):
        """Test getting context creates new if not exists"""
        context = await memory_manager.get_context("new_session")

        assert context is not None
        assert context.session_id == "new_session"
        assert "new_session" in memory_manager._contexts

    @pytest.mark.asyncio
    async def test_update_context(self, memory_manager):
        """Test updating context"""
        context = await memory_manager.get_context("test_session")
        context.add_message("user", "Hello")

        await memory_manager.update_context(context, {"test": "data"})

        # Verify context was updated
        updated_context = await memory_manager.retrieve_context("test_session")
        assert len(updated_context.history) > 0

    @pytest.mark.asyncio
    async def test_clear_context(self, memory_manager):
        """Test clearing context"""
        await memory_manager.get_context("test_session")
        await memory_manager.clear_context("test_session")

        retrieved = await memory_manager.retrieve_context("test_session")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_cleanup_old_contexts(self, memory_manager):
        """Test cleanup of old contexts"""
        # Create more contexts than max
        for i in range(12):
            context = await memory_manager.get_context(f"session_{i}")
            context.last_updated = datetime.now()

        # Trigger cleanup
        await memory_manager._cleanup_old_contexts()

        # Should have cleaned up old contexts
        assert len(memory_manager._contexts) <= memory_manager._max_contexts

    @pytest.mark.asyncio
    async def test_get_context_stats(self, memory_manager):
        """Test getting context statistics"""
        # Create some contexts and keep references to prevent garbage collection
        contexts = []
        for i in range(3):
            context = await memory_manager.get_context(f"session_{i}")
            contexts.append(context)  # Keep reference to prevent GC

        stats = await memory_manager.get_context_stats()

        assert "total_contexts" in stats
        assert "max_contexts" in stats
        assert "cleanup_threshold" in stats
        assert stats["total_contexts"] == 3

    @pytest.mark.asyncio
    async def test_context_manager(self, memory_manager):
        """Test async context manager"""
        async with memory_manager.context_manager("test_session") as context:
            assert context.session_id == "test_session"
            context.add_message("user", "Test message")

        # Context should be updated after exiting
        retrieved = await memory_manager.retrieve_context("test_session")
        assert len(retrieved.history) == 1

    @pytest.mark.asyncio
    async def test_register_agent_state(self, memory_manager):
        """Test registering agent state"""
        context = await memory_manager.get_context("test_session")
        mock_agent = MagicMock()

        await memory_manager.register_agent_state(
            context, "test_agent", mock_agent, {"state": "active"}
        )

        assert "test_agent" in context.active_agents
        agent_info = context.active_agents["test_agent"]
        assert agent_info["agent"] == mock_agent
        assert agent_info["state"] == {"state": "active"}

    @pytest.mark.asyncio
    async def test_semantic_cache(self, memory_manager):
        """Test semantic cache functionality"""
        # Create context with semantic hash
        context = await memory_manager.get_context("test_session_123")
        context.semantic_hash = "abc123"

        # Store in semantic cache
        memory_manager._semantic_cache["abc123"] = context

        # Find similar context
        found = await memory_manager._find_similar_context("test_session_456")
        assert found is None  # Different session

        found = await memory_manager._find_similar_context("test_session_123")
        assert found is not None  # Same session

    @pytest.mark.asyncio
    async def test_cleanup_all(self, memory_manager):
        """Test cleaning up all contexts"""
        # Create some contexts
        for i in range(3):
            await memory_manager.get_context(f"session_{i}")

        await memory_manager.cleanup_all()

        assert len(memory_manager._contexts) == 0
        assert len(memory_manager._semantic_cache) == 0


class TestIntegration:
    """Integration tests for memory management"""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test full conversation flow with memory management"""
        memory_manager = MemoryManager(
            max_contexts=100, enable_persistence=False, enable_semantic_cache=True
        )

        # Simulate conversation
        session_id = "user_123"

        # First message
        context = await memory_manager.get_context(session_id)
        context.add_message("user", "Hello, I need help with cooking")
        context.add_message(
            "assistant", "I'd be happy to help! What would you like to cook?"
        )
        await memory_manager.update_context(context)

        # Second message
        context = await memory_manager.get_context(session_id)
        context.add_message("user", "I want to make pasta")
        context.add_message(
            "assistant", "Great choice! What kind of pasta do you prefer?"
        )
        await memory_manager.update_context(context)

        # Third message
        context = await memory_manager.get_context(session_id)
        context.add_message("user", "I like Italian pasta")
        context.add_message(
            "assistant", "Perfect! Here's a simple Italian pasta recipe..."
        )
        await memory_manager.update_context(context)

        # Verify context persistence
        retrieved = await memory_manager.retrieve_context(session_id)
        assert len(retrieved.history) == 6  # 3 user + 3 assistant messages

        # Test optimization
        optimized = retrieved.get_optimized_context(max_tokens=2000)
        assert len(optimized) > 0

        # Verify conversation summary was created
        assert retrieved.conversation_summary is not None
        assert "cooking" in retrieved.conversation_summary.topics_discussed

    @pytest.mark.asyncio
    async def test_memory_compression_efficiency(self):
        """Test memory compression efficiency"""
        memory_manager = MemoryManager(
            max_contexts=100, enable_persistence=False, enable_semantic_cache=True
        )

        # Create long conversation
        context = await memory_manager.get_context("long_conversation")

        # Add many messages to trigger compression
        for i in range(50):
            context.add_message(
                "user", f"Message {i} with some content to make it longer"
            )
            context.add_message("assistant", f"Response {i} with detailed explanation")

        # Get optimized context
        optimized = context.get_optimized_context(max_tokens=4000)

        # Verify compression worked
        assert len(optimized) < 100  # Should be compressed
        assert context.conversation_summary is not None

        # Check stats
        stats = await memory_manager.get_context_stats()
        assert stats["compression_ratio"] > 0
        assert stats["compression_ratio"] < 1
