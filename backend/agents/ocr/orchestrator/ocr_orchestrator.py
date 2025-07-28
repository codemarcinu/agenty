"""
OCR Orchestrator

Main orchestrator for coordinating the multi-agent OCR pipeline.
Manages the complete flow from image preprocessing to final structured data extraction.
"""

import asyncio
import logging
import time
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.advanced.performance_monitoring_agent import (
    PerformanceMonitoringAgent,
)
from src.backend.agents.ocr.advanced.structure_parser_agent import StructureParserAgent
from src.backend.agents.ocr.base.ocr_agent_interface import OCREventType, OCRMessageBus
from src.backend.agents.ocr.core.data_validation_agent import DataValidationAgent
from src.backend.agents.ocr.core.image_preprocessing_agent import (
    ImagePreprocessingAgent,
)
from src.backend.agents.ocr.core.ocr_engine_agent import OCREngineAgent
from src.backend.agents.ocr.core.text_detection_agent import TextDetectionAgent
from src.backend.agents.ocr.polish.language_detection_agent import (
    LanguageDetectionAgent,
)
from src.backend.agents.ocr.polish.product_classification_agent import (
    ProductClassificationAgent,
)
from src.backend.agents.ocr.polish.store_recognition_agent import StoreRecognitionAgent

logger = logging.getLogger(__name__)


