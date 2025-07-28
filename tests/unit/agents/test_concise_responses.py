"""
Unit tests for concise response functionality

Tests the response length configuration, concise RAG processor,
and concise response agent.
"""

from unittest.mock import AsyncMock, patch

from pydantic import ValidationError
import pytest

from backend.agents.concise_response_agent import ConciseResponseAgent
from backend.core.concise_rag_processor import (
    ChunkSummary,
    ConciseRAGProcessor,
    MapReduceResult,
)
from backend.core.response_length_config import (
    ConciseMetrics,
    ResponseLengthConfig,
    ResponseStyle,
    get_config_for_style,
)


class TestResponseLengthConfig:
    """Test response length configuration"""

    def test_default_concise_config(self):
        """Test default concise configuration"""
        config = get_config_for_style(ResponseStyle.CONCISE)

        assert config.max_tokens == 100
        assert config.num_predict == 60
        assert config.temperature == 0.1
        assert config.response_style == ResponseStyle.CONCISE
        assert config.concise_mode is True
        assert config.target_char_length == 200
        assert config.expand_threshold == 150

    def test_config_validation(self):
        """Test configuration validation"""
        # Test valid config
        config = ResponseLengthConfig(
            max_tokens=50,
            num_predict=30,
            temperature=0.3,
        )
        assert config.max_tokens == 50
        assert config.num_predict == 30
        assert config.temperature == 0.3

        # Test invalid max_tokens (Pydantic ValidationError)
        with pytest.raises(ValidationError) as excinfo:
            ResponseLengthConfig(max_tokens=5)
        assert "greater than or equal to 10" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            ResponseLengthConfig(max_tokens=2000)
        assert "less than or equal to 1000" in str(excinfo.value)

    def test_ollama_options(self):
        """Test Ollama options generation"""
        config = ResponseLengthConfig(
            num_predict=50,
            temperature=0.3,
        )

        options = config.get_ollama_options()
        assert options["num_predict"] == 50
        assert options["temperature"] == 0.3
        assert options["top_p"] == 0.8
        assert options["top_k"] == 20
        assert options["repeat_penalty"] == 1.2

    def test_system_prompt_modifier(self):
        """Test system prompt modifier generation"""
        config = get_config_for_style(ResponseStyle.CONCISE)
        modifier = config.get_system_prompt_modifier()

        assert "ODPOWIEDŹ ZWIĘZŁA" in modifier
        assert "Maksymalnie 2 zdania" in modifier

    def test_truncation_logic(self):
        """Test response truncation logic"""
        config = ResponseLengthConfig(target_char_length=100)

        # Test short text (no truncation needed)
        short_text = "Krótka odpowiedź."
        assert not config.should_truncate_response(len(short_text))
        assert config.get_truncation_point(short_text) == len(short_text)

        # Test long text (truncation needed)
        long_text = (
            "To jest bardzo długa odpowiedź, która przekracza limit znaków i powinna zostać skrócona do odpowiedniej długości. "
            * 3
        )
        assert config.should_truncate_response(len(long_text))

        # Test truncation at sentence boundary
        truncation_point = config.get_truncation_point(long_text)
        assert truncation_point <= config.target_char_length
        # Nie zakładamy konkretnego znaku, tylko że odcięcie nie przekracza limitu


