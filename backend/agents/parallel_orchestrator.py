"""
Parallel Orchestrator for FoodSave AI

This module implements parallel agent processing and advanced orchestration patterns
for improved performance and scalability.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any
import uuid

from agents.interfaces import AgentResponse, AgentType, BaseAgent, MemoryContext
from agents.orchestrator import AsyncCircuitBreaker, CircuitBreakerError
from core.async_agent_communication import (
    AgentMessage,
    AsyncAgentCommunicator,
    MessageType,
    Priority,
)

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of execution tasks"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionStrategy(Enum):
    """Execution strategies for task orchestration"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    CONDITIONAL = "conditional"
    SCATTER_GATHER = "scatter_gather"


@dataclass
class ExecutionTask:
    """Task definition for parallel execution"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: AgentType = AgentType.GENERAL
    input_data: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)  # Task IDs this task depends on
    priority: Priority = Priority.NORMAL
    timeout: float | None = None
    retries: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: AgentResponse | None = None
    error: Exception | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float | None:
        """Get task execution duration"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_ready(self) -> bool:
        """Check if task is ready to execute (all dependencies met)"""
        return self.status == TaskStatus.PENDING


@dataclass
class ExecutionPlan:
    """Execution plan containing multiple tasks with dependencies"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tasks: dict[str, ExecutionTask] = field(default_factory=dict)
    strategy: ExecutionStrategy = ExecutionStrategy.PARALLEL
    timeout: float | None = None
    context: MemoryContext | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def add_task(self, task: ExecutionTask) -> None:
        """Add task to execution plan"""
        self.tasks[task.id] = task

    def get_ready_tasks(self) -> list[ExecutionTask]:
        """Get tasks that are ready to execute"""
        ready_tasks = []
        for task in self.tasks.values():
            if task.is_ready:
                # Check if all dependencies are completed
                dependencies_met = True
                for dep_id in task.depends_on:
                    dep_task = self.tasks.get(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                        dependencies_met = False
                        break

                if dependencies_met:
                    ready_tasks.append(task)

        return sorted(ready_tasks, key=lambda t: t.priority.value, reverse=True)

    def get_dependency_graph(self) -> dict[str, list[str]]:
        """Get dependency graph for visualization"""
        return {task_id: task.depends_on for task_id, task in self.tasks.items()}

    @property
    def is_complete(self) -> bool:
        """Check if all tasks are completed"""
        return all(
            task.status
            in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            for task in self.tasks.values()
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate of completed tasks"""
        completed_tasks = [
            task
            for task in self.tasks.values()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]
        if not completed_tasks:
            return 0.0

        successful_tasks = [
            task for task in completed_tasks if task.status == TaskStatus.COMPLETED
        ]
        return len(successful_tasks) / len(completed_tasks)