class OCROrchestrator:
    """
    Main orchestrator for the multi-agent OCR pipeline.

    Coordinates the complete flow:
    1. Image Preprocessing
    2. Text Detection
    3. OCR Engine (Multi-engine with voting)
    4. Language Detection
    5. Data Validation
    6. Store Recognition
    7. Structure Parsing
    8. Product Classification
    9. Performance Monitoring
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        enable_monitoring: bool = True,
        **kwargs: Any,
    ):
        self.redis_url = redis_url
        self.enable_monitoring = enable_monitoring

        # Initialize message bus
        self.message_bus = OCRMessageBus(redis_url)

        # Initialize agents
        self.agents = {}
        self.agent_order = [
            "preprocessing",
            "text_detection",
            "ocr_engine",
            "language_detection",
            "validation",
            "store_recognition",
            "structure_parser",
            "product_classification",
        ]

        # Performance tracking
        self.pipeline_stats = {
            "total_processed": 0,
            "successful_processed": 0,
            "failed_processed": 0,
            "average_pipeline_time": 0.0,
            "total_pipeline_time": 0.0,
            "agent_performance": {},
        }

        # Circuit breaker for fault tolerance
        self.max_retries = 3
        self.retry_delay = 1.0

        logger.info("OCR Orchestrator initialized")

    async def initialize(self) -> None:
        """Initialize all agents and message bus"""
        try:
            # Connect to message bus
            await self.message_bus.connect()

            # Initialize agents
            await self._initialize_agents()

            # Subscribe to events
            await self._subscribe_to_events()

            # Initialize monitoring if enabled
            if self.enable_monitoring:
                await self._initialize_monitoring()

            logger.info("OCR Orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OCR Orchestrator: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown orchestrator and all agents"""
        try:
            # Shutdown all agents
            for agent in self.agents.values():
                if hasattr(agent, "shutdown"):
                    await agent.shutdown()

            # Disconnect from message bus
            await self.message_bus.disconnect()

            logger.info("OCR Orchestrator shutdown successfully")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def _initialize_agents(self) -> None:
        """Initialize all OCR agents"""
        self.agents = {
            "preprocessing": ImagePreprocessingAgent(),
            "text_detection": TextDetectionAgent(),
            "ocr_engine": OCREngineAgent(),
            "validation": DataValidationAgent(),
            "language_detection": LanguageDetectionAgent(),
            "store_recognition": StoreRecognitionAgent(),
            "product_classification": ProductClassificationAgent(),
            "structure_parser": StructureParserAgent(),
        }

        # Initialize each agent
        for name, agent in self.agents.items():
            try:
                if hasattr(agent, "initialize"):
                    await agent.initialize()
                logger.info(f"Initialized agent: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize agent {name}: {e}")

    async def _subscribe_to_events(self) -> None:
        """Subscribe to agent events for monitoring"""
        event_types = [
            OCREventType.IMAGE_PREPROCESSED,
            OCREventType.TEXT_DETECTED,
            OCREventType.OCR_COMPLETED,
            OCREventType.VALIDATION_COMPLETED,
            OCREventType.STRUCTURE_PARSED,
            OCREventType.CLASSIFICATION_COMPLETED,
            OCREventType.LANGUAGE_DETECTED,
            OCREventType.STORE_RECOGNIZED,
            OCREventType.ERROR_OCCURRED,
            OCREventType.PERFORMANCE_METRIC,
        ]

        for event_type in event_types:
            await self.message_bus.subscribe(event_type.value, self._handle_event)

    async def _initialize_monitoring(self) -> None:
        """Initialize performance monitoring"""
        self.monitoring_agent = PerformanceMonitoringAgent()
        await self.monitoring_agent.initialize()
        self.agents["monitoring"] = self.monitoring_agent

    async def _handle_event(self, event_data: dict[str, Any]) -> None:
        """Handle events from agents"""
        try:
            agent_name = event_data.get("agent_name", "unknown")
            event_type = event_data.get("event_type", "unknown")

            logger.debug(f"Received event from {agent_name}: {event_type}")

            # Update performance metrics
            if "processing_time" in event_data:
                self._update_agent_performance(
                    agent_name, event_data["processing_time"]
                )

        except Exception as e:
            logger.error(f"Error handling event: {e}")

    def _update_agent_performance(
        self, agent_name: str, processing_time: float
    ) -> None:
        """Update performance metrics for an agent"""
        if agent_name not in self.pipeline_stats["agent_performance"]:
            self.pipeline_stats["agent_performance"][agent_name] = {
                "total_processed": 0,
                "total_time": 0.0,
                "average_time": 0.0,
            }

        stats = self.pipeline_stats["agent_performance"][agent_name]
        stats["total_processed"] += 1
        stats["total_time"] += processing_time
        stats["average_time"] = stats["total_time"] / stats["total_processed"]

    async def process_receipt(
        self, image_bytes: bytes, metadata: dict[str, Any] | None = None
    ) -> AgentResponse:
        """
        Process receipt through complete OCR pipeline.

        Args:
            image_bytes: Raw image bytes
            metadata: Optional metadata about the receipt

        Returns:
            AgentResponse with structured receipt data
        """
        start_time = time.time()

        try:
            # Prepare initial data
            pipeline_data = {
                "image_bytes": image_bytes,
                "metadata": metadata or {},
                "pipeline_start_time": start_time,
            }

            # Execute pipeline
            result = await self._execute_pipeline(pipeline_data)

            # Update pipeline statistics
            pipeline_time = time.time() - start_time
            self._update_pipeline_stats(True, pipeline_time)

            return result

        except Exception as e:
            pipeline_time = time.time() - start_time
            self._update_pipeline_stats(False, pipeline_time)

            logger.error(f"Pipeline execution failed: {e}")
            return AgentResponse(
                success=False,
                error=f"OCR pipeline failed: {e!s}",
                metadata={"pipeline_time": pipeline_time},
            )

    async def _execute_pipeline(self, pipeline_data: dict[str, Any]) -> AgentResponse:
        """Execute the complete OCR pipeline"""
        current_data = pipeline_data.copy()

        # Execute each agent in order
        for agent_name in self.agent_order:
            if agent_name not in self.agents:
                logger.warning(f"Agent {agent_name} not found, skipping")
                continue

            agent = self.agents[agent_name]

            try:
                # Process with current agent
                result = await self._process_with_agent(agent, agent_name, current_data)

                if not result.success:
                    logger.error(f"Agent {agent_name} failed: {result.error}")
                    return result

                # Update pipeline data with agent result
                current_data = self._merge_agent_result(
                    current_data, result, agent_name
                )

                logger.debug(f"Agent {agent_name} completed successfully")

            except Exception as e:
                logger.error(f"Agent {agent_name} failed with exception: {e}")
                return AgentResponse(
                    success=False, error=f"Agent {agent_name} failed: {e!s}"
                )

        # Prepare final response
        return self._prepare_final_response(current_data)

    async def _process_with_agent(
        self, agent: Any, agent_name: str, data: dict[str, Any]
    ) -> AgentResponse:
        """Process data with a specific agent with retry logic"""
        for attempt in range(self.max_retries):
            try:
                result = await agent.process(data)
                return result

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                logger.warning(f"Agent {agent_name} attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        return AgentResponse(
            success=False,
            error=f"Agent {agent_name} failed after {self.max_retries} attempts",
        )

    def _merge_agent_result(
        self, current_data: dict[str, Any], result: AgentResponse, agent_name: str
    ) -> dict[str, Any]:
        """Merge agent result into pipeline data"""
        # Add agent result to pipeline data
        current_data[f"{agent_name}_result"] = result.data or {}
        current_data[f"{agent_name}_metadata"] = result.metadata or {}

        # Update with agent output
        if agent_name == "preprocessing":
            current_data["processed_image_bytes"] = result.data.get(
                "processed_image_bytes"
            )
            current_data["quality_metrics"] = result.data.get("quality_metrics", {})

        elif agent_name == "ocr_engine":
            current_data["ocr_text"] = result.data.get("ocr_text", "")
            current_data["ocr_confidence"] = result.data.get("confidence", 0.0)

        elif agent_name == "language_detection":
            current_data["detected_language"] = result.data.get("language", "unknown")
            current_data["language_confidence"] = result.data.get("confidence", 0.0)

        elif agent_name == "store_recognition":
            current_data["store_info"] = result.data.get("store_info", {})
            current_data["store_confidence"] = result.data.get("confidence", 0.0)

        elif agent_name == "structure_parser":
            current_data["structured_data"] = result.data.get("structured_data", {})

        elif agent_name == "product_classification":
            current_data["classified_products"] = result.data.get(
                "classified_products", []
            )

        return current_data

    def _prepare_final_response(self, pipeline_data: dict[str, Any]) -> AgentResponse:
        """Prepare final response from pipeline data"""
        try:
            # Extract key information
            structured_data = pipeline_data.get("structured_data", {})
            store_info = pipeline_data.get("store_info", {})
            classified_products = pipeline_data.get("classified_products", [])
            ocr_confidence = pipeline_data.get("ocr_confidence", 0.0)

            # Calculate overall confidence
            confidences = [
                pipeline_data.get("ocr_confidence", 0.0),
                pipeline_data.get("store_confidence", 0.0),
                pipeline_data.get("language_confidence", 0.0),
            ]
            overall_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )

            # Prepare final data
            final_data = {
                "store": store_info,
                "products": classified_products,
                "total": structured_data.get("total", 0.0),
                "date": structured_data.get("date", ""),
                "confidence": overall_confidence,
                "pipeline_metadata": {
                    "ocr_confidence": ocr_confidence,
                    "store_confidence": pipeline_data.get("store_confidence", 0.0),
                    "language_confidence": pipeline_data.get(
                        "language_confidence", 0.0
                    ),
                    "quality_metrics": pipeline_data.get("quality_metrics", {}),
                },
            }

            return AgentResponse(
                success=True,
                text="Receipt processing completed successfully",
                metadata={
                    "overall_confidence": overall_confidence,
                    "agents_used": list(self.agents.keys()),
                    "pipeline_time": time.time()
                    - pipeline_data.get("pipeline_start_time", 0),
                },
                data=final_data,
            )

        except Exception as e:
            logger.error(f"Error preparing final response: {e}")
            return AgentResponse(
                success=False, error=f"Error preparing final response: {e!s}"
            )

    def _update_pipeline_stats(self, success: bool, pipeline_time: float) -> None:
        """Update pipeline statistics"""
        self.pipeline_stats["total_processed"] += 1
        self.pipeline_stats["total_pipeline_time"] += pipeline_time

        if success:
            self.pipeline_stats["successful_processed"] += 1
        else:
            self.pipeline_stats["failed_processed"] += 1

        # Update average pipeline time
        total = self.pipeline_stats["total_processed"]
        total_time = self.pipeline_stats["total_pipeline_time"]
        self.pipeline_stats["average_pipeline_time"] = total_time / total

    def get_pipeline_stats(self) -> dict[str, Any]:
        """Get pipeline statistics"""
        return self.pipeline_stats.copy()

    def get_success_rate(self) -> float:
        """Get pipeline success rate"""
        total = self.pipeline_stats["total_processed"]
        if total == 0:
            return 0.0
        return (self.pipeline_stats["successful_processed"] / total) * 100

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on all agents"""
        health_status = {
            "orchestrator": "healthy",
            "agents": {},
            "pipeline_stats": self.get_pipeline_stats(),
        }

        # Check each agent
        for agent_name, agent in self.agents.items():
            try:
                if hasattr(agent, "health_check"):
                    agent_health = await agent.health_check()
                    health_status["agents"][agent_name] = agent_health
                else:
                    health_status["agents"][agent_name] = {"status": "unknown"}
            except Exception as e:
                health_status["agents"][agent_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        return health_status
