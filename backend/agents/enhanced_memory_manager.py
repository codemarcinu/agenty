"""
Enhanced Memory Management for Conversation Context
Zgodnie z regułami MDC dla zaawansowanego zarządzania pamięcią konwersacyjną
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging
from typing import Any, TypedDict
import weakref

from sqlalchemy import select

from agents.interfaces import BaseAgent, IMemoryManager
from core.cache_manager import CacheManager
from core.database import get_db
from models.conversation import Conversation, Message

logger = logging.getLogger(__name__)


@dataclass
class ConversationSummary:
    """Podsumowanie konwersacji dla kompresji kontekstu"""

    key_points: list[str]
    user_preferences: dict[str, Any]
    conversation_style: str
    topics_discussed: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ContextWindow:
    """Okno kontekstowe z optymalizacją"""

    recent_messages: list[dict[str, Any]]  # Ostatnie N wiadomości (pełne)
    summary: ConversationSummary | None  # Podsumowanie starszych części
    semantic_cache_key: str | None  # Klucz cache'u semantycznego
    token_count: int  # Szacowana liczba tokenów
    last_optimized: datetime


class MemoryStats(TypedDict):
    total_contexts: int
    persistent_contexts: int
    cached_contexts: int
    last_cleanup: datetime | None
    cleanup_count: int
    compression_ratio: float
    cache_hit_rate: float


class EnhancedMemoryContext:
    """Rozszerzony kontekst pamięci z trwałym przechowywaniem"""

    __slots__ = [
        "__weakref__",
        "active_agents",
        "context_window",
        "conversation_summary",
        "created_at",
        "history",
        "last_command",
        "last_response",
        "last_updated",
        "persistent_id",
        "request_id",
        "semantic_hash",
        "session_id",
    ]

    def __init__(self, session_id: str, history: list[dict] | None = None) -> None:
        self.session_id = session_id
        self.history = history if history is not None else []
        self.active_agents: dict[str, BaseAgent] = {}
        self.last_response: Any | None = None
        self.last_command: str | None = None
        self.request_id: str | None = None
        self.created_at: datetime = datetime.now()
        self.last_updated: datetime = datetime.now()
        self.conversation_summary: ConversationSummary | None = None
        self.context_window: ContextWindow | None = None
        self.persistent_id: int | None = None
        self.semantic_hash: str | None = None

    def set_last_command(self, command: str) -> None:
        """Set the last command issued in this memory context."""
        self.last_command = command

    def add_message(
        self, role: str, content: str, metadata: dict | None = None
    ) -> None:
        """Add message to conversation history"""
        message_data = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.history.append(message_data)
        self.last_updated = datetime.now()

    def get_optimized_context(self, max_tokens: int = 4000) -> list[dict[str, Any]]:
        """Get optimized context for LLM within token limit"""
        if not self.context_window:
            self._optimize_context_window(max_tokens)

        messages = []

        # Add summary if available
        if self.context_window.summary:
            summary_text = self._format_summary(self.context_window.summary)
            messages.append(
                {
                    "role": "system",
                    "content": f"Podsumowanie poprzedniej rozmowy:\n{summary_text}",
                }
            )

        # Add recent messages
        messages.extend(self.context_window.recent_messages)

        return messages

    def _optimize_context_window(self, max_tokens: int) -> None:
        """Optimize context window to fit within token limit"""
        if len(self.history) <= 10:  # If short conversation, keep all
            self.context_window = ContextWindow(
                recent_messages=self.history[-10:],
                summary=None,
                semantic_cache_key=None,
                token_count=self._estimate_tokens(self.history),
                last_optimized=datetime.now(),
            )
            return

        # Calculate tokens for recent messages (keep last 10)
        recent_messages = self.history[-10:]
        recent_tokens = self._estimate_tokens(recent_messages)

        # If recent messages fit, use them with summary
        if recent_tokens < max_tokens * 0.7:  # Leave 30% for summary
            older_messages = self.history[:-10]
            if older_messages:
                # Create or update summary
                self.conversation_summary = self._create_conversation_summary(
                    older_messages
                )
                summary_tokens = self._estimate_tokens(
                    [{"content": self._format_summary(self.conversation_summary)}]
                )

                if recent_tokens + summary_tokens <= max_tokens:
                    self.context_window = ContextWindow(
                        recent_messages=recent_messages,
                        summary=self.conversation_summary,
                        semantic_cache_key=self._generate_semantic_hash(older_messages),
                        token_count=recent_tokens + summary_tokens,
                        last_optimized=datetime.now(),
                    )
                    return

        # Fallback: use only recent messages
        self.context_window = ContextWindow(
            recent_messages=recent_messages,
            summary=None,
            semantic_cache_key=None,
            token_count=recent_tokens,
            last_optimized=datetime.now(),
        )

    def _estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Estimate token count for messages (rough approximation)"""
        total_tokens = 0
        for message in messages:
            content = message.get("content", "")
            # Rough estimation: 1 token ≈ 4 characters
            total_tokens += len(content) // 4
        return total_tokens

    def _create_conversation_summary(
        self, messages: list[dict[str, Any]]
    ) -> ConversationSummary:
        """Create conversation summary from older messages"""
        # Extract key information from messages
        key_points = []
        topics = set()
        user_prefs = {}

        for msg in messages:
            content = msg.get("content", "").lower()
            role = msg.get("role", "")

            # Extract topics (simple keyword extraction)
            if "przepis" in content or "gotowanie" in content:
                topics.add("cooking")
            if "pogoda" in content:
                topics.add("weather")
            if "zakupy" in content or "lista" in content:
                topics.add("shopping")
            if "spiżarnia" in content or "produkty" in content:
                topics.add("pantry")

            # Extract user preferences
            if role == "user" and ("lubię" in content or "preferuję" in content):
                # Simple preference extraction
                pass

        return ConversationSummary(
            key_points=key_points[:5],  # Top 5 key points
            user_preferences=user_prefs,
            conversation_style="friendly",  # Default
            topics_discussed=list(topics),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def _format_summary(self, summary: ConversationSummary) -> str:
        """Format conversation summary for LLM context"""
        topics_str = (
            ", ".join(summary.topics_discussed)
            if summary.topics_discussed
            else "ogólne"
        )
        return f"""
Wcześniej rozmawialiśmy o: {topics_str}
Styl rozmowy: {summary.conversation_style}
Kluczowe punkty: {"; ".join(summary.key_points) if summary.key_points else "brak"}
"""

    def _generate_semantic_hash(self, messages: list[dict[str, Any]]) -> str:
        """Generate semantic hash for caching similar contexts"""
        content = " ".join([msg.get("content", "") for msg in messages])
        return hashlib.md5(content.encode()).hexdigest()


class EnhancedMemoryManager(IMemoryManager):
    """Zaawansowany menedżer pamięci z trwałym przechowywaniem i optymalizacją"""

    def __init__(
        self,
        max_contexts: int = 1000,
        cleanup_threshold_ratio: float = 0.8,
        enable_persistence: bool = True,
        enable_semantic_cache: bool = True,
    ) -> None:
        # In-memory contexts with weak references
        self._contexts: dict[str, weakref.ReferenceType[EnhancedMemoryContext]] = {}
        self._max_contexts = max_contexts
        self._cleanup_threshold = int(max_contexts * cleanup_threshold_ratio)
        self._cleanup_lock = asyncio.Lock()

        # Enhanced features
        self._enable_persistence = enable_persistence
        self._enable_semantic_cache = enable_semantic_cache
        self._cache_manager = CacheManager()
        self._semantic_cache: dict[str, EnhancedMemoryContext] = {}

        # Statistics
        self._memory_stats: MemoryStats = {
            "total_contexts": 0,
            "persistent_contexts": 0,
            "cached_contexts": 0,
            "last_cleanup": None,
            "cleanup_count": 0,
            "compression_ratio": 0.0,
            "cache_hit_rate": 0.0,
        }

    async def initialize(self) -> None:
        """Initialize the memory manager"""
        await self._cache_manager.connect()
        logger.info("Enhanced Memory Manager initialized")

    async def store_context(self, context: EnhancedMemoryContext) -> None:
        """Store context with persistence and caching"""
        if len(self._contexts) >= self._max_contexts:
            await self._cleanup_old_contexts()

        # Store in memory with weak reference
        self._contexts[context.session_id] = weakref.ref(
            context, self._cleanup_callback
        )
        context.last_updated = datetime.now()

        # Store in persistent storage
        if self._enable_persistence:
            await self._persist_context(context)

        # Store in semantic cache
        if self._enable_semantic_cache and context.semantic_hash:
            self._semantic_cache[context.semantic_hash] = context

        self._update_stats()
        logger.debug(f"Stored enhanced context for session: {context.session_id}")

    async def retrieve_context(self, session_id: str) -> EnhancedMemoryContext | None:
        """Retrieve context with fallback to persistent storage"""
        # Try memory first
        weak_ref = self._contexts.get(session_id)
        if weak_ref:
            context = weak_ref()
            if context:
                context.last_updated = datetime.now()
                logger.debug(f"Retrieved context from memory for session: {session_id}")
                return context
            del self._contexts[session_id]

        # Try persistent storage
        if self._enable_persistence:
            context = await self._load_from_persistence(session_id)
            if context:
                # Restore to memory
                await self.store_context(context)
                logger.debug(
                    f"Restored context from persistence for session: {session_id}"
                )
                return context

        # Try semantic cache
        if self._enable_semantic_cache:
            context = await self._find_similar_context(session_id)
            if context:
                logger.debug(
                    f"Found similar context in semantic cache for session: {session_id}"
                )
                return context

        return None

    async def get_context(self, session_id: str) -> EnhancedMemoryContext:
        """Get or create context for session"""
        context = await self.retrieve_context(session_id)
        if context is None:
            context = EnhancedMemoryContext(session_id)
            await self.store_context(context)
            logger.debug(f"Created new enhanced context for session: {session_id}")
        return context

    async def update_context(
        self, context: EnhancedMemoryContext, new_data: dict[str, Any] | None = None
    ) -> None:
        """Update context with new data and optimize"""
        if context.session_id in self._contexts:
            # Add new data to context history
            if new_data and isinstance(new_data, dict):
                # Handle different data formats
                if "message" in new_data:
                    context.add_message(
                        role=new_data.get("role", "user"),
                        content=new_data["message"],
                        metadata=new_data,
                    )
                elif "content" in new_data:
                    context.add_message(
                        role=new_data.get("role", "user"),
                        content=new_data["content"],
                        metadata=new_data,
                    )
                else:
                    # Generic data update
                    if not hasattr(context, "history"):
                        context.history = []
                    context.history.append(
                        {"timestamp": datetime.now().isoformat(), "data": new_data}
                    )

            # Optimize context window
            context._optimize_context_window(max_tokens=4000)

            # Update storage
            await self.store_context(context)
            logger.debug(f"Updated enhanced context for session: {context.session_id}")

    async def clear_context(self, session_id: str) -> None:
        """Clear context from all storage layers"""
        # Clear from memory
        if session_id in self._contexts:
            del self._contexts[session_id]

        # Clear from persistent storage
        if self._enable_persistence:
            await self._clear_from_persistence(session_id)

        # Clear from semantic cache
        if self._enable_semantic_cache:
            await self._clear_from_semantic_cache(session_id)

        self._update_stats()
        logger.debug(f"Cleared enhanced context for session: {session_id}")

    async def _persist_context(self, context: EnhancedMemoryContext) -> None:
        """Persist context to database"""
        try:
            async for db in get_db():
                # Create or update conversation
                if context.persistent_id:
                    # Update existing conversation
                    stmt = select(Conversation).where(
                        Conversation.id == context.persistent_id
                    )
                    result = await db.execute(stmt)
                    conversation = result.scalar_one_or_none()
                else:
                    # Create new conversation
                    conversation = Conversation(session_id=context.session_id)
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)
                    context.persistent_id = conversation.id

                # Add messages
                for msg_data in context.history[-5:]:  # Keep last 5 messages
                    if isinstance(msg_data, dict) and "content" in msg_data:
                        message = Message(
                            conversation_id=conversation.id,
                            role=msg_data.get("role", "user"),
                            content=msg_data["content"],
                        )
                        db.add(message)

                await db.commit()
                self._memory_stats["persistent_contexts"] += 1

        except Exception as e:
            logger.error(f"Error persisting context: {e}")

    async def _load_from_persistence(
        self, session_id: str
    ) -> EnhancedMemoryContext | None:
        """Load context from persistent storage"""
        try:
            async for db in get_db():
                stmt = select(Conversation).where(Conversation.session_id == session_id)
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()

                if conversation:
                    # Load messages
                    stmt = select(Message).where(
                        Message.conversation_id == conversation.id
                    )
                    result = await db.execute(stmt)
                    messages = result.scalars().all()

                    # Convert to context format
                    history = []
                    for msg in messages:
                        history.append(
                            {
                                "role": msg.role,
                                "content": msg.content,
                                "timestamp": msg.created_at.isoformat(),
                            }
                        )

                    context = EnhancedMemoryContext(session_id, history)
                    context.persistent_id = conversation.id
                    return context

        except Exception as e:
            logger.error(f"Error loading from persistence: {e}")

        return None

    async def _clear_from_persistence(self, session_id: str) -> None:
        """Clear context from persistent storage"""
        try:
            async for db in get_db():
                stmt = select(Conversation).where(Conversation.session_id == session_id)
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()

                if conversation:
                    # Delete messages first (cascade should handle this)
                    await db.delete(conversation)
                    await db.commit()

        except Exception as e:
            logger.error(f"Error clearing from persistence: {e}")

    async def _find_similar_context(
        self, session_id: str
    ) -> EnhancedMemoryContext | None:
        """Find similar context in semantic cache"""
        # Simple similarity check based on session_id pattern
        for cached_context in self._semantic_cache.values():
            if cached_context.session_id.startswith(session_id[:8]):  # First 8 chars
                return cached_context
        return None

    async def _clear_from_semantic_cache(self, session_id: str) -> None:
        """Clear context from semantic cache"""
        keys_to_remove = []
        for key, context in self._semantic_cache.items():
            if context.session_id == session_id:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._semantic_cache[key]

    def _cleanup_callback(self, weak_ref) -> None:
        """Callback when context is garbage collected"""
        for session_id, ref in list(self._contexts.items()):
            if ref is weak_ref:
                del self._contexts[session_id]
                logger.debug(f"Cleaned up garbage collected context: {session_id}")
                break

    async def _cleanup_old_contexts(self) -> None:
        """Remove old contexts when limit is reached"""
        async with self._cleanup_lock:
            if len(self._contexts) <= self._cleanup_threshold:
                return

            # Get valid contexts and their timestamps
            valid_contexts = []
            for session_id, weak_ref in self._contexts.items():
                context = weak_ref()
                if context:
                    valid_contexts.append((session_id, context, context.last_updated))
                else:
                    del self._contexts[session_id]

            # Sort by last_updated and remove oldest
            valid_contexts.sort(key=lambda x: x[2], reverse=True)
            contexts_to_keep = valid_contexts[: self._cleanup_threshold]

            # Rebuild contexts dict
            new_contexts = {}
            for session_id, context, _ in contexts_to_keep:
                new_contexts[session_id] = weakref.ref(context, self._cleanup_callback)

            removed_count = len(self._contexts) - len(new_contexts)
            self._contexts = new_contexts
            self._memory_stats["last_cleanup"] = datetime.now()
            self._memory_stats["cleanup_count"] += 1

            logger.info(
                f"Cleaned up {removed_count} old contexts. Total: {len(self._contexts)}"
            )

    def _update_stats(self) -> None:
        """Update memory statistics"""
        self._memory_stats["total_contexts"] = len(self._contexts)
        self._memory_stats["cached_contexts"] = len(self._semantic_cache)

        # Calculate compression ratio
        total_messages = sum(len(ctx.history) for ctx in self._get_valid_contexts())
        compressed_messages = sum(
            (
                len(ctx.context_window.recent_messages)
                if ctx.context_window
                else len(ctx.history)
            )
            for ctx in self._get_valid_contexts()
        )

        if total_messages > 0:
            self._memory_stats["compression_ratio"] = (
                compressed_messages / total_messages
            )

    def _get_valid_contexts(self) -> list[EnhancedMemoryContext]:
        """Get all valid contexts"""
        valid_contexts = []
        for weak_ref in self._contexts.values():
            context = weak_ref()
            if context:
                valid_contexts.append(context)
        return valid_contexts

    async def get_context_stats(self) -> dict[str, Any]:
        """Get enhanced memory manager statistics"""
        await self._cleanup_old_contexts()
        self._update_stats()

        valid_contexts = self._get_valid_contexts()

        return {
            "total_contexts": len(valid_contexts),
            "persistent_contexts": self._memory_stats["persistent_contexts"],
            "cached_contexts": self._memory_stats["cached_contexts"],
            "max_contexts": self._max_contexts,
            "cleanup_threshold": self._cleanup_threshold,
            "compression_ratio": self._memory_stats["compression_ratio"],
            "cache_hit_rate": self._memory_stats["cache_hit_rate"],
            "oldest_context": min(
                (ctx.last_updated for ctx in valid_contexts), default=None
            ),
            "newest_context": max(
                (ctx.last_updated for ctx in valid_contexts), default=None
            ),
            "memory_stats": self._memory_stats,
        }

    async def cleanup_all(self) -> None:
        """Cleanup all contexts and reset memory manager"""
        async with self._cleanup_lock:
            self._contexts.clear()
            self._semantic_cache.clear()
            self._memory_stats["total_contexts"] = 0
            self._memory_stats["cached_contexts"] = 0
            self._memory_stats["last_cleanup"] = datetime.now()
            self._memory_stats["cleanup_count"] += 1
            logger.info("Cleaned up all enhanced contexts")

    @asynccontextmanager
    async def context_manager(self, session_id: str):
        """Async context manager for enhanced memory context lifecycle"""
        context = await self.get_context(session_id)
        try:
            yield context
        finally:
            context.last_updated = datetime.now()
            await self.update_context(context, None)
            logger.debug(f"Enhanced context manager exited for session: {session_id}")

    async def shutdown(self) -> None:
        """Shutdown memory manager"""
        await self._cache_manager.disconnect()
        logger.info("Enhanced Memory Manager shutdown completed")