class ParallelOrchestrator:
    """Advanced parallel orchestrator with sophisticated execution patterns"""

    def __init__(
        self,
        agents: dict[AgentType, BaseAgent],
        max_parallel_tasks: int = 10,
        default_timeout: float = 30.0,
    ):
        self.agents = agents
        self.max_parallel_tasks = max_parallel_tasks
        self.default_timeout = default_timeout

        # Communication system
        self.communicator = AsyncAgentCommunicator("orchestrator")

        # Circuit breakers for each agent type
        self.circuit_breakers: dict[AgentType, AsyncCircuitBreaker] = {
            agent_type: AsyncCircuitBreaker(
                f"agent_{agent_type.value}", fail_max=3, reset_timeout=60
            )
            for agent_type in agents
        }

        # Task execution tracking
        self.active_plans: dict[str, ExecutionPlan] = {}
        self.execution_stats = {
            "total_plans": 0,
            "completed_plans": 0,
            "failed_plans": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_plan_duration": 0.0,
            "avg_task_duration": 0.0,
        }

        # Task semaphore to limit parallel execution
        self.task_semaphore = asyncio.Semaphore(max_parallel_tasks)

        logger.info(
            f"Initialized ParallelOrchestrator with {len(agents)} agents, max_parallel={max_parallel_tasks}"
        )

    async def initialize(self) -> None:
        """Initialize orchestrator and communication system"""
        await self.communicator.connect()
        await self.communicator.start_processing()

        # Register message handlers
        self.communicator.register_handler(
            MessageType.COMMAND, self._handle_command_message
        )
        self.communicator.register_handler(
            MessageType.QUERY, self._handle_query_message
        )

        logger.info("ParallelOrchestrator initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown orchestrator and cleanup resources"""
        # Cancel active plans
        for plan in self.active_plans.values():
            await self._cancel_plan(plan.id)

        await self.communicator.disconnect()
        logger.info("ParallelOrchestrator shutdown completed")

    async def execute_plan(self, plan: ExecutionPlan) -> dict[str, AgentResponse]:
        """Execute an execution plan with specified strategy"""
        plan_start_time = datetime.now()
        self.active_plans[plan.id] = plan
        self.execution_stats["total_plans"] += 1

        try:
            logger.info(f"Executing plan {plan.id} with strategy {plan.strategy.value}")

            if plan.strategy == ExecutionStrategy.SEQUENTIAL:
                results = await self._execute_sequential(plan)
            elif plan.strategy == ExecutionStrategy.PARALLEL:
                results = await self._execute_parallel(plan)
            elif plan.strategy == ExecutionStrategy.PIPELINE:
                results = await self._execute_pipeline(plan)
            elif plan.strategy == ExecutionStrategy.CONDITIONAL:
                results = await self._execute_conditional(plan)
            elif plan.strategy == ExecutionStrategy.SCATTER_GATHER:
                results = await self._execute_scatter_gather(plan)
            else:
                raise ValueError(f"Unsupported execution strategy: {plan.strategy}")

            # Update statistics
            plan_duration = (datetime.now() - plan_start_time).total_seconds()
            self.execution_stats["completed_plans"] += 1
            self.execution_stats["avg_plan_duration"] = (
                self.execution_stats["avg_plan_duration"]
                * (self.execution_stats["completed_plans"] - 1)
                + plan_duration
            ) / self.execution_stats["completed_plans"]

            logger.info(
                f"Plan {plan.id} completed successfully in {plan_duration:.2f}s"
            )
            return results

        except Exception as e:
            self.execution_stats["failed_plans"] += 1
            logger.error(f"Plan {plan.id} failed: {e}")
            raise
        finally:
            self.active_plans.pop(plan.id, None)

    async def _execute_sequential(
        self, plan: ExecutionPlan
    ) -> dict[str, AgentResponse]:
        """Execute tasks sequentially respecting dependencies"""
        results = {}

        while not plan.is_complete:
            ready_tasks = plan.get_ready_tasks()

            if not ready_tasks:
                # Check for deadlock or all remaining tasks failed
                remaining_tasks = [
                    task
                    for task in plan.tasks.values()
                    if task.status == TaskStatus.PENDING
                ]
                if remaining_tasks:
                    logger.error(
                        f"Deadlock detected in plan {plan.id} - no ready tasks but {len(remaining_tasks)} pending"
                    )
                    break
                else:
                    break  # All tasks completed

            # Execute one task at a time
            task = ready_tasks[0]
            try:
                result = await self._execute_single_task(task, plan.context)
                results[task.id] = result
            except Exception as e:
                logger.error(f"Task {task.id} failed in sequential execution: {e}")
                task.status = TaskStatus.FAILED
                task.error = e

        return results

    async def _execute_parallel(self, plan: ExecutionPlan) -> dict[str, AgentResponse]:
        """Execute tasks in parallel respecting dependencies and limits"""
        results = {}
        active_tasks: set[asyncio.Task] = set()

        while not plan.is_complete or active_tasks:
            # Start new tasks if possible
            ready_tasks = plan.get_ready_tasks()

            for task in ready_tasks:
                if len(active_tasks) >= self.max_parallel_tasks:
                    break

                # Create and start task
                async_task = asyncio.create_task(
                    self._execute_single_task(task, plan.context)
                )
                async_task.add_done_callback(
                    lambda t, task_id=task.id: self._task_completed(task_id, t)
                )
                active_tasks.add(async_task)

                # Store task reference for result collection
                async_task.task_id = task.id  # type: ignore

            # Wait for at least one task to complete
            if active_tasks:
                done, pending = await asyncio.wait(
                    active_tasks, return_when=asyncio.FIRST_COMPLETED
                )

                for completed_task in done:
                    task_id = getattr(completed_task, "task_id", None)
                    try:
                        result = await completed_task
                        if task_id:
                            results[task_id] = result
                    except Exception as e:
                        if task_id:
                            plan.tasks[task_id].status = TaskStatus.FAILED
                            plan.tasks[task_id].error = e
                        logger.error(f"Task {task_id} failed: {e}")

                active_tasks = pending

            # Break if no progress possible
            if not ready_tasks and not active_tasks:
                break

        return results

    async def _execute_pipeline(self, plan: ExecutionPlan) -> dict[str, AgentResponse]:
        """Execute tasks in pipeline fashion (streaming data between stages)"""
        # Sort tasks by dependencies to create pipeline stages
        stages = self._create_pipeline_stages(plan)
        results = {}

        # Process each stage
        for stage_tasks in stages:
            stage_results = await asyncio.gather(
                *[
                    self._execute_single_task(task, plan.context)
                    for task in stage_tasks
                ],
                return_exceptions=True,
            )

            for task, result in zip(stage_tasks, stage_results, strict=False):
                if isinstance(result, Exception):
                    task.status = TaskStatus.FAILED
                    task.error = result
                    logger.error(f"Pipeline task {task.id} failed: {result}")
                else:
                    results[task.id] = result
                    # Pass result to dependent tasks
                    self._propagate_pipeline_data(task, result, plan)

        return results

    async def _execute_conditional(
        self, plan: ExecutionPlan
    ) -> dict[str, AgentResponse]:
        """Execute tasks with conditional logic based on previous results"""
        results = {}

        while not plan.is_complete:
            ready_tasks = plan.get_ready_tasks()

            if not ready_tasks:
                break

            # Execute ready tasks and evaluate conditions
            for task in ready_tasks:
                # Check if task should execute based on conditions
                if self._evaluate_task_conditions(task, results, plan):
                    try:
                        result = await self._execute_single_task(task, plan.context)
                        results[task.id] = result
                    except Exception as e:
                        task.status = TaskStatus.FAILED
                        task.error = e
                        logger.error(f"Conditional task {task.id} failed: {e}")
                else:
                    # Skip task based on conditions
                    task.status = TaskStatus.CANCELLED
                    logger.info(f"Task {task.id} skipped due to conditions")

        return results

    async def _execute_scatter_gather(
        self, plan: ExecutionPlan
    ) -> dict[str, AgentResponse]:
        """Execute tasks in scatter-gather pattern"""
        # Identify scatter and gather phases
        scatter_tasks = [task for task in plan.tasks.values() if not task.depends_on]
        gather_tasks = [task for task in plan.tasks.values() if task.depends_on]

        results = {}

        # Scatter phase - execute independent tasks in parallel
        if scatter_tasks:
            logger.info(f"Scatter phase: executing {len(scatter_tasks)} tasks")
            scatter_results = await asyncio.gather(
                *[
                    self._execute_single_task(task, plan.context)
                    for task in scatter_tasks
                ],
                return_exceptions=True,
            )

            for task, result in zip(scatter_tasks, scatter_results, strict=False):
                if isinstance(result, Exception):
                    task.status = TaskStatus.FAILED
                    task.error = result
                else:
                    results[task.id] = result

        # Gather phase - execute dependent tasks
        if gather_tasks:
            logger.info(f"Gather phase: executing {len(gather_tasks)} tasks")
            for task in gather_tasks:
                try:
                    # Collect results from dependencies
                    dependency_results = {
                        dep_id: results.get(dep_id)
                        for dep_id in task.depends_on
                        if dep_id in results
                    }

                    # Add dependency results to task input
                    task.input_data["dependency_results"] = dependency_results

                    result = await self._execute_single_task(task, plan.context)
                    results[task.id] = result
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = e
                    logger.error(f"Gather task {task.id} failed: {e}")

        return results

    async def _execute_single_task(
        self, task: ExecutionTask, context: MemoryContext | None
    ) -> AgentResponse:
        """Execute a single task with circuit breaker protection"""
        async with self.task_semaphore:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            self.execution_stats["total_tasks"] += 1

            try:
                agent = self.agents.get(task.agent_type)
                if not agent:
                    raise ValueError(f"Agent type {task.agent_type} not available")

                circuit_breaker = self.circuit_breakers[task.agent_type]

                # Execute with circuit breaker protection
                result = await circuit_breaker.call_async(
                    agent.process, task.input_data
                )

                task.status = TaskStatus.COMPLETED
                task.result = result
                task.end_time = datetime.now()

                # Update statistics
                self.execution_stats["completed_tasks"] += 1
                if task.duration:
                    self.execution_stats["avg_task_duration"] = (
                        self.execution_stats["avg_task_duration"]
                        * (self.execution_stats["completed_tasks"] - 1)
                        + task.duration
                    ) / self.execution_stats["completed_tasks"]

                logger.debug(
                    f"Task {task.id} completed successfully in {task.duration:.2f}s"
                )
                return result

            except CircuitBreakerError as e:
                task.status = TaskStatus.FAILED
                task.error = e
                task.end_time = datetime.now()
                self.execution_stats["failed_tasks"] += 1
                logger.warning(f"Task {task.id} failed due to circuit breaker: {e}")
                raise

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = e
                task.end_time = datetime.now()
                self.execution_stats["failed_tasks"] += 1

                # Retry logic
                if task.retries < task.max_retries:
                    task.retries += 1
                    task.status = TaskStatus.PENDING
                    logger.warning(
                        f"Task {task.id} failed, retrying ({task.retries}/{task.max_retries}): {e}"
                    )
                    await asyncio.sleep(2**task.retries)  # Exponential backoff
                    return await self._execute_single_task(task, context)

                logger.error(f"Task {task.id} failed after {task.retries} retries: {e}")
                raise

    def _create_pipeline_stages(self, plan: ExecutionPlan) -> list[list[ExecutionTask]]:
        """Create pipeline stages based on task dependencies"""
        stages = []
        remaining_tasks = set(plan.tasks.values())

        while remaining_tasks:
            stage_tasks = []

            for task in list(remaining_tasks):
                # Check if all dependencies are satisfied by previous stages
                dependencies_satisfied = all(
                    dep_id not in [t.id for t in remaining_tasks]
                    for dep_id in task.depends_on
                )

                if dependencies_satisfied:
                    stage_tasks.append(task)
                    remaining_tasks.remove(task)

            if not stage_tasks:
                # Circular dependency detected
                logger.error("Circular dependency detected in pipeline")
                break

            stages.append(stage_tasks)

        return stages

    def _propagate_pipeline_data(
        self, task: ExecutionTask, result: AgentResponse, plan: ExecutionPlan
    ) -> None:
        """Propagate data from completed task to dependent tasks"""
        for dependent_task in plan.tasks.values():
            if task.id in dependent_task.depends_on:
                # Add result to dependent task's input
                if "pipeline_data" not in dependent_task.input_data:
                    dependent_task.input_data["pipeline_data"] = {}
                dependent_task.input_data["pipeline_data"][task.id] = result.data

    def _evaluate_task_conditions(
        self,
        task: ExecutionTask,
        results: dict[str, AgentResponse],
        plan: ExecutionPlan,
    ) -> bool:
        """Evaluate whether a task should execute based on conditions"""
        conditions = task.metadata.get("conditions", {})

        for condition_type, condition_value in conditions.items():
            if condition_type == "required_success":
                # Task only executes if specified tasks succeeded
                required_tasks = condition_value
                for req_task_id in required_tasks:
                    if req_task_id not in results or not results[req_task_id].success:
                        return False

            elif condition_type == "required_failure":
                # Task only executes if specified tasks failed
                required_failures = condition_value
                for req_task_id in required_failures:
                    if req_task_id not in results or results[req_task_id].success:
                        return False

            elif condition_type == "data_condition":
                # Task executes based on data from previous tasks
                pass
                # Implement custom data condition logic here

        return True

    def _task_completed(self, task_id: str, async_task: asyncio.Task) -> None:
        """Callback when an async task completes"""
        logger.debug(f"Async task for {task_id} completed")

    async def _cancel_plan(self, plan_id: str) -> None:
        """Cancel an active execution plan"""
        plan = self.active_plans.get(plan_id)
        if plan:
            for task in plan.tasks.values():
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.CANCELLED
            logger.info(f"Cancelled execution plan {plan_id}")

    async def _handle_command_message(self, message: AgentMessage) -> None:
        """Handle command messages for orchestration"""
        command = message.data.get("command")

        if command == "execute_plan":
            plan_data = message.data.get("plan")
            if plan_data:
                # Reconstruct execution plan and execute
                plan = self._deserialize_plan(plan_data)
                results = await self.execute_plan(plan)

                # Send response
                await self.communicator.send_response(
                    message,
                    {
                        "results": {
                            task_id: result.model_dump()
                            for task_id, result in results.items()
                        },
                        "plan_id": plan.id,
                    },
                )

    async def _handle_query_message(self, message: AgentMessage) -> None:
        """Handle query messages for status and statistics"""
        query = message.data.get("query")

        if query == "stats":
            await self.communicator.send_response(
                message,
                {
                    "stats": self.execution_stats,
                    "active_plans": len(self.active_plans),
                    "circuit_breaker_status": {
                        agent_type.value: {
                            "state": cb.state,
                            "failure_count": cb.failure_count,
                        }
                        for agent_type, cb in self.circuit_breakers.items()
                    },
                },
            )

        elif query == "active_plans":
            plans_info = {}
            for plan_id, plan in self.active_plans.items():
                plans_info[plan_id] = {
                    "strategy": plan.strategy.value,
                    "task_count": len(plan.tasks),
                    "completed_tasks": len(
                        [
                            t
                            for t in plan.tasks.values()
                            if t.status == TaskStatus.COMPLETED
                        ]
                    ),
                    "running_tasks": len(
                        [
                            t
                            for t in plan.tasks.values()
                            if t.status == TaskStatus.RUNNING
                        ]
                    ),
                    "success_rate": plan.success_rate,
                }

            await self.communicator.send_response(message, {"active_plans": plans_info})

    def _deserialize_plan(self, plan_data: dict[str, Any]) -> ExecutionPlan:
        """Deserialize execution plan from dictionary"""
        # Implementation for deserializing plan data
        # This would convert the plan_data dict back to an ExecutionPlan object

    def get_orchestrator_stats(self) -> dict[str, Any]:
        """Get comprehensive orchestrator statistics"""
        return {
            "execution_stats": self.execution_stats,
            "active_plans": len(self.active_plans),
            "max_parallel_tasks": self.max_parallel_tasks,
            "circuit_breakers": {
                agent_type.value: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure_time": (
                        cb.last_failure_time.isoformat()
                        if cb.last_failure_time
                        else None
                    ),
                }
                for agent_type, cb in self.circuit_breakers.items()
            },
            "communication_stats": self.communicator.get_stats(),
        }


