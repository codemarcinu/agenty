import asyncio
import datetime
import json
import types
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from backend.agents.interfaces import AgentResponse, BaseAgent
from backend.agents.orchestrator import Orchestrator
from backend.core import crud
from backend.core.database import AsyncSessionLocal
from backend.core.llm_client import llm_client
from backend.models.shopping import Product, ShoppingTrip
from backend.settings import settings

# --- Funkcje pomocnicze, które już znamy ---


def extract_json_from_text(text: str) -> str:
    try:
        start_index = text.find("{")
        end_index = text.rfind("}")
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return text[start_index : end_index + 1]
        return ""
    except Exception:
        return ""


def generate_clarification_question(options: list[Any]) -> str:
    if not options:
        return "Coś poszło nie tak, nie mam opcji do wyboru."
    formatted_options = []
    for i, obj in enumerate(options, 1):
        if isinstance(obj, ShoppingTrip):
            formatted_options.append(
                f"{i}. Paragon ze sklepu '{obj.store_name}' z dnia {obj.trip_date}."
            )
        elif isinstance(obj, Product):
            formatted_options.append(
                f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł."
            )
    return "\n".join(formatted_options)


# --- NOWA FUNKCJA Z INTELIGENCJĄ DO ROZUMIENIA ODPOWIEDZI ---


async def resolve_ambiguity(options: list[Any], user_reply: str) -> Any | None:
    """
    Na podstawie listy opcji i odpowiedzi użytkownika, prosi LLM o wybranie właściwego obiektu.
    """

    options_text = generate_clarification_question(options)

    resolver_prompt = f"""Twoim zadaniem jest analiza odpowiedzi użytkownika i dopasowanie jej do jednej z przedstawionych wcześniej opcji. Zwróć obiekt JSON z jednym kluczem: 'wybrany_indeks'. Indeks jest numerem opcji z listy (zaczynając od 1). Jeśli nie jesteś w stanie jednoznacznie dopasować odpowiedzi do żadnej z opcji, zwróć null.

### Kontekst
Użytkownik został poproszony o wybór jednej z poniższych opcji:
{options_text}

### Odpowiedź użytkownika do analizy
"{user_reply}"
"""
    try:
        messages = [
            {
                "role": "system",
                "content": "Jesteś pomocnym asystentem AI. Zawsze zwracaj tylko i wyłącznie obiekt JSON.",
            },
            {"role": "user", "content": resolver_prompt},
        ]

        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={"temperature": 0.0},
        )

        raw_response = response["message"]["content"]

        json_string = extract_json_from_text(raw_response)
        parsed_json = json.loads(json_string)
        selected_index = parsed_json.get("wybrany_indeks")

        if (
            selected_index is not None
            and isinstance(selected_index, int)
            and 1 <= selected_index <= len(options)
        ):
            chosen_object = options[selected_index - 1]
            return chosen_object
        return None
    except Exception:
        return None


# --- GŁÓWNA FUNKCJA SYMULUJĄCA DIALOG ---


async def run_dialogue_simulation():
    """
    Symuluje pełną, dwuetapową konwersację z agentem.
    """

    # Etap 1: Niejednoznaczne polecenie użytkownika

    async with AsyncSessionLocal() as db:
        try:
            # Agent próbuje znaleźć cel
            znalezione_obiekty = await crud.find_purchase_for_action(
                db, entities={"paragon_identyfikator": {"data": "wtorek"}}
            )

            if len(znalezione_obiekty) > 1:

                # Etap 2: Agent zadaje pytanie doprecyzowujące
                generate_clarification_question(znalezione_obiekty)

                # Etap 3: Użytkownik odpowiada, doprecyzowując
                user_input_2 = "ten z Lidla poproszę"

                # Etap 4: Agent próbuje zrozumieć odpowiedź
                finalny_cel = await resolve_ambiguity(znalezione_obiekty, user_input_2)

                if finalny_cel:
                    pass
                else:
                    pass

            elif len(znalezione_obiekty) == 1:
                pass

            else:
                pass

        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(run_dialogue_simulation())


