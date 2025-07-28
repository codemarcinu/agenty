"""Intelligent Agent Pool with Load Balancing and Resource Monitoring"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any

import psutil

from core.event_bus import AgentEvent, EventDrivenAgentCommunication, EventType

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_LOADED = "least_loaded"
    ADAPTIVE = "adaptive"
    CONSISTENT_HASH = "consistent_hash"


class AgentHealth(Enum):
    """Agent health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class AgentMetrics:
    """Real-time agent metrics"""

    agent_id: str
    agent_type: str
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    total_tasks: int = 0
    success_rate: float = 100.0
    avg_response_time: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    health_status: AgentHealth = AgentHealth.UNKNOWN
    load_capacity: int = 10
    current_load: int = 0
    weight: float = 1.0
    performance_score: float = 1.0

    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return self.health_status in [AgentHealth.HEALTHY, AgentHealth.DEGRADED]

    def is_overloaded(self) -> bool:
        """Check if agent is overloaded"""
        return self.current_load >= self.load_capacity

    def get_load_percentage(self) -> float:
        """Get current load percentage"""
        return (
            (self.current_load / self.load_capacity) * 100
            if self.load_capacity > 0
            else 0
        )

    def update_performance_score(self) -> None:
        """Update performance score based on metrics"""
        # Calculate performance score based on multiple factors
        health_factor = 1.0 if self.health_status == AgentHealth.HEALTHY else 0.5
        load_factor = 1.0 - (self.get_load_percentage() / 100)
        success_factor = self.success_rate / 100
        response_factor = max(
            0.1, 1.0 - (self.avg_response_time / 1000)
        )  # Normalize to 1 second

        self.performance_score = (
            health_factor * 0.3
            + load_factor * 0.3
            + success_factor * 0.2
            + response_factor * 0.2
        )


