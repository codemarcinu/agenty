"""
Zadania Celery do obsługi pamięci podsumowującej konwersacji
"""

from datetime import datetime
import json
import logging

from celery import Celery
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.llm_client import llm_client
from models.conversation import Conversation, ConversationSession, Message
from settings import settings

logger = logging.getLogger(__name__)

# Inicjalizacja Celery (zakładając, że jest już skonfigurowany w projekcie)
celery_app = Celery("conversation_tasks")
celery_app.config_from_object("backend.config.celery_config")


@celery_app.task
def update_conversation_summary_task(session_id: str) -> dict[str, any]:
    """
    Zadanie w tle do aktualizacji podsumowania konwersacji

    Args:
        session_id: ID sesji konwersacji

    Returns:
        Dict z wynikiem operacji
    """
    try:
        # Używamy asyncio.run do uruchomienia funkcji asynchronicznej w zadaniu Celery
        import asyncio

        return asyncio.run(_update_conversation_summary_async(session_id))
    except Exception as e:
        logger.error(f"Error in update_conversation_summary_task: {e}")
        return {"success": False, "error": str(e)}


async def _update_conversation_summary_async(session_id: str) -> dict[str, any]:
    """
    Asynchroniczna funkcja do aktualizacji podsumowania konwersacji
    """
    try:
        async for db in get_db():
            # Pobierz ostatnie wiadomości z konwersacji
            messages = await _get_recent_messages(db, session_id, limit=10)

            if not messages:
                logger.info(f"No messages found for session {session_id}")
                return {"success": True, "message": "No messages to summarize"}

            # Sprawdź czy podsumowanie jest potrzebne
            current_message_count = len(messages)
            existing_session = await _get_conversation_session(db, session_id)

            if (
                existing_session
                and existing_session.last_message_count >= current_message_count
            ):
                logger.info(f"Summary already up to date for session {session_id}")
                return {"success": True, "message": "Summary already up to date"}

            # Wygeneruj podsumowanie
            summary_data = await _generate_conversation_summary(messages)

            # Zapisz lub zaktualizuj podsumowanie
            await _save_conversation_summary(
                db, session_id, summary_data, current_message_count
            )

            logger.info(
                f"Successfully updated conversation summary for session {session_id}"
            )
            return {
                "success": True,
                "message": "Summary updated",
                "summary_length": len(summary_data.get("summary", "")),
                "key_points_count": len(summary_data.get("key_points", [])),
            }

    except Exception as e:
        logger.error(
            f"Error updating conversation summary for session {session_id}: {e}"
        )
        return {"success": False, "error": str(e)}


async def _get_recent_messages(
    db: AsyncSession, session_id: str, limit: int = 10
) -> list[dict]:
    """
    Pobierz ostatnie wiadomości z konwersacji
    """
    try:
        # Znajdź konwersację
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            logger.warning(f"Conversation not found for session {session_id}")
            return []

        # Pobierz ostatnie wiadomości
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        # Konwertuj na format słownika
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "metadata": msg.message_metadata or {},
            }
            for msg in reversed(messages)  # Odwróć kolejność, aby była chronologiczna
        ]

    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        return []


