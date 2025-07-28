"""
Gmail Inbox Zero API Endpoints

API endpoints for Gmail Inbox Zero management agent
"""

import logging
import json
import asyncio
from typing import TYPE_CHECKING, Any
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from agents.agent_factory import AgentFactory
from schemas.gmail_schemas import (
    InboxZeroRequest,
    InboxZeroResponse,
    InboxZeroStats,
)

if TYPE_CHECKING:
    from agents.interfaces import AgentResponse

logger = logging.getLogger()  # root logger

router = APIRouter()


# Global agent cache for better performance
_gmail_agent_cache: dict[str, Any] = {}

@lru_cache(maxsize=1)
def get_cached_gmail_agent() -> Any:
    """Get cached Gmail Inbox Zero agent instance"""
    factory = AgentFactory()
    agent = factory.create_agent("gmail_inbox_zero")
    logger.info("Created new Gmail agent instance")
    return agent

async def get_gmail_agent() -> Any:
    """Dependency to get Gmail Inbox Zero agent with caching"""
    try:
        return get_cached_gmail_agent()
    except Exception as e:
        logger.error(f"Failed to get Gmail agent: {e}")
        # Fallback to new instance
        factory = AgentFactory()
        return factory.create_agent("gmail_inbox_zero")


@router.post("/analyze", response_model=InboxZeroResponse)
async def analyze_email(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Analizuje email i sugeruje akcje dla Inbox Zero

    Args:
        request: Dane emaila do analizy
        agent: Gmail Inbox Zero agent

    Returns:
        Analiza emaila z sugestiami akcji
    """
    try:
        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "analyze",
            "message_id": request.message_id,
            "thread_id": request.thread_id,
            "user_feedback": request.user_feedback,
            "email_data": request.email_data,
        }
        
        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)
        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Analiza zakończona pomyślnie",
                    "data": response.data,
                    "suggestions": (
                        response.data.get("suggestions", []) if response.data else []
                    ),
                    "metadata": response.metadata,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas analizy emaila",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w analizie emaila: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas analizy: {e!s}"
        )


@router.post("/messages/modify", response_model=InboxZeroResponse)
async def modify_messages(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Modyfikuje wiadomości (dodaje/usuwa etykiety, oznacza jako przeczytane/nieprzeczytane)

    Args:
        request: Dane modyfikacji
        agent: Gmail Inbox Zero agent

    Returns:
        Status modyfikacji
    """
    try:
        if not request.message_ids:
            raise HTTPException(status_code=400, detail="Brak ID wiadomości do modyfikacji")

        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "batch_modify",
            "message_ids": request.message_ids,
            "add_labels": request.add_labels,
            "remove_labels": request.remove_labels,
            "mark_as_read": request.mark_as_read,
            "mark_as_unread": request.mark_as_unread,
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Wiadomości zostały zmodyfikowane",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas modyfikacji wiadomości",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w modyfikacji wiadomości: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas modyfikacji wiadomości: {e!s}"
        )


@router.post("/messages/archive", response_model=InboxZeroResponse)
async def archive_messages(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Archiwizuje wiadomości

    Args:
        request: Dane wiadomości do archiwizacji
        agent: Gmail Inbox Zero agent

    Returns:
        Status archiwizacji
    """
    try:
        if not request.message_ids:
            raise HTTPException(status_code=400, detail="Brak ID wiadomości do archiwizacji")

        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "batch_archive",
            "message_ids": request.message_ids,
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Wiadomości zostały zarchiwizowane",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas archiwizacji wiadomości",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w archiwizacji wiadomości: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas archiwizacji: {e!s}"
        )


@router.post("/messages/delete", response_model=InboxZeroResponse)
async def delete_messages(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Usuwa wiadomości

    Args:
        request: Dane wiadomości do usunięcia
        agent: Gmail Inbox Zero agent

    Returns:
        Status usunięcia
    """
    try:
        if not request.message_ids:
            raise HTTPException(status_code=400, detail="Brak ID wiadomości do usunięcia")

        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "batch_delete",
            "message_ids": request.message_ids,
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Wiadomości zostały usunięte",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas usuwania wiadomości",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w usuwaniu wiadomości: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas usuwania wiadomości: {e!s}"
        )


