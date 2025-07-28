"""
Hierarchical Multi-Agent Architecture with Manager-Worker Pattern
Zgodnie z regułami MDC dla skalowalnych systemów wieloagentowych
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from typing import Any
import uuid

from agents.base_agent import BaseAgent
from core.event_bus import (
    AgentEvent,
    EventDrivenAgentCommunication,
    EventPriority,
)

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in hierarchical architecture"""

    MANAGER = "manager"
    WORKER = "worker"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"


class TaskStatus(Enum):
    """Task status in hierarchical system"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class HierarchicalTask:
    """Task in hierarchical system"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    task_type: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str | None = None
    manager_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    estimated_duration: float | None = None
    actual_duration: float | None = None
    dependencies: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)
    result: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentNode:
    """Node in hierarchical agent tree"""

    agent_id: str
    agent_type: str
    role: AgentRole
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    load_capacity: int = 10
    current_load: int = 0
    is_active: bool = True
    last_heartbeat: datetime = field(default_factory=datetime.now)
    performance_metrics: dict[str, float] = field(default_factory=dict)


class ManagerAgent(BaseAgent):
    """Manager agent for coordinating worker agents"""

    def __init__(self, manager_id: str, **kwargs):
        super().__init__(**kwargs)
        self.manager_id = manager_id
        self.role = AgentRole.MANAGER

        # Worker management
        self.workers: dict[str, AgentNode] = {}
        self.available_workers: set[str] = set()

        # Task management
        self.tasks: dict[str, HierarchicalTask] = {}
        self.task_queue: deque = deque()
        self.completed_tasks: dict[str, HierarchicalTask] = {}

        # Communication
        self.event_communication = EventDrivenAgentCommunication(manager_id)

        # Performance tracking
        self.performance_metrics = {
            "tasks_managed": 0,
            "workers_managed": 0,
            "avg_task_completion_time": 0.0,
            "success_rate": 100.0,
        }

        logger.info(f"ManagerAgent {manager_id} initialized")

    async def initialize(self):
        """Initialize manager agent"""
        # Subscribe to worker events
        await self.event_communication.subscribe_to_events(
            [
                "worker_heartbeat",
                "task_completed",
                "task_failed",
                "worker_available",
                "worker_busy",
            ],
            self._handle_worker_event,
        )

        # Start background tasks
        asyncio.create_task(self._monitor_workers())
        asyncio.create_task(self._process_task_queue())

        logger.info(f"ManagerAgent {self.manager_id} initialized")

    async def register_worker(
        self,
        worker_id: str,
        agent_type: str,
        capabilities: list[str],
        load_capacity: int = 10,
    ) -> bool:
        """Register a worker agent"""
        try:
            worker_node = AgentNode(
                agent_id=worker_id,
                agent_type=agent_type,
                role=AgentRole.WORKER,
                parent_id=self.manager_id,
                capabilities=capabilities,
                load_capacity=load_capacity,
            )

            self.workers[worker_id] = worker_node
            self.available_workers.add(worker_id)
            self.performance_metrics["workers_managed"] = len(self.workers)

            logger.info(
                f"Worker {worker_id} registered with capabilities: {capabilities}"
            )
            return True

        except Exception as e:
            logger.error(f"Error registering worker {worker_id}: {e}")
            return False

    async def unregister_worker(self, worker_id: str) -> bool:
        """Unregister a worker agent"""
        try:
            if worker_id in self.workers:
                # Reassign tasks if any
                await self._reassign_worker_tasks(worker_id)

                del self.workers[worker_id]
                self.available_workers.discard(worker_id)
                self.performance_metrics["workers_managed"] = len(self.workers)

                logger.info(f"Worker {worker_id} unregistered")
                return True
            return False

        except Exception as e:
            logger.error(f"Error unregistering worker {worker_id}: {e}")
            return False

    async def create_task(
        self,
        title: str,
        description: str,
        task_type: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: list[str] | None = None,
        estimated_duration: float | None = None,
    ) -> str:
        """Create a new task"""
        try:
            task = HierarchicalTask(
                title=title,
                description=description,
                task_type=task_type,
                priority=priority,
                dependencies=dependencies or [],
                estimated_duration=estimated_duration,
                manager_id=self.manager_id,
            )

            self.tasks[task.id] = task
            self.task_queue.append(task.id)

            # Sort queue by priority
            self._sort_task_queue()

            self.performance_metrics["tasks_managed"] += 1
            logger.info(f"Task created: {task.id} - {title}")

            return task.id

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return ""

    async def assign_task(self, task_id: str, worker_id: str) -> bool:
        """Assign a task to a worker"""
        try:
            if task_id not in self.tasks or worker_id not in self.workers:
                return False

            task = self.tasks[task_id]
            worker = self.workers[worker_id]

            # Check if worker can handle the task
            if not self._can_worker_handle_task(worker, task):
                logger.warning(f"Worker {worker_id} cannot handle task {task_id}")
                return False

            # Check worker capacity
            if worker.current_load >= worker.load_capacity:
                logger.warning(f"Worker {worker_id} is at capacity")
                return False

            # Assign task
            task.status = TaskStatus.ASSIGNED
            task.assigned_agent = worker_id
            worker.current_load += 1

            # Remove from available workers if at capacity
            if worker.current_load >= worker.load_capacity:
                self.available_workers.discard(worker_id)

            # Send task to worker
            await self._send_task_to_worker(task, worker_id)

            logger.info(f"Task {task_id} assigned to worker {worker_id}")
            return True

        except Exception as e:
            logger.error(f"Error assigning task {task_id} to worker {worker_id}: {e}")
            return False

    async def _send_task_to_worker(self, task: HierarchicalTask, worker_id: str):
        """Send task to worker agent"""
        task_data = {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "priority": task.priority.value,
            "estimated_duration": task.estimated_duration,
            "dependencies": task.dependencies,
            "metadata": task.metadata,
        }

        await self.event_communication.publish_event(
            "task_assignment", task_data, target=worker_id, priority=EventPriority.HIGH
        )

    def _can_worker_handle_task(
        self, worker: AgentNode, task: HierarchicalTask
    ) -> bool:
        """Check if worker can handle the task"""
        # Check capabilities
        if task.task_type not in worker.capabilities:
            return False

        # Check dependencies
        return all(dep_id in self.completed_tasks for dep_id in task.dependencies)

    def _sort_task_queue(self):
        """Sort task queue by priority"""
        # Convert to list for sorting
        task_ids = list(self.task_queue)

        # Sort by priority (highest first)
        task_ids.sort(key=lambda tid: self.tasks[tid].priority.value, reverse=True)

        # Rebuild queue
        self.task_queue.clear()
        self.task_queue.extend(task_ids)

    async def _process_task_queue(self):
        """Process task queue and assign tasks to available workers"""
        while True:
            try:
                if self.task_queue and self.available_workers:
                    task_id = self.task_queue[0]
                    task = self.tasks[task_id]

                    # Find suitable worker
                    suitable_worker = await self._find_suitable_worker(task)

                    if suitable_worker:
                        # Remove from queue
                        self.task_queue.popleft()

                        # Assign task
                        await self.assign_task(task_id, suitable_worker)
                    else:
                        # No suitable worker available, wait
                        await asyncio.sleep(1)
                else:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error processing task queue: {e}")
                await asyncio.sleep(5)

    async def _find_suitable_worker(self, task: HierarchicalTask) -> str | None:
        """Find a suitable worker for the task"""
        suitable_workers = []

        for worker_id in self.available_workers:
            worker = self.workers[worker_id]

            if self._can_worker_handle_task(worker, task):
                # Calculate worker score based on load and performance
                load_score = 1.0 - (worker.current_load / worker.load_capacity)
                performance_score = worker.performance_metrics.get("success_rate", 0.8)

                total_score = load_score * 0.6 + performance_score * 0.4
                suitable_workers.append((worker_id, total_score))

        if suitable_workers:
            # Return worker with highest score
            suitable_workers.sort(key=lambda x: x[1], reverse=True)
            return suitable_workers[0][0]

        return None

    async def _reassign_worker_tasks(self, worker_id: str):
        """Reassign tasks from a worker that is being unregistered"""
        tasks_to_reassign = [
            task_id
            for task_id, task in self.tasks.items()
            if task.assigned_agent == worker_id
            and task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]
        ]

        for task_id in tasks_to_reassign:
            task = self.tasks[task_id]
            task.status = TaskStatus.PENDING
            task.assigned_agent = None

            # Add back to queue
            self.task_queue.append(task_id)

        self._sort_task_queue()
        logger.info(
            f"Reassigned {len(tasks_to_reassign)} tasks from worker {worker_id}"
        )

    async def _monitor_workers(self):
        """Monitor worker health and performance"""
        while True:
            try:
                current_time = datetime.now()

                for worker_id, worker in self.workers.items():
                    # Check heartbeat
                    if (current_time - worker.last_heartbeat) > timedelta(minutes=5):
                        logger.warning(f"Worker {worker_id} heartbeat timeout")
                        await self.unregister_worker(worker_id)
                        continue

                    # Update performance metrics
                    if worker_id in self.workers:  # Check if still exists
                        worker.performance_metrics["uptime"] = (
                            current_time - worker.last_heartbeat
                        ).total_seconds()

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error monitoring workers: {e}")
                await asyncio.sleep(60)

    async def _handle_worker_event(self, event: AgentEvent):
        """Handle events from workers"""
        try:
            if event.type == "worker_heartbeat":
                await self._handle_worker_heartbeat(event)
            elif event.type == "task_completed":
                await self._handle_task_completed(event)
            elif event.type == "task_failed":
                await self._handle_task_failed(event)
            elif event.type == "worker_available":
                await self._handle_worker_available(event)
            elif event.type == "worker_busy":
                await self._handle_worker_busy(event)

        except Exception as e:
            logger.error(f"Error handling worker event: {e}")

    async def _handle_worker_heartbeat(self, event: AgentEvent):
        """Handle worker heartbeat"""
        worker_id = event.payload.get("worker_id")
        if worker_id in self.workers:
            self.workers[worker_id].last_heartbeat = datetime.now()

            # Update performance metrics
            if "performance_metrics" in event.payload:
                self.workers[worker_id].performance_metrics.update(
                    event.payload["performance_metrics"]
                )

    async def _handle_task_completed(self, event: AgentEvent):
        """Handle task completion"""
        task_id = event.payload.get("task_id")
        worker_id = event.payload.get("worker_id")
        result = event.payload.get("result")
        duration = event.payload.get("duration")

        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.actual_duration = duration

            # Move to completed tasks
            self.completed_tasks[task_id] = task
            del self.tasks[task_id]

            # Update worker load
            if worker_id in self.workers:
                self.workers[worker_id].current_load = max(
                    0, self.workers[worker_id].current_load - 1
                )

                # Add back to available workers if under capacity
                if (
                    self.workers[worker_id].current_load
                    < self.workers[worker_id].load_capacity
                ):
                    self.available_workers.add(worker_id)

            # Update performance metrics
            if duration:
                self.performance_metrics["avg_task_completion_time"] = (
                    self.performance_metrics["avg_task_completion_time"] + duration
                ) / 2

            logger.info(f"Task {task_id} completed by worker {worker_id}")

    async def _handle_task_failed(self, event: AgentEvent):
        """Handle task failure"""
        task_id = event.payload.get("task_id")
        worker_id = event.payload.get("worker_id")
        error = event.payload.get("error")

        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error

            # Update worker load
            if worker_id in self.workers:
                self.workers[worker_id].current_load = max(
                    0, self.workers[worker_id].current_load - 1
                )

                # Add back to available workers if under capacity
                if (
                    self.workers[worker_id].current_load
                    < self.workers[worker_id].load_capacity
                ):
                    self.available_workers.add(worker_id)

            # Requeue task if retryable
            if task.metadata.get("retryable", True):
                task.status = TaskStatus.PENDING
                task.assigned_agent = None
                task.error = None
                self.task_queue.append(task_id)
                self._sort_task_queue()
                logger.info(f"Task {task_id} requeued for retry")
            else:
                logger.error(f"Task {task_id} failed permanently: {error}")

    async def _handle_worker_available(self, event: AgentEvent):
        """Handle worker availability notification"""
        worker_id = event.payload.get("worker_id")
        if worker_id in self.workers:
            self.available_workers.add(worker_id)
            logger.debug(f"Worker {worker_id} marked as available")

    async def _handle_worker_busy(self, event: AgentEvent):
        """Handle worker busy notification"""
        worker_id = event.payload.get("worker_id")
        if worker_id in self.workers:
            self.available_workers.discard(worker_id)
            logger.debug(f"Worker {worker_id} marked as busy")

    def get_manager_stats(self) -> dict[str, Any]:
        """Get manager statistics"""
        total_tasks = len(self.tasks) + len(self.completed_tasks)
        completed_tasks = len(self.completed_tasks)
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "manager_id": self.manager_id,
            "total_tasks": total_tasks,
            "pending_tasks": len(self.tasks),
            "completed_tasks": completed_tasks,
            "active_workers": len(self.available_workers),
            "total_workers": len(self.workers),
            "queue_size": len(self.task_queue),
            "success_rate": round(success_rate, 2),
            "avg_task_completion_time": self.performance_metrics[
                "avg_task_completion_time"
            ],
            "performance_metrics": self.performance_metrics,
        }


