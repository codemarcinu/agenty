"""
Multi-Agent System Optimization Example

This example demonstrates how to use the new optimization components:
- Event-driven communication
- Intelligent load balancing
- Advanced caching
- Hierarchical architecture
- Reactive patterns
"""

import asyncio
import logging
import time
from typing import Any

from agents.hierarchical_architecture import HierarchicalAgentSystem
from core.event_bus import EventDrivenAgentCommunication, global_event_bus
from core.multi_agent_cache import (
    CacheLevel,
    CacheStrategy,
    MultiAgentCacheManager,
)
from core.reactive_patterns import (
    ReactiveAgentOrchestrator,
    ResponseType,
    StimulusType,
)
from orchestrator_management.intelligent_pool import (
    IntelligentAgentPool,
    LoadBalancingStrategy,
)

logger = logging.getLogger(__name__)


class OptimizedMultiAgentSystem:
    """Example of an optimized multi-agent system"""

    def __init__(self, system_id: str):
        self.system_id = system_id

        # Initialize components
        self.event_communication = EventDrivenAgentCommunication(system_id)
        self.intelligent_pool = IntelligentAgentPool(
            pool_id=f"{system_id}_pool", strategy=LoadBalancingStrategy.ADAPTIVE
        )
        self.cache_manager = MultiAgentCacheManager(
            agent_id=system_id, coordination_strategy=CacheStrategy.VOTING
        )
        self.hierarchical_system = HierarchicalAgentSystem()
        self.reactive_orchestrator = ReactiveAgentOrchestrator(f"{system_id}_reactive")

        # Agent instances
        self.agents: dict[str, Any] = {}

        logger.info(f"OptimizedMultiAgentSystem {system_id} initialized")

    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing optimized multi-agent system...")

        # Initialize components
        await self.event_communication.initialize()
        await self.intelligent_pool.initialize()
        await self.cache_manager.initialize()
        await self.reactive_orchestrator.initialize()

        # Register with global event bus
        await global_event_bus.register_agent(self.system_id, self.event_communication)

        # Set up reactive patterns
        await self._setup_reactive_patterns()

        # Create hierarchical structure
        await self._create_hierarchical_structure()

        logger.info("Optimized multi-agent system initialized successfully")

    async def shutdown(self):
        """Shutdown all components"""
        logger.info("Shutting down optimized multi-agent system...")

        await self.event_communication.shutdown()
        await self.intelligent_pool.shutdown()
        await self.cache_manager.shutdown()
        await self.reactive_orchestrator.shutdown()

        await global_event_bus.unregister_agent(self.system_id)

        logger.info("Optimized multi-agent system shutdown complete")

    async def _setup_reactive_patterns(self):
        """Set up reactive patterns for system optimization"""

        # Load balancing pattern
        async def load_balance_handler(parameters: dict[str, Any]) -> dict[str, Any]:
            """Handle load balancing stimulus"""
            pool_stats = self.intelligent_pool.get_pool_stats()
            if pool_stats["system_metrics"]["system_load"] > 80:
                # Trigger rebalancing
                await self.intelligent_pool._trigger_rebalancing()
                return {"action": "rebalancing_triggered", "reason": "high_load"}
            return {
                "action": "no_action_needed",
                "load": pool_stats["system_metrics"]["system_load"],
            }

        await self.reactive_orchestrator.register_reactive_pattern(
            stimulus_type=StimulusType.RESOURCE_UPDATE,
            response_type=ResponseType.IMMEDIATE,
            handler=load_balance_handler,
            name="load_balancing_pattern",
            description="Automatically trigger load balancing when system load is high",
        )

        # Error recovery pattern
        async def error_recovery_handler(parameters: dict[str, Any]) -> dict[str, Any]:
            """Handle error recovery stimulus"""
            agent_id = parameters.get("agent_id")
            if agent_id and agent_id in self.agents:
                # Attempt to recover agent
                await self._recover_agent(agent_id)
                return {"action": "agent_recovery_attempted", "agent_id": agent_id}
            return {"action": "no_recovery_needed"}

        await self.reactive_orchestrator.register_reactive_pattern(
            stimulus_type=StimulusType.ERROR_OCCURRED,
            response_type=ResponseType.IMMEDIATE,
            handler=error_recovery_handler,
            name="error_recovery_pattern",
            description="Automatically attempt to recover failed agents",
        )

        # Cache optimization pattern
        async def cache_optimization_handler(
            parameters: dict[str, Any],
        ) -> dict[str, Any]:
            """Handle cache optimization stimulus"""
            cache_stats = await self.cache_manager.get_cache_stats()
            if cache_stats["local_hits"] < cache_stats["local_misses"]:
                # Optimize cache
                await self.cache_manager.clear_cache(CacheLevel.LOCAL)
                return {"action": "cache_cleared", "reason": "low_hit_rate"}
            return {"action": "no_cache_optimization_needed"}

        await self.reactive_orchestrator.register_reactive_pattern(
            stimulus_type=StimulusType.PERFORMANCE_ALERT,
            response_type=ResponseType.DELAYED,
            handler=cache_optimization_handler,
            name="cache_optimization_pattern",
            description="Optimize cache when performance degrades",
        )

    async def _create_hierarchical_structure(self):
        """Create hierarchical agent structure"""

        # Create manager
        manager = await self.hierarchical_system.create_manager("main_manager")
        await manager.initialize()

        # Create workers
        worker_types = [
            ("search_worker", "search", ["text_search", "image_search"]),
            ("analysis_worker", "analysis", ["data_analysis", "text_analysis"]),
            (
                "processing_worker",
                "processing",
                ["image_processing", "data_processing"],
            ),
        ]

        for worker_id, agent_type, capabilities in worker_types:
            worker = await self.hierarchical_system.create_worker(
                worker_id, agent_type, capabilities, "main_manager"
            )
            await worker.initialize()

            # Register with intelligent pool
            await self.intelligent_pool.register_agent(
                agent_id=worker_id,
                agent_instance=worker,
                agent_type=agent_type,
                load_capacity=15,
                weight=1.0,
            )

            self.agents[worker_id] = worker

    async def _recover_agent(self, agent_id: str):
        """Attempt to recover a failed agent"""
        try:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                await agent.initialize()

                # Re-register with pool
                await self.intelligent_pool.register_agent(
                    agent_id=agent_id,
                    agent_instance=agent,
                    agent_type=agent.agent_type,
                    load_capacity=15,
                    weight=1.0,
                )

                logger.info(f"Agent {agent_id} recovered successfully")
        except Exception as e:
            logger.error(f"Failed to recover agent {agent_id}: {e}")

    async def process_request(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Process a request using the optimized system"""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f"request_{hash(str(request_data))}"
            cached_result = await self.cache_manager.get(cache_key, CacheLevel.SHARED)

            if cached_result:
                logger.info("Request served from cache")
                return {
                    "success": True,
                    "result": cached_result,
                    "source": "cache",
                    "response_time": time.time() - start_time,
                }

            # Get appropriate agent from intelligent pool
            task_type = request_data.get("task_type", "general")
            priority = request_data.get("priority", 1)

            agent = await self.intelligent_pool.get_agent(
                task_type=task_type, priority=priority
            )

            if not agent:
                return {
                    "success": False,
                    "error": "No suitable agent available",
                    "response_time": time.time() - start_time,
                }

            # Process request
            result = await agent.process_task(request_data)

            # Cache result
            await self.cache_manager.set(
                cache_key, result, ttl=3600, cache_level=CacheLevel.SHARED
            )

            # Release agent
            response_time = time.time() - start_time
            await self.intelligent_pool.release_agent(
                agent.worker_id, success=True, response_time=response_time
            )

            return {
                "success": True,
                "result": result,
                "source": "agent",
                "response_time": response_time,
            }

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
            }

    async def get_system_stats(self) -> dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "system_id": self.system_id,
            "pool_stats": self.intelligent_pool.get_pool_stats(),
            "cache_stats": await self.cache_manager.get_cache_stats(),
            "reactive_stats": self.reactive_orchestrator.get_orchestrator_stats(),
            "event_stats": self.event_communication.get_metrics(),
        }


async def main():
    """Main example function"""
    logging.basicConfig(level=logging.INFO)

    # Create optimized system
    system = OptimizedMultiAgentSystem("example_system")

    try:
        # Initialize system
        await system.initialize()

        # Example requests
        requests = [
            {
                "task_type": "search",
                "query": "Find information about AI",
                "priority": 2,
            },
            {
                "task_type": "analysis",
                "data": "Sample data for analysis",
                "priority": 1,
            },
            {"task_type": "processing", "input": "Process this data", "priority": 3},
        ]

        # Process requests
        for i, request in enumerate(requests):
            logger.info(f"Processing request {i + 1}")
            result = await system.process_request(request)
            logger.info(f"Request {i + 1} result: {result}")

            # Small delay between requests
            await asyncio.sleep(0.1)

        # Get system stats
        stats = await system.get_system_stats()
        logger.info("System statistics:")
        logger.info(f"Pool stats: {stats['pool_stats']}")
        logger.info(f"Cache stats: {stats['cache_stats']}")
        logger.info(f"Reactive stats: {stats['reactive_stats']}")
        logger.info(f"Event stats: {stats['event_stats']}")

    finally:
        # Shutdown system
        await system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
