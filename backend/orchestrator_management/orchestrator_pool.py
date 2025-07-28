import asyncio
import contextlib
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class OrchestratorState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class OrchestratorInstance:
    id: str
    orchestrator: Any  # Tutaj EnhancedOrchestrator, ale unikamy cyklicznego importu
    state: OrchestratorState
    last_health_check: float
    failure_count: int = 0


class OrchestratorPool:
    def __init__(self, max_failures: int = 3, health_check_interval: int = 30) -> None:
        self.instances: list[OrchestratorInstance] = []
        self.current_index = 0
        self.max_failures = max_failures
        self.health_check_interval = health_check_interval
        self._health_check_task: asyncio.Task | None = None

    async def add_instance(self, orchestrator_id: str, orchestrator: Any) -> None:
        """Dodaje instancję orkiestratora do puli."""
        instance = OrchestratorInstance(
            id=orchestrator_id,
            orchestrator=orchestrator,
            state=OrchestratorState.HEALTHY,
            last_health_check=asyncio.get_event_loop().time(),
        )
        self.instances.append(instance)
        logger.info(f"Orchestrator instance '{orchestrator_id}' added to pool.")

    async def get_healthy_orchestrator(self) -> Any | None:
        """
        Zwraca kolejny zdrowy orkiestrator z puli, używając algorytmu round-robin.
        Jeśli brak zdrowych, próbuje użyć zdegradowanych.
        """
        logger.debug(
            f"get_healthy_orchestrator called. Total instances: {len(self.instances)}"
        )

        # Log all instances and their states
        for i, instance in enumerate(self.instances):
            logger.debug(
                f"Instance {i}: id={instance.id}, state={instance.state}, failure_count={instance.failure_count}"
            )

        healthy_instances = [
            i for i in self.instances if i.state == OrchestratorState.HEALTHY
        ]

        logger.debug(f"Found {len(healthy_instances)} healthy instances")

        if not healthy_instances:
            logger.warning(
                "No healthy orchestrator instances available. Trying degraded instances."
            )
            degraded_instances = [
                i for i in self.instances if i.state == OrchestratorState.DEGRADED
            ]
            logger.debug(f"Found {len(degraded_instances)} degraded instances")

            if degraded_instances:
                # W przypadku braku zdrowych, wybierz pierwszy zdegradowany
                selected_instance = degraded_instances[0]
                logger.debug(f"Selected degraded instance: {selected_instance.id}")
                return selected_instance.orchestrator
            logger.error("No available orchestrator instances (healthy or degraded).")
            return None

        # Round-robin
        selected_instance = healthy_instances[self.current_index]
        logger.debug(
            f"Selected healthy instance: {selected_instance.id} (index: {self.current_index})"
        )
        orchestrator_to_return = selected_instance.orchestrator
        self.current_index = (self.current_index + 1) % len(healthy_instances)
        return orchestrator_to_return

    def release_orchestrator(self, orchestrator: Any) -> None:
        """
        Release orchestrator back to pool. Currently a no-op since we don't track usage.
        """
        logger.debug("Releasing orchestrator back to pool")
        # In a more sophisticated implementation, this would track usage and availability
        # For now, we just log the release

    async def _run_health_checks(self) -> None:
        """Cykl przeprowadzania testów zdrowia dla wszystkich instancji."""
        while True:
            for instance in self.instances:
                await self._check_instance_health(instance)
            await asyncio.sleep(self.health_check_interval)

    async def _check_instance_health(self, instance: OrchestratorInstance) -> None:
        """Sprawdza zdrowie pojedynczej instancji orkiestratora."""
        try:
            logger.debug(
                f"Running health check for orchestrator instance '{instance.id}'"
            )

            # Simple health check - verify that orchestrator has required components
            orchestrator = instance.orchestrator

            # Check if orchestrator has required attributes
            required_attrs = [
                "profile_manager",
                "intent_detector",
                "agent_router",
                "memory_manager",
            ]
            missing_attrs = [
                attr
                for attr in required_attrs
                if not hasattr(orchestrator, attr)
                or getattr(orchestrator, attr) is None
            ]

            if missing_attrs:
                await self._mark_failed(
                    instance, f"Missing required components: {missing_attrs}"
                )
                return

            # Check if orchestrator can process a simple command
            try:
                # Use a simple health check command that should always work
                health_response = await orchestrator.process_command(
                    user_command="health",
                    session_id=f"health_check_{instance.id}",
                )

                if health_response and health_response.success:
                    await self._mark_healthy(instance)
                else:
                    await self._mark_failed(
                        instance,
                        f"Health check failed with response: {health_response.error if health_response else 'No response'}",
                    )
            except Exception as e:
                await self._mark_failed(instance, f"Health check command failed: {e!s}")

        except Exception as e:
            logger.error(
                f"Health check exception for '{instance.id}': {e!s}", exc_info=True
            )
            await self._mark_failed(instance, f"Health check threw exception: {e!s}")

    async def _mark_healthy(self, instance: OrchestratorInstance) -> None:
        if instance.state != OrchestratorState.HEALTHY:
            logger.info(f"Orchestrator '{instance.id}' is now HEALTHY.")
        instance.failure_count = 0
        instance.state = OrchestratorState.HEALTHY
        instance.last_health_check = asyncio.get_event_loop().time()

    async def _mark_failed(self, instance: OrchestratorInstance, reason: str) -> None:
        instance.failure_count += 1
        current_time = asyncio.get_event_loop().time()

        if (
            instance.failure_count >= self.max_failures
            and instance.state != OrchestratorState.FAILED
        ):
            instance.state = OrchestratorState.FAILED
            logger.error(
                f"Orchestrator '{instance.id}' marked as FAILED due to {reason} "
                f"after {instance.failure_count} failures."
            )
        elif instance.state != OrchestratorState.DEGRADED:
            instance.state = OrchestratorState.DEGRADED
            logger.warning(
                f"Orchestrator '{instance.id}' marked as DEGRADED due to {reason}. "
                f"Failures: {instance.failure_count}/{self.max_failures}."
            )
        instance.last_health_check = current_time

    async def start_health_checks(self) -> None:
        """Uruchamia zadanie w tle do regularnych testów zdrowia."""
        if not self._health_check_task or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._run_health_checks())
            logger.info("Orchestrator health checks started.")

    async def shutdown(self) -> None:
        """Zatrzymuje zadanie testów zdrowia i zamyka orkiestratory."""
        if self._health_check_task:
            self._health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._health_check_task
        for instance in self.instances:
            if hasattr(instance.orchestrator, "shutdown"):
                await instance.orchestrator.shutdown()
        logger.info("Orchestrator pool shut down.")


# Global instance of the orchestrator pool
orchestrator_pool = OrchestratorPool()