# Utility functions for creating execution plans


def create_sequential_plan(
    tasks: list[tuple[AgentType, dict[str, Any]]], context: MemoryContext | None = None
) -> ExecutionPlan:
    """Create a sequential execution plan"""
    plan = ExecutionPlan(strategy=ExecutionStrategy.SEQUENTIAL, context=context)

    previous_task_id = None
    for agent_type, input_data in tasks:
        task = ExecutionTask(
            agent_type=agent_type,
            input_data=input_data,
            depends_on=[previous_task_id] if previous_task_id else [],
        )
        plan.add_task(task)
        previous_task_id = task.id

    return plan


def create_parallel_plan(
    tasks: list[tuple[AgentType, dict[str, Any]]], context: MemoryContext | None = None
) -> ExecutionPlan:
    """Create a parallel execution plan"""
    plan = ExecutionPlan(strategy=ExecutionStrategy.PARALLEL, context=context)

    for agent_type, input_data in tasks:
        task = ExecutionTask(agent_type=agent_type, input_data=input_data)
        plan.add_task(task)

    return plan


def create_scatter_gather_plan(
    scatter_tasks: list[tuple[AgentType, dict[str, Any]]],
    gather_tasks: list[tuple[AgentType, dict[str, Any]]],
    context: MemoryContext | None = None,
) -> ExecutionPlan:
    """Create a scatter-gather execution plan"""
    plan = ExecutionPlan(strategy=ExecutionStrategy.SCATTER_GATHER, context=context)

    scatter_task_ids = []

    # Add scatter tasks (no dependencies)
    for agent_type, input_data in scatter_tasks:
        task = ExecutionTask(agent_type=agent_type, input_data=input_data)
        plan.add_task(task)
        scatter_task_ids.append(task.id)

    # Add gather tasks (depend on all scatter tasks)
    for agent_type, input_data in gather_tasks:
        task = ExecutionTask(
            agent_type=agent_type, input_data=input_data, depends_on=scatter_task_ids
        )
        plan.add_task(task)

    return plan