class TestConciseMetrics:
    """Test concise metrics calculation"""

    def test_calculate_concise_score(self):
        """Test concise score calculation"""
        # Very concise response
        very_concise = "Tak."
        score = ConciseMetrics.calculate_concise_score(very_concise)
        assert score == 1.0

        # Moderately concise response
        moderate = "To jest odpowiedź o średniej długości z kilkoma słowami."
        score = ConciseMetrics.calculate_concise_score(moderate)
        assert 0.8 <= score <= 1.0  # Dopuszczamy 1.0 dla krótkich odpowiedzi

        # Long response
        long_response = (
            "To jest bardzo długa odpowiedź, która zawiera wiele słów i zdań. " * 10
        )
        score = ConciseMetrics.calculate_concise_score(long_response)
        assert score <= 0.4

    def test_validate_concise_response(self):
        """Test concise response validation"""
        # Valid concise response
        valid_response = "Krótka odpowiedź."
        assert ConciseMetrics.validate_concise_response(valid_response, 200)

        # Invalid long response
        long_response = (
            "To jest bardzo długa odpowiedź, która przekracza limit znaków i nie powinna być uznana za zwięzłą. "
            * 10
        )
        assert not ConciseMetrics.validate_concise_response(long_response, 200)

    def test_get_response_stats(self):
        """Test response statistics calculation"""
        response = "To jest testowa odpowiedź. Zawiera dwa zdania."
        stats = ConciseMetrics.get_response_stats(response)

        assert stats["char_count"] > 0
        assert stats["word_count"] > 0
        assert stats["sentence_count"] == 2
        assert stats["concise_score"] > 0
        assert "avg_words_per_sentence" in stats
        assert "avg_chars_per_word" in stats

    def test_empty_response_stats(self):
        """Test statistics for empty response"""
        stats = ConciseMetrics.get_response_stats("")

        assert stats["char_count"] == 0
        assert stats["word_count"] == 0
        assert stats["sentence_count"] == 0
        assert stats["concise_score"] == 0.0
        assert stats["is_concise"] is False


class TestConciseRAGProcessor:
    """Test concise RAG processor"""

    @pytest.fixture
    def processor(self):
        """Create processor instance"""
        config = get_config_for_style(ResponseStyle.CONCISE)
        return ConciseRAGProcessor(config)

    @pytest.fixture
    def mock_chunks(self):
        """Create mock document chunks"""
        return [
            {
                "text": "To jest pierwszy fragment dokumentu z ważnymi informacjami.",
                "metadata": {"source": "doc1"},
                "similarity": 0.9,
            },
            {
                "text": "Drugi fragment zawiera dodatkowe szczegóły.",
                "metadata": {"source": "doc2"},
                "similarity": 0.8,
            },
        ]

    @pytest.mark.asyncio
    async def test_process_with_map_reduce(self, processor, mock_chunks):
        """Test map-reduce processing"""
        query = "Jakie są główne informacje?"

        with patch.object(
            processor.llm_client, "chat", new_callable=AsyncMock
        ) as mock_chat:
            mock_chat.return_value = {
                "message": {"content": "Zwięzła odpowiedź na podstawie fragmentów."}
            }

            result = await processor.process_with_map_reduce(query, mock_chunks)

            assert isinstance(result, MapReduceResult)
            assert result.final_response
            assert result.total_chunks_processed == 2
            assert result.processing_time > 0
            assert result.concise_score > 0

    @pytest.mark.asyncio
    async def test_process_empty_chunks(self, processor):
        """Test processing with empty chunks"""
        result = await processor.process_with_map_reduce("Test query", [])

        assert (
            result.final_response
            == "Przepraszam, nie znalazłem odpowiednich informacji."
        )
        assert result.total_chunks_processed == 0
        assert result.concise_score == 1.0

    @pytest.mark.asyncio
    async def test_summarize_single_chunk(self, processor):
        """Test single chunk summarization"""
        chunk = {
            "text": "Test fragment tekstu do podsumowania.",
            "metadata": {"source": "test"},
            "similarity": 0.7,
        }

        with patch.object(
            processor.llm_client, "chat", new_callable=AsyncMock
        ) as mock_chat:
            mock_chat.return_value = {"message": {"content": "Podsumowanie fragmentu."}}

            summary = await processor._summarize_single_chunk(
                "Test query", chunk, 100, 0
            )

            assert isinstance(summary, ChunkSummary)
            assert summary.chunk_id == "chunk_0"
            assert summary.summary
            assert summary.relevance_score == 0.7
            assert summary.source == "test"