async def _generate_conversation_summary(messages: list[dict]) -> dict[str, any]:
    """
    Wygeneruj podsumowanie konwersacji używając LLM
    """
    try:
        # Przygotuj kontekst dla LLM
        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in messages]
        )

        # Prompt do generowania podsumowania
        system_prompt = """
Jesteś ekspertem w analizie konwersacji. Twoim zadaniem jest stworzenie zwięzłego podsumowania rozmowy.

Zawsze zwracaj odpowiedź w formacie JSON z następującymi polami:
- "summary": zwięzłe podsumowanie rozmowy (2-3 zdania)
- "key_points": lista kluczowych punktów z rozmowy
- "topics_discussed": lista tematów poruszonych w rozmowie
- "user_preferences": słownik z preferencjami użytkownika (jeśli jakieś się pojawiły)
- "conversation_style": styl rozmowy (friendly, formal, technical, casual)

Przykład odpowiedzi:
{
    "summary": "Użytkownik pytał o przepisy na dania z kurczaka i pogodę na jutro.",
    "key_points": ["szuka przepisów z kurczakiem", "interesuje się pogodą", "planuje gotowanie"],
    "topics_discussed": ["cooking", "weather", "meal planning"],
    "user_preferences": {"cooking_style": "simple", "weather_concern": "rain"},
    "conversation_style": "friendly"
}
"""

        # Wywołaj LLM
        response = await llm_client.chat(
            model=settings.DEFAULT_CODE_MODEL,  # Użyj szybszego modelu
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Przeanalizuj tę konwersację:\n\n{conversation_text}",
                },
            ],
            stream=False,
            options={"temperature": 0.1},  # Niska temperatura dla spójności
        )

        if isinstance(response, dict) and response.get("message"):
            content = response["message"]["content"]

            # Spróbuj sparsować JSON
            try:
                from core.utils import extract_json_from_text

                json_str = extract_json_from_text(content)
                if json_str:
                    summary_data = json.loads(json_str)
                    return summary_data
                logger.warning(f"No valid JSON found in summary response: {content}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from summary response: {e}")

        # Fallback: zwróć podstawowe podsumowanie
        return {
            "summary": "Konwersacja zawierała różne tematy.",
            "key_points": [],
            "topics_discussed": ["general"],
            "user_preferences": {},
            "conversation_style": "friendly",
        }

    except Exception as e:
        logger.error(f"Error generating conversation summary: {e}")
        return {
            "summary": "Błąd podczas generowania podsumowania.",
            "key_points": [],
            "topics_discussed": [],
            "user_preferences": {},
            "conversation_style": "friendly",
        }


async def _get_conversation_session(
    db: AsyncSession, session_id: str
) -> ConversationSession | None:
    """
    Pobierz istniejącą sesję konwersacji
    """
    try:
        stmt = select(ConversationSession).where(
            ConversationSession.session_id == session_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting conversation session: {e}")
        return None


async def _save_conversation_summary(
    db: AsyncSession, session_id: str, summary_data: dict[str, any], message_count: int
) -> None:
    """
    Zapisz lub zaktualizuj podsumowanie konwersacji
    """
    try:
        existing_session = await _get_conversation_session(db, session_id)

        if existing_session:
            # Aktualizuj istniejącą sesję
            stmt = (
                update(ConversationSession)
                .where(ConversationSession.session_id == session_id)
                .values(
                    summary=summary_data.get("summary"),
                    key_points=summary_data.get("key_points", []),
                    topics_discussed=summary_data.get("topics_discussed", []),
                    user_preferences=summary_data.get("user_preferences", {}),
                    conversation_style=summary_data.get(
                        "conversation_style", "friendly"
                    ),
                    updated_at=datetime.utcnow(),
                    last_message_count=message_count,
                )
            )
            await db.execute(stmt)
        else:
            # Utwórz nową sesję
            new_session = ConversationSession(
                session_id=session_id,
                summary=summary_data.get("summary"),
                key_points=summary_data.get("key_points", []),
                topics_discussed=summary_data.get("topics_discussed", []),
                user_preferences=summary_data.get("user_preferences", {}),
                conversation_style=summary_data.get("conversation_style", "friendly"),
                last_message_count=message_count,
            )
            db.add(new_session)

        await db.commit()
        logger.info(f"Successfully saved conversation summary for session {session_id}")

    except Exception as e:
        logger.error(f"Error saving conversation summary: {e}")
        await db.rollback()
        raise


async def get_conversation_summary(session_id: str) -> dict[str, any] | None:
    """
    Pobierz podsumowanie konwersacji dla danej sesji
    """
    try:
        async for db in get_db():
            session = await _get_conversation_session(db, session_id)
            if session:
                return {
                    "summary": session.summary,
                    "key_points": session.key_points,
                    "topics_discussed": session.topics_discussed,
                    "user_preferences": session.user_preferences,
                    "conversation_style": session.conversation_style,
                    "last_message_count": session.last_message_count,
                }
            return None
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        return None
