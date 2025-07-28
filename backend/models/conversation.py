from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    messages: Mapped[list[Message]] = relationship(
        f"{__name__}.Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Text dla dużych treści wiadomości
    role: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )  # "user" or "assistant"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    message_metadata: Mapped[dict] = mapped_column(JSON, default={})

    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=False
    )
    conversation: Mapped[Conversation] = relationship(
        f"{__name__}.Conversation",
        back_populates="messages",
        lazy="selectin",
    )


# Composite index for common message queries
Index("ix_message_conversation_created", Message.conversation_id, Message.created_at)


class ConversationSession(Base):
    """Tabela do przechowywania podsumowań konwersacji"""

    __tablename__ = "conversation_sessions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String, index=True, nullable=True
    )  # Opcjonalne, dla przyszłej funkcjonalności
    summary: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # Podsumowanie konwersacji
    key_points: Mapped[list] = mapped_column(
        JSON, default=[]
    )  # Kluczowe punkty jako lista
    topics_discussed: Mapped[list] = mapped_column(JSON, default=[])  # Tematy rozmowy
    user_preferences: Mapped[dict] = mapped_column(
        JSON, default={}
    )  # Preferencje użytkownika
    conversation_style: Mapped[str] = mapped_column(
        String, default="friendly"
    )  # Styl rozmowy
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    last_message_count: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Liczba wiadomości w momencie ostatniego podsumowania
