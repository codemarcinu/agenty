import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any
import hashlib

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.async_patterns import CircuitBreakerConfig, timeout_context
from core.llm_client import llm_client
from infrastructure.database.database import get_db
from orchestrator_management.orchestrator_pool import orchestrator_pool
from orchestrator_management.request_queue import request_queue
from core.cache_manager import get_cache_manager

router = APIRouter()
logger = logging.getLogger(__name__)


def get_selected_model() -> str:
    """Get the selected model from config file or fallback to default"""
    try:
        # Path to the LLM settings file
        llm_settings_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "data",
            "config",
            "llm_settings.json",
        )

        if Path(llm_settings_path).exists():
            with open(llm_settings_path, encoding="utf-8") as f:
                data = json.load(f)
                selected_model = data.get("selected_model", "")
                if selected_model:
                    logger.info(f"Using selected model from config: {selected_model}")
                    return selected_model

        # Fallback to hardcoded default
        fallback_default = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        logger.info(
            f"No valid selected model in config, using fallback: {fallback_default}"
        )
        return fallback_default

    except Exception as e:
        logger.warning(f"Error reading selected model from config: {e}")
        fallback_default = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        logger.info(f"Using fallback default model: {fallback_default}")
        return fallback_default


class ChatRequest(BaseModel):
    prompt: str
    model: str | None = None  # Pole opcjonalne


class ChatResponse(BaseModel):
    response: str
    model: str


class WebSocketResponse(BaseModel):
    message: str
    type: str = "message"


class MemoryChatRequest(BaseModel):
    message: str
    session_id: str  # Kluczowe do śledzenia i odróżniania konwersacji
    use_perplexity: bool = False  # Nowe pole
    use_bielik: bool = True  # Domyślnie używamy Bielika
    agent_states: dict[str, bool] = {}  # Stany agentów


class MemoryChatResponse(BaseModel):
    reply: str
    history_length: int


# Circuit breaker dla LLM client
llm_circuit_breaker = CircuitBreakerConfig(
    failure_threshold=3, recovery_timeout=30.0, name="llm_client"
)


async def chat_response_generator(prompt: str, model: str) -> AsyncGenerator[str, None]:
    """
    Asynchroniczny generator streamujący odpowiedzi LLM do FastAPI (zgodny z najlepszymi praktykami).
    """
    try:
        async for chunk in llm_client.generate_stream_from_prompt_async(
            model=model, prompt=prompt, system_prompt=""
        ):
            # Obsługa błędów z LLM client
            if isinstance(chunk, dict) and chunk.get("error"):
                logger.error(f"LLM client error: {chunk['error']}")
                raise Exception(f"LLM client error: {chunk['error']}")

            # Sprawdź różne możliwe struktury odpowiedzi z Ollama
            response_text = None

            # Struktura 1: pole "response" (słownik)
            if isinstance(chunk, dict) and "response" in chunk:
                response_text = chunk["response"]
            # Struktura 2: pole "message" z "content" (słownik)
            elif (
                isinstance(chunk, dict)
                and "message" in chunk
                and isinstance(chunk["message"], dict)
            ):
                if "content" in chunk["message"]:
                    response_text = chunk["message"]["content"]
            # Struktura 3: pole "content" bezpośrednio (słownik)
            elif isinstance(chunk, dict) and "content" in chunk:
                response_text = chunk["content"]
            # Struktura 4: obiekt ChatResponse z Ollama (atrybuty obiektu)
            elif hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                response_text = chunk.message.content
            # Struktura 5: obiekt z atrybutem content
            elif hasattr(chunk, "content"):
                response_text = chunk.content

            if response_text:
                yield response_text

    except Exception as e:
        logger.error(f"Error in chat response generator: {e}")
        raise e


@router.post("/chat")
async def chat_with_model(request: Request) -> dict[str, Any]:
    body = await request.json()
    prompt = body.get("prompt")

    # Walidacja prompt
    if not prompt or prompt.strip() == "":
        raise HTTPException(status_code=422, detail="Prompt cannot be empty or null")

    model = body.get("model") or get_selected_model()
    logger.info(f"[DEBUG] Selected model for chat: {model}")

    try:
        # 🚀 OPTIMIZATION: Check cache first
        cache_key = f"chat:{hashlib.md5(prompt.encode()).hexdigest()}"
        cached_response = await get_cache_manager().get(cache_key)
        if cached_response:
            logger.info("Returning cached response")
            return cached_response

        # Collect all chunks from the generator
        response_text = ""
        async for chunk in chat_response_generator(prompt, model):
            response_text += chunk

        # Create response
        response = {
            "data": response_text,
            "status": "success",
            "message": "Chat response generated successfully",
            "timestamp": datetime.now().isoformat(),
        }

        # Cache response for 30 minutes
        await get_cache_manager().set(cache_key, response, ttl=1800)

        return response

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return {
            "data": f"Przepraszam, wystąpił błąd: {e!s}",
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        }


