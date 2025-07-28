"""
Concise RAG Processor with Map-Reduce

This module implements a two-stage RAG pipeline with map-reduce pattern
to generate Perplexity.ai-style concise responses.
"""

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from core.response_length_config import ConciseMetrics, ResponseLengthConfig

logger = logging.getLogger(__name__)


@dataclass
class ChunkSummary:
    """Summary of a document chunk"""

    chunk_id: str
    summary: str
    relevance_score: float
    source: str


@dataclass
class MapReduceResult:
    """Result of map-reduce processing"""

    final_response: str
    chunk_summaries: list[ChunkSummary]
    total_chunks_processed: int
    processing_time: float
    concise_score: float


class ConciseRAGProcessor:
    """
    Two-stage RAG processor with map-reduce pattern for concise responses

    This processor implements the map-reduce pattern to generate concise
    responses from multiple document chunks:
    1. Map: Summarize each chunk individually
    2. Reduce: Combine summaries into final concise response
    """

    def __init__(self, config: ResponseLengthConfig | None = None):
        """
        Initialize the concise RAG processor

        Args:
            config: Configuration for response length control
        """
        self.config = config or ResponseLengthConfig()
        self.llm_client = hybrid_llm_client

    async def process_with_map_reduce(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        max_summary_length: int | None = None,
    ) -> MapReduceResult:
        """
        Process query using map-reduce pattern for concise responses

        Args:
            query: User query
            chunks: List of document chunks with metadata
            max_summary_length: Maximum length for chunk summaries

        Returns:
            MapReduceResult with final response and metadata
        """
        start_time = asyncio.get_event_loop().time()

        if not chunks:
            logger.warning("No chunks provided for map-reduce processing")
            return MapReduceResult(
                final_response="Przepraszam, nie znalazłem odpowiednich informacji.",
                chunk_summaries=[],
                total_chunks_processed=0,
                processing_time=0.0,
                concise_score=1.0,
            )

        # Limit chunks for processing
        max_chunks = self.config.max_chunks_for_summary
        if len(chunks) > max_chunks:
            logger.info(f"Limiting chunks from {len(chunks)} to {max_chunks}")
            chunks = chunks[:max_chunks]

        try:
            # Stage 1: Map - Summarize each chunk
            chunk_summaries = await self._summarize_chunks(
                query, chunks, max_summary_length
            )

            # Stage 2: Reduce - Generate final concise response
            final_response = await self._generate_concise_response(
                query, chunk_summaries
            )

            # Calculate metrics
            processing_time = asyncio.get_event_loop().time() - start_time
            concise_score = ConciseMetrics.calculate_concise_score(final_response)

            logger.info(
                f"Map-reduce processing completed in {processing_time:.2f}s, "
                f"concise score: {concise_score:.2f}"
            )

            return MapReduceResult(
                final_response=final_response,
                chunk_summaries=chunk_summaries,
                total_chunks_processed=len(chunks),
                processing_time=processing_time,
                concise_score=concise_score,
            )

        except Exception as e:
            logger.error(f"Error in map-reduce processing: {e!s}")
            return MapReduceResult(
                final_response="Przepraszam, wystąpił błąd podczas przetwarzania.",
                chunk_summaries=[],
                total_chunks_processed=len(chunks),
                processing_time=asyncio.get_event_loop().time() - start_time,
                concise_score=0.0,
            )

    async def _summarize_chunks(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        max_summary_length: int | None = None,
    ) -> list[ChunkSummary]:
        """
        Map stage: Summarize each chunk individually

        Args:
            query: User query
            chunks: List of document chunks
            max_summary_length: Maximum length for summaries

        Returns:
            List of chunk summaries
        """
        max_length = max_summary_length or self.config.chunk_summary_length

        # Create summarization tasks
        tasks = []
        for i, chunk in enumerate(chunks):
            task = self._summarize_single_chunk(query, chunk, max_length, i)
            tasks.append(task)

        # Execute summarization in parallel
        summaries = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed summaries
        valid_summaries = []
        for summary in summaries:
            if isinstance(summary, ChunkSummary):
                valid_summaries.append(summary)
            else:
                logger.warning(f"Failed to summarize chunk: {summary}")

        return valid_summaries

    async def _summarize_single_chunk(
        self,
        query: str,
        chunk: dict[str, Any],
        max_length: int,
        chunk_index: int,
    ) -> ChunkSummary:
        """
        Summarize a single document chunk

        Args:
            query: User query
            chunk: Document chunk with content and metadata
            max_length: Maximum summary length
            chunk_index: Index of the chunk

        Returns:
            ChunkSummary object
        """
        try:
            chunk_content = chunk.get("text", "")
            chunk_source = chunk.get("metadata", {}).get(
                "source", f"chunk_{chunk_index}"
            )
            relevance_score = chunk.get("similarity", 0.5)

            if not chunk_content.strip():
                return ChunkSummary(
                    chunk_id=f"chunk_{chunk_index}",
                    summary="",
                    relevance_score=relevance_score,
                    source=chunk_source,
                )

            # Create summarization prompt
            summary_prompt = (
                f"Podsumuj poniższy fragment tekstu w kontekście pytania użytkownika.\n"
                f"Maksymalnie {max_length} znaków. Zachowaj najważniejsze informacje.\n\n"
                f"PYTANIE: {query}\n\n"
                f"FRAGMENT:\n"
                f"{chunk_content}\n\n"
                f"PODSUMOWANIE:"
            )

            # Generate summary using LLM
            response = await self.llm_client.chat(
                messages=[{"role": "user", "content": summary_prompt}],
                options=self.config.get_ollama_options(),
                force_complexity=ModelComplexity.SIMPLE,
            )

            # Handle response properly
            if isinstance(response, dict) and "message" in response:
                summary = response["message"]["content"].strip()
                # Truncate if too long
                if len(summary) > max_length:
                    summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
            else:
                summary = chunk_content[:max_length] + "..."

            return ChunkSummary(
                chunk_id=f"chunk_{chunk_index}",
                summary=summary,
                relevance_score=relevance_score,
                source=chunk_source,
            )

        except Exception as e:
            logger.error(f"Error summarizing chunk {chunk_index}: {e!s}")
            return ChunkSummary(
                chunk_id=f"chunk_{chunk_index}",
                summary="",
                relevance_score=0.0,
                source=f"chunk_{chunk_index}",
            )

    async def _generate_concise_response(
        self, query: str, chunk_summaries: list[ChunkSummary]
    ) -> str:
        """
        Reduce stage: Generate final concise response from summaries

        Args:
            query: User query
            chunk_summaries: List of chunk summaries

        Returns:
            Final concise response
        """
        if not chunk_summaries:
            return "Przepraszam, nie znalazłem odpowiednich informacji."

        # Filter out empty summaries and sort by relevance
        valid_summaries = [
            s for s in chunk_summaries if s.summary and s.summary.strip()
        ]

        if not valid_summaries:
            return "Przepraszam, nie znalazłem odpowiednich informacji."

        # Sort by relevance score
        valid_summaries.sort(key=lambda x: x.relevance_score, reverse=True)

        # Take top summaries
        top_summaries = valid_summaries[:3]  # Limit to top 3 for conciseness

        # Build context from summaries
        context_parts = []
        for summary in top_summaries:
            context_parts.append(f"• {summary.summary}")

        context_text = "\n".join(context_parts)

        # Create final response prompt
        final_prompt = (
            f"Na podstawie poniższych podsumowań udziel zwięzłej odpowiedzi na pytanie użytkownika.\n"
            f"Maksymalnie 2 zdania. Unikaj zbędnego formatowania.\n\n"
            f"PYTANIE: {query}\n\n"
            f"PODSUMOWANIA:\n"
            f"{context_text}\n\n"
            f"ODPOWIEDŹ:"
        )

        # Generate final response
        response = await self.llm_client.chat(
            messages=[{"role": "user", "content": final_prompt}],
            options=self.config.get_ollama_options(),
            force_complexity=ModelComplexity.SIMPLE,
        )

        # Handle response properly
        if isinstance(response, dict) and "message" in response:
            final_response = response["message"]["content"].strip()

            # Validate and potentially truncate
            if self.config.should_truncate_response(len(final_response)):
                truncation_point = self.config.get_truncation_point(final_response)
                final_response = final_response[:truncation_point].strip()
                if not final_response.endswith((".", "!", "?")):
                    final_response += "..."

            return final_response
        # Fallback: combine top summaries manually
        return self._create_fallback_response(query, top_summaries)

    def _create_fallback_response(
        self, query: str, summaries: list[ChunkSummary]
    ) -> str:
        """
        Create fallback response when LLM fails

        Args:
            query: User query
            summaries: List of chunk summaries

        Returns:
            Fallback response
        """
        if not summaries:
            return "Przepraszam, nie znalazłem odpowiednich informacji."

        # Take the most relevant summary
        best_summary = summaries[0]

        # Create a simple response
        if len(best_summary.summary) > 100:
            response = best_summary.summary[:100].rsplit(" ", 1)[0] + "..."
        else:
            response = best_summary.summary

        return response


# Global instance for easy access
concise_rag_processor = ConciseRAGProcessor()
