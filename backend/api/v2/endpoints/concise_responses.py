"""
Concise Response API Endpoints

This module provides API endpoints for generating Perplexity.ai-style
concise responses with controlled length and formatting.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agents.concise_response_agent import concise_response_agent
from core.response_length_config import (
    ConciseMetrics,
    ResponseStyle,
    get_config_for_style,
)
from core.vector_store import vector_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["concise-responses"])


class ConciseRequest(BaseModel):
    """Request model for concise response generation"""

    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    response_style: ResponseStyle = Field(
        default=ResponseStyle.CONCISE,
        description="Response style (concise, standard, detailed)",
    )
    use_rag: bool = Field(default=True, description="Use RAG processing")
    max_tokens: int | None = Field(
        default=None, ge=10, le=1000, description="Maximum tokens for response"
    )
    temperature: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Temperature for response generation"
    )
    target_length: int | None = Field(
        default=None, ge=50, le=1000, description="Target character length"
    )


class ConciseResponse(BaseModel):
    """Response model for concise response generation"""

    text: str = Field(..., description="Generated response text")
    response_style: str = Field(..., description="Applied response style")
    concise_score: float = Field(..., description="Conciseness score (0-1)")
    can_expand: bool = Field(..., description="Whether response can be expanded")
    processing_time: float = Field(0.0, description="Processing time in seconds")
    chunks_processed: int | None = Field(
        None, description="Number of RAG chunks processed"
    )
    response_stats: dict[str, Any] | None = Field(
        None, description="Response statistics"
    )
    metadata: dict = {}


class ExpandRequest(BaseModel):
    """Request model for response expansion"""

    concise_response: str = Field(..., description="Original concise response")
    original_query: str = Field(..., description="Original user query")


class ExpandResponse(BaseModel):
    """Response model for response expansion"""

    expanded_text: str = Field(..., description="Expanded response text")
    original_concise: str = Field(..., description="Original concise response")
    expansion_successful: bool = Field(
        ..., description="Whether expansion was successful"
    )
    original_length: int = Field(..., description="Original response length")
    expanded_length: int = Field(..., description="Expanded response length")


@router.post("/generate", response_model=ConciseResponse)
async def generate_concise_response(request: ConciseRequest) -> ConciseResponse:
    """
    Generate a concise response in Perplexity.ai style

    This endpoint generates responses with controlled length and formatting,
    optionally using RAG processing for enhanced context.
    """
    try:
        # Create response length configuration
        config = get_config_for_style(request.response_style)

        # Override config with request parameters if provided
        if request.max_tokens is not None:
            config.max_tokens = request.max_tokens
            config.num_predict = min(request.max_tokens, config.num_predict)

        if request.temperature is not None:
            config.temperature = request.temperature

        if request.target_length is not None:
            config.target_char_length = request.target_length
            config.expand_threshold = max(50, request.target_length - 50)

        # Prepare context for agent
        context = {
            "query": request.query,
            "response_style": request.response_style,
            "use_rag": request.use_rag,
        }

        # Add RAG chunks if requested
        if request.use_rag:
            try:
                # Search for relevant documents
                search_results = await vector_store.search(
                    query=request.query,
                    top_k=5,  # Limit for concise responses
                    similarity_threshold=0.7,
                )

                if search_results and search_results.get("chunks"):
                    context["rag_chunks"] = search_results["chunks"]
                    logger.info(f"Found {len(search_results['chunks'])} RAG chunks")
                else:
                    logger.info("No relevant RAG chunks found")

            except Exception as e:
                logger.warning(f"RAG search failed: {e!s}, continuing without RAG")
                context["use_rag"] = False

        # Update agent configuration
        await concise_response_agent.update_config(config)

        # Generate response
        response = await concise_response_agent.process(context)

        if not response.success:
            raise HTTPException(
                status_code=500, detail=f"Failed to generate response: {response.text}"
            )

        # Extract response data
        response_data = response.data or {}

        return ConciseResponse(
            text=response.text,
            response_style=response_data.get(
                "response_style", request.response_style.value
            ),
            concise_score=response_data.get("concise_score", 0.0),
            can_expand=response_data.get("can_expand", False),
            processing_time=response_data.get("processing_time", 0.0),
            chunks_processed=response_data.get("chunks_processed"),
            response_stats=response_data.get("response_stats"),
            metadata=response.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating concise response: {e!s}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/expand", response_model=ExpandResponse)
async def expand_response(request: ExpandRequest) -> ExpandResponse:
    """
    Expand a concise response with additional details

    This endpoint takes a concise response and expands it with more
    context, examples, and explanations.
    """
    try:
        # Expand response using agent
        response = await concise_response_agent.expand_response(
            concise_response=request.concise_response,
            original_query=request.original_query,
        )

        if not response.success:
            raise HTTPException(
                status_code=500, detail=f"Failed to expand response: {response.text}"
            )

        response_data = response.data or {}

        return ExpandResponse(
            expanded_text=response.text,
            original_concise=response_data.get(
                "original_concise", request.concise_response
            ),
            expansion_successful=response_data.get("expansion_successful", True),
            original_length=len(request.concise_response),
            expanded_length=len(response.text),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error expanding response: {e!s}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/analyze")
async def analyze_response_conciseness(
    text: str = Query(..., description="Text to analyze for conciseness"),
) -> dict[str, Any]:
    """
    Analyze text for conciseness metrics

    This endpoint provides detailed analysis of text conciseness,
    including character count, word count, sentence count, and conciseness score.
    """
    try:
        # Calculate metrics
        stats = ConciseMetrics.get_response_stats(text)
        concise_score = ConciseMetrics.calculate_concise_score(text)
        is_concise = ConciseMetrics.validate_concise_response(text)

        return {
            "text_length": len(text),
            "concise_score": concise_score,
            "is_concise": is_concise,
            "stats": stats,
            "recommendations": _get_conciseness_recommendations(stats),
        }

    except Exception as e:
        logger.error(f"Error analyzing conciseness: {e!s}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/config/{style}")
async def get_response_config(style: ResponseStyle) -> dict[str, Any]:
    """
    Get configuration for a specific response style

    This endpoint returns the default configuration parameters
    for the specified response style.
    """
    try:
        config = get_config_for_style(style)

        return {
            "response_style": style.value,
            "max_tokens": config.max_tokens,
            "num_predict": config.num_predict,
            "temperature": config.temperature,
            "target_char_length": config.target_char_length,
            "expand_threshold": config.expand_threshold,
            "concise_mode": config.concise_mode,
            "ollama_options": config.get_ollama_options(),
            "system_prompt_modifier": config.get_system_prompt_modifier(),
        }

    except Exception as e:
        logger.error(f"Error getting config: {e!s}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/agent/status")
async def get_agent_status() -> dict[str, Any]:
    """
    Get status of the concise response agent

    This endpoint returns metadata about the agent's configuration
    and current status.
    """
    try:
        metadata = concise_response_agent.get_metadata()

        return {
            "agent_name": metadata["name"],
            "description": metadata["description"],
            "current_config": {
                "response_style": metadata["response_style"],
                "concise_mode": metadata["concise_mode"],
                "target_char_length": metadata["target_char_length"],
                "max_tokens": metadata["max_tokens"],
                "temperature": metadata["temperature"],
            },
            "status": "active",
        }

    except Exception as e:
        logger.error(f"Error getting agent status: {e!s}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


def _get_conciseness_recommendations(stats: dict[str, Any]) -> list[str]:
    """Get recommendations for improving conciseness"""
    recommendations = []

    char_count = stats.get("char_count", 0)
    word_count = stats.get("word_count", 0)
    sentence_count = stats.get("sentence_count", 0)
    avg_words_per_sentence = stats.get("avg_words_per_sentence", 0)

    if char_count > 200:
        recommendations.append(
            "Consider reducing response length to under 200 characters"
        )

    if word_count > 40:
        recommendations.append("Aim for fewer than 40 words for maximum conciseness")

    if sentence_count > 3:
        recommendations.append("Limit to 2-3 sentences for concise responses")

    if avg_words_per_sentence > 15:
        recommendations.append("Use shorter sentences for better readability")

    if not recommendations:
        recommendations.append("Response is already quite concise")

    return recommendations


@router.post("/generate", response_model=ConciseResponse)
async def concise_generate_stub(request: ConciseRequest):
    """Stub: Zwraca przykładową odpowiedź zgodną ze schematem kontraktowym"""
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")

    return ConciseResponse(
        text="Stub concise response",
        response_style=request.response_style,
        concise_score=1.0,
        can_expand=False,
        processing_time=0.01,
        metadata={"stub": True},
    )