async def memory_chat_generator(
    request: MemoryChatRequest, db: AsyncSession
) -> AsyncGenerator[str, None]:
    """
    Generator for streaming responses from the orchestrator.
    Każdy yield to linia NDJSON: {"text": ...}
    """
    start_time = asyncio.get_event_loop().time()  # Czas rozpoczęcia przetwarzania
    try:
        # Rozszerzone logowanie czatu
        logger.info(
            "Chat request received",
            extra={
                "session_id": request.session_id,
                "message_length": len(request.message),
                "use_perplexity": request.use_perplexity,
                "use_bielik": request.use_bielik,
                "agent_states": request.agent_states,
                "chat_event": "request_received",
            },
        )

        # Get a healthy orchestrator from the pool
        logger.debug("Getting healthy orchestrator from pool...")
        orchestrator = await orchestrator_pool.get_healthy_orchestrator()
        logger.debug(f"Orchestrator result: {orchestrator}")

        if not orchestrator:
            logger.warning("No healthy orchestrator available, queuing request")

            # Check if request_queue is properly initialized
            if request_queue is None:
                logger.error("Request queue is not initialized")
                yield (
                    json.dumps(
                        {
                            "text": "Service temporarily unavailable. Request queue not initialized.",
                            "success": False,
                        }
                    )
                    + "\n"
                )
                return

            try:
                request_id = await request_queue.enqueue_request(
                    user_command=request.message, session_id=request.session_id
                )
                yield (
                    json.dumps(
                        {
                            "text": "Service temporarily unavailable. Request queued for processing.",
                            "request_id": request_id,
                            "success": False,
                        }
                    )
                    + "\n"
                )
            except Exception as e:
                logger.error(f"Error enqueueing request: {e}")
                yield (
                    json.dumps(
                        {
                            "text": "Service temporarily unavailable. Failed to queue request.",
                            "success": False,
                        }
                    )
                    + "\n"
                )
            return

        # Process with orchestrator using streaming
        async with timeout_context(60.0):  # 60 second timeout for memory chat
            # Create a list to collect chunks
            chunks = []

            # Define the callback function
            def handle_chunk(chunk) -> None:
                chunks.append(chunk)

            # Process the command with streaming
            response = await orchestrator.process_command(
                user_command=request.message,
                session_id=request.session_id,
                agent_states=request.agent_states,
                use_perplexity=request.use_perplexity,
                use_bielik=request.use_bielik,
                stream=True,
                stream_callback=handle_chunk,
            )

            # Update context with the conversation
            try:
                context = await orchestrator.memory_manager.get_context(
                    request.session_id
                )
                # Add user message to context
                context.add_message(
                    role="user",
                    content=request.message,
                    metadata={
                        "session_id": request.session_id,
                        "timestamp": datetime.now().isoformat(),
                        "agent_states": request.agent_states,
                    },
                )

                # Add assistant response to context
                if response and response.text:
                    context.add_message(
                        role="assistant",
                        content=response.text,
                        metadata={
                            "session_id": request.session_id,
                            "timestamp": datetime.now().isoformat(),
                            "success": response.success,
                        },
                    )

                # Update context with optimized storage
                await orchestrator.memory_manager.update_context(context)

            except Exception as e:
                logger.error(f"Error updating conversation context: {e}")

            # If no chunks were collected, use the response
            if not chunks and response:
                response_text = response.text or ""

                # Jeśli orchestrator nie wygenerował odpowiedzi, użyj fallback
                if not response_text.strip():
                    logger.warning(
                        "Orchestrator returned empty response, using fallback to direct LLM"
                    )
                    try:
                        # Fallback do bezpośredniego wywołania LLM
                        fallback_response = await llm_client.generate_stream_from_prompt_async(
                            model=get_selected_model(),
                            prompt=request.message,
                            system_prompt="Jesteś pomocnym asystentem AI. Odpowiadaj w języku polskim.",
                        )

                        fallback_text = ""
                        async for chunk in fallback_response:
                            if hasattr(chunk, "response") and chunk.response:
                                fallback_text += chunk.response
                            elif isinstance(chunk, dict) and "response" in chunk:
                                fallback_text += chunk["response"]

                        if fallback_text.strip():
                            response_text = fallback_text
                            logger.info("Fallback LLM response successful")
                        else:
                            response_text = "Przepraszam, nie udało się wygenerować odpowiedzi. Spróbuj ponownie."
                            logger.error("Fallback LLM also failed")
                    except Exception as fallback_error:
                        logger.error(f"Fallback LLM error: {fallback_error}")
                        response_text = "Przepraszam, wystąpił błąd techniczny. Spróbuj ponownie za chwilę."

                logger.info(
                    "Chat response completed",
                    extra={
                        "session_id": request.session_id,
                        "response_length": len(response_text),
                        "success": response.success,
                        "chat_event": "response_completed",
                        "processing_time_ms": int(
                            (asyncio.get_event_loop().time() - start_time) * 1000
                        ),
                    },
                )
                yield (
                    json.dumps(
                        {
                            "text": response_text,
                            "success": response.success,
                            "session_id": request.session_id,
                            "data": response.data,
                        }
                    )
                    + "\n"
                )
            else:
                # Stream all collected chunks
                total_response_length = sum(
                    len(chunk.get("text", "")) for chunk in chunks
                )
                logger.info(
                    "Chat streaming response completed",
                    extra={
                        "session_id": request.session_id,
                        "chunks_count": len(chunks),
                        "total_response_length": total_response_length,
                        "success": all(chunk.get("success", True) for chunk in chunks),
                        "chat_event": "streaming_completed",
                        "processing_time_ms": int(
                            (asyncio.get_event_loop().time() - start_time) * 1000
                        ),
                    },
                )
                for chunk in chunks:
                    yield (
                        json.dumps(
                            {
                                "text": chunk.get("text", ""),
                                "success": chunk.get("success", True),
                                "session_id": request.session_id,
                                "data": chunk.get("data"),
                            }
                        )
                        + "\n"
                    )

    except TimeoutError:
        logger.error(
            "Memory chat processing timed out",
            extra={
                "session_id": request.session_id,
                "chat_event": "timeout",
            },
        )
        yield (
            json.dumps(
                {"text": "Processing timed out. Please try again.", "success": False}
            )
            + "\n"
        )
    except Exception as e:
        logger.error(
            f"An error occurred during memory chat processing: {e}",
            exc_info=True,
            extra={
                "session_id": request.session_id,
                "chat_event": "error",
                "error_message": str(e),
            },
        )
        yield json.dumps({"text": f"An error occurred: {e!s}", "success": False}) + "\n"
    finally:
        if orchestrator:
            orchestrator_pool.release_orchestrator(orchestrator)
            logger.debug(
                f"Orchestrator {orchestrator.orchestrator_id} released from pool."
            )


