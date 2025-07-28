# Skopiuj i wklej ten kod jako całą zawartość pliku state.py

from dataclasses import dataclass, field
from typing import Any

from agents.interfaces import AgentStatus


@dataclass
class AgentState:
    """Represents the state of an individual agent"""

    name: str
    status: AgentStatus = AgentStatus.IDLE
    last_activity: float = 0.0  # timestamp
    error_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    """Represents the state of a conversation."""

    session_id: str
    history: list[dict[str, Any]] = field(default_factory=list)
    is_awaiting_clarification: bool = False
    is_cooking_confirmation: bool = False
    original_intent: str | None = None
    original_entities: dict[str, Any] | None = None
    ambiguous_options: list[Any] = field(default_factory=list)
    cooking_ingredients: list[dict[str, Any]] = field(default_factory=list)
    agent_states: dict[str, bool] = field(
        default_factory=lambda: {
            "weather": True,
            "search": True,
            "shopping": False,
            "cooking": False,
        }
    )
    current_model: str = (
        "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"  # Default model to use for LLM operations
    )

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def set_clarification_mode(
        self, intent: str, entities: dict[str, Any], options: list[Any]
    ) -> None:
        self.is_awaiting_clarification = True
        self.original_intent = intent
        self.original_entities = entities
        self.ambiguous_options = options

    def set_cooking_state(self, ingredients: list[dict[str, Any]]) -> None:
        """Set state for cooking confirmation flow."""
        self.is_cooking_confirmation = True
        self.cooking_ingredients = ingredients

    def reset(self) -> None:
        self.is_awaiting_clarification = False
        self.is_cooking_confirmation = False
        self.original_intent = None
        self.original_entities = None
        self.ambiguous_options = []
        self.cooking_ingredients = []

    def to_dict(self) -> dict[str, Any]:
        result = {
            "session_id": self.session_id,
            "history_length": len(self.history),
            "is_awaiting_clarification": self.is_awaiting_clarification,
            "is_cooking_confirmation": self.is_cooking_confirmation,
            "cooking_ingredients": self.cooking_ingredients,
            "original_intent": self.original_intent,
            "ambiguous_options": self.ambiguous_options,
            "agent_states": self.agent_states,
            "current_model": self.current_model,
        }
        return result
