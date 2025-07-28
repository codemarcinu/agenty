"""
Performance Monitoring Agent

Monitors performance of OCR pipeline and agents.
"""

import logging
from typing import Any

from agents.interfaces import AgentResponse
from src.backend.agents.ocr.base.base_ocr_agent import BaseOCRAgentImpl

logger = logging.getLogger(__name__)


class PerformanceMonitoringAgent(BaseOCRAgentImpl):
    """Performance monitoring agent for OCR pipeline"""

    def __init__(self, name: str = "PerformanceMonitoringAgent", **kwargs: Any) -> None:
        super().__init__(name=name, timeout=5.0, **kwargs)

        self.metrics = {
            "total_events": 0,
            "agent_performance": {},
            "pipeline_performance": {},
        }

    async def validate_input(self, input_data: dict) -> bool:
        """Validate input data"""
        return True  # Accept any input for monitoring

    async def _process_impl(self, input_data: dict) -> AgentResponse:
        """Process monitoring data"""
        try:
            # Update metrics
            self.metrics["total_events"] += 1

            # Extract performance data if available
            if "performance_data" in input_data:
                self._update_performance_metrics(input_data["performance_data"])

            return AgentResponse(
                success=True,
                text="Performance monitoring updated",
                metadata={"total_events": self.metrics["total_events"]},
                data={"metrics": self.metrics},
            )

        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
            return AgentResponse(
                success=False, error=f"Performance monitoring failed: {e!s}"
            )

    def _update_performance_metrics(self, performance_data: dict[str, Any]) -> None:
        """Update performance metrics"""
        agent_name = performance_data.get("agent_name", "unknown")

        if agent_name not in self.metrics["agent_performance"]:
            self.metrics["agent_performance"][agent_name] = {
                "total_processed": 0,
                "total_time": 0.0,
                "average_time": 0.0,
                "success_rate": 0.0,
            }

        agent_metrics = self.metrics["agent_performance"][agent_name]
        agent_metrics["total_processed"] += 1

        if "processing_time" in performance_data:
            agent_metrics["total_time"] += performance_data["processing_time"]
            agent_metrics["average_time"] = (
                agent_metrics["total_time"] / agent_metrics["total_processed"]
            )

        if "success" in performance_data:
            # Update success rate (simplified)
            agent_metrics["success_rate"] = 0.95  # Placeholder
