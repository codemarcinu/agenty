import asyncio
from datetime import datetime
import gc
import logging
from typing import Any
import weakref

from agents.interfaces import MemoryContext

logger = logging.getLogger(__name__)


class MemoryManager:
    """Core memory management for conversation context with optimization"""

    def __init__(self, max_contexts: int = 1000, cleanup_interval: int = 300) -> None:
        # Use weak references to prevent memory leaks
        self._contexts: dict[str, weakref.ref] = {}
        self._access_times: dict[str, datetime] = {}
        self._max_contexts = max_contexts
        self._cleanup_interval = cleanup_interval
        self._memory_pool: set[str] = set()
        self._cleanup_task: asyncio.Task | None = None
        self._start_cleanup_task()

    def get_or_create_context(self, session_id: str) -> MemoryContext:
        """Get existing context or create new one with memory optimization"""
        # Check if context exists and is still alive
        context_ref = self._contexts.get(session_id)
        if context_ref is not None:
            context = context_ref()
            if context is not None:
                self._access_times[session_id] = datetime.now()
                return context
            else:
                # Context was garbage collected, remove dead reference
                del self._contexts[session_id]
                self._access_times.pop(session_id, None)

        # Create new context
        context = MemoryContext(session_id)
        self._contexts[session_id] = weakref.ref(
            context, lambda ref: self._cleanup_context(session_id)
        )
        self._access_times[session_id] = datetime.now()
        self._memory_pool.add(session_id)

        # Trigger cleanup if we have too many contexts
        if len(self._contexts) > self._max_contexts:
            asyncio.create_task(self._cleanup_old_contexts())

        logger.info(f"Created new memory context for session: {session_id}")
        return context

    def update_context(self, session_id: str, data: dict[str, Any]) -> None:
        """Update context with new data and memory optimization"""
        context = self.get_or_create_context(session_id)

        # Compress history if it gets too large
        if len(context.history) > 100:
            # Keep only the last 50 entries and a summary of older ones
            older_entries = context.history[:-50]
            context.history = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "summary": f"Compressed {len(older_entries)} older entries"
                    },
                    "compressed": True,
                }
            ] + context.history[-50:]

        context.history.append({"timestamp": datetime.now().isoformat(), "data": data})
        context.last_updated = datetime.now()
        self._access_times[session_id] = datetime.now()

    def get_context_history(self, session_id: str) -> list[dict[str, Any]]:
        """Get conversation history for session"""
        context_ref = self._contexts.get(session_id)
        if context_ref is not None:
            context = context_ref()
            if context is not None:
                self._access_times[session_id] = datetime.now()
                return context.history
        return []

    def clear_context(self, session_id: str) -> None:
        """Clear context for session"""
        if session_id in self._contexts:
            del self._contexts[session_id]
            self._access_times.pop(session_id, None)
            self._memory_pool.discard(session_id)
            logger.info(f"Cleared memory context for session: {session_id}")

    def get_all_contexts(self) -> dict[str, MemoryContext]:
        """Get all contexts (for debugging)"""
        contexts = {}
        for session_id, context_ref in self._contexts.items():
            context = context_ref()
            if context is not None:
                contexts[session_id] = context
        return contexts

    def _cleanup_context(self, session_id: str) -> None:
        """Callback for when a context is garbage collected"""
        self._access_times.pop(session_id, None)
        self._memory_pool.discard(session_id)
        logger.debug(f"Context {session_id} was garbage collected")

    def _start_cleanup_task(self) -> None:
        """Start the periodic cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old contexts"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_old_contexts()
                # Force garbage collection
                gc.collect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    async def _cleanup_old_contexts(self) -> None:
        """Remove old or inactive contexts"""
        current_time = datetime.now()
        contexts_to_remove = []

        for session_id, access_time in self._access_times.items():
            # Remove contexts older than 1 hour
            if (current_time - access_time).total_seconds() > 3600:
                contexts_to_remove.append(session_id)

        # Remove oldest contexts if we're over the limit
        if len(self._contexts) > self._max_contexts:
            sorted_contexts = sorted(self._access_times.items(), key=lambda x: x[1])
            contexts_to_remove.extend(
                [
                    session_id
                    for session_id, _ in sorted_contexts[
                        : len(self._contexts) - self._max_contexts
                    ]
                ]
            )

        for session_id in contexts_to_remove:
            self.clear_context(session_id)

        if contexts_to_remove:
            logger.info(f"Cleaned up {len(contexts_to_remove)} old contexts")

    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory usage statistics"""
        alive_contexts = sum(1 for ref in self._contexts.values() if ref() is not None)
        return {
            "total_contexts": len(self._contexts),
            "alive_contexts": alive_contexts,
            "dead_references": len(self._contexts) - alive_contexts,
            "memory_pool_size": len(self._memory_pool),
            "access_times_tracked": len(self._access_times),
        }

    async def force_cleanup(self) -> None:
        """Force immediate cleanup of memory"""
        await self._cleanup_old_contexts()
        # Remove dead references
        dead_refs = []
        for session_id, context_ref in self._contexts.items():
            if context_ref() is None:
                dead_refs.append(session_id)

        for session_id in dead_refs:
            del self._contexts[session_id]
            self._access_times.pop(session_id, None)
            self._memory_pool.discard(session_id)

        gc.collect()
        logger.info(
            f"Force cleanup completed, removed {len(dead_refs)} dead references"
        )

    def __del__(self) -> None:
        """Cleanup when manager is destroyed"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