@router.post("/memory_chat")
async def chat_with_memory(
    request: MemoryChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    # Dodaj zadanie w tle, aby monitorować i usuwać stare sesje, jeśli to konieczne
    # background_tasks.add_task(cleanup_old_sessions, request.session_id)

    return StreamingResponse(
        memory_chat_generator(request, db), media_type="application/x-ndjson"
    )


@router.post("/test_simple_chat")
async def test_simple_chat(request: MemoryChatRequest) -> dict[str, Any]:
    """Test endpoint for automatic switching between general chat and search mode"""
    try:
        # Get a healthy orchestrator from the pool
        orchestrator = await orchestrator_pool.get_healthy_orchestrator()
        if not orchestrator:
            return {
                "success": False,
                "error": "No healthy orchestrator available",
                "message": "Brak dostępnego orchestratora",
            }

        # Process the message through the orchestrator
        response = await orchestrator.process_query(
            query=request.message,
            session_id=request.session_id,
            use_perplexity=request.use_perplexity,
            use_bielik=request.use_bielik,
        )

        return {
            "success": True,
            "message": response.text or "Brak odpowiedzi",
            "session_id": request.session_id,
            "use_perplexity": request.use_perplexity,
            "use_bielik": request.use_bielik,
        }

    except Exception as e:
        logger.error(f"Error in test_simple_chat: {e}")
        return {"success": False, "error": str(e), "message": f"Błąd: {e}"}


@router.post("/test_chat_simple")
async def test_chat_simple(request: ChatRequest) -> dict[str, Any]:
    # Placeholder for actual chat logic
    return {"reply": f"You said: {request.prompt}", "model": request.model}


@router.get("/memory_chat")
async def get_chat_history(
    session_id: str = "default",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get chat history for a session with enhanced memory management"""
    try:
        # Get orchestrator to access memory manager
        orchestrator = await orchestrator_pool.get_healthy_orchestrator()
        if not orchestrator:
            return {
                "success": False,
                "error": "No healthy orchestrator available",
                "data": [],
            }

        # Get context from memory manager
        context = await orchestrator.memory_manager.get_context(session_id)

        # Extract chat history from context with optimization
        history = []
        if hasattr(context, "history") and context.history:
            # Use optimized context if available
            if hasattr(context, "get_optimized_context"):
                optimized_messages = context.get_optimized_context(max_tokens=4000)
                # Convert optimized messages to history format
                for i, msg in enumerate(optimized_messages):
                    if msg.get("role") != "system":  # Skip system messages
                        history.append(
                            {
                                "id": f"history-{i}",
                                "content": msg.get("content", ""),
                                "type": msg.get("role", "user"),
                                "timestamp": datetime.now().isoformat(),
                                "metadata": {"optimized": True},
                            }
                        )
            else:
                # Fallback to traditional approach
                recent_history = (
                    context.history[-limit:] if limit > 0 else context.history
                )

                for i, entry in enumerate(recent_history):
                    if isinstance(entry, dict) and "data" in entry:
                        data = entry["data"]
                        if isinstance(data, dict):
                            # Extract message content from various possible formats
                            content = (
                                data.get("message")
                                or data.get("content")
                                or data.get("text", "")
                            )
                            role = data.get("role") or data.get("type", "user")

                            history.append(
                                {
                                    "id": f"history-{i}",
                                    "content": content,
                                    "type": role,
                                    "timestamp": entry.get(
                                        "timestamp", datetime.now().isoformat()
                                    ),
                                    "metadata": data,
                                }
                            )

        # Get memory statistics
        memory_stats = await orchestrator.memory_manager.get_context_stats()

        return {
            "success": True,
            "data": history,
            "session_id": session_id,
            "total_count": len(history),
            "memory_stats": {
                "compression_ratio": memory_stats.get("compression_ratio", 0.0),
                "persistent_contexts": memory_stats.get("persistent_contexts", 0),
                "cached_contexts": memory_stats.get("cached_contexts", 0),
            },
        }

    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return {"success": False, "error": str(e), "data": []}


@router.delete("/memory_chat")
async def clear_chat_history(
    session_id: str = "default",
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Clear chat history for a session"""
    try:
        # Get orchestrator to access memory manager
        orchestrator = await orchestrator_pool.get_healthy_orchestrator()
        if not orchestrator:
            return {"success": False, "error": "No healthy orchestrator available"}

        # Clear context from memory manager
        await orchestrator.memory_manager.clear_context(session_id)

        return {
            "success": True,
            "message": f"Chat history cleared for session: {session_id}",
        }

    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return {"success": False, "error": str(e)}


@router.get("/memory_stats")
async def get_memory_statistics(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get memory management statistics"""
    try:
        # Get orchestrator to access memory manager
        orchestrator = await orchestrator_pool.get_healthy_orchestrator()
        if not orchestrator:
            return {
                "success": False,
                "error": "No healthy orchestrator available",
                "stats": {},
            }

        # Get comprehensive memory statistics
        memory_stats = await orchestrator.memory_manager.get_context_stats()

        return {
            "success": True,
            "stats": memory_stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting memory statistics: {e}")
        return {"success": False, "error": str(e), "stats": {}}


@router.post("/memory_optimize")
async def optimize_memory_contexts(
    session_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Manually trigger memory optimization for specific session or all sessions"""
    try:
        # Get orchestrator to access memory manager
        orchestrator = await orchestrator_pool.get_healthy_orchestrator()
        if not orchestrator:
            return {"success": False, "error": "No healthy orchestrator available"}

        if session_id:
            # Optimize specific session
            context = await orchestrator.memory_manager.get_context(session_id)
            context._optimize_context_window(max_tokens=4000)
            await orchestrator.memory_manager.update_context(context)

            return {
                "success": True,
                "message": f"Memory optimized for session: {session_id}",
                "session_id": session_id,
            }
        # Optimize all sessions
        all_contexts = await orchestrator.memory_manager.get_all_contexts()
        optimized_count = 0

        for ctx in all_contexts.values():
            if hasattr(ctx, "_optimize_context_window"):
                ctx._optimize_context_window(max_tokens=4000)
                await orchestrator.memory_manager.update_context(ctx)
                optimized_count += 1

        return {
            "success": True,
            "message": f"Memory optimized for {optimized_count} sessions",
            "optimized_count": optimized_count,
        }

    except Exception as e:
        logger.error(f"Error optimizing memory: {e}")
        return {"success": False, "error": str(e)}