@router.post("/mark-read", response_model=InboxZeroResponse)
async def mark_as_read(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Oznacza email jako przeczytany

    Args:
        request: Dane emaila do oznaczenia
        agent: Gmail Inbox Zero agent

    Returns:
        Status oznaczenia jako przeczytany
    """
    try:
        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "mark_read",
            "message_id": request.message_id,
            "thread_id": request.thread_id,
            "user_feedback": request.user_feedback,
            "email_data": request.email_data,
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Email oznaczony jako przeczytany",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas oznaczenia jako przeczytany",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w oznaczeniu jako przeczytany: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas oznaczenia jako przeczytany: {e!s}",
        )


@router.post("/star", response_model=InboxZeroResponse)
async def star_message(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Oznacza email gwiazdką

    Args:
        request: Dane emaila do oznaczenia gwiazdką
        agent: Gmail Inbox Zero agent

    Returns:
        Status oznaczenia gwiazdką
    """
    try:
        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "star",
            "message_id": request.message_id,
            "thread_id": request.thread_id,
            "user_feedback": request.user_feedback,
            "email_data": request.email_data,
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Email oznaczony gwiazdką",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas oznaczenia gwiazdką",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w oznaczeniu gwiazdką: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas oznaczenia gwiazdką: {e!s}"
        )


@router.post("/learn", response_model=InboxZeroResponse)
async def learn_from_interaction(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Uczy się na podstawie interakcji z użytkownikiem

    Args:
        request: Dane uczenia się
        agent: Gmail Inbox Zero agent

    Returns:
        Status uczenia się
    """
    try:
        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "learn",
            "message_id": request.message_id,
            "thread_id": request.thread_id,
            "user_feedback": request.user_feedback,
            "learning_data": request.learning_data,
            "email_data": request.email_data,
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Dane uczenia się zostały przetworzone",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas uczenia się",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w uczeniu się: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas uczenia się: {e!s}"
        )


@router.get("/stats/{user_id}", response_model=InboxZeroStats)
async def get_inbox_stats(
    user_id: str, request: Request, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Pobiera statystyki Inbox Zero dla użytkownika

    Args:
        user_id: ID użytkownika lub "current-user"
        request: FastAPI request object
        agent: Gmail Inbox Zero agent

    Returns:
        Statystyki Inbox Zero
    """
    try:
        # Handle "current-user" case with better validation
        actual_user_id = user_id
        if user_id == "current-user":
            # Try to get user ID from request state (authentication middleware)
            if hasattr(request.state, "user_id") and request.state.user_id:
                actual_user_id = str(request.state.user_id)
                logger.info(f"Using authenticated user ID: {actual_user_id}")
            else:
                # Try to get from headers
                auth_user = request.headers.get("X-User-ID")
                if auth_user:
                    actual_user_id = auth_user
                    logger.info(f"Using user ID from headers: {actual_user_id}")
                else:
                    # Fallback to a default user ID for development
                    actual_user_id = "dev_user"
                    logger.warning(f"No authenticated user found, using default: {actual_user_id}")

        # Pobierz statystyki z agenta
        stats = await agent.get_inbox_stats(actual_user_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "total_messages": stats.total_messages,
                    "unread_messages": stats.unread_messages,
                    "labeled_messages": stats.labeled_messages,
                    "archived_messages": stats.archived_messages,
                    "deleted_messages": stats.deleted_messages,
                    "inbox_zero_percentage": stats.inbox_zero_percentage,
                    "learning_accuracy": stats.learning_accuracy,
                    "last_analysis": (
                        stats.last_analysis.isoformat() if stats.last_analysis else None
                    ),
                },
            },
        )

    except Exception as e:
        logger.error(f"Błąd w pobieraniu statystyk: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas pobierania statystyk: {e!s}"
        )


