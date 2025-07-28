"""
Base OCR Agent Implementation

Provides the base implementation for all OCR agents with common functionality.
"""

import asyncio
import time
from typing import Any

from agents.interfaces import AgentResponse
from core.decorators import handle_exceptions

from .ocr_agent_interface import BaseOCRAgent, OCREventType


class BaseOCRAgentImpl(BaseOCRAgent):
    """Base implementation for OCR agents with common functionality"""

    def __init__(
        self, name: str, timeout: float = 30.0, max_retries: int = 3, **kwargs: Any
    ) -> None:
        super().__init__(name=name, **kwargs)
        self.timeout = timeout
        self.max_retries = max_retries
        self.processing_stats = {
            "total_processed": 0,
            "successful_processed": 0,
            "failed_processed": 0,
            "average_processing_time": 0.0,
            "total_processing_time": 0.0,
        }

    @handle_exceptions(max_retries=3, retry_delay=1.0)
    async def process(self, input_data: dict) -> AgentResponse:
        """Process input data with error handling and performance tracking"""
        start_time = time.time()

        try:
            # Validate input
            if not await self.validate_input(input_data):
                return AgentResponse(
                    success=False, error=f"Invalid input data for {self.name}"
                )

            # Process with timeout
            result = await asyncio.wait_for(
                self._process_impl(input_data), timeout=self.timeout
            )

            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(True, processing_time)

            # Publish success event
            await self.publish_event(
                OCREventType.PERFORMANCE_METRIC,
                {
                    "agent": self.name,
                    "processing_time": processing_time,
                    "success": True,
                },
            )

            return result

        except TimeoutError:
            processing_time = time.time() - start_time
            self._update_stats(False, processing_time)

            error_msg = f"Processing timeout after {self.timeout}s in {self.name}"
            await self._handle_error(TimeoutError(error_msg), input_data)

            return AgentResponse(
                success=False, error=error_msg, metadata={"timeout": self.timeout}
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(False, processing_time)

            return await self._handle_error(e, input_data)

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Implementation of processing logic - to be overridden by subclasses"""
        raise NotImplementedError

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data - to be overridden by subclasses"""
        return isinstance(input_data, dict) and len(input_data) > 0

    def _update_stats(self, success: bool, processing_time: float) -> None:
        """Update processing statistics"""
        self.processing_stats["total_processed"] += 1
        self.processing_stats["total_processing_time"] += processing_time

        if success:
            self.processing_stats["successful_processed"] += 1
        else:
            self.processing_stats["failed_processed"] += 1

        # Update average processing time
        total = self.processing_stats["total_processed"]
        total_time = self.processing_stats["total_processing_time"]
        self.processing_stats["average_processing_time"] = total_time / total

    def get_processing_stats(self) -> dict[str, Any]:
        """Get processing statistics"""
        return self.processing_stats.copy()

    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        total = self.processing_stats["total_processed"]
        if total == 0:
            return 0.0
        return (self.processing_stats["successful_processed"] / total) * 100

    async def health_check(self) -> dict[str, Any]:
        """Perform health check"""
        return {
            "agent_name": self.name,
            "status": "healthy",
            "success_rate": self.get_success_rate(),
            "average_processing_time": self.processing_stats["average_processing_time"],
            "total_processed": self.processing_stats["total_processed"],
        }
