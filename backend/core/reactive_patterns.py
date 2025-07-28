"""
Reactive Multi-Agent Patterns for Responsive System Architecture
Zgodnie z regułami MDC dla reaktywnych systemów wieloagentowych
"""

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

from core.event_bus import (
    AgentEvent,
    EventDrivenAgentCommunication,
    EventPriority,
    EventType,
)

logger = logging.getLogger(__name__)


class StimulusType(Enum):
    """Types of stimuli that can trigger reactive responses"""

    USER_INPUT = "user_input"
    SYSTEM_EVENT = "system_event"
    AGENT_STATE_CHANGE = "agent_state_change"
    RESOURCE_UPDATE = "resource_update"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_ALERT = "performance_alert"
    EXTERNAL_API_CALL = "external_api_call"
    TIMER_EXPIRED = "timer_expired"


class ResponseType(Enum):
    """Types of reactive responses"""

    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    CONDITIONAL = "conditional"
    CASCADE = "cascade"
    FALLBACK = "fallback"


@dataclass
class Stimulus:
    """Stimulus that triggers reactive response"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: StimulusType = StimulusType.SYSTEM_EVENT
    source: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReactiveResponse:
    """Reactive response to stimulus"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stimulus_id: str = ""
    type: ResponseType = ResponseType.IMMEDIATE
    handler_id: str = ""
    action: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    conditions: list[dict[str, Any]] = field(default_factory=list)
    delay: float | None = None
    timeout: float | None = None
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: datetime | None = None
    result: Any | None = None
    success: bool = True
    error: str | None = None