@router.get("/messages/{user_id}")
async def get_messages(
    user_id: str,
    request: Request,
    limit: int = 50,
    agent: Any = Depends(get_gmail_agent),
) -> JSONResponse:
    """
    Pobiera listę wiadomości z Gmail dla użytkownika

    Args:
        user_id: ID użytkownika lub "current-user"
        request: FastAPI request object
        limit: Maksymalna liczba wiadomości do pobrania
        agent: Gmail Inbox Zero agent

    Returns:
        Lista wiadomości Gmail
    """
    try:
        # Handle "current-user" case with better validation
        actual_user_id = user_id
        if user_id == "current-user":
            if hasattr(request.state, "user_id") and request.state.user_id:
                actual_user_id = str(request.state.user_id)
                logger.info(f"Using authenticated user ID: {actual_user_id}")
            else:
                # Try to get from headers
                auth_user = request.headers.get("X-User-ID")
                if auth_user:
                    actual_user_id = auth_user
                    logger.info(f"Using user ID from headers: {actual_user_id}")
                else:
                    actual_user_id = "dev_user"
                    logger.warning(f"No authenticated user found, using default: {actual_user_id}")

        # Pobierz wiadomości z Gmail API
        if agent.gmail_service:
            try:
                # Pobierz listę wiadomości z inbox - wrapped in asyncio.to_thread to avoid blocking
                messages_result = await asyncio.to_thread(
                    lambda: agent.gmail_service.users()
                    .messages()
                    .list(userId="me", labelIds=["INBOX"], maxResults=limit)
                    .execute()
                )

                messages = messages_result.get("messages", [])

                # Pobierz szczegóły dla każdej wiadomości
                detailed_messages = []
                for msg in messages:
                    try:
                        # Pobierz pełne dane wiadomości - wrapped in asyncio.to_thread
                        message = await asyncio.to_thread(
                            lambda msg_id=msg["id"]: agent.gmail_service.users()
                            .messages()
                            .get(userId="me", id=msg_id, format="full")
                            .execute()
                        )

                        # Wyciągnij nagłówki
                        headers = message["payload"]["headers"]
                        subject = next(
                            (h["value"] for h in headers if h["name"] == "Subject"),
                            "Brak tematu",
                        )
                        sender = next(
                            (h["value"] for h in headers if h["name"] == "From"),
                            "Nieznany nadawca",
                        )
                        date = next(
                            (h["value"] for h in headers if h["name"] == "Date"), ""
                        )

                        # Wyciągnij snippet
                        snippet = message.get("snippet", "")

                        # Sprawdź labele
                        labels = message.get("labelIds", [])
                        is_read = "UNREAD" not in labels
                        is_starred = "STARRED" in labels

                        detailed_messages.append(
                            {
                                "message_id": msg["id"],
                                "subject": subject,
                                "sender": sender,
                                "date": date,
                                "snippet": snippet,
                                "is_read": is_read,
                                "is_starred": is_starred,
                                "labels": labels,
                            }
                        )

                    except Exception as e:
                        logger.error(
                            f"Error getting message details for {msg['id']}: {e}"
                        )
                        continue

                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "data": detailed_messages,
                        "total": len(detailed_messages),
                    },
                )

            except Exception as e:
                logger.error(f"Gmail API error: {e}")
                # Return proper error response instead of fake success
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "error": "Gmail API temporarily unavailable",
                        "data": [],
                        "total": 0,
                        "message": f"Gmail API error: {str(e)}",
                    },
                )
        else:
            # Mock data when Gmail API is not available
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": [],
                    "total": 0,
                    "message": "Gmail API not connected, no messages to display",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w pobieraniu wiadomości: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas pobierania wiadomości: {e!s}",
        )


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Health check dla endpointów Gmail Inbox Zero

    Returns:
        Status zdrowia systemu
    """
    try:
        factory = AgentFactory()
        agent = factory.create_agent("gmail_inbox_zero")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Gmail Inbox Zero agent jest dostępny",
                "agent_metadata": agent.get_metadata(),
            },
        )

    except Exception as e:
        logger.error(f"Błąd w health check: {e}")
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": f"Agent niedostępny: {e!s}"},
        )


@router.post("/analyze-all-unread")
async def analyze_all_unread(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Analizuje wszystkie nieprzeczytane wiadomości

    Args:
        request: Dane żądania
        agent: Gmail Inbox Zero agent

    Returns:
        Status analizy wszystkich nieprzeczytanych wiadomości
    """
    try:
        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "analyze_all_unread",
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Analiza wszystkich nieprzeczytanych wiadomości zakończona",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas analizy wszystkich nieprzeczytanych wiadomości",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w analizie wszystkich nieprzeczytanych: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas analizy: {e!s}"
        )


