"""
WebSocket endpoint for general chat with tool access and agent routing
"""

from datetime import datetime
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from agents.orchestrator_factory import create_orchestrator
from agents.tools.tool_interface import ToolInterface
from core.async_patterns import timeout_context
from infrastructure.database.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Chat message model for WebSocket communication"""

    type: str  # 'message', 'tool_request', 'agent_switch', 'ping'
    content: str
    session_id: str | None = None
    agent_id: str | None = None
    tool_name: str | None = None
    metadata: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """Chat response model for WebSocket communication"""

    type: str  # 'message', 'tool_response', 'agent_status', 'error'
    content: str
    agent_id: str | None = None
    tool_used: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] | None = None
    timestamp: str


class ChatConnectionManager:
    """Manages WebSocket connections for chat"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.session_data: dict[str, dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_data[session_id] = {
            "active_agent": None,
            "conversation_history": [],
            "last_activity": datetime.now(),
            "tools_used": [],
        }
        logger.info(f"Chat WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_data:
            del self.session_data[session_id]
        logger.info(f"Chat WebSocket disconnected for session: {session_id}")

    async def send_personal_message(self, session_id: str, message: ChatResponse):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(
                    message.model_dump_json()
                )
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                self.disconnect(session_id)

    def get_session_data(self, session_id: str) -> dict[str, Any] | None:
        return self.session_data.get(session_id)

    def update_session_data(self, session_id: str, data: dict[str, Any]):
        if session_id in self.session_data:
            self.session_data[session_id].update(data)
            self.session_data[session_id]["last_activity"] = datetime.now()


# Global connection manager
chat_manager = ChatConnectionManager()


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for general chat with tool access"""

    try:
        await chat_manager.connect(websocket, session_id)

        # Send initial connection message
        await chat_manager.send_personal_message(
            session_id,
            ChatResponse(
                type="connection",
                content="Connected to general chat",
                timestamp=datetime.now().isoformat(),
            ),
        )

        # Initialize session components
        db = await get_db().__anext__()
        orchestrator = create_orchestrator(db)
        tool_interface = ToolInterface()

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                message = ChatMessage(**message_data)

                # Handle different message types
                if message.type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    continue

                if message.type == "message":
                    await handle_chat_message(
                        session_id, message, orchestrator, tool_interface
                    )

                elif message.type == "tool_request":
                    await handle_tool_request(session_id, message, tool_interface)

                elif message.type == "agent_switch":
                    await handle_agent_switch(session_id, message, orchestrator)

                else:
                    logger.warning(f"Unknown message type: {message.type}")
                    await chat_manager.send_personal_message(
                        session_id,
                        ChatResponse(
                            type="error",
                            content=f"Unknown message type: {message.type}",
                            timestamp=datetime.now().isoformat(),
                        ),
                    )

            except json.JSONDecodeError:
                logger.error("Invalid JSON received from WebSocket")
                await chat_manager.send_personal_message(
                    session_id,
                    ChatResponse(
                        type="error",
                        content="Invalid JSON format",
                        timestamp=datetime.now().isoformat(),
                    ),
                )
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await chat_manager.send_personal_message(
                    session_id,
                    ChatResponse(
                        type="error",
                        content=f"Error processing message: {e!s}",
                        timestamp=datetime.now().isoformat(),
                    ),
                )
                break

    except WebSocketDisconnect:
        logger.info(f"Chat WebSocket client disconnected for session: {session_id}")
        chat_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"Chat WebSocket error for session {session_id}: {e}")
        chat_manager.disconnect(session_id)


async def handle_chat_message(
    session_id: str,
    message: ChatMessage,
    orchestrator: Any,
    tool_interface: ToolInterface,
):
    """Handle incoming chat messages with intent detection and routing"""

    try:
        # Update session data
        session_data = chat_manager.get_session_data(session_id)
        if session_data:
            session_data["conversation_history"].append(
                {
                    "role": "user",
                    "content": message.content,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            chat_manager.update_session_data(session_id, session_data)

        # Send typing indicator
        await chat_manager.send_personal_message(
            session_id,
            ChatResponse(
                type="agent_status",
                content="Agent is thinking...",
                agent_id=session_data.get("active_agent") if session_data else None,
                timestamp=datetime.now().isoformat(),
            ),
        )

        # Process message with orchestrator
        async with timeout_context(30.0):  # 30 second timeout
            response = await orchestrator.process_command(
                user_command=message.content,
                session_id=session_id,
                agent_states={},
                use_perplexity=True,  # Enable web search
                use_bielik=True,
                stream=False,
            )

        # Send response
        await chat_manager.send_personal_message(
            session_id,
            ChatResponse(
                type="message",
                content=response.text
                or "Przepraszam, nie udało się przetworzyć wiadomości.",
                agent_id=session_data.get("active_agent") if session_data else None,
                confidence=response.data.get("confidence") if response.data else None,
                metadata={
                    "intent": response.data.get("intent") if response.data else None,
                    "tools_used": (
                        response.data.get("tools_used") if response.data else []
                    ),
                },
                timestamp=datetime.now().isoformat(),
            ),
        )

        # Update session with response
        if session_data:
            session_data["conversation_history"].append(
                {
                    "role": "assistant",
                    "content": response.text
                    or "Przepraszam, nie udało się przetworzyć wiadomości.",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            chat_manager.update_session_data(session_id, session_data)

    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        await chat_manager.send_personal_message(
            session_id,
            ChatResponse(
                type="error",
                content=f"Błąd podczas przetwarzania wiadomości: {e!s}",
                timestamp=datetime.now().isoformat(),
            ),
        )


async def handle_tool_request(
    session_id: str, message: ChatMessage, tool_interface: ToolInterface
):
    """Handle direct tool requests"""

    try:
        if not message.tool_name:
            await chat_manager.send_personal_message(
                session_id,
                ChatResponse(
                    type="error",
                    content="Nazwa narzędzia jest wymagana",
                    timestamp=datetime.now().isoformat(),
                ),
            )
            return

        # Execute tool
        tool_result = await tool_interface.execute_tool(
            tool_name=message.tool_name,
            parameters=message.metadata or {},
            session_id=session_id,
        )

        # Send tool response
        await chat_manager.send_personal_message(
            session_id,
            ChatResponse(
                type="tool_response",
                content=tool_result.get("result", "Narzędzie zostało wykonane"),
                tool_used=message.tool_name,
                metadata=tool_result,
                timestamp=datetime.now().isoformat(),
            ),
        )

        # Update session with tool usage
        session_data = chat_manager.get_session_data(session_id)
        if session_data:
            session_data["tools_used"].append(
                {
                    "tool": message.tool_name,
                    "timestamp": datetime.now().isoformat(),
                    "result": tool_result,
                }
            )
            chat_manager.update_session_data(session_id, session_data)

    except Exception as e:
        logger.error(f"Error executing tool {message.tool_name}: {e}")
        await chat_manager.send_personal_message(
            session_id,
            ChatResponse(
                type="error",
                content=f"Błąd podczas wykonywania narzędzia: {e!s}",
                timestamp=datetime.now().isoformat(),
            ),
        )


async def handle_agent_switch(session_id: str, message: ChatMessage, orchestrator: Any):
    """Handle agent switching requests"""

    try:
        agent_id = message.agent_id
        if not agent_id:
            await chat_manager.send_personal_message(
                session_id,
                ChatResponse(
                    type="error",
                    content="ID agenta jest wymagane",
                    timestamp=datetime.now().isoformat(),
                ),
            )
            return

        # Update session with new active agent
        session_data = chat_manager.get_session_data(session_id)
        if session_data:
            session_data["active_agent"] = agent_id
            chat_manager.update_session_data(session_id, session_data)

        # Send confirmation
        await chat_manager.send_personal_message(
            session_id,
            ChatResponse(
                type="agent_status",
                content=f"Przełączono na agenta: {agent_id}",
                agent_id=agent_id,
                timestamp=datetime.now().isoformat(),
            ),
        )

    except Exception as e:
        logger.error(f"Error switching agent: {e}")
        await chat_manager.send_personal_message(
            session_id,
            ChatResponse(
                type="error",
                content=f"Błąd podczas przełączania agenta: {e!s}",
                timestamp=datetime.now().isoformat(),
            ),
        )
