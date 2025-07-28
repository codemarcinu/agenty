from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any
import uuid

from agents.error_types import ErrorSeverity
from agents.executor import Executor
from agents.interfaces import AgentResponse, AgentType, IntentData
from agents.memory_manager import MemoryManager
from agents.orchestrator_errors import OrchestratorError
from agents.planner import Planner
from agents.synthesizer import Synthesizer
from models.user_profile import InteractionType

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from sqlalchemy.ext.asyncio import AsyncSession

    from agents.base_agent import BaseAgent
    from agents.intent_detector import SimpleIntentDetector as IntentDetector
    from agents.response_generator import ResponseGenerator
    from agents.router_service import AgentRouter
    from core.profile_manager import ProfileManager

logger = logging.getLogger(__name__)


class CircuitBreakerError(Exception):
    """Custom exception for circuit breaker errors"""


class AsyncCircuitBreaker:
    """Simple async circuit breaker implementation"""

    def __init__(self, name: str, fail_max: int = 3, reset_timeout: int = 60) -> None:
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

        logger.info(
            f"Initialized AsyncCircuitBreaker({name}) with fail_max={fail_max}, reset_timeout={reset_timeout}"
        )

    async def call_async(
        self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute async function with circuit breaker protection"""
        try:
            # Check circuit breaker state
            if self.state == "OPEN":
                if (
                    self.last_failure_time
                    and datetime.now() - self.last_failure_time
                    > timedelta(seconds=self.reset_timeout)
                ):
                    self.state = "HALF_OPEN"
                    logger.info(f"CircuitBreaker({self.name}) moved to HALF_OPEN")
                else:
                    raise CircuitBreakerError(
                        f"CircuitBreaker {self.name} is OPEN. Try again later."
                    )

            # Execute function
            result = await func(*args, **kwargs)

            # Success - reset failure count
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                logger.info(f"CircuitBreaker({self.name}) moved to CLOSED")

            self.failure_count = 0
            return result

        except Exception as e:
            # Increment failure count
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            # Check if circuit should open
            if self.failure_count >= self.fail_max:
                self.state = "OPEN"
                logger.warning(
                    f"CircuitBreaker({self.name}) moved to OPEN after {self.failure_count} failures"
                )

            # Re-raise the original exception
            raise e


class Orchestrator:
    """Enhanced orchestrator with planner-executor-synthesizer architecture"""

    def __init__(
        self,
        db_session: AsyncSession,
        profile_manager: ProfileManager | None = None,
        intent_detector: IntentDetector | None = None,
        agent_router: AgentRouter | None = None,
        memory_manager: MemoryManager | None = None,
        response_generator: ResponseGenerator | None = None,
        orchestrator_id: str | None = None,
        use_planner_executor: bool = False,  # Tymczasowo wyłączone
    ) -> None:
        self.db = db_session
        self.profile_manager = profile_manager
        self.intent_detector = intent_detector
        self.agent_router = agent_router
        self.memory_manager = memory_manager or MemoryManager(
            enable_persistence=True, enable_semantic_cache=True
        )
        self.response_generator = response_generator
        self.orchestrator_id = orchestrator_id or str(uuid.uuid4())
        self.use_planner_executor = use_planner_executor

        # Initialize new architecture components
        if self.use_planner_executor:
            self.planner = Planner()
            self.executor = Executor()
            self.synthesizer = Synthesizer()
        else:
            self.planner = None
            self.executor = None
            self.synthesizer = None

        # Initialize circuit breaker for fault tolerance
        self.circuit_breaker = AsyncCircuitBreaker(
            name="orchestrator_circuit_breaker",
            fail_max=5,
            reset_timeout=60,
        )

        # Initialize memory manager if provided
        # if self.memory_manager:
        #     asyncio.create_task(self.memory_manager.initialize())

        logger.info(
            f"Orchestrator {self.orchestrator_id} initialized with {'new' if use_planner_executor else 'legacy'} architecture"
        )

        # Registered agents will be added via register_agent()
        self._agents: dict[AgentType, BaseAgent] = {}
        self._fallback_agent: BaseAgent | None = None

    async def initialize(self) -> None:
        """Initialize orchestrator components"""
        if (
            self.use_planner_executor
            and self.planner
            and self.executor
            and self.synthesizer
        ):
            await self.planner.initialize()
            await self.executor.initialize()
            await self.synthesizer.initialize()
            logger.info("New architecture components initialized")

    def _initialize_default_agents(self) -> None:
        """Initialize default agents - now properly implemented"""
        logger.info("Initializing default agents")
        try:
            # This method is now properly implemented but agents are injected
            # via factory
            # The actual agent initialization happens in AgentFactory
            logger.info(
                "Default agent initialization completed via dependency injection"
            )
        except Exception as e:
            logger.error(f"Error initializing default agents: {e}")

    def _format_error_response(self, error: Exception) -> AgentResponse:
        """Format a standardized error response using AgentResponse"""
        if isinstance(error, OrchestratorError | ValueError):
            error_message = (
                str(error) or "An error occurred while processing your request"
            )
        else:
            error_message = "An error occurred while processing your request"
        return AgentResponse(
            success=False,
            error=error_message,
            severity=ErrorSeverity.HIGH.value,
            request_id=str(uuid.uuid4()),
            data={
                "error_type": type(error).__name__,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def process_file(
        self,
        file_bytes: bytes,
        filename: str,
        session_id: str,
        content_type: str,
    ) -> AgentResponse:
        """Process an uploaded file through the orchestrator
        (OCR + structured analysis pipeline)"""
        try:
            # 1. Get user profile and context
            if self.profile_manager is None:
                logger.error("Profile manager is None")
                return self._format_error_response(
                    OrchestratorError("Profile manager not initialized")
                )

            await self.profile_manager.get_or_create_profile(session_id)

            if self.memory_manager is None:
                logger.error("Memory manager is None")
                return self._format_error_response(
                    OrchestratorError("Memory manager not initialized")
                )

            context = await self.memory_manager.get_context(session_id)

            # 2. Log activity
            await self.profile_manager.log_activity(
                session_id, InteractionType.FILE_UPLOAD, filename
            )

            # 3. Determine intent based on file type
            intent_type = (
                "image_processing"
                if content_type.startswith("image/")
                else (
                    "document_processing" if content_type == "application/pdf" else None
                )
            )

            if not intent_type:
                raise ValueError(f"Unsupported content type: {content_type}")

            # 4. Create intent data
            intent = IntentData(
                type=intent_type,
                entities={"filename": filename, "content_type": content_type},
            )

            # 5. Route to OCR agent with circuit breaker
            try:
                if self.agent_router is None:
                    logger.error("Agent router is None")
                    return self._format_error_response(
                        OrchestratorError("Agent router not initialized")
                    )

                # --- STAGE 1: OCR ---
                ocr_response = await self.circuit_breaker.call_async(
                    self.agent_router.route_to_agent,
                    intent,
                    context,
                    user_command=filename,
                    file_bytes=file_bytes,  # Pass file bytes to agent
                )

                if not ocr_response.success or not ocr_response.text:
                    return ocr_response

                # --- STAGE 2: Structured Receipt Analysis ---
                # Prepare intent for analysis
                analysis_intent = IntentData(
                    type="receipt_processing",
                    entities={"ocr_text": ocr_response.text, "filename": filename},
                )
                analysis_response = await self.circuit_breaker.call_async(
                    self.agent_router.route_to_agent,
                    analysis_intent,
                    context,
                    user_command=filename,
                )

                # Add file data to context
                await self.memory_manager.update_context(
                    context,
                    {"file_processed": filename, "response": analysis_response.data},
                )

                return analysis_response

            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker tripped: {e}")
                return self._format_error_response(
                    OrchestratorError("Service temporarily unavailable")
                )

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return self._format_error_response(e)

    async def process_query(
        self, query: str, session_id: str, **kwargs: Any
    ) -> AgentResponse:
        """Process user query through the agent system."""
        return await self.process_command(
            user_command=query, session_id=session_id, **kwargs
        )

    async def process_command(
        self,
        user_command: str,
        session_id: str,
        stream: bool = False,
        stream_callback: Callable[[dict[str, Any]], None] | None = None,
        agent_states: dict[str, bool] | None = None,
        use_perplexity: bool = False,
        use_bielik: bool = True,
    ) -> AgentResponse:
        """Process user command through the agent system"""
        request_id = str(uuid.uuid4())
        logger.info(
            f"[Request ID: {request_id}] Received command: '{user_command}' for session: {session_id}"
        )

        try:
            # Special handling for health check command
            if user_command.lower() in [
                "health",
                "health_check",
                "health_check_internal",
            ]:
                return AgentResponse(
                    success=True,
                    text="Orchestrator is healthy",
                    data={"status": "ok", "components": "all_available"},
                    request_id=request_id,
                )

            # Choose processing method based on architecture
            if (
                self.use_planner_executor
                and self.planner
                and self.executor
                and self.synthesizer
            ):
                return await self._process_with_planner_executor(
                    user_command, session_id, request_id, stream_callback
                )
            return await self._process_with_legacy_architecture(
                user_command, session_id, request_id
            )

        except OrchestratorError as e:
            logger.error(
                f"[Request ID: {request_id}] Orchestrator error: {e}", exc_info=True
            )
            return self._format_error_response(e)
        except Exception as e:
            logger.error(
                f"[Request ID: {request_id}] Unhandled error: {e}", exc_info=True
            )
            return self._format_error_response(
                OrchestratorError(f"An unexpected error occurred: {e}")
            )

    async def _process_with_planner_executor(
        self,
        user_command: str,
        session_id: str,
        request_id: str,
        stream_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> AgentResponse:
        """Process command using new planner-executor-synthesizer architecture"""
        try:
            # 1. Get user profile and context
            context = await self.memory_manager.get_context(session_id)
            context.last_command = user_command
            context.request_id = request_id

            # 2. Log activity (only if profile_manager is available)
            if self.profile_manager:
                await self.profile_manager.log_activity(
                    session_id, InteractionType.QUERY, user_command
                )

            # 3. Get conversation summary for context
            conversation_context = {}
            try:
                from tasks.conversation_tasks import get_conversation_summary

                summary_data = await get_conversation_summary(session_id)
                if summary_data:
                    conversation_context = {
                        "conversation_summary": summary_data.get("summary"),
                        "user_preferences": summary_data.get("user_preferences", {}),
                        "topics_discussed": summary_data.get("topics_discussed", []),
                    }
            except Exception as e:
                logger.warning(f"Failed to get conversation summary: {e}")

            # 4. Create execution plan
            plan = await self.planner.create_plan(user_command, conversation_context)

            # Validate plan
            if not self.planner.validate_plan(plan):
                logger.warning(
                    "Invalid plan created, falling back to legacy architecture"
                )
                return await self._process_with_legacy_architecture(
                    user_command, session_id, request_id
                )

            # 5. Set up streaming if requested
            if stream_callback:
                self.executor.set_stream_callback(stream_callback)

            # 6. Execute plan
            execution_result = await self.executor.execute_plan(
                plan, conversation_context
            )

            # 7. Synthesize final response
            final_response = await self.synthesizer.generate_response(
                execution_result, user_command, conversation_context
            )

            # 8. Update context with final response
            await self.memory_manager.update_context(
                context, {"last_response": final_response}
            )

            # 9. Trigger conversation summary update in background
            if final_response.success and len(context.history) >= 5:
                try:
                    from tasks.conversation_tasks import (
                        update_conversation_summary_task,
                    )

                    update_conversation_summary_task.delay(session_id)
                    logger.debug(
                        f"Scheduled conversation summary update for session {session_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to schedule conversation summary update: {e}"
                    )

            logger.info(
                f"[Request ID: {request_id}] Successfully processed command with new architecture"
            )
            return final_response

        except Exception as e:
            logger.error(f"Error in planner-executor processing: {e}")
            # Fallback to legacy architecture
            return await self._process_with_legacy_architecture(
                user_command, session_id, request_id
            )

    async def _process_with_legacy_architecture(
        self,
        user_command: str,
        session_id: str,
        request_id: str,
    ) -> AgentResponse:
        """Process command using optimized legacy router-based architecture"""
        try:
            # 1. Get user profile and context
            context = await self.memory_manager.get_context(session_id)
            context.last_command = user_command
            context.request_id = request_id

            # 2. Log activity (only if profile_manager is available)
            if self.profile_manager:
                await self.profile_manager.log_activity(
                    session_id, InteractionType.QUERY, user_command
                )

            # 3. OPTIMIZATION: Try smart query router for fast path
            try:
                from agents.query_router import query_router
                from agents.quick_handlers import quick_handler_registry

                routing_decision = query_router.route_query(
                    user_command, {"session_id": session_id}
                )

                logger.info(
                    f"Query routing: {routing_decision.category.value} "
                    f"(confidence: {routing_decision.confidence:.2f}, "
                    f"fast_path: {routing_decision.fast_path})"
                )

                # If high confidence and fast path available, use quick handler
                if routing_decision.fast_path and routing_decision.confidence > 0.8:
                    if quick_handler_registry.is_quick_handler(
                        routing_decision.suggested_handler
                    ):
                        logger.info(
                            f"Using quick handler: {routing_decision.suggested_handler}"
                        )

                        quick_response = (
                            await quick_handler_registry.handle_quick_query(
                                routing_decision.suggested_handler,
                                user_command,
                                routing_decision.context_hints,
                            )
                        )

                        if quick_response:
                            # Update context and return quick response
                            quick_agent_response = AgentResponse(
                                success=True,
                                text=quick_response,
                                data={
                                    "query": user_command,
                                    "routing_category": routing_decision.category.value,
                                    "handler_used": routing_decision.suggested_handler,
                                    "fast_path": True,
                                    "confidence": routing_decision.confidence,
                                    "session_id": session_id,
                                },
                                request_id=request_id,
                            )

                            await self.memory_manager.update_context(
                                context, {"last_response": quick_agent_response}
                            )

                            logger.info(
                                f"[Request ID: {request_id}] Quick handler response completed"
                            )
                            return quick_agent_response

            except Exception as e:
                logger.warning(f"Smart routing failed, falling back to legacy: {e}")

            # 4. Fallback to legacy: Detect intent
            intent = await self.intent_detector.detect_intent(user_command, context)

            # 5. Route to agent with circuit breaker
            try:
                agent_response = await self.circuit_breaker.call_async(
                    self.agent_router.route_to_agent,
                    intent,
                    context,
                    user_command=user_command,
                    db_session=self.db,
                )
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker tripped for intent {intent.type}: {e}")
                return self._format_error_response(
                    OrchestratorError(
                        "Service temporarily unavailable due to repeated errors.",
                        severity=ErrorSeverity.HIGH.value,
                    )
                )

            # 6. Update context with agent's response
            await self.memory_manager.update_context(
                context, {"last_response": agent_response}
            )

            # 7. Trigger conversation summary update in background
            if agent_response.success and len(context.history) >= 5:
                try:
                    from tasks.conversation_tasks import (
                        update_conversation_summary_task,
                    )

                    update_conversation_summary_task.delay(session_id)
                    logger.debug(
                        f"Scheduled conversation summary update for session {session_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to schedule conversation summary update: {e}"
                    )

            logger.info(
                f"[Request ID: {request_id}] Successfully processed command with legacy architecture"
            )
            return agent_response

        except Exception as e:
            logger.error(f"Error in legacy processing: {e}")
            raise

    async def shutdown(self) -> None:
        """Perform graceful shutdown of orchestrator components."""
        logger.info("Orchestrator shutdown initiated.")
        # Example: close database connection if it was opened by orchestrator
        if self.db:
            await self.db.close()
        # Add any other cleanup logic here
        logger.info("Orchestrator shutdown completed.")

    def _determine_command_complexity(self, command: str) -> str:
        """Determine command complexity (e.g., 'simple', 'medium', 'complex')."""
        if len(command) < 20:
            return "simple"
        if len(command) < 100:
            return "medium"
        return "complex"

    def _initialize_agents(self) -> None:
        """Initialize agents managed by this orchestrator, if not already injected."""
        # This method is primarily for internal setup or when agents are not
        # fully injected at __init__. In current DI approach, it might be less needed.
        logger.debug("Ensuring agents are initialized within orchestrator.")
        # Example: self.agent_router = self.agent_router or AgentRouter()


# Export for direct import will be handled elsewhere to avoid circular imports
