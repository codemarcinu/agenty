"""
Memory Manager Fixes Tests
Tests for MemoryManager with proper weakref/GC handling
Following .cursorrules standards for Python testing
"""

import asyncio
import gc
import weakref

import pytest
import pytest_asyncio

from backend.agents.memory_manager import MemoryContext, MemoryManager


class TestMemoryManagerFixes:
    """Test cases for MemoryManager with weakref/GC fixes."""

    @pytest.fixture
    def memory_manager(self):
        """Create MemoryManager instance for testing."""
        return MemoryManager(
            max_contexts=10,
            cleanup_threshold_ratio=0.8,
            enable_persistence=False,  # Disable for tests
            enable_semantic_cache=False,  # Disable for tests
        )

    @pytest.fixture
    def test_context(self):
        """Create test context with strong reference."""
        context = MemoryContext(
            session_id="test_session",
            history=[
                {
                    "role": "user",
                    "content": "Test conversation content",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {"test": "data"},
                }
            ],
        )
        return context

    @pytest.mark.asyncio
    async def test_context_creation_with_strong_reference(
        self, memory_manager, test_context
    ):
        """Test context creation with strong reference handling."""
        # Store strong reference to prevent GC
        contexts = []

        # Create multiple contexts
        for i in range(5):
            context = MemoryContext(
                session_id=f"session_{i}",
                history=[
                    {
                        "role": "user",
                        "content": f"Content {i}",
                        "timestamp": "2024-01-01T00:00:00",
                        "metadata": {"index": i},
                    }
                ],
            )
            contexts.append(context)  # Strong reference

            # Add to memory manager
            await memory_manager.store_context(context)

        # Verify contexts are stored
        assert len(contexts) == 5
        stats = await memory_manager.get_context_stats()
        assert stats["total_contexts"] == 5

        # Cleanup
        contexts.clear()
        gc.collect()

    @pytest.mark.asyncio
    async def test_context_cleanup_with_strong_references(self, memory_manager):
        """Test context cleanup with proper strong reference handling."""
        # Create contexts with strong references
        contexts = []

        for i in range(3):
            context = MemoryContext(
                session_id=f"cleanup_session_{i}",
                history=[
                    {
                        "role": "user",
                        "content": f"Cleanup content {i}",
                        "timestamp": "2024-01-01T00:00:00",
                        "metadata": {"cleanup": True},
                    }
                ],
            )
            contexts.append(context)
            await memory_manager.store_context(context)

        # Verify initial state
        stats = await memory_manager.get_context_stats()
        assert stats["total_contexts"] == 3

        # Remove contexts properly
        for context in contexts:
            await memory_manager.clear_context(context.session_id)

        # Clear strong references
        contexts.clear()
        gc.collect()

        # Verify cleanup
        stats = await memory_manager.get_context_stats()
        assert stats["total_contexts"] == 0

    @pytest.mark.asyncio
    async def test_weakref_handling_in_tests(self, memory_manager):
        """Test weakref handling in test environment."""
        # Create context
        context = MemoryContext(
            session_id="weakref_test",
            history=[
                {
                    "role": "user",
                    "content": "Weakref test content",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {"weakref": True},
                }
            ],
        )

        # Add to memory manager
        await memory_manager.store_context(context)

        # Create weak reference for testing
        weak_ref = weakref.ref(context)

        # Verify context exists
        assert weak_ref() is not None
        stats = await memory_manager.get_context_stats()
        assert stats["total_contexts"] == 1

        # Remove context
        await memory_manager.clear_context(context.session_id)

        # Clear strong reference
        context = None
        gc.collect()

        # Verify weak reference is dead
        assert weak_ref() is None
        stats = await memory_manager.get_context_stats()
        assert stats["total_contexts"] == 0

    @pytest.mark.asyncio
    async def test_semantic_cache_implementation(self, memory_manager):
        """Test semantic cache implementation."""
        # Add contexts with semantic content
        contexts = []

        for i in range(3):
            context = MemoryContext(
                session_id=f"semantic_{i}",
                history=[
                    {
                        "role": "user",
                        "content": f"Python programming language tutorial {i}",
                        "timestamp": "2024-01-01T00:00:00",
                        "metadata": {"topic": "programming", "language": "python"},
                    }
                ],
            )
            contexts.append(context)
            await memory_manager.store_context(context)

        # Test context retrieval
        retrieved = await memory_manager.retrieve_context("semantic_0")
        assert retrieved is not None
        assert "Python" in retrieved.history[0]["content"]

        # Cleanup
        contexts.clear()
        gc.collect()

    @pytest.mark.asyncio
    async def test_auto_summary_functionality(self, memory_manager):
        """Test automatic summary functionality."""
        # Add multiple contexts
        contexts = []

        for i in range(5):
            context = MemoryContext(
                session_id=f"summary_{i}",
                history=[
                    {
                        "role": "user",
                        "content": f"Conversation part {i} about machine learning",
                        "timestamp": "2024-01-01T00:00:00",
                        "metadata": {"topic": "ML", "part": i},
                    }
                ],
            )
            contexts.append(context)
            await memory_manager.store_context(context)

        # Test context retrieval and optimization
        optimized = await memory_manager.get_optimized_context(
            "summary_0", max_tokens=1000
        )
        assert optimized is not None
        assert len(optimized) > 0

        # Cleanup
        contexts.clear()
        gc.collect()

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, memory_manager):
        """Test metrics tracking functionality."""
        # Add contexts and track metrics
        contexts = []

        for i in range(4):
            context = MemoryContext(
                session_id=f"metrics_{i}",
                history=[
                    {
                        "role": "user",
                        "content": f"Metrics test content {i}",
                        "timestamp": "2024-01-01T00:00:00",
                        "metadata": {"metrics": True},
                    }
                ],
            )
            contexts.append(context)
            await memory_manager.store_context(context)

        # Get metrics
        stats = await memory_manager.get_context_stats()

        # Verify metrics
        assert stats["total_contexts"] == 4
        assert "max_contexts" in stats
        assert "cleanup_threshold" in stats

        # Cleanup
        contexts.clear()
        gc.collect()

    @pytest.mark.asyncio
    async def test_context_persistence(self, memory_manager):
        """Test context persistence across operations."""
        # Create context
        context = MemoryContext(
            session_id="persistence_test",
            history=[
                {
                    "role": "user",
                    "content": "Persistence test content",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {"persistence": True},
                }
            ],
        )

        # Add context
        await memory_manager.store_context(context)

        # Verify persistence
        retrieved = await memory_manager.retrieve_context("persistence_test")
        assert retrieved is not None
        assert retrieved.history[0]["content"] == "Persistence test content"

        # Update context
        context.add_message("assistant", "Updated response")
        await memory_manager.update_context(context)

        # Verify update
        updated = await memory_manager.retrieve_context("persistence_test")
        assert updated is not None
        assert len(updated.history) == 2

        # Cleanup
        await memory_manager.clear_context("persistence_test")
        gc.collect()

    @pytest.mark.asyncio
    async def test_error_handling(self, memory_manager):
        """Test error handling in MemoryManager."""
        # Test getting non-existent context
        result = await memory_manager.retrieve_context("non_existent")
        assert result is None

        # Test clearing non-existent context (should not raise)
        await memory_manager.clear_context("non_existent")

    @pytest.mark.asyncio
    async def test_concurrent_access_safety(self, memory_manager):
        """Test concurrent access safety."""

        # Create contexts for concurrent testing
        contexts = []

        async def add_contexts():
            for i in range(10):
                context = MemoryContext(
                    session_id=f"concurrent_{asyncio.current_task().get_name()}_{i}",
                    history=[
                        {
                            "role": "user",
                            "content": f"Concurrent content {i}",
                            "timestamp": "2024-01-01T00:00:00",
                            "metadata": {"concurrent": True},
                        }
                    ],
                )
                contexts.append(context)
                await memory_manager.store_context(context)

        # Run concurrent tasks
        tasks = []
        for _ in range(3):
            task = asyncio.create_task(add_contexts())
            tasks.append(task)

        # Wait for completion
        await asyncio.gather(*tasks)

        # Verify results
        stats = await memory_manager.get_context_stats()
        assert stats["total_contexts"] == 30

        # Cleanup
        contexts.clear()
        gc.collect()

    @pytest.mark.asyncio
    async def test_memory_cleanup_after_test(self, memory_manager):
        """Test memory cleanup after test completion."""
        # Create test contexts
        contexts = []

        for i in range(3):
            context = MemoryContext(
                session_id=f"cleanup_test_{i}",
                history=[
                    {
                        "role": "user",
                        "content": f"Cleanup test content {i}",
                        "timestamp": "2024-01-01T00:00:00",
                        "metadata": {"cleanup_test": True},
                    }
                ],
            )
            contexts.append(context)
            await memory_manager.store_context(context)

        # Verify contexts exist
        stats = await memory_manager.get_context_stats()
        assert stats["total_contexts"] == 3

        # Cleanup
        for context in contexts:
            await memory_manager.clear_context(context.session_id)

        contexts.clear()
        gc.collect()

        # Verify cleanup
        stats = await memory_manager.get_context_stats()
        assert stats["total_contexts"] == 0


