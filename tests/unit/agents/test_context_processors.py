"""
Unit tests for Context Processors module
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.conversation.context_processors import ContextProcessor


class TestContextProcessor:
    """Test cases for ContextProcessor class"""

    def test_combine_context_empty(self):
        """Test combining empty context lists"""
        result = ContextProcessor.combine_context([], [])
        assert result == []

    def test_combine_context_rag_only(self):
        """Test combining context with RAG results only"""
        rag_results = [{"content": "RAG content", "source": "document1"}]
        result = ContextProcessor.combine_context(rag_results, [])
        assert len(result) == 1
        assert result[0]["content"] == "RAG content"

    def test_combine_context_internet_only(self):
        """Test combining context with internet results only"""
        internet_results = [{"title": "Web result", "content": "Web content"}]
        result = ContextProcessor.combine_context([], internet_results)
        assert len(result) == 1
        assert result[0]["title"] == "Web result"

    def test_combine_context_both(self):
        """Test combining context with both RAG and internet results"""
        rag_results = [{"content": "RAG content"}]
        internet_results = [{"content": "Web content"}]
        result = ContextProcessor.combine_context(rag_results, internet_results)
        assert len(result) == 2
        # RAG results should come first
        assert result[0]["content"] == "RAG content"
        assert result[1]["content"] == "Web content"

    def test_format_context_for_llm_empty(self):
        """Test formatting empty context"""
        result = ContextProcessor.format_context_for_llm([])
        assert result == ""

    def test_format_context_for_llm_single_item(self):
        """Test formatting single context item"""
        context = [{"title": "Test Title", "content": "Test content", "url": "http://test.com"}]
        result = ContextProcessor.format_context_for_llm(context)
        
        assert "Oto informacje" in result
        assert "Test Title" in result
        assert "Test content" in result
        assert "http://test.com" in result

    def test_format_context_for_llm_no_url(self):
        """Test formatting context item without URL"""
        context = [{"title": "Test Title", "content": "Test content"}]
        result = ContextProcessor.format_context_for_llm(context)
        
        assert "Test Title" in result
        assert "Test content" in result
        assert "http" not in result

    def test_prepare_messages_basic(self):
        """Test preparing basic messages for LLM"""
        query = "Test query"
        history = []
        context = ""
        
        result = ContextProcessor.prepare_messages(query, history, context)
        
        # Should have system message and user query
        assert len(result) >= 2
        assert result[0]["role"] == "system"
        assert result[-1]["role"] == "user"
        assert result[-1]["content"] == query

    def test_prepare_messages_with_context(self):
        """Test preparing messages with context"""
        query = "Test query"
        history = []
        context = "Some context information"
        
        result = ContextProcessor.prepare_messages(query, history, context)
        
        system_message = result[0]["content"]
        assert "FoodSave" in system_message
        assert "Some context information" in system_message

    def test_prepare_messages_with_history(self):
        """Test preparing messages with conversation history"""
        query = "Current query"
        history = [
            {"role": "user", "content": "Previous user message"},
            {"role": "assistant", "content": "Previous assistant response"},
            {"role": "user", "content": "Another user message"},
            {"role": "assistant", "content": "Another assistant response"},
        ]
        context = ""
        
        result = ContextProcessor.prepare_messages(query, history, context)
        
        # Should include system message, last 3 history messages, and current query
        # With 4 history items, should take last 3 + system + current = 5 messages
        assert len(result) >= 4  # At least system + current + some history

    def test_prepare_messages_filters_invalid_roles(self):
        """Test that prepare_messages filters out invalid roles"""
        query = "Test query"
        history = [
            {"role": "user", "content": "Valid user message"},
            {"role": "system", "content": "Should be filtered"},  # system role in history
            {"role": "assistant", "content": "Valid assistant message"},
            {"role": "invalid", "content": "Invalid role"},  # invalid role
        ]
        context = ""
        
        result = ContextProcessor.prepare_messages(query, history, context)
        
        # Count messages excluding the new system message
        content_messages = [msg for msg in result if msg["role"] in ["user", "assistant"]]
        
        # Should only include valid user/assistant messages from history + current query
        valid_history_count = len([msg for msg in history if msg["role"] in ["user", "assistant"]])
        assert len(content_messages) == valid_history_count + 1  # +1 for current query

    @pytest.mark.asyncio
    async def test_get_rag_context_no_embedding(self):
        """Test RAG context when embedding fails"""
        with patch("backend.agents.conversation.context_processors.mmlw_client") as mock_client:
            mock_client.embed_text.return_value = []
            
            result = await ContextProcessor.get_rag_context("test query")
            
            assert result == ("", 0.0)

    @pytest.mark.asyncio
    async def test_get_rag_context_no_vector_store(self):
        """Test RAG context when vector store is not available"""
        with patch("backend.agents.conversation.context_processors.mmlw_client") as mock_client, \
             patch("backend.agents.conversation.context_processors.vector_store", None):
            
            mock_client.embed_text.return_value = [0.1, 0.2, 0.3]
            
            result = await ContextProcessor.get_rag_context("test query")
            
            assert result == ("", 0.0)

    @pytest.mark.asyncio
    async def test_get_internet_context_no_search(self):
        """Test internet context when web_search is not available"""
        with patch("backend.agents.conversation.context_processors.web_search", None):
            
            result = await ContextProcessor.get_internet_context("test query", False)
            
            assert result == ""

    @pytest.mark.asyncio 
    async def test_get_rag_results_placeholder(self):
        """Test RAG results placeholder implementation"""
        result = await ContextProcessor.get_rag_results("test query")
        
        # Current implementation returns empty list
        assert result == []

    @pytest.mark.asyncio
    async def test_get_internet_results_no_web_search(self):
        """Test internet results when web_search is unavailable"""
        with patch("backend.agents.conversation.context_processors.web_search", None):
            
            result = await ContextProcessor.get_internet_results("test query")
            
            assert result == []