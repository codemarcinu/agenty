"""Event-Driven Communication System for Multi-Agent Architecture"""

import asyncio
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for agent communication"""

    AGENT_STATE_CHANGE = "agent_state_change"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    RESOURCE_UPDATE = "resource_update"
    CACHE_UPDATE = "cache_update"
    ERROR_EVENT = "error_event"
    PERFORMANCE_ALERT = "performance_alert"
    SYSTEM_HEALTH = "system_health"
    USER_INPUT = "user_input"
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    COORDINATION_EVENT = "coordination_event"


class EventPriority(Enum):
    """Event priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentEvent:
    """Event for agent communication"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.SYSTEM_HEALTH
    source: str = ""
    target: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None
    reply_to: str | None = None
    ttl: float | None = None  # Time to live in seconds
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if event is expired"""
        if self.ttl is None:
            return False
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "target": self.target,
            "data": self.data,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "ttl": self.ttl,
            "metadata": self.metadata,
        }


@dataclass
class EventSubscription:
    """Event subscription configuration"""

    agent_id: str
    event_types: list[EventType]
    handler: Callable
    priority: EventPriority = EventPriority.NORMAL
    filters: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class PriorityEventQueue:
    """Priority queue for events"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues: dict[EventPriority, deque] = {
            EventPriority.LOW: deque(maxlen=max_size // 4),
            EventPriority.NORMAL: deque(maxlen=max_size // 2),
            EventPriority.HIGH: deque(maxlen=max_size // 4),
            EventPriority.CRITICAL: deque(maxlen=max_size // 4),
        }
        self._lock = asyncio.Lock()

    async def put(self, event: AgentEvent) -> bool:
        """Add event to queue"""
        async with self._lock:
            if self._is_full():
                # Remove lowest priority event if queue is full
                self._remove_lowest_priority()

            self.queues[event.priority].append(event)
            return True

    async def get(self) -> AgentEvent | None:
        """Get highest priority event"""
        async with self._lock:
            # Check queues in priority order
            for priority in [
                EventPriority.CRITICAL,
                EventPriority.HIGH,
                EventPriority.NORMAL,
                EventPriority.LOW,
            ]:
                if self.queues[priority]:
                    return self.queues[priority].popleft()
            return None

    def _is_full(self) -> bool:
        """Check if queue is full"""
        total_size = sum(len(queue) for queue in self.queues.values())
        return total_size >= self.max_size

    def _remove_lowest_priority(self) -> None:
        """Remove lowest priority event"""
        for priority in [
            EventPriority.LOW,
            EventPriority.NORMAL,
            EventPriority.HIGH,
            EventPriority.CRITICAL,
        ]:
            if self.queues[priority]:
                self.queues[priority].popleft()
                break

    def size(self) -> int:
        """Get total queue size"""
        return sum(len(queue) for queue in self.queues.values())


class EventDrivenAgentCommunication:
    """Event-driven communication system for agents"""

    def __init__(self, agent_id: str, max_queue_size: int = 10000):
        self.agent_id = agent_id

        # Event queues
        self.incoming_queue = PriorityEventQueue(max_queue_size)
        self.outgoing_queue = PriorityEventQueue(max_queue_size)

        # Subscriptions
        self.subscriptions: dict[str, EventSubscription] = {}
        self.event_handlers: dict[EventType, list[EventSubscription]] = defaultdict(
            list
        )

        # Request-response tracking
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.request_timeouts: dict[str, asyncio.Task] = {}

        # Performance metrics
        self.metrics = {
            "events_sent": 0,
            "events_received": 0,
            "requests_sent": 0,
            "responses_received": 0,
            "avg_processing_time": 0.0,
            "queue_size": 0,
        }

        # Background tasks
        self.event_processor_task: asyncio.Task | None = None
        self.cleanup_task: asyncio.Task | None = None

        # Configuration
        self.default_request_timeout = 30.0  # seconds
        self.cleanup_interval = 60.0  # seconds

        logger.info(f"EventDrivenAgentCommunication initialized for agent {agent_id}")

    async def initialize(self):
        """Initialize the communication system"""
        # Start background tasks
        self.event_processor_task = asyncio.create_task(self._process_events())
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_events())

        logger.info(f"EventDrivenAgentCommunication {self.agent_id} initialized")

    async def shutdown(self):
        """Shutdown the communication system"""
        if self.event_processor_task:
            self.event_processor_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        # Cancel pending requests
        for future in self.pending_requests.values():
            future.cancel()

        logger.info(f"EventDrivenAgentCommunication {self.agent_id} shutdown")

    async def publish_event(
        self,
        event_type: EventType,
        data: dict[str, Any],
        target: str | None = None,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: str | None = None,
        ttl: float | None = None,
    ) -> str:
        """Publish an event"""
        event = AgentEvent(
            type=event_type,
            source=self.agent_id,
            target=target,
            data=data,
            priority=priority,
            correlation_id=correlation_id,
            ttl=ttl,
        )

        await self.outgoing_queue.put(event)
        self.metrics["events_sent"] += 1

        logger.debug(f"Event published: {event.type.value} from {self.agent_id}")
        return event.id

    async def subscribe_to_events(
        self,
        event_types: list[EventType | str],
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL,
        filters: dict[str, Any] | None = None,
    ) -> str:
        """Subscribe to events"""
        # Convert string event types to EventType
        event_type_list = []
        for event_type in event_types:
            if isinstance(event_type, str):
                try:
                    event_type_list.append(EventType(event_type))
                except ValueError:
                    logger.warning(f"Unknown event type: {event_type}")
            else:
                event_type_list.append(event_type)

        subscription_id = str(uuid.uuid4())
        subscription = EventSubscription(
            agent_id=self.agent_id,
            event_types=event_type_list,
            handler=handler,
            priority=priority,
            filters=filters or {},
        )

        self.subscriptions[subscription_id] = subscription

        # Register handlers for each event type
        for event_type in event_type_list:
            self.event_handlers[event_type].append(subscription)

        logger.info(f"Subscribed to events: {[et.value for et in event_type_list]}")
        return subscription_id

    async def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]

            # Remove from event handlers
            for event_type in subscription.event_types:
                if event_type in self.event_handlers:
                    self.event_handlers[event_type] = [
                        sub
                        for sub in self.event_handlers[event_type]
                        if sub.agent_id != subscription.agent_id
                    ]

            del self.subscriptions[subscription_id]
            logger.info(f"Unsubscribed from events: {subscription_id}")
            return True
        return False

    async def send_request(
        self, target: str, data: dict[str, Any], timeout: float | None = None
    ) -> Any:
        """Send a request and wait for response"""
        request_id = str(uuid.uuid4())
        timeout = timeout or self.default_request_timeout

        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future

        # Set timeout
        timeout_task = asyncio.create_task(self._request_timeout(request_id, timeout))
        self.request_timeouts[request_id] = timeout_task

        # Send request event
        await self.publish_event(
            event_type=EventType.AGENT_REQUEST,
            data={"request_id": request_id, **data},
            target=target,
            priority=EventPriority.HIGH,
            correlation_id=request_id,
        )

        self.metrics["requests_sent"] += 1

        try:
            # Wait for response
            response = await future
            return response
        except asyncio.CancelledError:
            logger.warning(f"Request {request_id} was cancelled")
            raise
        finally:
            # Cleanup
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            if request_id in self.request_timeouts:
                self.request_timeouts[request_id].cancel()
                del self.request_timeouts[request_id]

    async def send_response(
        self, request_id: str, data: dict[str, Any], target: str, success: bool = True
    ) -> str:
        """Send a response to a request"""
        response_data = {"request_id": request_id, "success": success, "data": data}

        event_id = await self.publish_event(
            event_type=EventType.AGENT_RESPONSE,
            data=response_data,
            target=target,
            priority=EventPriority.HIGH,
            correlation_id=request_id,
        )

        self.metrics["responses_received"] += 1
        return event_id

    async def receive_event(self, event: AgentEvent) -> None:
        """Receive an event from external source"""
        await self.incoming_queue.put(event)
        self.metrics["events_received"] += 1

    async def _process_events(self):
        """Process incoming events"""
        while True:
            try:
                event = await self.incoming_queue.get()
                if event is None:
                    await asyncio.sleep(0.1)
                    continue

                # Check if event is expired
                if event.is_expired():
                    logger.debug(f"Discarding expired event: {event.id}")
                    continue

                # Check if event is for this agent
                if event.target and event.target != self.agent_id:
                    continue

                # Process event
                await self._handle_event(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                await asyncio.sleep(1)

    async def _handle_event(self, event: AgentEvent):
        """Handle a single event"""
        start_time = time.time()

        try:
            # Check for request-response pattern
            if event.type == EventType.AGENT_REQUEST:
                await self._handle_request(event)
            elif event.type == EventType.AGENT_RESPONSE:
                await self._handle_response(event)
            else:
                # Handle regular events
                await self._handle_regular_event(event)

            # Update metrics
            processing_time = time.time() - start_time
            self.metrics["avg_processing_time"] = (
                self.metrics["avg_processing_time"] + processing_time
            ) / 2

        except Exception as e:
            logger.error(f"Error handling event {event.id}: {e}")

    async def _handle_request(self, event: AgentEvent):
        """Handle incoming request"""
        request_id = event.data.get("request_id")
        if not request_id:
            logger.warning("Request event missing request_id")
            return

        # Create response event
        response_data = {
            "request_id": request_id,
            "success": True,
            "data": {"message": "Request received"},
        }

        await self.send_response(request_id, response_data, event.source)

    async def _handle_response(self, event: AgentEvent):
        """Handle incoming response"""
        request_id = event.data.get("request_id")
        if request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                future.set_result(event.data)

    async def _handle_regular_event(self, event: AgentEvent):
        """Handle regular event"""
        if event.type in self.event_handlers:
            handlers = self.event_handlers[event.type]

            # Filter handlers based on event filters
            matching_handlers = []
            for handler in handlers:
                if self._matches_filters(event, handler.filters):
                    matching_handlers.append(handler)

            # Execute handlers
            tasks = []
            for handler in matching_handlers:
                try:
                    task = asyncio.create_task(handler.handler(event))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Error executing event handler: {e}")

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    def _matches_filters(self, event: AgentEvent, filters: dict[str, Any]) -> bool:
        """Check if event matches filters"""
        for key, value in filters.items():
            if (key == "source" and event.source != value) or (
                key == "target" and event.target != value
            ):
                return False
            if key in event.data and event.data[key] != value:
                return False
        return True

    async def _request_timeout(self, request_id: str, timeout: float):
        """Handle request timeout"""
        await asyncio.sleep(timeout)

        if request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                future.set_exception(TimeoutError(f"Request {request_id} timed out"))

    async def _cleanup_expired_events(self):
        """Clean up expired events and requests"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                # Clean up expired requests
                time.time()
                expired_requests = []

                for request_id, future in self.pending_requests.items():
                    if future.done():
                        expired_requests.append(request_id)

                for request_id in expired_requests:
                    del self.pending_requests[request_id]
                    if request_id in self.request_timeouts:
                        self.request_timeouts[request_id].cancel()
                        del self.request_timeouts[request_id]

                # Update metrics
                self.metrics["queue_size"] = self.incoming_queue.size()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def get_metrics(self) -> dict[str, Any]:
        """Get communication metrics"""
        return {
            **self.metrics,
            "subscriptions_count": len(self.subscriptions),
            "pending_requests_count": len(self.pending_requests),
        }