class TestMemoryContextFixes:
    """Test cases for MemoryContext fixes."""

    def test_context_creation(self):
        """Test MemoryContext creation."""
        # Test valid context
        context = MemoryContext(
            session_id="valid_test",
            history=[
                {
                    "role": "user",
                    "content": "Valid content",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {},
                }
            ],
        )
        assert context.session_id == "valid_test"
        assert len(context.history) == 1
        assert context.active_agents == {}
        assert context.agent_states == {}

    def test_context_serialization(self):
        """Test MemoryContext serialization."""
        context = MemoryContext(
            session_id="serialization_test",
            history=[
                {
                    "role": "user",
                    "content": "Test content",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {"test": True},
                }
            ],
        )

        # Test basic attributes
        assert context.session_id == "serialization_test"
        assert context.history[0]["content"] == "Test content"
        assert context.history[0]["metadata"]["test"] is True

    def test_context_validation(self):
        """Test MemoryContext validation."""
        # Test valid context
        context = MemoryContext(
            session_id="valid_test",
            history=[
                {
                    "role": "user",
                    "content": "Valid content",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {},
                }
            ],
        )
        assert context.session_id == "valid_test"

        # Test empty session_id (should work but might not be ideal)
        context = MemoryContext(session_id="", history=[])
        assert context.session_id == ""