@pytest_asyncio.fixture
async def db_session():
    """Pytest fixture to provide a test database session and handle setup/teardown."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.mark.asyncio
@patch(
    "src.backend.core.llm_client.llm_client.chat",
    new_callable=AsyncMock,
    return_value={"message": {"content": '{"mocked": true}'}},
)
class TestFullDialogue:
    @pytest.mark.asyncio
    @pytest.mark.db_dependent
    async def test_add_new_item_dialogue(self, mock_llm, db_session):
        """Test full dialogue for adding a new item"""
        # Mock required dependencies
        mock_profile_manager = AsyncMock()
        mock_intent_detector = AsyncMock()
        mock_intent_detector.detect_intent.return_value = MagicMock(
            type="database", confidence=0.9
        )
        mock_memory_manager = MagicMock()
        context_obj = types.SimpleNamespace(
            session_id="test_session_add",
            history=[],
            active_agents={},
            last_response=None,
            created_at=datetime.datetime.now(),
            last_updated=datetime.datetime.now(),
        )
        mock_memory_manager.get_context = AsyncMock(return_value=context_obj)
        mock_memory_manager.update_context = AsyncMock()
        mock_agent_router = MagicMock()
        mock_agent_router.route_to_agent = AsyncMock(
            return_value=AgentResponse(success=True, text="OK", data={})
        )

        orchestrator = Orchestrator(
            db_session=db_session,
            profile_manager=mock_profile_manager,
            intent_detector=mock_intent_detector,
            memory_manager=mock_memory_manager,
            agent_router=mock_agent_router,
        )

        command = "dodaj parówki za 12 zł do wczorajszych zakupów"
        result = await orchestrator.process_command(command, "test_session_add")
        assert result.text is not None or result.data is not None

    @pytest.mark.asyncio
    @pytest.mark.db_dependent
    async def test_update_item_dialogue(self, mock_llm, db_session):
        """Test full dialogue for updating an item"""
        mock_profile_manager = AsyncMock()
        mock_intent_detector = AsyncMock()
        mock_intent_detector.detect_intent.return_value = MagicMock(
            type="database", confidence=0.9
        )
        mock_memory_manager = MagicMock()
        context_obj = types.SimpleNamespace(
            session_id="test_session",
            history=[],
            active_agents={},
            last_response=None,
            created_at=datetime.datetime.now(),
            last_updated=datetime.datetime.now(),
        )
        mock_memory_manager.get_context = AsyncMock(return_value=context_obj)
        mock_memory_manager.update_context = AsyncMock()
        mock_agent_router = MagicMock()
        mock_agent_router.route_to_agent = AsyncMock(
            return_value=AgentResponse(success=True, text="OK", data={})
        )

        orchestrator = Orchestrator(
            db_session=db_session,
            profile_manager=mock_profile_manager,
            intent_detector=mock_intent_detector,
            memory_manager=mock_memory_manager,
            agent_router=mock_agent_router,
        )

        command = "zmień cenę mleka na 4.50 zł"
        result = await orchestrator.process_command(command, "test_session")
        assert result.success is not False

    @pytest.mark.asyncio
    @pytest.mark.db_dependent
    async def test_delete_item_dialogue(self, mock_llm, db_session):
        """Test full dialogue for deleting an item"""
        mock_profile_manager = AsyncMock()
        mock_intent_detector = AsyncMock()
        mock_intent_detector.detect_intent.return_value = MagicMock(
            type="database", confidence=0.9
        )
        mock_memory_manager = MagicMock()
        context_obj = types.SimpleNamespace(
            session_id="test_session",
            history=[],
            active_agents={},
            last_response=None,
            created_at=datetime.datetime.now(),
            last_updated=datetime.datetime.now(),
        )
        mock_memory_manager.get_context = AsyncMock(return_value=context_obj)
        mock_memory_manager.update_context = AsyncMock()
        mock_agent_router = MagicMock()
        mock_agent_router.route_to_agent = AsyncMock(
            return_value=AgentResponse(success=True, text="OK", data={})
        )

        orchestrator = Orchestrator(
            db_session=db_session,
            profile_manager=mock_profile_manager,
            intent_detector=mock_intent_detector,
            memory_manager=mock_memory_manager,
            agent_router=mock_agent_router,
        )

        command = "usuń masło z ostatniego paragonu"
        result = await orchestrator.process_command(command, "test_session")
        assert result.success is not False


class DummyAgent(BaseAgent):
    async def process(self, input_data):
        return AgentResponse(success=True, text="dummy")

    def get_metadata(self):
        return {}

    def get_dependencies(self):
        return []

    def is_healthy(self):
        return True
