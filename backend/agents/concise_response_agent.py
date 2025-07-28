"""
Concise Response Agent

This agent specializes in generating Perplexity.ai-style concise responses
with controlled length and formatting.
"""

import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from agents.prompts import CONCISE_SYSTEM_PROMPT, EXPAND_RESPONSE_PROMPT
from core.concise_rag_processor import ConciseRAGProcessor
from core.hybrid_llm_client import hybrid_llm_client
from core.response_length_config import (
    ConciseMetrics,
    ResponseLengthConfig,
    ResponseStyle,
    get_config_for_style,
)

logger = logging.getLogger(__name__)


class ConciseResponseAgent(BaseAgent):
    """
    Agent specializing in concise responses with Perplexity.ai-style formatting

    This agent provides:
    - Controlled response length
    - Map-reduce RAG processing
    - Response expansion capabilities
    - Concise metrics tracking
    """

    def __init__(
        self,
        name: str = "ConciseResponseAgent",
        config: ResponseLengthConfig | None = None,
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the concise response agent

        Args:
            name: Agent name
            config: Response length configuration
            error_handler: Error handling component
            fallback_manager: Fallback management component
        """
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )
        self.config = config or get_config_for_style(ResponseStyle.CONCISE)
        self.rag_processor = ConciseRAGProcessor(config=self.config)
        self.llm_client = hybrid_llm_client

    async def process(self, context: dict[str, Any]) -> AgentResponse:
        """
        Process query and generate concise response

        Args:
            context: Request context with query and optional parameters

        Returns:
            AgentResponse with concise text and metadata
        """
        try:
            # Extract query and parameters
            query = self._extract_query(context)
            if not query:
                return AgentResponse(
                    text="Nie podano zapytania.",
                    data={},
                    success=False,
                )

            # Get response style from context or use default
            response_style = context.get("response_style", ResponseStyle.CONCISE)
            if isinstance(response_style, str):
                response_style = ResponseStyle(response_style)

            # Update config if style changed
            if response_style != self.config.response_style:
                self.config = get_config_for_style(response_style)
                self.rag_processor.config = self.config

            # Check if RAG processing is needed
            use_rag = context.get("use_rag", True)
            if use_rag and context.get("rag_chunks"):
                return await self._process_with_rag(query, context)
            return await self._process_direct(query, context)

        except Exception as e:
            logger.error(f"Error in concise response agent: {e!s}")
            return AgentResponse(
                text="Przepraszam, wystąpił błąd podczas generowania odpowiedzi.",
                data={"error": str(e)},
                success=False,
            )

    async def _process_with_rag(
        self, query: str, context: dict[str, Any]
    ) -> AgentResponse:
        """
        Process query using RAG with map-reduce

        Args:
            query: User query
            context: Request context

        Returns:
            AgentResponse with RAG-enhanced concise response
        """
        try:
            # Get RAG chunks from context
            chunks = context.get("rag_chunks", [])
            if not chunks:
                return await self._process_direct(query, context)

            # Process with map-reduce
            result = await self.rag_processor.process_with_map_reduce(
                query=query,
                chunks=chunks,
                max_summary_length=self.config.chunk_summary_length,
            )

            # Prepare response data
            response_data = {
                "response_style": self.config.response_style.value,
                "concise_score": result.concise_score,
                "processing_time": result.processing_time,
                "chunks_processed": result.total_chunks_processed,
                "can_expand": len(result.final_response) > self.config.expand_threshold,
                "full_response": result.final_response,  # Store for potential expansion
                "chunk_summaries": [
                    {
                        "chunk_id": s.chunk_id,
                        "summary": s.summary,
                        "relevance_score": s.relevance_score,
                        "source": s.source,
                    }
                    for s in result.chunk_summaries
                ],
            }

            return AgentResponse(
                text=result.final_response,
                data=response_data,
                success=True,
                metadata={
                    "agent_type": "concise_response",
                    "response_style": self.config.response_style.value,
                    "concise_score": result.concise_score,
                    "processing_time": result.processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Error in RAG processing: {e!s}")
            return await self._process_direct(query, context)

    async def _process_direct(
        self, query: str, context: dict[str, Any]
    ) -> AgentResponse:
        """
        Process query directly without RAG

        Args:
            query: User query
            context: Request context

        Returns:
            AgentResponse with direct concise response
        """
        try:
            # Build system prompt with concise instructions
            system_prompt = (
                CONCISE_SYSTEM_PROMPT + self.config.get_system_prompt_modifier()
            )

            # Create messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ]

            # Generate response
            response = await self.llm_client.chat(
                messages=messages,
                options=self.config.get_ollama_options(),
                force_complexity="simple",
            )

            if not response or "message" not in response:
                return AgentResponse(
                    text="Przepraszam, nie udało się wygenerować odpowiedzi.",
                    data={},
                    success=False,
                )

            response_text = response["message"]["content"].strip()

            # Validate and potentially truncate
            if self.config.should_truncate_response(len(response_text)):
                truncation_point = self.config.get_truncation_point(response_text)
                response_text = response_text[:truncation_point].strip()
                if not response_text.endswith((".", "!", "?")):
                    response_text += "..."

            # Calculate metrics
            concise_score = ConciseMetrics.calculate_concise_score(response_text)
            response_stats = ConciseMetrics.get_response_stats(response_text)

            # Prepare response data
            response_data = {
                "response_style": self.config.response_style.value,
                "concise_score": concise_score,
                "response_stats": response_stats,
                "can_expand": len(response_text) > self.config.expand_threshold,
                "full_response": response_text,  # Store for potential expansion
            }

            return AgentResponse(
                text=response_text,
                data=response_data,
                success=True,
                metadata={
                    "agent_type": "concise_response",
                    "response_style": self.config.response_style.value,
                    "concise_score": concise_score,
                    "response_stats": response_stats,
                },
            )

        except Exception as e:
            logger.error(f"Error in direct processing: {e!s}")
            return AgentResponse(
                text="Przepraszam, wystąpił błąd podczas generowania odpowiedzi.",
                data={"error": str(e)},
                success=False,
            )

    async def expand_response(
        self, concise_response: str, original_query: str
    ) -> AgentResponse:
        """
        Expand a concise response with additional details

        Args:
            concise_response: Original concise response
            original_query: Original user query

        Returns:
            AgentResponse with expanded response
        """
        try:
            # Create expansion prompt
            expansion_prompt = EXPAND_RESPONSE_PROMPT.format(
                concise_response=concise_response,
                original_query=original_query,
            )

            # Use standard config for expansion
            expansion_config = get_config_for_style(ResponseStyle.STANDARD)

            # Generate expanded response
            response = await self.llm_client.chat(
                messages=[{"role": "user", "content": expansion_prompt}],
                options=expansion_config.get_ollama_options(),
                force_complexity="standard",
            )

            if not response or "message" not in response:
                return AgentResponse(
                    text=concise_response,  # Return original if expansion fails
                    data={"expansion_failed": True},
                    success=False,
                )

            expanded_text = response["message"]["content"].strip()

            return AgentResponse(
                text=expanded_text,
                data={
                    "original_concise": concise_response,
                    "expansion_successful": True,
                    "response_style": ResponseStyle.STANDARD.value,
                },
                success=True,
                metadata={
                    "agent_type": "concise_response",
                    "operation": "expand",
                    "original_length": len(concise_response),
                    "expanded_length": len(expanded_text),
                },
            )

        except Exception as e:
            logger.error(f"Error expanding response: {e!s}")
            return AgentResponse(
                text=concise_response,  # Return original if expansion fails
                data={"expansion_failed": True, "error": str(e)},
                success=False,
            )

    def _extract_query(self, context: dict[str, Any]) -> str:
        """Extract query from context"""
        possible_fields = ["query", "question", "text", "message", "prompt"]
        for field in possible_fields:
            value = context.get(field)
            if value and isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def get_metadata(self) -> dict[str, Any]:
        """Return metadata about this agent"""
        return {
            "name": self.name,
            "description": self.__doc__,
            "response_style": self.config.response_style.value,
            "concise_mode": self.config.concise_mode,
            "target_char_length": self.config.target_char_length,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

    async def update_config(self, new_config: ResponseLengthConfig) -> None:
        """
        Update agent configuration

        Args:
            new_config: New configuration to apply
        """
        self.config = new_config
        self.rag_processor.config = new_config
        logger.info(f"Updated configuration for {self.name}")


# Global instance for easy access
concise_response_agent = ConciseResponseAgent()
