"""
Multi-Agent Caching Framework with Intelligent Coordination
Zgodnie z regułami MDC dla optymalizacji cache'owania w systemach wieloagentowych
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any
import uuid

from core.cache_manager import CacheManager
from core.event_bus import AgentEvent, EventDrivenAgentCommunication, EventType

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels for multi-agent system"""

    LOCAL = "local"
    SHARED = "shared"
    DISTRIBUTED = "distributed"


class CacheStrategy(Enum):
    """Cache coordination strategies"""

    MASTER_SLAVE = "master_slave"
    VOTING = "voting"
    NEGOTIATION = "negotiation"
    CONSENSUS = "consensus"


class CacheEntry:
    """Cache entry with metadata"""

    def __init__(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        cache_level: CacheLevel = CacheLevel.LOCAL,
        created_by: str = "system",
    ):
        self.key = key
        self.value = value
        self.ttl = ttl
        self.cache_level = cache_level
        self.created_by = created_by
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.metadata = {}

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)

    def access(self) -> None:
        """Record cache access"""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "key": self.key,
            "value": self.value,
            "ttl": self.ttl,
            "cache_level": self.cache_level.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "metadata": self.metadata,
        }


class CacheVote:
    """Vote for cache coordination"""

    def __init__(
        self, agent_id: str, vote: bool, reason: str = "", confidence: float = 1.0
    ):
        self.agent_id = agent_id
        self.vote = vote
        self.reason = reason
        self.confidence = confidence
        self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "vote": self.vote,
            "reason": self.reason,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class MultiAgentCacheManager:
    """Advanced cache manager for multi-agent systems"""

    def __init__(
        self, agent_id: str, coordination_strategy: CacheStrategy = CacheStrategy.VOTING
    ):
        self.agent_id = agent_id
        self.coordination_strategy = coordination_strategy

        # Cache storage by level
        self.local_cache: dict[str, CacheEntry] = {}
        self.shared_cache: dict[str, CacheEntry] = {}

        # Cache manager for Redis
        self.cache_manager = CacheManager()

        # Event communication
        self.event_communication = EventDrivenAgentCommunication(agent_id)

        # Coordination state
        self.pending_votes: dict[str, list[CacheVote]] = defaultdict(list)
        self.vote_timeouts: dict[str, asyncio.Task] = {}
        self.negotiation_sessions: dict[str, dict[str, Any]] = {}

        # Statistics
        self.cache_stats = {
            "local_hits": 0,
            "local_misses": 0,
            "shared_hits": 0,
            "shared_misses": 0,
            "coordination_events": 0,
            "votes_cast": 0,
            "negotiations": 0,
        }

        # Configuration
        self.max_local_cache_size = 1000
        self.max_shared_cache_size = 5000
        self.vote_timeout = 30.0  # seconds
        self.negotiation_timeout = 60.0  # seconds

        logger.info(f"MultiAgentCacheManager initialized for agent {agent_id}")

    async def initialize(self):
        """Initialize the cache manager"""
        # Connect to Redis
        await self.cache_manager.connect()

        # Subscribe to cache events
        await self.event_communication.subscribe_to_events(
            [
                EventType.CACHE_UPDATE.value,
                "cache_vote_request",
                "cache_vote_response",
                "cache_negotiation_request",
                "cache_negotiation_response",
            ],
            self._handle_cache_event,
        )

        logger.info(f"MultiAgentCacheManager {self.agent_id} initialized")

    async def shutdown(self):
        """Shutdown the cache manager"""
        await self.cache_manager.disconnect()

        # Cancel pending timeouts
        for task in self.vote_timeouts.values():
            task.cancel()

        logger.info(f"MultiAgentCacheManager {self.agent_id} shutdown")

    async def get(
        self, key: str, cache_level: CacheLevel = CacheLevel.LOCAL
    ) -> Any | None:
        """Get value from cache"""
        try:
            if cache_level == CacheLevel.LOCAL:
                return await self._get_local(key)
            if cache_level == CacheLevel.SHARED:
                return await self._get_shared(key)
            if cache_level == CacheLevel.DISTRIBUTED:
                return await self._get_distributed(key)
            return None

        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        cache_level: CacheLevel = CacheLevel.LOCAL,
    ) -> bool:
        """Set value in cache"""
        try:
            if cache_level == CacheLevel.LOCAL:
                return await self._set_local(key, value, ttl)
            if cache_level == CacheLevel.SHARED:
                return await self._set_shared(key, value, ttl)
            if cache_level == CacheLevel.DISTRIBUTED:
                return await self._set_distributed(key, value, ttl)
            return False

        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def _get_local(self, key: str) -> Any | None:
        """Get from local cache"""
        if key in self.local_cache:
            entry = self.local_cache[key]
            if not entry.is_expired():
                entry.access()
                self.cache_stats["local_hits"] += 1
                logger.debug(f"Local cache HIT: {key}")
                return entry.value
            del self.local_cache[key]

        self.cache_stats["local_misses"] += 1
        logger.debug(f"Local cache MISS: {key}")
        return None

    async def _set_local(self, key: str, value: Any, ttl: int) -> bool:
        """Set in local cache"""
        try:
            # Check cache size limit
            if len(self.local_cache) >= self.max_local_cache_size:
                await self._evict_local_cache()

            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                cache_level=CacheLevel.LOCAL,
                created_by=self.agent_id,
            )

            self.local_cache[key] = entry
            logger.debug(f"Local cache SET: {key}")
            return True

        except Exception as e:
            logger.error(f"Error setting local cache: {e}")
            return False

    async def _get_shared(self, key: str) -> Any | None:
        """Get from shared cache (Redis)"""
        try:
            value = await self.cache_manager.get(key)
            if value is not None:
                self.cache_stats["shared_hits"] += 1
                logger.debug(f"Shared cache HIT: {key}")
                return value
            self.cache_stats["shared_misses"] += 1
            logger.debug(f"Shared cache MISS: {key}")
            return None

        except Exception as e:
            logger.error(f"Error getting from shared cache: {e}")
            return None

    async def _set_shared(self, key: str, value: Any, ttl: int) -> bool:
        """Set in shared cache (Redis)"""
        try:
            success = await self.cache_manager.set(key, value, ttl)
            if success:
                logger.debug(f"Shared cache SET: {key}")
            return success

        except Exception as e:
            logger.error(f"Error setting shared cache: {e}")
            return False

    async def _get_distributed(self, key: str) -> Any | None:
        """Get from distributed cache with coordination"""
        # First try local cache
        local_value = await self._get_local(key)
        if local_value is not None:
            return local_value

        # Then try shared cache
        shared_value = await self._get_shared(key)
        if shared_value is not None:
            # Cache locally for future access
            await self._set_local(key, shared_value, 1800)  # 30 minutes
            return shared_value

        # Request from other agents
        return await self._request_from_agents(key)

    async def _set_distributed(self, key: str, value: Any, ttl: int) -> bool:
        """Set in distributed cache with coordination"""
        # Always set locally
        await self._set_local(key, value, ttl)

        # Coordinate with other agents for shared cache
        if self.coordination_strategy == CacheStrategy.VOTING:
            return await self._coordinate_with_voting(key, value, ttl)
        if self.coordination_strategy == CacheStrategy.NEGOTIATION:
            return await self._coordinate_with_negotiation(key, value, ttl)
        # Default: set in shared cache
        return await self._set_shared(key, value, ttl)

    async def _coordinate_with_voting(self, key: str, value: Any, ttl: int) -> bool:
        """Coordinate cache setting using voting"""
        vote_id = str(uuid.uuid4())

        # Create vote request
        vote_request = {
            "vote_id": vote_id,
            "key": key,
            "value": value,
            "ttl": ttl,
            "requester": self.agent_id,
            "timestamp": datetime.now().isoformat(),
        }

        # Publish vote request
        await self.event_communication.publish_event(
            "cache_vote_request", vote_request, priority=EventPriority.HIGH
        )

        # Start vote timeout
        self.vote_timeouts[vote_id] = asyncio.create_task(
            self._vote_timeout_handler(vote_id)
        )

        self.cache_stats["coordination_events"] += 1
        logger.debug(f"Vote request sent for cache key: {key}")

        return True  # Return immediately, result will be handled asynchronously

    async def _coordinate_with_negotiation(
        self, key: str, value: Any, ttl: int
    ) -> bool:
        """Coordinate cache setting using negotiation"""
        negotiation_id = str(uuid.uuid4())

        # Create negotiation session
        self.negotiation_sessions[negotiation_id] = {
            "key": key,
            "value": value,
            "ttl": ttl,
            "participants": set(),
            "responses": {},
            "start_time": datetime.now(),
        }

        # Send negotiation request
        negotiation_request = {
            "negotiation_id": negotiation_id,
            "key": key,
            "value": value,
            "ttl": ttl,
            "initiator": self.agent_id,
            "timestamp": datetime.now().isoformat(),
        }

        await self.event_communication.publish_event(
            "cache_negotiation_request",
            negotiation_request,
            priority=EventPriority.HIGH,
        )

        self.cache_stats["negotiations"] += 1
        logger.debug(f"Negotiation started for cache key: {key}")

        return True

    async def _request_from_agents(self, key: str) -> Any | None:
        """Request cache value from other agents"""
        request_id = str(uuid.uuid4())

        # Create request
        request = {
            "request_id": request_id,
            "key": key,
            "requester": self.agent_id,
            "timestamp": datetime.now().isoformat(),
        }

        # Publish request
        await self.event_communication.publish_event(
            "cache_value_request", request, priority=EventPriority.HIGH
        )

        # Wait for response (with timeout)
        try:
            response = await asyncio.wait_for(
                self._wait_for_cache_response(request_id), timeout=10.0
            )
            return response
        except TimeoutError:
            logger.warning(f"Cache value request timeout for key: {key}")
            return None

    async def _wait_for_cache_response(self, request_id: str) -> Any | None:
        """Wait for cache response from other agents"""
        # This is a simplified implementation
        # In a full implementation, you would use a proper response tracking mechanism
        await asyncio.sleep(0.1)  # Small delay to allow for response
        return None

    async def _vote_timeout_handler(self, vote_id: str):
        """Handle vote timeout"""
        await asyncio.sleep(self.vote_timeout)

        if vote_id in self.pending_votes:
            votes = self.pending_votes[vote_id]

            # Count votes
            approve_votes = sum(1 for vote in votes if vote.vote)
            total_votes = len(votes)

            # Simple majority rule
            if total_votes > 0 and approve_votes > total_votes / 2:
                logger.info(
                    f"Vote approved for {vote_id} ({approve_votes}/{total_votes})"
                )
                # Set in shared cache
                # Note: In a full implementation, you would get the original request data
            else:
                logger.info(
                    f"Vote rejected for {vote_id} ({approve_votes}/{total_votes})"
                )

            # Cleanup
            del self.pending_votes[vote_id]
            if vote_id in self.vote_timeouts:
                del self.vote_timeouts[vote_id]

    async def _handle_cache_event(self, event: AgentEvent):
        """Handle cache-related events"""
        try:
            if event.type == "cache_vote_request":
                await self._handle_vote_request(event)
            elif event.type == "cache_vote_response":
                await self._handle_vote_response(event)
            elif event.type == "cache_negotiation_request":
                await self._handle_negotiation_request(event)
            elif event.type == "cache_negotiation_response":
                await self._handle_negotiation_response(event)
            elif event.type == "cache_value_request":
                await self._handle_value_request(event)
            elif event.type == EventType.CACHE_UPDATE.value:
                await self._handle_cache_update(event)

        except Exception as e:
            logger.error(f"Error handling cache event: {e}")

    async def _handle_vote_request(self, event: AgentEvent):
        """Handle cache vote request"""
        payload = event.payload
        vote_id = payload.get("vote_id")
        key = payload.get("key")

        if not vote_id or not key:
            return

        # Simple voting logic: vote yes if we don't have the key or if it's older
        should_vote_yes = True
        reason = "No existing cache entry"

        if key in self.local_cache:
            entry = self.local_cache[key]
            if not entry.is_expired():
                # Vote no if we have a recent entry
                should_vote_yes = False
                reason = "Recent local cache entry exists"

        # Create vote
        vote = CacheVote(
            agent_id=self.agent_id,
            vote=should_vote_yes,
            reason=reason,
            confidence=0.8 if should_vote_yes else 0.9,
        )

        # Send vote response
        vote_response = {
            "vote_id": vote_id,
            "vote": vote.to_dict(),
            "responder": self.agent_id,
        }

        await self.event_communication.publish_event(
            "cache_vote_response", vote_response, target=payload.get("requester")
        )

        self.cache_stats["votes_cast"] += 1
        logger.debug(f"Vote cast for {vote_id}: {should_vote_yes}")

    async def _handle_vote_response(self, event: AgentEvent):
        """Handle cache vote response"""
        payload = event.payload
        vote_id = payload.get("vote_id")
        vote_data = payload.get("vote")

        if not vote_id or not vote_data:
            return

        # Add vote to pending votes
        vote = CacheVote(
            agent_id=vote_data["agent_id"],
            vote=vote_data["vote"],
            reason=vote_data["reason"],
            confidence=vote_data["confidence"],
        )

        self.pending_votes[vote_id].append(vote)
        logger.debug(f"Vote received for {vote_id} from {vote.agent_id}")

    async def _handle_negotiation_request(self, event: AgentEvent):
        """Handle cache negotiation request"""
        payload = event.payload
        negotiation_id = payload.get("negotiation_id")
        key = payload.get("key")

        if not negotiation_id or not key:
            return

        # Simple negotiation logic
        response = {
            "negotiation_id": negotiation_id,
            "agent_id": self.agent_id,
            "approved": True,
            "reason": "Cache space available",
            "suggested_ttl": payload.get("ttl", 3600),
        }

        await self.event_communication.publish_event(
            "cache_negotiation_response", response, target=payload.get("initiator")
        )

        logger.debug(f"Negotiation response sent for {negotiation_id}")

    async def _handle_negotiation_response(self, event: AgentEvent):
        """Handle cache negotiation response"""
        payload = event.payload
        negotiation_id = payload.get("negotiation_id")

        if negotiation_id not in self.negotiation_sessions:
            return

        session = self.negotiation_sessions[negotiation_id]
        agent_id = payload.get("agent_id")

        session["participants"].add(agent_id)
        session["responses"][agent_id] = payload

        # Check if we have enough responses
        if len(session["responses"]) >= 3:  # Minimum 3 agents
            await self._finalize_negotiation(negotiation_id)

    async def _handle_value_request(self, event: AgentEvent):
        """Handle cache value request from other agents"""
        payload = event.payload
        request_id = payload.get("request_id")
        key = payload.get("key")
        requester = payload.get("requester")

        if not request_id or not key or not requester:
            return

        # Check if we have the value
        value = await self._get_local(key)
        if value is not None:
            response = {
                "request_id": request_id,
                "key": key,
                "value": value,
                "provider": self.agent_id,
                "timestamp": datetime.now().isoformat(),
            }

            await self.event_communication.publish_event(
                "cache_value_response", response, target=requester
            )

            logger.debug(f"Cache value provided for {key} to {requester}")

    async def _handle_cache_update(self, event: AgentEvent):
        """Handle cache update event"""
        payload = event.payload
        key = payload.get("key")
        value = payload.get("value")
        ttl = payload.get("ttl", 3600)

        if key and value:
            # Update local cache
            await self._set_local(key, value, ttl)
            logger.debug(f"Cache updated from event: {key}")

    async def _finalize_negotiation(self, negotiation_id: str):
        """Finalize negotiation and set cache"""
        session = self.negotiation_sessions[negotiation_id]

        # Count approvals
        approvals = sum(
            1
            for response in session["responses"].values()
            if response.get("approved", False)
        )

        if approvals > len(session["responses"]) / 2:
            # Set in shared cache
            await self._set_shared(session["key"], session["value"], session["ttl"])
            logger.info(f"Negotiation approved for {session['key']}")
        else:
            logger.info(f"Negotiation rejected for {session['key']}")

        # Cleanup
        del self.negotiation_sessions[negotiation_id]

    async def _evict_local_cache(self):
        """Evict entries from local cache"""
        if not self.local_cache:
            return

        # Simple LRU eviction
        entries = list(self.local_cache.items())
        entries.sort(key=lambda x: x[1].last_accessed)

        # Remove 10% of entries
        to_remove = max(1, len(entries) // 10)
        for key, _ in entries[:to_remove]:
            del self.local_cache[key]

        logger.debug(f"Evicted {to_remove} entries from local cache")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        local_hit_rate = 0.0
        shared_hit_rate = 0.0

        if self.cache_stats["local_hits"] + self.cache_stats["local_misses"] > 0:
            local_hit_rate = (
                self.cache_stats["local_hits"]
                / (self.cache_stats["local_hits"] + self.cache_stats["local_misses"])
            ) * 100

        if self.cache_stats["shared_hits"] + self.cache_stats["shared_misses"] > 0:
            shared_hit_rate = (
                self.cache_stats["shared_hits"]
                / (self.cache_stats["shared_hits"] + self.cache_stats["shared_misses"])
            ) * 100

        return {
            "agent_id": self.agent_id,
            "coordination_strategy": self.coordination_strategy.value,
            "local_cache_size": len(self.local_cache),
            "shared_cache_connected": self.cache_manager.is_connected,
            "local_hit_rate": round(local_hit_rate, 2),
            "shared_hit_rate": round(shared_hit_rate, 2),
            "coordination_events": self.cache_stats["coordination_events"],
            "votes_cast": self.cache_stats["votes_cast"],
            "negotiations": self.cache_stats["negotiations"],
            "pending_votes": len(self.pending_votes),
            "active_negotiations": len(self.negotiation_sessions),
        }

    async def clear_cache(self, cache_level: CacheLevel = CacheLevel.LOCAL):
        """Clear cache at specified level"""
        if cache_level == CacheLevel.LOCAL:
            self.local_cache.clear()
            logger.info("Local cache cleared")
        elif cache_level == CacheLevel.SHARED:
            # Clear Redis cache (this would need pattern-based clearing)
            logger.info("Shared cache clear requested")
        elif cache_level == CacheLevel.DISTRIBUTED:
            self.local_cache.clear()
            # Notify other agents
            await self.event_communication.publish_event(
                EventType.CACHE_UPDATE.value,
                {"action": "clear_all", "source": self.agent_id},
            )
            logger.info("Distributed cache clear requested")


# Global cache manager instance
multi_agent_cache = MultiAgentCacheManager("system_cache")
