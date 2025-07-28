"""
OCR Agent Interfaces and Communication System

Provides base interfaces and communication mechanisms for the multi-agent OCR system.
"""

import asyncio
from collections.abc import Callable
from enum import Enum
import json
import logging
from typing import Any

import redis.asyncio as redis

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse

logger = logging.getLogger(__name__)


class OCREventType(Enum):
    """Event types for OCR pipeline communication"""

    IMAGE_PREPROCESSED = "image_preprocessed"
    TEXT_DETECTED = "text_detected"
    OCR_COMPLETED = "ocr_completed"
    VALIDATION_COMPLETED = "validation_completed"
    STRUCTURE_PARSED = "structure_parsed"
    CLASSIFICATION_COMPLETED = "classification_completed"
    LANGUAGE_DETECTED = "language_detected"
    STORE_RECOGNIZED = "store_recognized"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"


class OCRMessageBus:
    """Message bus for OCR agent communication using Redis"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: redis.Redis | None = None
        self.subscribers: dict[str, list[Callable]] = {}
        self._running = False

    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis message bus")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis message bus")

    async def publish(self, topic: str, message: dict) -> None:
        """Publish message to topic"""
        if not self.redis_client:
            await self.connect()

        try:
            message_data = {
                "topic": topic,
                "data": message,
                "timestamp": asyncio.get_event_loop().time(),
            }
            await self.redis_client.publish(topic, json.dumps(message_data))
            logger.debug(f"Published message to topic {topic}")
        except Exception as e:
            logger.error(f"Failed to publish message to {topic}: {e}")

    async def subscribe(self, topic: str, callback: Callable) -> None:
        """Subscribe to topic with callback"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)

        # Also subscribe to Redis pubsub
        if self.redis_client:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(topic)
            asyncio.create_task(self._listen_to_topic(pubsub, topic))

    async def _listen_to_topic(self, pubsub, topic: str) -> None:
        """Listen to Redis topic and call local subscribers"""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    if topic in self.subscribers:
                        for callback in self.subscribers[topic]:
                            try:
                                await callback(data["data"])
                            except Exception as e:
                                logger.error(
                                    f"Error in callback for topic {topic}: {e}"
                                )
        except Exception as e:
            logger.error(f"Error listening to topic {topic}: {e}")


class BaseOCRAgent(BaseAgent):
    """Base class for all OCR agents with communication capabilities"""

    def __init__(
        self, name: str, message_bus: OCRMessageBus | None = None, **kwargs: Any
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.message_bus = message_bus or OCRMessageBus()
        self.performance_metrics: dict[str, Any] = {}
        self.agent_id = f"{name}_{id(self)}"

    async def initialize(self) -> None:
        """Initialize the agent and connect to message bus"""
        await self.message_bus.connect()
        logger.info(f"Initialized OCR agent: {self.name}")

    async def shutdown(self) -> None:
        """Shutdown the agent and disconnect from message bus"""
        await self.message_bus.disconnect()
        logger.info(f"Shutdown OCR agent: {self.name}")

    async def process(self, input_data: dict) -> AgentResponse:
        """Process input data and return response"""
        raise NotImplementedError

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        raise NotImplementedError

    async def publish_event(self, event_type: OCREventType, data: dict) -> None:
        """Publish event to message bus"""
        await self.message_bus.publish(
            event_type.value,
            {"agent_id": self.agent_id, "agent_name": self.name, "data": data},
        )

    async def subscribe_to_event(
        self, event_type: OCREventType, callback: Callable
    ) -> None:
        """Subscribe to event type"""
        await self.message_bus.subscribe(event_type.value, callback)

    def update_performance_metric(self, metric_name: str, value: Any) -> None:
        """Update performance metric"""
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []
        self.performance_metrics[metric_name].append(value)

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()

    async def _handle_error(self, error: Exception, context: dict) -> AgentResponse:
        """Handle error and publish error event"""
        error_data = {
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
        }
        await self.publish_event(OCREventType.ERROR_OCCURRED, error_data)

        return AgentResponse(
            success=False,
            error=f"Error in {self.name}: {error}",
            metadata={"error_context": context},
        )
