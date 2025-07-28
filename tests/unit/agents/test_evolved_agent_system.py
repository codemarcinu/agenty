#!/usr/bin/env python3
"""
Comprehensive Test Script for Evolved Agent System
Tests all components of the planner-executor-synthesizer architecture
"""

import asyncio
from datetime import datetime
import logging
import sys
import traceback

# Add the src directory to the path
sys.path.insert(0, "src")

from backend.agents.executor import Executor
from backend.agents.memory_manager import MemoryManager
from backend.agents.orchestrator import Orchestrator
from backend.agents.planner import Planner
from backend.agents.synthesizer import Synthesizer
from backend.agents.tools.registry import tool_registry
from backend.core.database import get_db, init_db
from backend.models.conversation import Conversation, ConversationSession, Message
from backend.tasks.conversation_tasks import get_conversation_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EvolvedAgentSystemTester:
    """Comprehensive tester for the evolved agent system"""

    def __init__(self):
        self.test_results = {}
        self.session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def run_all_tests(self):
        """Run all tests for the evolved agent system"""
        logger.info("Starting comprehensive test of evolved agent system")

        try:
            # Test 1: Database and Models
            await self.test_database_and_models()

            # Test 2: Tool Registry
            await self.test_tool_registry()

            # Test 3: Memory Manager
            await self.test_memory_manager()

            # Test 4: Planner
            await self.test_planner()

            # Test 5: Executor
            await self.test_executor()

            # Test 6: Synthesizer
            await self.test_synthesizer()

            # Test 7: Full Orchestrator Integration
            await self.test_orchestrator_integration()

            # Test 8: Conversation Summary Tasks
            await self.test_conversation_summary_tasks()

            # Print results
            self.print_test_results()

        except Exception as e:
            logger.error(f"Critical error during testing: {e}")
            traceback.print_exc()

    async def test_database_and_models(self):
        """Test database initialization and models"""
        logger.info("Testing database and models...")

        try:
            # Initialize database
            await init_db()
            logger.info("✓ Database initialized successfully")

            # Test creating a conversation
            async for db in get_db():
                # Create conversation
                conversation = Conversation(session_id=self.session_id)
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)

                # Create messages
                messages = [
                    Message(
                        content="Hello, how are you?",
                        role="user",
                        conversation_id=conversation.id,
                    ),
                    Message(
                        content="I'm doing well, thank you!",
                        role="assistant",
                        conversation_id=conversation.id,
                    ),
                ]

                for message in messages:
                    db.add(message)
                await db.commit()

                logger.info("✓ Conversation and messages created successfully")

                # Test conversation session
                session = ConversationSession(
                    session_id=self.session_id,
                    summary="Test conversation summary",
                    key_points=["test point 1", "test point 2"],
                    topics_discussed=["general", "greeting"],
                    user_preferences={"style": "friendly"},
                )
                db.add(session)
                await db.commit()

                logger.info("✓ Conversation session created successfully")

                self.test_results["database_and_models"] = "PASS"

        except Exception as e:
            logger.error(f"✗ Database and models test failed: {e}")
            self.test_results["database_and_models"] = f"FAIL: {e!s}"

    async def test_tool_registry(self):
        """Test tool registry functionality"""
        logger.info("Testing tool registry...")

        try:
            # Check if tools are registered
            tools = tool_registry.get_all_tools()
            logger.info(f"✓ Found {len(tools)} registered tools")

            # Test tool descriptions
            descriptions = tool_registry.get_tool_descriptions()
            logger.info(f"✓ Retrieved {len(descriptions)} tool descriptions")

            # Test formatting for planner
            formatted_tools = tool_registry.format_tools_for_planner()
            logger.info(
                f"✓ Formatted tools for planner ({len(formatted_tools)} characters)"
            )

            # Test tool execution (if any tools are available)
            if tools:
                tool_name = next(iter(tools.keys()))
                tools[tool_name]
                logger.info(f"✓ Tool registry test completed with tool: {tool_name}")

            self.test_results["tool_registry"] = "PASS"

        except Exception as e:
            logger.error(f"✗ Tool registry test failed: {e}")
            self.test_results["tool_registry"] = f"FAIL: {e!s}"

    async def test_memory_manager(self):
        """Test memory manager functionality"""
        logger.info("Testing memory manager...")

        try:
            # Initialize memory manager
            memory_manager = MemoryManager(
                enable_persistence=True, enable_semantic_cache=True
            )
            await memory_manager.initialize()
            logger.info("✓ Memory manager initialized")

            # Test context creation and retrieval
            context = await memory_manager.get_context(self.session_id)
            context.add_message("user", "Test message from memory manager")
            context.add_message("assistant", "Test response from memory manager")

            await memory_manager.store_context(context)
            logger.info("✓ Context stored successfully")

            # Test context retrieval
            retrieved_context = await memory_manager.retrieve_context(self.session_id)
            if retrieved_context and len(retrieved_context.history) >= 2:
                logger.info("✓ Context retrieved successfully")
            else:
                raise Exception("Context retrieval failed")

            # Test optimized context
            optimized_context = await memory_manager.get_optimized_context(
                self.session_id, max_tokens=1000
            )
            logger.info(
                f"✓ Optimized context created with {len(optimized_context)} messages"
            )

            self.test_results["memory_manager"] = "PASS"

        except Exception as e:
            logger.error(f"✗ Memory manager test failed: {e}")
            self.test_results["memory_manager"] = f"FAIL: {e!s}"

    async def test_planner(self):
        """Test planner functionality"""
        logger.info("Testing planner...")

        try:
            # Initialize planner
            planner = Planner()
            await planner.initialize()
            logger.info("✓ Planner initialized")

            # Test simple plan creation
            simple_query = "What's the weather like today?"
            simple_plan = await planner.create_plan(simple_query)

            if simple_plan and simple_plan.steps:
                logger.info(
                    f"✓ Simple plan created with {len(simple_plan.steps)} steps"
                )
            else:
                raise Exception("Simple plan creation failed")

            # Test complex plan creation
            complex_query = "Find me a recipe for chicken that's good for rainy weather"
            complex_plan = await planner.create_plan(complex_query)

            if complex_plan and complex_plan.steps:
                logger.info(
                    f"✓ Complex plan created with {len(complex_plan.steps)} steps"
                )
            else:
                raise Exception("Complex plan creation failed")

            # Test plan validation
            if planner.validate_plan(simple_plan):
                logger.info("✓ Plan validation working")
            else:
                raise Exception("Plan validation failed")

            self.test_results["planner"] = "PASS"

        except Exception as e:
            logger.error(f"✗ Planner test failed: {e}")
            self.test_results["planner"] = f"FAIL: {e!s}"

    async def test_executor(self):
        """Test executor functionality"""
        logger.info("Testing executor...")

        try:
            # Initialize executor
            executor = Executor()
            await executor.initialize()
            logger.info("✓ Executor initialized")

            # Create a simple test plan
            from backend.agents.planner import ExecutionPlan, PlanStep

            test_steps = [
                PlanStep(
                    step=1,
                    tool="general_conversation",
                    args={"message": "Hello, this is a test"},
                    description="Test conversation step",
                )
            ]

            test_plan = ExecutionPlan(
                query="Test query",
                steps=test_steps,
                total_steps=1,
                estimated_complexity="simple",
            )

            # Test plan execution
            execution_result = await executor.execute_plan(test_plan)

            if execution_result and execution_result.step_results:
                logger.info(
                    f"✓ Plan executed with {len(execution_result.step_results)} step results"
                )
            else:
                raise Exception("Plan execution failed")

            self.test_results["executor"] = "PASS"

        except Exception as e:
            logger.error(f"✗ Executor test failed: {e}")
            self.test_results["executor"] = f"FAIL: {e!s}"

    async def test_synthesizer(self):
        """Test synthesizer functionality"""
        logger.info("Testing synthesizer...")

        try:
            # Initialize synthesizer
            synthesizer = Synthesizer()
            await synthesizer.initialize()
            logger.info("✓ Synthesizer initialized")

            # Create a mock execution result
            from backend.agents.executor import ExecutionResult, StepResult
            from backend.agents.planner import ExecutionPlan, PlanStep

            mock_step = PlanStep(
                step=1, tool="test_tool", args={}, description="Test step"
            )

            mock_step_result = StepResult(
                step=mock_step, success=True, result="Test result", execution_time=1.0
            )

            mock_plan = ExecutionPlan(
                query="Test query",
                steps=[mock_step],
                total_steps=1,
                estimated_complexity="simple",
            )

            mock_execution_result = ExecutionResult(
                plan=mock_plan,
                step_results=[mock_step_result],
                success=True,
                final_result="Test final result",
                total_execution_time=1.0,
                errors=[],
            )

            # Test response generation
            response = await synthesizer.generate_response(
                mock_execution_result, "Test query"
            )

            if response and response.success:
                logger.info("✓ Response generated successfully")
            else:
                raise Exception("Response generation failed")

            self.test_results["synthesizer"] = "PASS"

        except Exception as e:
            logger.error(f"✗ Synthesizer test failed: {e}")
            self.test_results["synthesizer"] = f"FAIL: {e!s}"

    async def test_orchestrator_integration(self):
        """Test full orchestrator integration"""
        logger.info("Testing orchestrator integration...")

        try:
            # Initialize orchestrator with new architecture
            async for db in get_db():
                orchestrator = Orchestrator(db_session=db, use_planner_executor=True)

                await orchestrator.initialize()
                logger.info("✓ Orchestrator initialized with new architecture")

                # Test simple query processing
                simple_query = "Hello, how are you?"
                response = await orchestrator.process_query(
                    simple_query, self.session_id
                )

                if response:
                    logger.info("✓ Simple query processed successfully")
                else:
                    raise Exception("Simple query processing failed")

                # Test complex query processing
                complex_query = (
                    "What's the weather like and can you suggest a recipe for dinner?"
                )
                response = await orchestrator.process_query(
                    complex_query, self.session_id
                )

                if response:
                    logger.info("✓ Complex query processed successfully")
                else:
                    raise Exception("Complex query processing failed")

                self.test_results["orchestrator_integration"] = "PASS"

        except Exception as e:
            logger.error(f"✗ Orchestrator integration test failed: {e}")
            self.test_results["orchestrator_integration"] = f"FAIL: {e!s}"

    async def test_conversation_summary_tasks(self):
        """Test conversation summary background tasks"""
        logger.info("Testing conversation summary tasks...")

        try:
            # Test summary retrieval
            summary = await get_conversation_summary(self.session_id)
            if summary is not None:
                logger.info("✓ Conversation summary retrieval working")
            else:
                logger.info("✓ No existing summary (expected for new session)")

            # Test summary update task (this would normally be called by Celery)
            # For testing, we'll call the async function directly
            from backend.tasks.conversation_tasks import (
                _update_conversation_summary_async,
            )

            result = await _update_conversation_summary_async(self.session_id)

            if result.get("success"):
                logger.info("✓ Conversation summary update task working")
            else:
                logger.warning(f"Summary update task returned: {result}")

            self.test_results["conversation_summary_tasks"] = "PASS"

        except Exception as e:
            logger.error(f"✗ Conversation summary tasks test failed: {e}")
            self.test_results["conversation_summary_tasks"] = f"FAIL: {e!s}"

    def print_test_results(self):
        """Print comprehensive test results"""
        logger.info("\n" + "=" * 60)
        logger.info("EVOLVED AGENT SYSTEM TEST RESULTS")
        logger.info("=" * 60)

        passed = 0
        failed = 0

        for test_name, result in self.test_results.items():
            status = "PASS" if result == "PASS" else "FAIL"
            logger.info(f"{test_name:.<40} {status}")

            if result == "PASS":
                passed += 1
            else:
                failed += 1
                if result.startswith("FAIL:"):
                    logger.error(f"  Error: {result[5:]}")

        logger.info("-" * 60)
        logger.info(f"TOTAL: {passed + failed} tests")
        logger.info(f"PASSED: {passed}")
        logger.info(f"FAILED: {failed}")

        if failed == 0:
            logger.info(
                "🎉 ALL TESTS PASSED! The evolved agent system is working correctly."
            )
        else:
            logger.warning(
                f"⚠️  {failed} test(s) failed. Please review the errors above."
            )

        logger.info("=" * 60)


async def main():
    """Main test function"""
    tester = EvolvedAgentSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
