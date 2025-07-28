"""
Memory Management for Conversation Context
Zgodnie z regułami MDC dla zarządzania pamięcią
"""

from contextlib import asynccontextmanager
from datetime import datetime
import hashlib
import logging
from typing import Any, TypedDict
import weakref

from sqlalchemy import select

from agents.interfaces import BaseAgent, IMemoryManager
from core.cache_manager import CacheManager
from core.database import get_db
from models.conversation import Conversation, ConversationSession, Message
from tasks.conversation_tasks import (
    get_conversation_summary,
    update_conversation_summary_task,
)

logger = logging.getLogger(__name__)


class MemoryStats(TypedDict):
    total_contexts: int
    persistent_contexts: int
    cached_contexts: int
    last_cleanup: datetime | None
    cleanup_count: int
    compression_ratio: float
    cache_hit_rate: float


class ConversationSummary:
    """Podsumowanie konwersacji dla kompresji kontekstu"""

    def __init__(
        self,
        key_points: list[str],
        topics_discussed: list[str],
        user_preferences: dict[str, Any],
        conversation_style: str = "friendly",
    ):
        self.key_points = key_points
        self.topics_discussed = topics_discussed
        self.user_preferences = user_preferences
        self.conversation_style = conversation_style
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def format_for_llm(self) -> str:
        """Format conversation summary for LLM context"""
        topics_str = (
            ", ".join(self.topics_discussed) if self.topics_discussed else "ogólne"
        )
        return f"""
Wcześniej rozmawialiśmy o: {topics_str}
Styl rozmowy: {self.conversation_style}
Kluczowe punkty: {"; ".join(self.key_points) if self.key_points else "brak"}
"""


class ContextWindow:
    """Okno kontekstowe z optymalizacją"""

    def __init__(
        self,
        recent_messages: list[dict[str, Any]],
        summary: ConversationSummary | None = None,
        token_count: int = 0,
    ):
        self.recent_messages = recent_messages
        self.summary = summary
        self.token_count = token_count
        self.last_optimized = datetime.now()

    def get_optimized_messages(self) -> list[dict[str, Any]]:
        """Get optimized messages for LLM"""
        messages = []

        # Add summary if available
        if self.summary:
            messages.append(
                {"role": "system", "content": self.summary.format_for_llm()}
            )

        # Add recent messages
        messages.extend(self.recent_messages)

        return messages


