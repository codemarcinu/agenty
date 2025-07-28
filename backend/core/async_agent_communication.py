"""
Asynchronous Agent Communication System for FoodSave AI

This module implements advanced asynchronous communication patterns between agents
including pub-sub messaging, event streaming, and parallel processing capabilities.
"""

import asyncio
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import time
from typing import Any, Generic, TypeVar
import uuid
import weakref

try:
    import redis.asyncio as redis
    from redis.asyncio.client import Redis as RedisClient

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    RedisClient = None

from settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MessageType(Enum):
    """Types of messages in the system"""

    COMMAND = "command"
    EVENT = "event"
    QUERY = "query"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"


class Priority(Enum):
    """Message priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    """Message structure for agent communication"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.COMMAND
    priority: Priority = Priority.NORMAL
    source_agent: str = ""
    target_agent: str | None = None
    channel: str = "default"
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int | None = None  # Time to live in seconds
    correlation_id: str | None = None
    reply_to: str | None = None
    retries: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "channel": self.channel,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "retries": self.retries,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary"""
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            priority=Priority(data["priority"]),
            source_agent=data["source_agent"],
            target_agent=data.get("target_agent"),
            channel=data["channel"],
            data=data["data"],
            metadata=data["metadata"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl=data.get("ttl"),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            retries=data.get("retries", 0),
            max_retries=data.get("max_retries", 3),
        )

    def is_expired(self) -> bool:
        """Check if message has expired"""
        if self.ttl is None:
            return False
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl


class EventEmitter(Generic[T]):
    """Advanced event emitter with weak references and async support"""

    def __init__(self):
        self._listeners: dict[str, list[weakref.ref]] = defaultdict(list)
        self._once_listeners: dict[str, list[weakref.ref]] = defaultdict(list)
        self._max_listeners = 50

    def on(self, event: str, callback: Callable) -> None:
        """Register event listener"""
        if len(self._listeners[event]) >= self._max_listeners:
            logger.warning(
                f"Max listeners ({self._max_listeners}) reached for event: {event}"
            )
            return

        self._listeners[event].append(weakref.ref(callback))

    def once(self, event: str, callback: Callable) -> None:
        """Register one-time event listener"""
        self._once_listeners[event].append(weakref.ref(callback))

    def off(self, event: str, callback: Callable) -> None:
        """Remove event listener"""
        callback_ref = weakref.ref(callback)
        self._listeners[event] = [
            ref for ref in self._listeners[event] if ref != callback_ref
        ]
        self._once_listeners[event] = [
            ref for ref in self._once_listeners[event] if ref != callback_ref
        ]

    async def emit(self, event: str, *args, **kwargs) -> list[Any]:
        """Emit event to all listeners"""
        results = []

        # Clean up dead references
        self._cleanup_dead_refs(event)

        # Call regular listeners
        for ref in self._listeners[event][
            :
        ]:  # Copy list to avoid modification during iteration
            callback = ref()
            if callback is not None:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        result = await callback(*args, **kwargs)
                    else:
                        result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in event listener for {event}: {e}")

        # Call once listeners and remove them
        for ref in self._once_listeners[event][:]:
            callback = ref()
            if callback is not None:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        result = await callback(*args, **kwargs)
                    else:
                        result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in once event listener for {event}: {e}")

        self._once_listeners[event].clear()

        return results

    def _cleanup_dead_refs(self, event: str) -> None:
        """Remove dead weak references"""
        self._listeners[event] = [
            ref for ref in self._listeners[event] if ref() is not None
        ]
        self._once_listeners[event] = [
            ref for ref in self._once_listeners[event] if ref() is not None
        ]


class AsyncMessageQueue:
    """High-performance async message queue with priority support"""

    def __init__(self, name: str, max_size: int = 10000):
        self.name = name
        self.max_size = max_size
        self._queues: dict[Priority, asyncio.Queue] = {
            Priority.CRITICAL: asyncio.Queue(maxsize=max_size // 10),
            Priority.HIGH: asyncio.Queue(maxsize=max_size // 4),
            Priority.NORMAL: asyncio.Queue(maxsize=max_size // 2),
            Priority.LOW: asyncio.Queue(maxsize=max_size // 4),
        }
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_dropped": 0,
            "total_processing_time": 0.0,
        }
        self._processing = False

    async def put(self, message: AgentMessage) -> bool:
        """Put message in queue with priority handling"""
        try:
            queue = self._queues[message.priority]
            if queue.full():
                # Drop lowest priority message if queue is full
                if message.priority in [Priority.CRITICAL, Priority.HIGH]:
                    await self._drop_lowest_priority_message()
                else:
                    self._stats["messages_dropped"] += 1
                    logger.warning(f"Dropped message {message.id} due to full queue")
                    return False

            await queue.put(message)
            self._stats["messages_sent"] += 1
            return True

        except Exception as e:
            logger.error(f"Error putting message in queue {self.name}: {e}")
            return False

    async def get(self, timeout: float | None = None) -> AgentMessage | None:
        """Get message from queue with priority ordering"""
        start_time = time.time()

        try:
            # Check queues in priority order
            for priority in [
                Priority.CRITICAL,
                Priority.HIGH,
                Priority.NORMAL,
                Priority.LOW,
            ]:
                queue = self._queues[priority]
                try:
                    message = queue.get_nowait()
                    self._stats["messages_received"] += 1
                    self._stats["total_processing_time"] += time.time() - start_time
                    return message
                except asyncio.QueueEmpty:
                    continue

            # If no messages available, wait for any message
            if timeout is not None:
                try:
                    # Wait for first available message with timeout
                    done, pending = await asyncio.wait_for(
                        asyncio.wait(
                            [
                                asyncio.create_task(queue.get())
                                for queue in self._queues.values()
                            ],
                            return_when=asyncio.FIRST_COMPLETED,
                        ),
                        timeout=timeout,
                    )

                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()

                    if done:
                        message = done.pop().result()
                        self._stats["messages_received"] += 1
                        self._stats["total_processing_time"] += time.time() - start_time
                        return message

                except TimeoutError:
                    return None

            return None

        except Exception as e:
            logger.error(f"Error getting message from queue {self.name}: {e}")
            return None

    async def _drop_lowest_priority_message(self) -> None:
        """Drop lowest priority message to make room"""
        for priority in [Priority.LOW, Priority.NORMAL, Priority.HIGH]:
            queue = self._queues[priority]
            try:
                dropped_msg = queue.get_nowait()
                self._stats["messages_dropped"] += 1
                logger.warning(
                    f"Dropped low priority message {dropped_msg.id} to make room"
                )
                return
            except asyncio.QueueEmpty:
                continue

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics"""
        total_size = sum(queue.qsize() for queue in self._queues.values())
        avg_processing_time = (
            self._stats["total_processing_time"] / self._stats["messages_received"]
            if self._stats["messages_received"] > 0
            else 0
        )

        return {
            "name": self.name,
            "total_size": total_size,
            "queue_sizes": {
                priority.name: queue.qsize() for priority, queue in self._queues.items()
            },
            "stats": self._stats,
            "avg_processing_time": avg_processing_time,
            "max_size": self.max_size,
        }