@router.post("/auto-archive")
async def auto_archive_old_messages(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Automatycznie archiwizuje stare wiadomości

    Args:
        request: Dane żądania
        agent: Gmail Inbox Zero agent

    Returns:
        Status auto-archiwizacji
    """
    try:
        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "auto_archive",
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Auto-archiwizacja starych wiadomości zakończona",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas auto-archiwizacji",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w auto-archiwizacji: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas auto-archiwizacji: {e!s}"
        )


@router.post("/apply-smart-labels")
async def apply_smart_labels(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Zastosowuje inteligentne etykiety do wiadomości

    Args:
        request: Dane żądania
        agent: Gmail Inbox Zero agent

    Returns:
        Status zastosowania inteligentnych etykiet
    """
    try:
        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "apply_smart_labels",
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Inteligentne etykiety zostały zastosowane",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas zastosowania inteligentnych etykiet",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w zastosowaniu inteligentnych etykiet: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas zastosowania inteligentnych etykiet: {e!s}"
        )


@router.post("/mark-important")
async def mark_important_messages(
    request: InboxZeroRequest, agent: Any = Depends(get_gmail_agent)
) -> JSONResponse:
    """
    Oznacza ważne wiadomości

    Args:
        request: Dane żądania
        agent: Gmail Inbox Zero agent

    Returns:
        Status oznaczenia ważnych wiadomości
    """
    try:
        # Przygotuj dane dla agenta
        agent_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "operation": "mark_important",
        }

        # Wywołaj agenta
        response: AgentResponse = await agent.process(agent_data)

        if response.success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response.text or "Ważne wiadomości zostały oznaczone",
                    "data": response.data,
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": response.error,
                    "message": "Błąd podczas oznaczania ważnych wiadomości",
                },
            )

    except Exception as e:
        logger.error(f"Błąd w oznaczaniu ważnych wiadomości: {e}")
        raise HTTPException(
            status_code=500, detail=f"Wystąpił błąd podczas oznaczania ważnych wiadomości: {e!s}"
        )


@router.get("/stream")
async def stream_updates():
    """
    Server-Sent Events endpoint dla aktualizacji w czasie rzeczywistym
    
    Returns:
        Stream z aktualizacjami Gmail Inbox Zero
    """
    async def event_stream():
        """Generator dla SSE stream"""
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connection', 'message': 'SSE connection established'})}\n\n"
            
            # Keep connection alive with periodic updates
            while True:
                try:
                    # Get latest stats
                    agent = get_cached_gmail_agent()
                    stats = await agent.get_inbox_stats("current-user")
                    
                    # Send stats update
                    yield f"data: {json.dumps({'type': 'stats_update', 'stats': stats.dict()})}\n\n"
                    
                    # Wait before next update
                    await asyncio.sleep(30)  # Update every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    await asyncio.sleep(5)  # Wait before retry
                    
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Stream connection lost'})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )


@router.get("/labels/{user_id}")
async def get_gmail_labels(
    user_id: str,
    request: Request,
    agent: Any = Depends(get_gmail_agent),
) -> JSONResponse:
    """
    Pobiera wszystkie etykiety Gmail użytkownika (systemowe i własne)
    """
    try:
        # Handle "current-user" case
        actual_user_id = user_id
        if user_id == "current-user":
            if hasattr(request.state, "user_id") and request.state.user_id:
                actual_user_id = str(request.state.user_id)
            else:
                auth_user = request.headers.get("X-User-ID")
                if auth_user:
                    actual_user_id = auth_user
                else:
                    actual_user_id = "dev_user"

        if agent.gmail_service:
            import asyncio
            labels_result = await asyncio.to_thread(
                lambda: agent.gmail_service.users().labels().list(userId="me").execute()
            )
            labels = labels_result.get("labels", [])
            # Zwróć tylko name i id
            label_list = [{"id": l["id"], "name": l["name"], "type": l.get("type", "user") } for l in labels]
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": label_list,
                    "total": len(label_list),
                },
            )
        else:
            # Mock dane jeśli Gmail API nie jest dostępne
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": [],
                    "total": 0,
                    "message": "Gmail API not connected, no labels to display",
                },
            )
    except Exception as e:
        logger.error(f"Błąd w pobieraniu etykiet: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas pobierania etykiet: {e!s}",
        )