@dataclass
class ReactivePattern:
    """Reactive pattern definition"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    stimulus_type: StimulusType = StimulusType.SYSTEM_EVENT
    response_type: ResponseType = ResponseType.IMMEDIATE
    handler: Callable = None
    conditions: list[dict[str, Any]] = field(default_factory=list)
    priority: int = 1
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    execution_count: int = 0
    last_executed: datetime | None = None
    success_rate: float = 100.0


class ReactiveAgentOrchestrator:
    """Reactive orchestrator for multi-agent systems"""

    def __init__(self, orchestrator_id: str):
        self.orchestrator_id = orchestrator_id

        # Pattern management
        self.reactive_patterns: dict[str, ReactivePattern] = {}
        self.stimulus_response_map: dict[StimulusType, list[ReactivePattern]] = (
            defaultdict(list)
        )

        # Response tracking
        self.active_responses: dict[str, ReactiveResponse] = {}
        self.response_history: deque = deque(maxlen=1000)

        # Communication
        self.event_communication = EventDrivenAgentCommunication(orchestrator_id)

        # Performance tracking
        self.performance_metrics = {
            "stimuli_processed": 0,
            "responses_executed": 0,
            "avg_response_time": 0.0,
            "success_rate": 100.0,
            "active_patterns": 0,
        }

        # Background tasks
        self.stimulus_processor_task: asyncio.Task | None = None
        self.response_monitor_task: asyncio.Task | None = None

        logger.info(f"ReactiveAgentOrchestrator {orchestrator_id} initialized")

    async def initialize(self):
        """Initialize the reactive orchestrator"""
        # Subscribe to stimulus events
        await self.event_communication.subscribe_to_events(
            [
                EventType.AGENT_STATE_CHANGE.value,
                EventType.RESOURCE_UPDATE.value,
                "user_input",
                "system_alert",
                "performance_alert",
                "error_event",
            ],
            self._handle_stimulus_event,
        )

        # Start background tasks
        self.stimulus_processor_task = asyncio.create_task(self._process_stimuli())
        self.response_monitor_task = asyncio.create_task(self._monitor_responses())

        logger.info(f"ReactiveAgentOrchestrator {self.orchestrator_id} initialized")

    async def shutdown(self):
        """Shutdown the reactive orchestrator"""
        if self.stimulus_processor_task:
            self.stimulus_processor_task.cancel()
        if self.response_monitor_task:
            self.response_monitor_task.cancel()

        logger.info(f"ReactiveAgentOrchestrator {self.orchestrator_id} shutdown")

    async def register_reactive_pattern(
        self,
        stimulus_type: StimulusType,
        response_type: ResponseType,
        handler: Callable,
        name: str = "",
        description: str = "",
        conditions: list[dict[str, Any]] | None = None,
        priority: int = 1,
    ) -> str:
        """Register a reactive pattern"""
        try:
            pattern = ReactivePattern(
                name=name or f"pattern_{len(self.reactive_patterns)}",
                description=description,
                stimulus_type=stimulus_type,
                response_type=response_type,
                handler=handler,
                conditions=conditions or [],
                priority=priority,
            )

            self.reactive_patterns[pattern.id] = pattern
            self.stimulus_response_map[stimulus_type].append(pattern)

            # Sort by priority (highest first)
            self.stimulus_response_map[stimulus_type].sort(
                key=lambda p: p.priority, reverse=True
            )

            self.performance_metrics["active_patterns"] = len(self.reactive_patterns)

            logger.info(
                f"Reactive pattern registered: {pattern.name} for {stimulus_type.value}"
            )
            return pattern.id

        except Exception as e:
            logger.error(f"Error registering reactive pattern: {e}")
            return ""

    async def unregister_reactive_pattern(self, pattern_id: str) -> bool:
        """Unregister a reactive pattern"""
        try:
            if pattern_id in self.reactive_patterns:
                pattern = self.reactive_patterns[pattern_id]

                # Remove from stimulus map
                if pattern.stimulus_type in self.stimulus_response_map:
                    self.stimulus_response_map[pattern.stimulus_type] = [
                        p
                        for p in self.stimulus_response_map[pattern.stimulus_type]
                        if p.id != pattern_id
                    ]

                del self.reactive_patterns[pattern_id]
                self.performance_metrics["active_patterns"] = len(
                    self.reactive_patterns
                )

                logger.info(f"Reactive pattern unregistered: {pattern.name}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error unregistering reactive pattern: {e}")
            return False

    async def handle_stimulus(self, stimulus_data: dict[str, Any]) -> list[str]:
        """Handle a stimulus and trigger reactive responses"""
        try:
            # Create stimulus object
            stimulus = Stimulus(
                type=StimulusType(
                    stimulus_data.get("type", StimulusType.SYSTEM_EVENT.value)
                ),
                source=stimulus_data.get("source", "unknown"),
                data=stimulus_data.get("data", {}),
                priority=EventPriority(
                    stimulus_data.get("priority", EventPriority.NORMAL.value)
                ),
                correlation_id=stimulus_data.get("correlation_id"),
                metadata=stimulus_data.get("metadata", {}),
            )

            # Find matching patterns
            matching_patterns = self._find_matching_patterns(stimulus)

            # Execute responses
            response_ids = []
            for pattern in matching_patterns:
                response_id = await self._execute_reactive_response(stimulus, pattern)
                if response_id:
                    response_ids.append(response_id)

            self.performance_metrics["stimuli_processed"] += 1
            logger.debug(
                f"Stimulus {stimulus.id} processed, {len(response_ids)} responses triggered"
            )

            return response_ids

        except Exception as e:
            logger.error(f"Error handling stimulus: {e}")
            return []

    def _find_matching_patterns(self, stimulus: Stimulus) -> list[ReactivePattern]:
        """Find patterns that match the stimulus"""
        matching_patterns = []

        # Get patterns for this stimulus type
        patterns = self.stimulus_response_map.get(stimulus.type, [])

        for pattern in patterns:
            if not pattern.enabled:
                continue

            # Check conditions
            if self._check_pattern_conditions(pattern, stimulus):
                matching_patterns.append(pattern)

        return matching_patterns

    def _check_pattern_conditions(
        self, pattern: ReactivePattern, stimulus: Stimulus
    ) -> bool:
        """Check if pattern conditions are met"""
        if not pattern.conditions:
            return True

        for condition in pattern.conditions:
            condition_type = condition.get("type")
            condition_value = condition.get("value")

            if condition_type == "source_match":
                if stimulus.source != condition_value:
                    return False
            elif condition_type == "data_contains":
                if condition_value not in stimulus.data:
                    return False
            elif condition_type == "priority_greater":
                if stimulus.priority.value <= condition_value:
                    return False
            elif condition_type == "time_window":
                # Check if stimulus is within time window
                window_start = condition.get("start_time")
                window_end = condition.get("end_time")
                if window_start and window_end:
                    current_time = datetime.now().time()
                    if not (window_start <= current_time <= window_end):
                        return False
            elif condition_type == "custom":
                # Custom condition function
                condition_func = condition.get("function")
                if condition_func and not condition_func(stimulus):
                    return False

        return True

    async def _execute_reactive_response(
        self, stimulus: Stimulus, pattern: ReactivePattern
    ) -> str | None:
        """Execute a reactive response"""
        try:
            # Create response object
            response = ReactiveResponse(
                stimulus_id=stimulus.id,
                type=pattern.response_type,
                handler_id=pattern.id,
                action=pattern.name,
                parameters=stimulus.data,
                conditions=pattern.conditions,
                delay=(pattern.response_type == ResponseType.DELAYED and 1.0) or None,
                timeout=30.0,  # Default timeout
            )

            # Update pattern stats
            pattern.execution_count += 1
            pattern.last_executed = datetime.now()

            # Execute based on response type
            if pattern.response_type == ResponseType.IMMEDIATE:
                await self._execute_immediate_response(response, pattern)
            elif pattern.response_type == ResponseType.DELAYED:
                await self._execute_delayed_response(response, pattern)
            elif pattern.response_type == ResponseType.CONDITIONAL:
                await self._execute_conditional_response(response, pattern)
            elif pattern.response_type == ResponseType.CASCADE:
                await self._execute_cascade_response(response, pattern)
            elif pattern.response_type == ResponseType.FALLBACK:
                await self._execute_fallback_response(response, pattern)

            # Track response
            self.active_responses[response.id] = response
            self.response_history.append(response)

            self.performance_metrics["responses_executed"] += 1
            logger.debug(
                f"Reactive response executed: {response.id} for pattern {pattern.name}"
            )

            return response.id

        except Exception as e:
            logger.error(f"Error executing reactive response: {e}")
            return None

    async def _execute_immediate_response(
        self, response: ReactiveResponse, pattern: ReactivePattern
    ):
        """Execute immediate response"""
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(pattern.handler):
                result = await pattern.handler(response.parameters)
            else:
                result = pattern.handler(response.parameters)

            response.executed_at = datetime.now()
            response.result = result
            response.success = True

            execution_time = time.time() - start_time
            self.performance_metrics["avg_response_time"] = (
                self.performance_metrics["avg_response_time"] + execution_time
            ) / 2

            # Update pattern success rate
            pattern.success_rate = (
                pattern.success_rate * (pattern.execution_count - 1) + 100
            ) / pattern.execution_count

        except Exception as e:
            response.executed_at = datetime.now()
            response.error = str(e)
            response.success = False

            # Update pattern success rate
            pattern.success_rate = (
                pattern.success_rate * (pattern.execution_count - 1) + 0
            ) / pattern.execution_count

            logger.error(f"Error in immediate response {response.id}: {e}")

    async def _execute_delayed_response(
        self, response: ReactiveResponse, pattern: ReactivePattern
    ):
        """Execute delayed response"""
        delay = response.delay or 1.0

        async def delayed_execution():
            await asyncio.sleep(delay)
            await self._execute_immediate_response(response, pattern)

        asyncio.create_task(delayed_execution())

    async def _execute_conditional_response(
        self, response: ReactiveResponse, pattern: ReactivePattern
    ):
        """Execute conditional response"""
        # Check additional conditions before execution
        if self._check_response_conditions(response):
            await self._execute_immediate_response(response, pattern)
        else:
            response.executed_at = datetime.now()
            response.success = False
            response.error = "Conditions not met"

    async def _execute_cascade_response(
        self, response: ReactiveResponse, pattern: ReactivePattern
    ):
        """Execute cascade response (triggers other responses)"""
        # Execute the main response
        await self._execute_immediate_response(response, pattern)

        # Trigger cascade events
        cascade_events = response.parameters.get("cascade_events", [])
        for event_data in cascade_events:
            await self.event_communication.publish_event(
                event_data.get("type", "cascade_event"),
                event_data.get("data", {}),
                priority=EventPriority.HIGH,
            )

    async def _execute_fallback_response(
        self, response: ReactiveResponse, pattern: ReactivePattern
    ):
        """Execute fallback response"""
        # Try primary response first
        try:
            await self._execute_immediate_response(response, pattern)
        except Exception as e:
            # Execute fallback
            fallback_handler = response.parameters.get("fallback_handler")
            if fallback_handler:
                try:
                    if asyncio.iscoroutinefunction(fallback_handler):
                        result = await fallback_handler(response.parameters)
                    else:
                        result = fallback_handler(response.parameters)

                    response.result = result
                    response.success = True
                    response.error = f"Primary failed, fallback succeeded: {e!s}"
                except Exception as fallback_error:
                    response.success = False
                    response.error = (
                        f"Both primary and fallback failed: {e!s}, {fallback_error!s}"
                    )

    def _check_response_conditions(self, response: ReactiveResponse) -> bool:
        """Check conditions for response execution"""
        # This is a simplified implementation
        # In a full system, you would have more sophisticated condition checking
        return True

    async def _process_stimuli(self):
        """Process stimuli in background"""
        while True:
            try:
                # Process any pending stimuli
                # This would typically involve processing a queue
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing stimuli: {e}")
                await asyncio.sleep(1)

    async def _monitor_responses(self):
        """Monitor active responses"""
        while True:
            try:
                current_time = datetime.now()

                # Check for timed out responses
                timed_out_responses = []
                for response_id, response in self.active_responses.items():
                    if (
                        response.timeout
                        and response.created_at
                        and (current_time - response.created_at).total_seconds()
                        > response.timeout
                    ):
                        timed_out_responses.append(response_id)

                # Handle timed out responses
                for response_id in timed_out_responses:
                    response = self.active_responses[response_id]
                    response.executed_at = current_time
                    response.success = False
                    response.error = "Response timeout"

                    del self.active_responses[response_id]
                    logger.warning(f"Response {response_id} timed out")

                # Clean up old responses from history
                cutoff_time = current_time - timedelta(hours=24)
                self.response_history = deque(
                    [r for r in self.response_history if r.created_at > cutoff_time],
                    maxlen=1000,
                )

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error monitoring responses: {e}")
                await asyncio.sleep(30)

    async def _handle_stimulus_event(self, event: AgentEvent):
        """Handle stimulus events"""
        try:
            # Convert event to stimulus data
            stimulus_data = {
                "type": event.type,
                "source": event.source,
                "data": event.payload,
                "priority": event.priority.value,
                "correlation_id": event.correlation_id,
                "metadata": event.metadata,
            }

            # Handle stimulus
            response_ids = await self.handle_stimulus(stimulus_data)

            if response_ids:
                logger.debug(f"Stimulus event triggered {len(response_ids)} responses")

        except Exception as e:
            logger.error(f"Error handling stimulus event: {e}")

    def get_orchestrator_stats(self) -> dict[str, Any]:
        """Get orchestrator statistics"""
        total_responses = self.performance_metrics["responses_executed"]
        successful_responses = sum(1 for r in self.response_history if r.success)
        success_rate = (
            (successful_responses / total_responses * 100) if total_responses > 0 else 0
        )

        return {
            "orchestrator_id": self.orchestrator_id,
            "active_patterns": self.performance_metrics["active_patterns"],
            "stimuli_processed": self.performance_metrics["stimuli_processed"],
            "responses_executed": self.performance_metrics["responses_executed"],
            "active_responses": len(self.active_responses),
            "avg_response_time": round(
                self.performance_metrics["avg_response_time"], 3
            ),
            "success_rate": round(success_rate, 2),
            "response_history_size": len(self.response_history),
            "performance_metrics": self.performance_metrics,
        }

    def get_pattern_stats(self) -> dict[str, Any]:
        """Get statistics for all patterns"""
        pattern_stats = {}

        for pattern_id, pattern in self.reactive_patterns.items():
            pattern_stats[pattern_id] = {
                "name": pattern.name,
                "description": pattern.description,
                "stimulus_type": pattern.stimulus_type.value,
                "response_type": pattern.response_type.value,
                "enabled": pattern.enabled,
                "priority": pattern.priority,
                "execution_count": pattern.execution_count,
                "success_rate": round(pattern.success_rate, 2),
                "last_executed": (
                    pattern.last_executed.isoformat() if pattern.last_executed else None
                ),
            }

        return pattern_stats


# Predefined reactive patterns
class ReactivePatterns:
    """Collection of predefined reactive patterns"""

    @staticmethod
    async def load_balancing_pattern(orchestrator: ReactiveAgentOrchestrator):
        """Register load balancing reactive pattern"""

        async def load_balance_handler(parameters: dict[str, Any]) -> dict[str, Any]:
            # Implement load balancing logic
            agent_load = parameters.get("agent_load", {})
            if agent_load:
                # Find least loaded agent
                least_loaded = min(agent_load.items(), key=lambda x: x[1])
                return {"action": "redirect", "target_agent": least_loaded[0]}
            return {"action": "no_action"}

        await orchestrator.register_reactive_pattern(
            stimulus_type=StimulusType.PERFORMANCE_ALERT,
            response_type=ResponseType.IMMEDIATE,
            handler=load_balance_handler,
            name="Load Balancing",
            description="Automatically balance load across agents",
            priority=10,
        )

    @staticmethod
    async def error_recovery_pattern(orchestrator: ReactiveAgentOrchestrator):
        """Register error recovery reactive pattern"""

        async def error_recovery_handler(parameters: dict[str, Any]) -> dict[str, Any]:
            error_type = parameters.get("error_type")
            agent_id = parameters.get("agent_id")

            if error_type == "timeout":
                return {"action": "retry", "agent_id": agent_id, "max_retries": 3}
            if error_type == "resource_exhausted":
                return {"action": "scale_up", "resource_type": "memory"}
            return {"action": "fallback", "fallback_agent": "backup_agent"}

        await orchestrator.register_reactive_pattern(
            stimulus_type=StimulusType.ERROR_OCCURRED,
            response_type=ResponseType.IMMEDIATE,
            handler=error_recovery_handler,
            name="Error Recovery",
            description="Automatically recover from errors",
            priority=9,
        )

    @staticmethod
    async def resource_optimization_pattern(orchestrator: ReactiveAgentOrchestrator):
        """Register resource optimization reactive pattern"""

        async def resource_optimization_handler(
            parameters: dict[str, Any],
        ) -> dict[str, Any]:
            resource_usage = parameters.get("resource_usage", {})

            if resource_usage.get("memory_usage", 0) > 80:
                return {"action": "cleanup_cache", "target": "memory"}
            if resource_usage.get("cpu_usage", 0) > 90:
                return {"action": "throttle_requests", "factor": 0.5}
            return {"action": "no_action"}

        await orchestrator.register_reactive_pattern(
            stimulus_type=StimulusType.RESOURCE_UPDATE,
            response_type=ResponseType.CONDITIONAL,
            handler=resource_optimization_handler,
            name="Resource Optimization",
            description="Optimize resource usage based on metrics",
            priority=8,
        )

    @staticmethod
    async def user_experience_pattern(orchestrator: ReactiveAgentOrchestrator):
        """Register user experience reactive pattern"""

        async def user_experience_handler(parameters: dict[str, Any]) -> dict[str, Any]:
            response_time = parameters.get("response_time", 0)
            user_satisfaction = parameters.get("user_satisfaction", 0)

            if response_time > 5.0:
                return {"action": "optimize_response", "target": "response_time"}
            if user_satisfaction < 0.7:
                return {"action": "improve_accuracy", "target": "response_quality"}
            return {"action": "maintain_quality"}

        await orchestrator.register_reactive_pattern(
            stimulus_type=StimulusType.USER_INPUT,
            response_type=ResponseType.DELAYED,
            handler=user_experience_handler,
            name="User Experience",
            description="Improve user experience based on feedback",
            priority=7,
        )


# Global reactive orchestrator instance
reactive_orchestrator = ReactiveAgentOrchestrator("system_reactive_orchestrator")