class AsyncAgentCommunicator:
    """Advanced asynchronous agent communication system"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.redis_client: RedisClient | None = None
        self.is_connected = False

        # Message queues
        self.incoming_queue = AsyncMessageQueue(f"{agent_id}_incoming")
        self.outgoing_queue = AsyncMessageQueue(f"{agent_id}_outgoing")

        # Event system
        self.events = EventEmitter[AgentMessage]()

        # Subscriptions and channels
        self.subscriptions: set[str] = set()
        self.private_channel = f"agent:{agent_id}"

        # Message handlers
        self.message_handlers: dict[MessageType, Callable] = {}

        # Processing tasks
        self._processing_tasks: list[asyncio.Task] = []
        self._running = False

        # Circuit breaker for Redis operations
        self._redis_failures = 0
        self._redis_circuit_open = False
        self._last_redis_failure = None

        logger.info(f"Initialized AsyncAgentCommunicator for agent: {agent_id}")

    async def connect(self) -> bool:
        """Connect to Redis for distributed messaging"""
        try:
            if not REDIS_AVAILABLE or not settings.REDIS_USE_CACHE:
                logger.warning("Redis not available - using local messaging only")
                return False

            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            await self.redis_client.ping()
            self.is_connected = True

            # Subscribe to private channel
            await self.subscribe(self.private_channel)

            logger.info(f"Agent {self.agent_id} connected to Redis messaging")
            return True

        except Exception as e:
            logger.error(f"Failed to connect agent {self.agent_id} to Redis: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis and cleanup"""
        self._running = False

        # Cancel processing tasks
        for task in self._processing_tasks:
            task.cancel()

        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)

        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False

        logger.info(f"Agent {self.agent_id} disconnected from messaging")

    async def start_processing(self) -> None:
        """Start message processing tasks"""
        if self._running:
            return

        self._running = True

        # Start processing tasks
        self._processing_tasks = [
            asyncio.create_task(self._process_outgoing_messages()),
            asyncio.create_task(self._process_incoming_messages()),
            asyncio.create_task(self._heartbeat_task()),
            asyncio.create_task(self._cleanup_task()),
        ]

        if self.is_connected:
            self._processing_tasks.append(asyncio.create_task(self._redis_listener()))

        logger.info(f"Started message processing for agent {self.agent_id}")

    async def send_message(
        self,
        message: AgentMessage,
        wait_for_response: bool = False,
        timeout: float = 30.0,
    ) -> AgentMessage | None:
        """Send message to another agent"""
        message.source_agent = self.agent_id

        if wait_for_response:
            # Generate correlation ID for response tracking
            message.correlation_id = str(uuid.uuid4())
            message.reply_to = self.private_channel

            # Create future for response
            response_future = asyncio.Future()

            # Register response handler
            def response_handler(response_msg: AgentMessage):
                if response_msg.correlation_id == message.correlation_id:
                    response_future.set_result(response_msg)

            self.events.once(f"response:{message.correlation_id}", response_handler)

        # Queue message for sending
        await self.outgoing_queue.put(message)

        if wait_for_response:
            try:
                return await asyncio.wait_for(response_future, timeout=timeout)
            except TimeoutError:
                logger.warning(f"Timeout waiting for response to message {message.id}")
                return None

        return None

    async def send_response(
        self, original_message: AgentMessage, response_data: dict[str, Any]
    ) -> None:
        """Send response to a message"""
        if not original_message.reply_to or not original_message.correlation_id:
            logger.warning("Cannot send response - missing reply_to or correlation_id")
            return

        response = AgentMessage(
            type=MessageType.RESPONSE,
            source_agent=self.agent_id,
            channel=original_message.reply_to,
            data=response_data,
            correlation_id=original_message.correlation_id,
        )

        await self.outgoing_queue.put(response)

    async def broadcast_message(self, channel: str, data: dict[str, Any]) -> None:
        """Broadcast message to all subscribers of a channel"""
        message = AgentMessage(
            type=MessageType.BROADCAST,
            source_agent=self.agent_id,
            channel=channel,
            data=data,
        )

        await self.outgoing_queue.put(message)

    async def subscribe(self, channel: str) -> None:
        """Subscribe to a channel"""
        self.subscriptions.add(channel)

        if self.is_connected and self.redis_client:
            try:
                pubsub = self.redis_client.pubsub()
                await pubsub.subscribe(channel)
                logger.info(f"Agent {self.agent_id} subscribed to channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to subscribe to channel {channel}: {e}")

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel"""
        self.subscriptions.discard(channel)

        if self.is_connected and self.redis_client:
            try:
                pubsub = self.redis_client.pubsub()
                await pubsub.unsubscribe(channel)
                logger.info(
                    f"Agent {self.agent_id} unsubscribed from channel: {channel}"
                )
            except Exception as e:
                logger.error(f"Failed to unsubscribe from channel {channel}: {e}")

    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register message handler for specific message type"""
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type} in agent {self.agent_id}")

    async def _process_outgoing_messages(self) -> None:
        """Process outgoing message queue"""
        while self._running:
            try:
                message = await self.outgoing_queue.get(timeout=1.0)
                if message:
                    await self._send_message_via_redis(message)
            except Exception as e:
                logger.error(f"Error processing outgoing messages: {e}")
                await asyncio.sleep(1.0)

    async def _process_incoming_messages(self) -> None:
        """Process incoming message queue"""
        while self._running:
            try:
                message = await self.incoming_queue.get(timeout=1.0)
                if message:
                    await self._handle_message(message)
            except Exception as e:
                logger.error(f"Error processing incoming messages: {e}")
                await asyncio.sleep(1.0)

    async def _send_message_via_redis(self, message: AgentMessage) -> None:
        """Send message via Redis"""
        if not self.is_connected or not self.redis_client or self._redis_circuit_open:
            logger.debug(f"Redis unavailable - message {message.id} queued locally")
            return

        try:
            # Serialize message
            message_data = json.dumps(message.to_dict())

            if message.target_agent:
                # Direct message to specific agent
                channel = f"agent:{message.target_agent}"
            else:
                # Broadcast message
                channel = message.channel

            await self.redis_client.publish(channel, message_data)
            logger.debug(f"Sent message {message.id} to channel {channel}")

            # Reset circuit breaker on success
            self._redis_failures = 0
            self._redis_circuit_open = False

        except Exception as e:
            logger.error(f"Failed to send message via Redis: {e}")
            self._redis_failures += 1
            self._last_redis_failure = datetime.now()

            # Open circuit breaker after 3 failures
            if self._redis_failures >= 3:
                self._redis_circuit_open = True
                logger.warning("Redis circuit breaker opened due to repeated failures")

    async def _redis_listener(self) -> None:
        """Listen for Redis messages"""
        if not self.is_connected or not self.redis_client:
            return

        try:
            pubsub = self.redis_client.pubsub()

            # Subscribe to all relevant channels
            channels = list(self.subscriptions)
            if channels:
                await pubsub.subscribe(*channels)

            while self._running:
                try:
                    redis_message = await pubsub.get_message(timeout=1.0)
                    if redis_message and redis_message["type"] == "message":
                        try:
                            message_data = json.loads(redis_message["data"])
                            message = AgentMessage.from_dict(message_data)
                            await self.incoming_queue.put(message)
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.error(f"Failed to parse Redis message: {e}")
                except Exception as e:
                    logger.error(f"Error in Redis listener: {e}")
                    await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"Redis listener error: {e}")
        finally:
            if "pubsub" in locals():
                await pubsub.close()

    async def _handle_message(self, message: AgentMessage) -> None:
        """Handle incoming message"""
        try:
            # Check if message is expired
            if message.is_expired():
                logger.debug(f"Dropped expired message {message.id}")
                return

            # Emit event for message
            await self.events.emit(f"message:{message.type.value}", message)

            # Handle response messages specially
            if message.type == MessageType.RESPONSE and message.correlation_id:
                await self.events.emit(f"response:{message.correlation_id}", message)
                return

            # Call registered handler
            handler = self.message_handlers.get(message.type)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            else:
                logger.debug(f"No handler registered for message type {message.type}")

        except Exception as e:
            logger.error(f"Error handling message {message.id}: {e}")

    async def _heartbeat_task(self) -> None:
        """Send periodic heartbeat messages"""
        while self._running:
            try:
                heartbeat = AgentMessage(
                    type=MessageType.HEARTBEAT,
                    source_agent=self.agent_id,
                    channel="system.heartbeat",
                    data={"timestamp": datetime.now().isoformat(), "status": "alive"},
                )

                await self.outgoing_queue.put(heartbeat)
                await asyncio.sleep(30)  # Heartbeat every 30 seconds

            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(30)

    async def _cleanup_task(self) -> None:
        """Periodic cleanup of expired messages and stats"""
        while self._running:
            try:
                # Reset circuit breaker if enough time has passed
                if (
                    self._redis_circuit_open
                    and self._last_redis_failure
                    and datetime.now() - self._last_redis_failure > timedelta(minutes=5)
                ):
                    self._redis_circuit_open = False
                    self._redis_failures = 0
                    logger.info("Redis circuit breaker reset")

                await asyncio.sleep(60)  # Cleanup every minute

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

    def get_stats(self) -> dict[str, Any]:
        """Get communication statistics"""
        return {
            "agent_id": self.agent_id,
            "is_connected": self.is_connected,
            "subscriptions": list(self.subscriptions),
            "incoming_queue": self.incoming_queue.get_stats(),
            "outgoing_queue": self.outgoing_queue.get_stats(),
            "redis_stats": {
                "failures": self._redis_failures,
                "circuit_open": self._redis_circuit_open,
                "last_failure": (
                    self._last_redis_failure.isoformat()
                    if self._last_redis_failure
                    else None
                ),
            },
            "running": self._running,
            "active_tasks": len(
                [task for task in self._processing_tasks if not task.done()]
            ),
        }