class MemoryContext:
    """Context for maintaining conversation state and memory with __slots__
    optimization"""

    __slots__ = [
        "__weakref__",  # Allow weak references
        "active_agents",
        "agent_states",
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
        self.active_agents: dict[str, dict[str, Any]] = {}
        self.agent_states: dict[str, dict[str, Any]] = {}
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

        return self.context_window.get_optimized_messages()

    def _optimize_context_window(self, max_tokens: int) -> None:
        """Optimize context window to fit within token limit"""
        if len(self.history) <= 10:  # If short conversation, keep all
            self.context_window = ContextWindow(
                recent_messages=self.history[-10:],
                summary=None,
                token_count=self._estimate_tokens(self.history),
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
                    [{"content": self.conversation_summary.format_for_llm()}]
                )

                if recent_tokens + summary_tokens <= max_tokens:
                    self.context_window = ContextWindow(
                        recent_messages=recent_messages,
                        summary=self.conversation_summary,
                        token_count=recent_tokens + summary_tokens,
                    )
                    return

        # Fallback: use only recent messages
        self.context_window = ContextWindow(
            recent_messages=recent_messages, summary=None, token_count=recent_tokens
        )

    def _estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Estimate token count for messages (rough approximation)"""
        total_tokens = 0
        for message in messages:
            content = message.get("content", "")
            # Rough estimation: 1 token ≈ 4 characters
            total_tokens += len(content) // 4
        return total_tokens

    def _generate_semantic_hash(self, messages: list[dict[str, Any]]) -> str:
        """Generate semantic hash for context similarity detection"""
        content = " ".join([msg.get("content", "") for msg in messages[-5:]])
        return hashlib.md5(content.encode()).hexdigest()

    def _create_conversation_summary(
        self, messages: list[dict[str, Any]]
    ) -> ConversationSummary:
        """Create conversation summary from older messages"""
        # Extract key information from messages
        key_points = []
        topics = set()
        user_prefs = {}

        # Keywords for topic detection (both English and Polish)
        topic_keywords = {
            "cooking": [
                "przepis",
                "gotowanie",
                "cook",
                "recipe",
                "kitchen",
                "kuchnia",
                "food",
                "jedzenie",
            ],
            "weather": [
                "pogoda",
                "weather",
                "temperature",
                "temperatura",
                "rain",
                "deszcz",
            ],
            "shopping": [
                "zakupy",
                "shopping",
                "lista",
                "list",
                "buy",
                "kupić",
                "store",
                "sklep",
            ],
            "pantry": [
                "spiżarnia",
                "pantry",
                "produkty",
                "products",
                "food items",
                "artykuły spożywcze",
            ],
            "health": ["zdrowie", "health", "diet", "dieta", "nutrition", "odżywianie"],
            "travel": ["podróż", "travel", "trip", "wycieczka", "vacation", "wakacje"],
            "work": ["praca", "work", "job", "office", "biuro", "project", "projekt"],
            "family": ["rodzina", "family", "children", "dzieci", "parents", "rodzice"],
            "entertainment": [
                "rozrywka",
                "entertainment",
                "movie",
                "film",
                "music",
                "muzyka",
                "game",
                "gra",
            ],
        }

        for message in messages:
            content = message.get("content", "").lower()
            role = message.get("role", "")

            # Detect topics
            for topic, keywords in topic_keywords.items():
                if any(keyword in content for keyword in keywords):
                    topics.add(topic)

            # Extract key points from user messages
            if role == "user" and len(content) > 10:
                # Simple key point extraction (first sentence or main idea)
                sentences = content.split(".")
                if sentences:
                    key_point = sentences[0].strip()
                    if len(key_point) > 5:
                        key_points.append(key_point)

            # Extract user preferences
            if role == "user" and ("lubię" in content or "like" in content):
                # Simple preference extraction
                if "prosty" in content or "simple" in content:
                    user_prefs["cooking_style"] = "simple"
                if "zdrowy" in content or "healthy" in content:
                    user_prefs["diet_preference"] = "healthy"

        # Limit key points to avoid overwhelming context
        key_points = key_points[-5:] if len(key_points) > 5 else key_points

        return ConversationSummary(
            key_points=key_points,
            topics_discussed=list(topics),
            user_preferences=user_prefs,
            conversation_style="friendly",
        )


class MemoryManager(IMemoryManager):
    """Enhanced Memory Manager with conversation summary integration"""

    def __init__(
        self,
        max_contexts: int = 1000,
        cleanup_threshold_ratio: float = 0.8,
        enable_persistence: bool = True,
        enable_semantic_cache: bool = True,
    ) -> None:
        # Use weak references to avoid memory leaks
        self._contexts: dict[str, weakref.ref] = {}
        self._max_contexts = max_contexts
        self._cleanup_threshold_ratio = cleanup_threshold_ratio
        self._cleanup_threshold = int(max_contexts * cleanup_threshold_ratio)
        self._enable_persistence = enable_persistence
        self._enable_semantic_cache = enable_semantic_cache
        self._cache_manager = CacheManager() if enable_semantic_cache else None
        self._semantic_cache: dict[str, MemoryContext] = {}
        self._stats = {
            "total_contexts": 0,
            "persistent_contexts": 0,
            "cached_contexts": 0,
            "last_cleanup": None,
            "cleanup_count": 0,
            "compression_ratio": 0.0,
            "cache_hit_rate": 0.0,
        }
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize memory manager"""
        if self._initialized:
            return
        self._initialized = True
        logger.info("MemoryManager initialized")

    async def store_context(self, context: MemoryContext) -> None:
        """Store context with weak reference"""
        if context.session_id in self._contexts:
            logger.warning(f"Context for session {context.session_id} already exists")
            return

        # Create weak reference with cleanup callback
        weak_ref = weakref.ref(context, self._cleanup_callback)
        self._contexts[context.session_id] = weak_ref
        self._stats["total_contexts"] += 1
        logger.debug(
            f"Stored context for session {context.session_id}, total_contexts: {self._stats['total_contexts']}"
        )

        # Persist to database if enabled
        if self._enable_persistence:
            await self._persist_context(context)

        # Store in semantic cache if enabled
        if self._enable_semantic_cache and self._cache_manager:
            await self._cache_manager.store_semantic_context(
                context.session_id, context._generate_semantic_hash(context.history)
            )

        logger.debug(f"Stored context for session {context.session_id}")

    def _cleanup_callback(self, weak_ref) -> None:
        """Callback for weak reference cleanup"""
        self._stats["total_contexts"] -= 1
        logger.debug(
            f"Context cleaned up from memory, total_contexts: {self._stats['total_contexts']}"
        )

    async def retrieve_context(self, session_id: str) -> MemoryContext | None:
        """Retrieve context with fallback to persistence"""
        # Try memory first
        weak_ref = self._contexts.get(session_id)
        if weak_ref:
            context = weak_ref()
            if context:
                logger.debug(f"Retrieved context from memory for session {session_id}")
                return context

        # Try persistence
        if self._enable_persistence:
            context = await self._load_from_persistence(session_id)
            if context:
                # Re-store in memory
                await self.store_context(context)
                logger.debug(
                    f"Retrieved context from persistence for session {session_id}"
                )
                return context

        # Try semantic cache
        if self._enable_semantic_cache and self._cache_manager:
            similar_context = await self._find_similar_context(session_id)
            if similar_context:
                logger.debug(f"Found similar context for session {session_id}")
                return similar_context

        logger.debug(f"No context found for session {session_id}")
        return None

    async def get_context(self, session_id: str) -> MemoryContext:
        """Get or create context for session"""
        context = await self.retrieve_context(session_id)
        if context is None:
            context = MemoryContext(session_id)
            await self.store_context(context)
            logger.info(f"Created new context for session {session_id}")
        return context

    async def update_context(
        self, context: MemoryContext, new_data: dict[str, Any] | None = None
    ) -> None:
        """Update context and persist if enabled. Automatycznie generuj summary jeśli nie istnieje lub jest nieaktualne."""
        # Update context with new data - tylko dla istniejących atrybutów w __slots__
        if new_data:
            for k, v in new_data.items():
                if hasattr(context, k):
                    setattr(context, k, v)
                else:
                    logger.warning(
                        f"Cannot set attribute '{k}' on MemoryContext - not in __slots__"
                    )

        # Automatyczne podsumowanie konwersacji
        if not context.conversation_summary or (
            len(context.history) > 0
            and (
                not hasattr(context.conversation_summary, "last_updated")
                or getattr(context.conversation_summary, "last_updated", None) is None
                or (
                    hasattr(context, "last_updated")
                    and context.last_updated
                    > getattr(
                        context.conversation_summary, "last_updated", context.created_at
                    )
                )
            )
        ):
            context.conversation_summary = context._create_conversation_summary(
                context.history
            )

        # Persist to database if enabled
        if self._enable_persistence:
            await self._persist_context(context)
        logger.debug(f"Updated context for session {context.session_id}")

        # Trigger conversation summary update in background
        if (
            len(context.history) >= 5
        ):  # Only update summary if there are enough messages
            try:
                # Schedule background task to update conversation summary
                update_conversation_summary_task.delay(context.session_id)
                logger.debug(
                    f"Scheduled conversation summary update for session {context.session_id}"
                )
            except Exception as e:
                logger.error(f"Failed to schedule conversation summary update: {e}")

    async def get_optimized_context(
        self, session_id: str, max_tokens: int = 4000
    ) -> list[dict[str, Any]]:
        """Get optimized context with conversation summary integration"""
        context = await self.get_context(session_id)

        # Try to get conversation summary from database
        try:
            summary_data = await get_conversation_summary(session_id)
            if summary_data:
                # Create ConversationSummary object from database data
                context.conversation_summary = ConversationSummary(
                    key_points=summary_data.get("key_points", []),
                    topics_discussed=summary_data.get("topics_discussed", []),
                    user_preferences=summary_data.get("user_preferences", {}),
                    conversation_style=summary_data.get(
                        "conversation_style", "friendly"
                    ),
                )
                logger.debug(f"Loaded conversation summary for session {session_id}")
        except Exception as e:
            logger.warning(
                f"Failed to load conversation summary for session {session_id}: {e}"
            )

        return context.get_optimized_context(max_tokens)

    async def clear_context(self, session_id: str) -> None:
        """Clear context from all storage layers"""
        # Remove from memory
        if session_id in self._contexts:
            del self._contexts[session_id]
            self._stats["total_contexts"] -= 1

        # Clear from persistence
        if self._enable_persistence:
            await self._clear_from_persistence(session_id)

        # Clear from semantic cache
        if self._enable_semantic_cache and self._cache_manager:
            await self._clear_from_semantic_cache(session_id)

        logger.info(f"Cleared context for session {session_id}")

    async def _persist_context(self, context: MemoryContext) -> None:
        """Persist context to database"""
        try:
            async for db in get_db():
                # Check if conversation exists
                stmt = select(Conversation).where(
                    Conversation.session_id == context.session_id
                )
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()

                if not conversation:
                    # Create new conversation
                    conversation = Conversation(session_id=context.session_id)
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)

                # Save messages
                for message_data in context.history[-10:]:  # Save last 10 messages
                    message = Message(
                        content=message_data.get("content", ""),
                        role=message_data.get("role", "user"),
                        conversation_id=conversation.id,
                        message_metadata=message_data.get("metadata", {}),
                    )
                    db.add(message)

                await db.commit()
                context.persistent_id = conversation.id
                logger.debug(f"Persisted context for session {context.session_id}")

        except Exception as e:
            logger.error(f"Error persisting context: {e}")
            if "db" in locals():
                await db.rollback()

    async def _load_from_persistence(self, session_id: str) -> MemoryContext | None:
        """Load context from database"""
        try:
            async for db in get_db():
                # Find conversation
                stmt = select(Conversation).where(Conversation.session_id == session_id)
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()

                if not conversation:
                    return None

                # Load messages
                stmt = (
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at)
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
                            "metadata": msg.message_metadata or {},
                        }
                    )

                # Create context
                context = MemoryContext(session_id=session_id, history=history)
                context.persistent_id = conversation.id

                # Load conversation summary if available
                summary_stmt = select(ConversationSession).where(
                    ConversationSession.session_id == session_id
                )
                summary_result = await db.execute(summary_stmt)
                summary_session = summary_result.scalar_one_or_none()

                if summary_session:
                    context.conversation_summary = ConversationSummary(
                        key_points=summary_session.key_points or [],
                        topics_discussed=summary_session.topics_discussed or [],
                        user_preferences=summary_session.user_preferences or {},
                        conversation_style=summary_session.conversation_style
                        or "friendly",
                    )

                logger.debug(
                    f"Loaded context for session {session_id} with {len(history)} messages"
                )
                return context

        except Exception as e:
            logger.error(f"Error loading context from persistence: {e}")
            return None

    async def _clear_from_persistence(self, session_id: str) -> None:
        """Clear context from database"""
        try:
            async for db in get_db():
                # Find and delete conversation
                stmt = select(Conversation).where(Conversation.session_id == session_id)
                result = await db.execute(stmt)
                conversation = result.scalar_one_or_none()

                if conversation:
                    # Delete messages (cascade should handle this)
                    await db.delete(conversation)

                    # Delete conversation session
                    session_stmt = select(ConversationSession).where(
                        ConversationSession.session_id == session_id
                    )
                    session_result = await db.execute(session_stmt)
                    session = session_result.scalar_one_or_none()
                    if session:
                        await db.delete(session)

                    await db.commit()
                    logger.debug(f"Cleared context for session {session_id}")

        except Exception as e:
            logger.error(f"Error clearing context from persistence: {e}")
            if "db" in locals():
                await db.rollback()

    async def _find_similar_context(self, session_id: str) -> MemoryContext | None:
        """Find similar context using semantic cache"""
        if not self._enable_semantic_cache:
            return None

        try:
            # Sprawdź bezpośrednio w _semantic_cache - może być też po hash
            if session_id in self._semantic_cache:
                return self._semantic_cache[session_id]

            # Sprawdź czy istnieje kontext o tym session_id i czy ma hash
            for context in self._semantic_cache.values():
                if hasattr(context, "session_id") and context.session_id == session_id:
                    return context

            # Potem próbuj przez cache_manager jeśli istnieje
            if self._cache_manager:
                similar_session_id = await self._cache_manager.find_similar_context(
                    session_id
                )
                if similar_session_id and similar_session_id in self._semantic_cache:
                    return self._semantic_cache[similar_session_id]
        except Exception as e:
            logger.error(f"Error finding similar context: {e}")

        return None

    async def _clear_from_semantic_cache(self, session_id: str) -> None:
        """Clear context from semantic cache"""
        if not self._cache_manager:
            return

        try:
            await self._cache_manager.remove_semantic_context(session_id)
        except Exception as e:
            logger.error(f"Error clearing from semantic cache: {e}")

    async def _cleanup_old_contexts(self) -> None:
        """Cleanup old contexts to prevent memory leaks"""
        try:
            valid_contexts = self._get_valid_contexts()

            if len(valid_contexts) > self._max_contexts * self._cleanup_threshold_ratio:
                # Remove oldest contexts
                sorted_contexts = sorted(valid_contexts, key=lambda c: c.last_updated)
                contexts_to_remove = sorted_contexts[
                    : len(valid_contexts) - self._max_contexts
                ]

                for context in contexts_to_remove:
                    await self.clear_context(context.session_id)

                self._stats["cleanup_count"] += 1
                self._stats["last_cleanup"] = datetime.now()
                logger.info(f"Cleaned up {len(contexts_to_remove)} old contexts")

            # USUŃ martwe referencje z _contexts
            dead_keys = [sid for sid, ref in self._contexts.items() if ref() is None]
            for sid in dead_keys:
                del self._contexts[sid]

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def register_agent_state(
        self,
        context: MemoryContext,
        agent_type: str,
        agent: BaseAgent,
        state: dict[str, Any],
    ) -> None:
        """Register agent state in context"""
        context.active_agents[agent_type] = {"agent": agent, "state": state}
        # Store agent state in context metadata
        context.agent_states[agent_type] = state
        logger.debug(
            f"Registered agent state for {agent_type} in session {context.session_id}"
        )

    async def get_all_contexts(self) -> dict[str, MemoryContext]:
        """Get all active contexts"""
        contexts = {}
        for session_id, weak_ref in self._contexts.items():
            context = weak_ref()
            if context:
                contexts[session_id] = context
        return contexts

    def _update_stats(self) -> None:
        """Update memory statistics"""
        valid_contexts = self._get_valid_contexts()
        # Update total_contexts
        self._stats["total_contexts"] = len(valid_contexts)

        if len(valid_contexts) > 0:
            total_messages = sum(len(c.history) for c in valid_contexts)
            total_optimized = sum(
                len(c.get_optimized_context()) for c in valid_contexts
            )
            if total_messages > 0:
                self._stats["compression_ratio"] = total_optimized / total_messages
            else:
                self._stats["compression_ratio"] = 1.0

        # Update cache hit rate if cache manager exists
        if self._cache_manager:
            self._stats["cache_hit_rate"] = self._cache_manager.get_hit_rate()

    def _get_valid_contexts(self) -> list[MemoryContext]:
        """Get list of valid contexts (not garbage collected)"""
        contexts = []
        for weak_ref in self._contexts.values():
            context = weak_ref()
            if context:
                contexts.append(context)
        return contexts

    async def get_context_stats(self) -> dict[str, Any]:
        """Get memory manager statistics"""
        self._update_stats()
        stats = self._stats.copy()
        stats["max_contexts"] = self._max_contexts
        stats["cleanup_threshold"] = self._cleanup_threshold
        logger.debug(
            f"get_context_stats called, total_contexts: {self._stats['total_contexts']}"
        )
        return stats

    async def cleanup_all(self) -> None:
        """Cleanup all contexts"""
        try:
            session_ids = list(self._contexts.keys())
            for session_id in session_ids:
                await self.clear_context(session_id)
            logger.info("Cleaned up all contexts")
        except Exception as e:
            logger.error(f"Error during full cleanup: {e}")

    @asynccontextmanager
    async def context_manager(self, session_id: str):
        """Context manager for automatic cleanup"""
        context = await self.get_context(session_id)
        try:
            yield context
        finally:
            await self.update_context(context)

    async def __aenter__(self) -> MemoryContext:
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit"""
        await self.cleanup_all()

    def get_memory_stats(self) -> "MemoryStats":
        """Get memory statistics"""
        return self._stats.copy()

    async def shutdown(self) -> None:
        """Shutdown memory manager"""
        await self.cleanup_all()
        logger.info("MemoryManager shutdown completed")