# Global event bus for system-wide communication
class GlobalEventBus:
    """Global event bus for system-wide communication"""

    def __init__(self):
        self.agents: dict[str, EventDrivenAgentCommunication] = {}
        self._lock = asyncio.Lock()

    async def register_agent(
        self, agent_id: str, communication: EventDrivenAgentCommunication
    ):
        """Register an agent with the global event bus"""
        async with self._lock:
            self.agents[agent_id] = communication
            logger.info(f"Agent {agent_id} registered with global event bus")

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the global event bus"""
        async with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.info(f"Agent {agent_id} unregistered from global event bus")

    async def broadcast_event(self, event: AgentEvent, exclude_source: bool = True):
        """Broadcast event to all agents"""
        async with self._lock:
            for agent_id, communication in self.agents.items():
                if exclude_source and agent_id == event.source:
                    continue
                try:
                    await communication.receive_event(event)
                except Exception as e:
                    logger.error(f"Error broadcasting to agent {agent_id}: {e}")

    async def send_event(self, event: AgentEvent):
        """Send event to specific target"""
        if event.target and event.target in self.agents:
            try:
                await self.agents[event.target].receive_event(event)
            except Exception as e:
                logger.error(f"Error sending event to {event.target}: {e}")


# Global instance
global_event_bus = GlobalEventBus()