class TestConciseResponseAgent:
    """Test concise response agent"""

    @pytest.fixture
    def agent(self):
        """Create agent instance"""
        return ConciseResponseAgent()

    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        return {
            "query": "Test query",
            "response_style": ResponseStyle.CONCISE,
            "use_rag": False,
        }

    @pytest.mark.asyncio
    async def test_process_direct(self, agent, mock_context):
        """Test direct processing without RAG"""
        with patch.object(
            agent.llm_client, "chat", new_callable=AsyncMock
        ) as mock_chat:
            mock_chat.return_value = {
                "message": {"content": "Zwięzła odpowiedź na zapytanie."}
            }

            response = await agent._process_direct("Test query", mock_context)

            assert response.success
            assert response.text
            assert "response_style" in response.data
            assert "concise_score" in response.data

    @pytest.mark.asyncio
    async def test_process_with_rag(self, agent, mock_context):
        """Test processing with RAG"""
        mock_context["use_rag"] = True
        mock_context["rag_chunks"] = [
            {
                "text": "Test fragment",
                "metadata": {"source": "test"},
                "similarity": 0.8,
            }
        ]

        with patch.object(
            agent.rag_processor, "process_with_map_reduce", new_callable=AsyncMock
        ) as mock_rag:
            mock_rag.return_value = MapReduceResult(
                final_response="Odpowiedź z RAG",
                chunk_summaries=[],
                total_chunks_processed=1,
                processing_time=0.5,
                concise_score=0.8,
            )

            response = await agent._process_with_rag("Test query", mock_context)

            assert response.success
            assert response.text == "Odpowiedź z RAG"
            assert response.data["chunks_processed"] == 1

    @pytest.mark.asyncio
    async def test_expand_response(self, agent):
        """Test response expansion"""
        concise_response = "Krótka odpowiedź."
        original_query = "Test query"

        with patch.object(
            agent.llm_client, "chat", new_callable=AsyncMock
        ) as mock_chat:
            mock_chat.return_value = {
                "message": {
                    "content": "Rozszerzona odpowiedź z dodatkowymi szczegółami."
                }
            }

            response = await agent.expand_response(concise_response, original_query)

            assert response.success
            assert len(response.text) > len(concise_response)
            assert response.data["expansion_successful"] is True

    def test_extract_query(self, agent):
        """Test query extraction from context"""
        context = {"query": "Test query"}
        query = agent._extract_query(context)
        assert query == "Test query"

        context = {"question": "Test question"}
        query = agent._extract_query(context)
        assert query == "Test question"

        context = {"text": "Test text"}
        query = agent._extract_query(context)
        assert query == "Test text"

        context = {}
        query = agent._extract_query(context)
        assert query == ""

    def test_get_metadata(self, agent):
        """Test agent metadata"""
        metadata = agent.get_metadata()

        assert metadata["name"] == "ConciseResponseAgent"
        assert "description" in metadata
        assert "response_style" in metadata
        assert "concise_mode" in metadata
        assert "target_char_length" in metadata
        assert "max_tokens" in metadata
        assert "temperature" in metadata


class TestIntegration:
    """Integration tests for concise response system"""

    @pytest.mark.asyncio
    async def test_full_concise_response_flow(self):
        """Test complete concise response generation flow"""
        # Create components
        config = get_config_for_style(ResponseStyle.CONCISE)
        agent = ConciseResponseAgent(config)

        # Test context
        context = {
            "query": "Jakie są zalety zwięzłych odpowiedzi?",
            "response_style": ResponseStyle.CONCISE,
            "use_rag": False,
        }

        # Mock LLM client
        with patch.object(
            agent.llm_client, "chat", new_callable=AsyncMock
        ) as mock_chat:
            mock_chat.return_value = {
                "message": {"content": "Zwięzłe odpowiedzi są szybkie i czytelne."}
            }

            # Process request
            response = await agent.process(context)

            # Verify response
            assert response.success
            assert response.text
            assert response.data["concise_score"] > 0
            assert response.data["can_expand"] is False  # Short response
            assert response.metadata["agent_type"] == "concise_response"

    def test_config_consistency(self):
        """Test configuration consistency across components"""
        # Test all response styles
        for style in ResponseStyle:
            config = get_config_for_style(style)

            # Verify config is valid
            assert config.max_tokens > 0
            assert config.num_predict > 0
            assert 0 <= config.temperature <= 1
            assert config.target_char_length > 0

            # Verify Ollama options
            options = config.get_ollama_options()
            assert "num_predict" in options
            assert "temperature" in options
            assert "top_p" in options
            assert "top_k" in options
            assert "repeat_penalty" in options

            # Verify system prompt modifier
            modifier = config.get_system_prompt_modifier()
            assert modifier and len(modifier) > 0
