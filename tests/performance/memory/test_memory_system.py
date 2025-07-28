#!/usr/bin/env python3
"""
Simple test script to verify the enhanced memory management system
"""

import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


async def test_memory_system():
    """Test the enhanced memory management system"""
    try:
        from backend.agents.memory_manager import MemoryManager


        # Initialize memory manager
        memory_manager = MemoryManager(
            max_contexts=100, enable_persistence=True, enable_semantic_cache=True
        )

        await memory_manager.initialize()

        # Create a test context
        session_id = "test_session_123"
        context = await memory_manager.get_context(session_id)

        # Add some messages to simulate conversation
        messages = [
            ("user", "Hello! I need help with cooking."),
            (
                "assistant",
                "Hi! I'd be happy to help you with cooking. What would you like to know?",
            ),
            ("user", "I want to make pasta for dinner."),
            ("assistant", "Great choice! What type of pasta do you prefer?"),
            ("user", "I like spaghetti with tomato sauce."),
            (
                "assistant",
                "Perfect! Here's a simple recipe for spaghetti with tomato sauce...",
            ),
            ("user", "What ingredients do I need?"),
            (
                "assistant",
                "You'll need spaghetti, tomatoes, garlic, olive oil, and herbs...",
            ),
            ("user", "How long does it take to cook?"),
            ("assistant", "The pasta takes about 10-12 minutes to cook al dente..."),
            ("user", "Can I add meat to the sauce?"),
            (
                "assistant",
                "Absolutely! You can add ground beef, sausage, or meatballs...",
            ),
            ("user", "What about vegetarian options?"),
            (
                "assistant",
                "For vegetarian options, you can add mushrooms, bell peppers...",
            ),
            ("user", "I have some mushrooms in the fridge."),
            ("assistant", "Great! Mushrooms are perfect for adding umami flavor..."),
            ("user", "How do I prepare the mushrooms?"),
            ("assistant", "Clean them with a damp cloth, slice them, and sauté..."),
            ("user", "What temperature should I use?"),
            ("assistant", "Medium-high heat works best for sautéing mushrooms..."),
            ("user", "Thank you for the help!"),
            ("assistant", "You're welcome! Enjoy your pasta dinner!"),
        ]

        # Add messages to context
        for role, content in messages:
            context.add_message(role, content)


        # Test context optimization
        context.get_optimized_context(max_tokens=4000)

        # Check if summary was created
        if context.conversation_summary:
            pass

        # Update context in memory manager
        await memory_manager.update_context(context)

        # Get memory statistics
        await memory_manager.get_context_stats()

        # Test retrieving context
        await memory_manager.get_context(session_id)

        # Test semantic cache
        similar_context = await memory_manager._find_similar_context(session_id)
        if similar_context:
            pass


    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_memory_system())