@dataclass
class SystemMetrics:
    """System-wide metrics"""

    total_cpu_usage: float = 0.0
    total_memory_usage: float = 0.0
    total_agents: int = 0
    healthy_agents: int = 0
    active_tasks: int = 0
    avg_response_time: float = 0.0
    system_load: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class IntelligentAgentPool:
    """Intelligent agent pool with advanced load balancing"""

    def __init__(
        self,
        pool_id: str,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE,
    ):
        self.pool_id = pool_id
        self.strategy = strategy

        # Agent management
        self.agents: dict[str, AgentMetrics] = {}
        self.agent_instances: dict[str, Any] = {}  # Actual agent instances

        # Load balancing state
        self.current_index = 0
        self.agent_weights: dict[str, float] = {}
        self.consistent_hash_ring: dict[int, str] = {}

        # Communication
        self.event_communication = EventDrivenAgentCommunication(pool_id)

        # Performance tracking
        self.performance_metrics = {
            "requests_processed": 0,
            "avg_response_time": 0.0,
            "load_balancing_decisions": 0,
            "agent_failures": 0,
            "rebalancing_events": 0,
        }

        # System monitoring
        self.system_metrics = SystemMetrics()

        # Background tasks
        self.metrics_collector_task: asyncio.Task | None = None
        self.health_checker_task: asyncio.Task | None = None
        self.rebalancing_task: asyncio.Task | None = None

        # Configuration
        self.health_check_interval = 30.0  # seconds
        self.metrics_collection_interval = 10.0  # seconds
        self.rebalancing_interval = 60.0  # seconds
        self.max_agent_load = 0.8  # 80% load threshold
        self.min_healthy_agents = 2

        logger.info(
            f"IntelligentAgentPool {pool_id} initialized with strategy: {strategy.value}"
        )

    async def initialize(self):
        """Initialize the intelligent pool"""
        # Subscribe to agent events
        await self.event_communication.subscribe_to_events(
            [
                EventType.AGENT_STATE_CHANGE.value,
                EventType.TASK_COMPLETION.value,
                EventType.ERROR_EVENT.value,
                "agent_heartbeat",
                "agent_metrics_update",
            ],
            self._handle_agent_event,
        )

        # Start background tasks
        self.metrics_collector_task = asyncio.create_task(self._collect_metrics())
        self.health_checker_task = asyncio.create_task(self._check_agent_health())
        self.rebalancing_task = asyncio.create_task(self._rebalancing_monitor())

        logger.info(f"IntelligentAgentPool {self.pool_id} initialized")

    async def shutdown(self):
        """Shutdown the intelligent pool"""
        if self.metrics_collector_task:
            self.metrics_collector_task.cancel()
        if self.health_checker_task:
            self.health_checker_task.cancel()
        if self.rebalancing_task:
            self.rebalancing_task.cancel()

        logger.info(f"IntelligentAgentPool {self.pool_id} shutdown")

    async def register_agent(
        self,
        agent_id: str,
        agent_instance: Any,
        agent_type: str,
        load_capacity: int = 10,
        weight: float = 1.0,
    ) -> bool:
        """Register an agent with the pool"""
        try:
            metrics = AgentMetrics(
                agent_id=agent_id,
                agent_type=agent_type,
                load_capacity=load_capacity,
                weight=weight,
                health_status=AgentHealth.HEALTHY,
            )

            self.agents[agent_id] = metrics
            self.agent_instances[agent_id] = agent_instance
            self.agent_weights[agent_id] = weight

            # Update consistent hash ring
            self._update_consistent_hash_ring()

            # Update system metrics
            self.system_metrics.total_agents = len(self.agents)
            self.system_metrics.healthy_agents = len(
                [a for a in self.agents.values() if a.is_healthy()]
            )

            logger.info(
                f"Agent {agent_id} registered with capacity {load_capacity}, weight {weight}"
            )
            return True

        except Exception as e:
            logger.error(f"Error registering agent {agent_id}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the pool"""
        try:
            if agent_id in self.agents:
                del self.agents[agent_id]
                del self.agent_instances[agent_id]
                if agent_id in self.agent_weights:
                    del self.agent_weights[agent_id]

                # Update consistent hash ring
                self._update_consistent_hash_ring()

                # Update system metrics
                self.system_metrics.total_agents = len(self.agents)
                self.system_metrics.healthy_agents = len(
                    [a for a in self.agents.values() if a.is_healthy()]
                )

                logger.info(f"Agent {agent_id} unregistered")
                return True
            return False

        except Exception as e:
            logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False

    async def get_agent(
        self, task_type: str | None = None, priority: int = 1
    ) -> Any | None:
        """Get an agent using the configured load balancing strategy"""
        try:
            healthy_agents = [a for a in self.agents.values() if a.is_healthy()]

            if not healthy_agents:
                logger.warning("No healthy agents available")
                return None

            # Filter by task type if specified
            if task_type:
                suitable_agents = [
                    a for a in healthy_agents if a.agent_type == task_type
                ]
                if not suitable_agents:
                    logger.warning(f"No agents available for task type: {task_type}")
                    return None
                healthy_agents = suitable_agents

            # Select agent based on strategy
            selected_agent_id = await self._select_agent(healthy_agents, priority)

            if selected_agent_id:
                agent = self.agents[selected_agent_id]
                agent.current_load += 1
                agent.active_tasks += 1
                agent.total_tasks += 1

                self.performance_metrics["load_balancing_decisions"] += 1

                logger.debug(
                    f"Selected agent {selected_agent_id} for task (load: {agent.current_load}/{agent.load_capacity})"
                )
                return self.agent_instances[selected_agent_id]

            return None

        except Exception as e:
            logger.error(f"Error selecting agent: {e}")
            return None

    async def release_agent(
        self, agent_id: str, success: bool = True, response_time: float = 0.0
    ):
        """Release an agent back to the pool"""
        try:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.current_load = max(0, agent.current_load - 1)
                agent.active_tasks = max(0, agent.active_tasks - 1)

                # Update success rate
                if agent.total_tasks > 0:
                    if success:
                        successful_tasks = (
                            int((agent.success_rate / 100) * agent.total_tasks) + 1
                        )
                        agent.success_rate = (
                            successful_tasks / agent.total_tasks
                        ) * 100
                    else:
                        agent.success_rate = max(0, agent.success_rate - 1)

                # Update response time
                if response_time > 0:
                    agent.avg_response_time = (
                        agent.avg_response_time + response_time
                    ) / 2

                # Update performance score
                agent.update_performance_score()

                logger.debug(
                    f"Released agent {agent_id} (load: {agent.current_load}/{agent.load_capacity})"
                )

        except Exception as e:
            logger.error(f"Error releasing agent {agent_id}: {e}")

    async def _select_agent(
        self, healthy_agents: list[AgentMetrics], priority: int
    ) -> str | None:
        """Select agent based on load balancing strategy"""
        if not healthy_agents:
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_agents)
        if self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_agents)
        if self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._least_loaded_select(healthy_agents)
        if self.strategy == LoadBalancingStrategy.ADAPTIVE:
            return self._adaptive_select(healthy_agents, priority)
        if self.strategy == LoadBalancingStrategy.CONSISTENT_HASH:
            return self._consistent_hash_select(healthy_agents)
        return self._round_robin_select(healthy_agents)

    def _round_robin_select(self, healthy_agents: list[AgentMetrics]) -> str:
        """Round-robin selection"""
        if not healthy_agents:
            return None

        selected_agent = healthy_agents[self.current_index % len(healthy_agents)]
        self.current_index = (self.current_index + 1) % len(healthy_agents)
        return selected_agent.agent_id

    def _weighted_round_robin_select(self, healthy_agents: list[AgentMetrics]) -> str:
        """Weighted round-robin selection"""
        if not healthy_agents:
            return None

        # Calculate total weight
        total_weight = sum(agent.weight for agent in healthy_agents)
        if total_weight == 0:
            return self._round_robin_select(healthy_agents)

        # Use weighted selection
        current_weight = 0
        for agent in healthy_agents:
            current_weight += agent.weight
            if self.current_index < current_weight:
                self.current_index = (self.current_index + 1) % total_weight
                return agent.agent_id

        # Fallback
        return healthy_agents[0].agent_id

    def _least_loaded_select(self, healthy_agents: list[AgentMetrics]) -> str:
        """Least loaded selection"""
        if not healthy_agents:
            return None

        # Sort by load percentage and performance score
        sorted_agents = sorted(
            healthy_agents,
            key=lambda a: (a.get_load_percentage(), -a.performance_score),
        )

        return sorted_agents[0].agent_id

    def _adaptive_select(
        self, healthy_agents: list[AgentMetrics], priority: int
    ) -> str:
        """Adaptive selection based on multiple factors"""
        if not healthy_agents:
            return None

        # Calculate selection scores
        agent_scores = []
        for agent in healthy_agents:
            # Base score from performance
            score = agent.performance_score

            # Adjust for load (prefer less loaded agents)
            load_factor = 1.0 - (agent.get_load_percentage() / 100)
            score *= load_factor

            # Adjust for priority (high priority tasks prefer high-performance agents)
            if priority > 2:
                score *= agent.performance_score

            # Adjust for health status
            if agent.health_status == AgentHealth.DEGRADED:
                score *= 0.5

            agent_scores.append((agent.agent_id, score))

        # Select agent with highest score
        if agent_scores:
            selected_agent_id = max(agent_scores, key=lambda x: x[1])[0]
            return selected_agent_id

        return None

    def _consistent_hash_select(self, healthy_agents: list[AgentMetrics]) -> str:
        """Consistent hash selection"""
        if not healthy_agents:
            return None

        # Use current index as hash key
        hash_key = self.current_index
        self.current_index += 1

        # Find the next agent in the hash ring
        for i in range(hash_key, hash_key + 1000):  # Search range
            if i in self.consistent_hash_ring:
                agent_id = self.consistent_hash_ring[i]
                if agent_id in self.agents and self.agents[agent_id].is_healthy():
                    return agent_id

        # Fallback to first healthy agent
        return healthy_agents[0].agent_id

    def _update_consistent_hash_ring(self):
        """Update consistent hash ring"""
        self.consistent_hash_ring.clear()

        for agent_id in self.agents:
            # Create multiple virtual nodes for each agent
            for i in range(10):  # 10 virtual nodes per agent
                hash_value = hash(f"{agent_id}_{i}") % 1000
                self.consistent_hash_ring[hash_value] = agent_id

    async def _collect_metrics(self):
        """Collect system and agent metrics"""
        while True:
            try:
                await asyncio.sleep(self.metrics_collection_interval)

                # Collect system metrics
                self.system_metrics.total_cpu_usage = psutil.cpu_percent()
                self.system_metrics.total_memory_usage = psutil.virtual_memory().percent
                self.system_metrics.total_agents = len(self.agents)
                self.system_metrics.healthy_agents = len(
                    [a for a in self.agents.values() if a.is_healthy()]
                )
                self.system_metrics.active_tasks = sum(
                    a.active_tasks for a in self.agents.values()
                )

                # Calculate average response time
                response_times = [
                    a.avg_response_time
                    for a in self.agents.values()
                    if a.avg_response_time > 0
                ]
                if response_times:
                    self.system_metrics.avg_response_time = sum(response_times) / len(
                        response_times
                    )

                # Calculate system load
                total_load = sum(a.get_load_percentage() for a in self.agents.values())
                self.system_metrics.system_load = (
                    total_load / len(self.agents) if self.agents else 0
                )

                self.system_metrics.last_updated = datetime.now()

                # Publish metrics update event
                await self.event_communication.publish_event(
                    EventType.RESOURCE_UPDATE,
                    {
                        "pool_id": self.pool_id,
                        "system_metrics": {
                            "total_cpu_usage": self.system_metrics.total_cpu_usage,
                            "total_memory_usage": self.system_metrics.total_memory_usage,
                            "total_agents": self.system_metrics.total_agents,
                            "healthy_agents": self.system_metrics.healthy_agents,
                            "active_tasks": self.system_metrics.active_tasks,
                            "avg_response_time": self.system_metrics.avg_response_time,
                            "system_load": self.system_metrics.system_load,
                        },
                    },
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

    async def _check_agent_health(self):
        """Check health of all agents"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                for agent_id, agent in self.agents.items():
                    # Check if agent is responding
                    is_healthy = await self._check_agent_health_status(agent_id, agent)

                    if not is_healthy and agent.health_status != AgentHealth.FAILED:
                        agent.health_status = AgentHealth.FAILED
                        self.performance_metrics["agent_failures"] += 1

                        # Publish health event
                        await self.event_communication.publish_event(
                            EventType.AGENT_STATE_CHANGE,
                            {
                                "agent_id": agent_id,
                                "status": "failed",
                                "reason": "Health check failed",
                            },
                        )

                        logger.warning(f"Agent {agent_id} marked as failed")

                    elif is_healthy and agent.health_status == AgentHealth.FAILED:
                        agent.health_status = AgentHealth.HEALTHY
                        logger.info(f"Agent {agent_id} recovered")

                # Update healthy agents count
                self.system_metrics.healthy_agents = len(
                    [a for a in self.agents.values() if a.is_healthy()]
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error checking agent health: {e}")

    async def _check_agent_health_status(
        self, agent_id: str, agent: AgentMetrics
    ) -> bool:
        """Check if specific agent is healthy"""
        try:
            # Check if agent instance exists and is responsive
            if agent_id not in self.agent_instances:
                return False

            # Check if agent has been active recently
            time_since_heartbeat = (
                datetime.now() - agent.last_heartbeat
            ).total_seconds()
            if time_since_heartbeat > self.health_check_interval * 2:
                return False

            # Check if agent is overloaded
            if agent.is_overloaded():
                agent.health_status = AgentHealth.DEGRADED
                return True  # Still healthy but degraded

            return True

        except Exception as e:
            logger.error(f"Error checking health for agent {agent_id}: {e}")
            return False

    async def _rebalancing_monitor(self):
        """Monitor and trigger rebalancing when needed"""
        while True:
            try:
                await asyncio.sleep(self.rebalancing_interval)

                # Check if rebalancing is needed
                if await self._should_rebalance():
                    await self._trigger_rebalancing()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rebalancing monitor: {e}")

    async def _should_rebalance(self) -> bool:
        """Check if rebalancing is needed"""
        if len(self.agents) < 2:
            return False

        # Check load distribution
        loads = [
            a.get_load_percentage() for a in self.agents.values() if a.is_healthy()
        ]
        if not loads:
            return False

        avg_load = sum(loads) / len(loads)
        max_load = max(loads)
        min_load = min(loads)

        # Rebalance if load distribution is uneven
        load_variance = max_load - min_load
        if load_variance > 30:  # More than 30% difference
            return True

        # Rebalance if average load is too high
        return avg_load > 80

    async def _trigger_rebalancing(self):
        """Trigger rebalancing of agent loads"""
        try:
            self.performance_metrics["rebalancing_events"] += 1

            # Publish rebalancing event
            await self.event_communication.publish_event(
                EventType.COORDINATION_EVENT,
                {
                    "type": "rebalancing",
                    "pool_id": self.pool_id,
                    "reason": "Load distribution optimization",
                },
            )

            logger.info("Agent pool rebalancing triggered")

        except Exception as e:
            logger.error(f"Error triggering rebalancing: {e}")

    async def _handle_agent_event(self, event: AgentEvent):
        """Handle agent-related events"""
        try:
            if event.type == EventType.AGENT_STATE_CHANGE:
                await self._handle_agent_state_change(event)
            elif event.type == EventType.TASK_COMPLETION:
                await self._handle_task_completion(event)
            elif event.type == EventType.ERROR_EVENT:
                await self._handle_error_event(event)
            elif event.data.get("type") == "agent_heartbeat":
                await self._handle_agent_heartbeat(event)
            elif event.data.get("type") == "agent_metrics_update":
                await self._handle_agent_metrics_update(event)

        except Exception as e:
            logger.error(f"Error handling agent event: {e}")

    async def _handle_agent_state_change(self, event: AgentEvent):
        """Handle agent state change event"""
        agent_id = event.data.get("agent_id")
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.last_heartbeat = datetime.now()

    async def _handle_task_completion(self, event: AgentEvent):
        """Handle task completion event"""
        agent_id = event.data.get("agent_id")
        success = event.data.get("success", True)
        response_time = event.data.get("response_time", 0.0)

        if agent_id:
            await self.release_agent(agent_id, success, response_time)

    async def _handle_error_event(self, event: AgentEvent):
        """Handle error event"""
        agent_id = event.data.get("agent_id")
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.health_status = AgentHealth.DEGRADED

    async def _handle_agent_heartbeat(self, event: AgentEvent):
        """Handle agent heartbeat"""
        agent_id = event.data.get("agent_id")
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.last_heartbeat = datetime.now()

    async def _handle_agent_metrics_update(self, event: AgentEvent):
        """Handle agent metrics update"""
        agent_id = event.data.get("agent_id")
        if agent_id in self.agents:
            agent = self.agents[agent_id]

            # Update metrics from event data
            metrics_data = event.data.get("metrics", {})
            if "cpu_usage" in metrics_data:
                agent.cpu_usage = metrics_data["cpu_usage"]
            if "memory_usage" in metrics_data:
                agent.memory_usage = metrics_data["memory_usage"]
            if "active_tasks" in metrics_data:
                agent.active_tasks = metrics_data["active_tasks"]

            agent.update_performance_score()

    def get_pool_stats(self) -> dict[str, Any]:
        """Get pool statistics"""
        return {
            "pool_id": self.pool_id,
            "strategy": self.strategy.value,
            "total_agents": len(self.agents),
            "healthy_agents": len([a for a in self.agents.values() if a.is_healthy()]),
            "system_metrics": {
                "total_cpu_usage": self.system_metrics.total_cpu_usage,
                "total_memory_usage": self.system_metrics.total_memory_usage,
                "active_tasks": self.system_metrics.active_tasks,
                "avg_response_time": self.system_metrics.avg_response_time,
                "system_load": self.system_metrics.system_load,
            },
            "performance_metrics": self.performance_metrics,
            "agent_details": {
                agent_id: {
                    "type": agent.agent_type,
                    "health": agent.health_status.value,
                    "load": f"{agent.current_load}/{agent.load_capacity}",
                    "performance_score": agent.performance_score,
                    "success_rate": agent.success_rate,
                    "avg_response_time": agent.avg_response_time,
                }
                for agent_id, agent in self.agents.items()
            },
        }