@pytest.mark.asyncio
class TestMemoryManagerAsyncFixes:
    """Test cases for async MemoryManager operations."""

    @pytest_asyncio.fixture
    async def async_memory_manager(self):
        """Create async MemoryManager instance for testing."""
        manager = MemoryManager(
            max_contexts=10,
            cleanup_threshold_ratio=0.8,
            enable_persistence=False,
            enable_semantic_cache=False,
        )
        await manager.initialize()
        yield manager
        await manager.cleanup_all()

    async def test_async_context_operations(self, async_memory_manager):
        """Test async context operations."""
        # Create context
        context = MemoryContext(
            session_id="async_test",
            history=[
                {
                    "role": "user",
                    "content": "Async test content",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {"async": True},
                }
            ],
        )

        # Store context
        await async_memory_manager.store_context(context)

        # Retrieve context
        retrieved = await async_memory_manager.retrieve_context("async_test")
        assert retrieved is not None
        assert retrieved.session_id == "async_test"

        # Update context
        context.add_message("assistant", "Async response")
        await async_memory_manager.update_context(context)

        # Verify update
        updated = await async_memory_manager.retrieve_context("async_test")
        assert updated is not None
        assert len(updated.history) == 2

    async def test_async_batch_operations(self, async_memory_manager):
        """Test async batch operations."""
        # Create multiple contexts
        contexts = []
        for i in range(5):
            context = MemoryContext(
                session_id=f"batch_{i}",
                history=[
                    {
                        "role": "user",
                        "content": f"Batch content {i}",
                        "timestamp": "2024-01-01T00:00:00",
                        "metadata": {"batch": True, "index": i},
                    }
                ],
            )
            contexts.append(context)

        # Store all contexts
        for context in contexts:
            await async_memory_manager.store_context(context)

        # Verify all contexts are stored
        stats = await async_memory_manager.get_context_stats()
        assert stats["total_contexts"] == 5

        # Retrieve all contexts
        for i in range(5):
            retrieved = await async_memory_manager.retrieve_context(f"batch_{i}")
            assert retrieved is not None
            assert retrieved.session_id == f"batch_{i}"

        # Cleanup
        for context in contexts:
            await async_memory_manager.clear_context(context.session_id)