class WorkerAgent(BaseAgent):
    """Worker agent for executing tasks"""

    def __init__(
        self, worker_id: str, agent_type: str, capabilities: list[str], **kwargs
    ):
        super().__init__(**kwargs)
        self.worker_id = worker_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.role = AgentRole.WORKER

        # Task management
        self.current_task: HierarchicalTask | None = None
        self.task_history: list[HierarchicalTask] = []

        # Communication
        self.event_communication = EventDrivenAgentCommunication(worker_id)

        # Performance tracking
        self.performance_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_task_duration": 0.0,
            "success_rate": 100.0,
            "uptime": 0.0,
        }

        logger.info(
            f"WorkerAgent {worker_id} initialized with capabilities: {capabilities}"
        )

    async def initialize(self):
        """Initialize worker agent"""
        # Subscribe to manager events
        await self.event_communication.subscribe_to_events(
            ["task_assignment"], self._handle_manager_event
        )

        # Start background tasks
        asyncio.create_task(self._send_heartbeat())

        logger.info(f"WorkerAgent {self.worker_id} initialized")

    async def _send_heartbeat(self):
        """Send periodic heartbeat to manager"""
        while True:
            try:
                heartbeat = {
                    "worker_id": self.worker_id,
                    "agent_type": self.agent_type,
                    "capabilities": self.capabilities,
                    "current_load": 1 if self.current_task else 0,
                    "is_available": self.current_task is None,
                    "performance_metrics": self.performance_metrics,
                    "timestamp": datetime.now().isoformat(),
                }

                await self.event_communication.publish_event(
                    "worker_heartbeat", heartbeat, priority=EventPriority.NORMAL
                )

                await asyncio.sleep(30)  # Send heartbeat every 30 seconds

            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                await asyncio.sleep(60)

    async def _handle_manager_event(self, event: AgentEvent):
        """Handle events from manager"""
        try:
            if event.type == "task_assignment":
                await self._handle_task_assignment(event)

        except Exception as e:
            logger.error(f"Error handling manager event: {e}")

    async def _handle_task_assignment(self, event: AgentEvent):
        """Handle task assignment from manager"""
        payload = event.payload
        task_id = payload.get("task_id")

        if self.current_task is not None:
            logger.warning(
                f"Worker {self.worker_id} already has a task, rejecting {task_id}"
            )
            return

        # Create task object
        task = HierarchicalTask(
            id=task_id,
            title=payload.get("title", ""),
            description=payload.get("description", ""),
            task_type=payload.get("task_type", ""),
            priority=TaskPriority(payload.get("priority", TaskPriority.NORMAL.value)),
            estimated_duration=payload.get("estimated_duration"),
            dependencies=payload.get("dependencies", []),
            metadata=payload.get("metadata", {}),
        )

        self.current_task = task
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        logger.info(f"Worker {self.worker_id} received task: {task_id}")

        # Execute task
        asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: HierarchicalTask):
        """Execute the assigned task"""
        start_time = time.time()

        try:
            # Execute task based on type
            result = await self._process_task(task)

            # Calculate duration
            duration = time.time() - start_time

            # Update task
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.actual_duration = duration

            # Update performance metrics
            self.performance_metrics["tasks_completed"] += 1
            self.performance_metrics["avg_task_duration"] = (
                self.performance_metrics["avg_task_duration"] + duration
            ) / 2

            # Calculate success rate
            total_tasks = (
                self.performance_metrics["tasks_completed"]
                + self.performance_metrics["tasks_failed"]
            )
            self.performance_metrics["success_rate"] = (
                self.performance_metrics["tasks_completed"] / total_tasks * 100
            )

            # Send completion notification
            await self._notify_task_completion(task, result, duration)

            # Add to history
            self.task_history.append(task)

            # Clear current task
            self.current_task = None

            logger.info(f"Task {task.id} completed successfully in {duration:.2f}s")

        except Exception as e:
            # Handle task failure
            duration = time.time() - start_time
            task.status = TaskStatus.FAILED
            task.error = str(e)

            # Update performance metrics
            self.performance_metrics["tasks_failed"] += 1

            # Calculate success rate
            total_tasks = (
                self.performance_metrics["tasks_completed"]
                + self.performance_metrics["tasks_failed"]
            )
            self.performance_metrics["success_rate"] = (
                self.performance_metrics["tasks_completed"] / total_tasks * 100
            )

            # Send failure notification
            await self._notify_task_failure(task, str(e), duration)

            # Add to history
            self.task_history.append(task)

            # Clear current task
            self.current_task = None

            logger.error(f"Task {task.id} failed: {e}")

    async def _process_task(self, task: HierarchicalTask) -> Any:
        """Process the task based on its type"""
        # This is a simplified implementation
        # In a real system, you would have specific task processors

        if task.task_type == "text_processing":
            return await self._process_text_task(task)
        if task.task_type == "data_analysis":
            return await self._process_data_task(task)
        if task.task_type == "image_processing":
            return await self._process_image_task(task)
        # Generic task processing
        await asyncio.sleep(task.estimated_duration or 1.0)
        return {"status": "completed", "task_id": task.id, "worker_id": self.worker_id}

    async def _process_text_task(self, task: HierarchicalTask) -> dict[str, Any]:
        """Process text-related tasks"""
        # Simulate text processing
        await asyncio.sleep(task.estimated_duration or 2.0)
        return {
            "type": "text_processing",
            "result": f"Processed text: {task.description[:50]}...",
            "word_count": len(task.description.split()),
            "processing_time": task.estimated_duration or 2.0,
        }

    async def _process_data_task(self, task: HierarchicalTask) -> dict[str, Any]:
        """Process data analysis tasks"""
        # Simulate data analysis
        await asyncio.sleep(task.estimated_duration or 5.0)
        return {
            "type": "data_analysis",
            "result": "Data analysis completed",
            "records_processed": 1000,
            "analysis_time": task.estimated_duration or 5.0,
        }

    async def _process_image_task(self, task: HierarchicalTask) -> dict[str, Any]:
        """Process image-related tasks"""
        # Simulate image processing
        await asyncio.sleep(task.estimated_duration or 3.0)
        return {
            "type": "image_processing",
            "result": "Image processed successfully",
            "resolution": "1920x1080",
            "processing_time": task.estimated_duration or 3.0,
        }

    async def _notify_task_completion(
        self, task: HierarchicalTask, result: Any, duration: float
    ):
        """Notify manager of task completion"""
        completion_data = {
            "task_id": task.id,
            "worker_id": self.worker_id,
            "result": result,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

        await self.event_communication.publish_event(
            "task_completed", completion_data, priority=EventPriority.HIGH
        )

    async def _notify_task_failure(
        self, task: HierarchicalTask, error: str, duration: float
    ):
        """Notify manager of task failure"""
        failure_data = {
            "task_id": task.id,
            "worker_id": self.worker_id,
            "error": error,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

        await self.event_communication.publish_event(
            "task_failed", failure_data, priority=EventPriority.HIGH
        )

    def get_worker_stats(self) -> dict[str, Any]:
        """Get worker statistics"""
        return {
            "worker_id": self.worker_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "current_task": self.current_task.id if self.current_task else None,
            "tasks_completed": self.performance_metrics["tasks_completed"],
            "tasks_failed": self.performance_metrics["tasks_failed"],
            "success_rate": round(self.performance_metrics["success_rate"], 2),
            "avg_task_duration": round(
                self.performance_metrics["avg_task_duration"], 2
            ),
            "is_available": self.current_task is None,
            "performance_metrics": self.performance_metrics,
        }


class HierarchicalAgentSystem:
    """Main hierarchical agent system"""

    def __init__(self):
        self.managers: dict[str, ManagerAgent] = {}
        self.workers: dict[str, WorkerAgent] = {}
        self.system_stats = {
            "total_managers": 0,
            "total_workers": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "system_uptime": 0.0,
        }
        self.start_time = datetime.now()

        logger.info("HierarchicalAgentSystem initialized")

    async def create_manager(self, manager_id: str) -> ManagerAgent:
        """Create a new manager agent"""
        manager = ManagerAgent(manager_id)
        await manager.initialize()

        self.managers[manager_id] = manager
        self.system_stats["total_managers"] = len(self.managers)

        logger.info(f"Manager {manager_id} created")
        return manager

    async def create_worker(
        self, worker_id: str, agent_type: str, capabilities: list[str], manager_id: str
    ) -> WorkerAgent:
        """Create a new worker agent"""
        worker = WorkerAgent(worker_id, agent_type, capabilities)
        await worker.initialize()

        self.workers[worker_id] = worker
        self.system_stats["total_workers"] = len(self.workers)

        # Register with manager
        if manager_id in self.managers:
            await self.managers[manager_id].register_worker(
                worker_id, agent_type, capabilities
            )

        logger.info(
            f"Worker {worker_id} created and registered with manager {manager_id}"
        )
        return worker

    async def create_complex_task(
        self, title: str, description: str, subtasks: list[dict[str, Any]]
    ) -> str:
        """Create a complex task with subtasks"""
        # This would be implemented to create a task that requires multiple workers
        # For now, return a simple task ID
        return str(uuid.uuid4())

    def get_system_stats(self) -> dict[str, Any]:
        """Get system statistics"""
        total_tasks = 0
        completed_tasks = 0

        for manager in self.managers.values():
            stats = manager.get_manager_stats()
            total_tasks += stats["total_tasks"]
            completed_tasks += stats["completed_tasks"]

        self.system_stats["total_tasks"] = total_tasks
        self.system_stats["completed_tasks"] = completed_tasks
        self.system_stats["system_uptime"] = (
            datetime.now() - self.start_time
        ).total_seconds()

        return {
            "system_stats": self.system_stats,
            "managers": {
                mid: manager.get_manager_stats()
                for mid, manager in self.managers.items()
            },
            "workers": {
                wid: worker.get_worker_stats() for wid, worker in self.workers.items()
            },
        }


# Global hierarchical system instance
hierarchical_system = HierarchicalAgentSystem()
