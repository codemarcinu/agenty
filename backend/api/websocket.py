"""
WebSocket endpoints for real-time dashboard updates
"""

from datetime import datetime
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agents.agent_factory import AgentFactory
from api.monitoring import health_check

router = APIRouter()
logger = logging.getLogger(__name__)


# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    """WebSocket endpoint for dashboard real-time updates"""
    logger.info(
        f"WebSocket handshake attempt from {websocket.client.host}:{websocket.client.port}"
    )

    try:
        await manager.connect(websocket)

        # Send initial connection message
        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "connection",
                    "data": {"message": "Connected to dashboard WebSocket"},
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            websocket,
        )

        # Send initial agent status
        await send_agent_status(websocket)

        # Send initial system metrics
        await send_system_metrics(websocket)

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    continue

                # Handle different message types
                if message.get("type") == "request_agent_status":
                    await send_agent_status(websocket)
                elif message.get("type") == "request_system_metrics":
                    await send_system_metrics(websocket)
                elif message.get("type") == "subscribe_agent":
                    # TODO: Implement agent subscription
                    pass
                elif message.get("type") == "unsubscribe_agent":
                    # TODO: Implement agent unsubscription
                    pass
                else:
                    logger.warning(
                        f"Unknown WebSocket message type: {message.get('type')}"
                    )

            except json.JSONDecodeError:
                logger.error("Invalid JSON received from WebSocket")
                await manager.send_personal_message(
                    json.dumps(
                        {
                            "type": "error",
                            "data": {"message": "Invalid JSON format"},
                            "timestamp": datetime.now().isoformat(),
                        }
                    ),
                    websocket,
                )
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps(
                        {
                            "type": "error",
                            "data": {"message": f"Error processing message: {e!s}"},
                            "timestamp": datetime.now().isoformat(),
                        }
                    ),
                    websocket,
                )
                break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def send_agent_status(websocket: WebSocket):
    """Send current agent status to WebSocket client"""
    try:
        # Get agent status from AgentFactory
        agents = []
        for agent_name in AgentFactory.AGENT_REGISTRY:
            try:
                # Create a mock agent status for now
                agent_status = {
                    "name": agent_name,
                    "status": "online",  # TODO: Implement real status checking
                    "lastActivity": datetime.now().isoformat(),
                    "responseTime": 100,  # Mock response time
                    "errorCount": 0,
                    "confidence": 0.95,
                }
                agents.append(agent_status)
            except Exception as e:
                logger.error(f"Error getting status for agent {agent_name}: {e}")
                agent_status = {
                    "name": agent_name,
                    "status": "error",
                    "lastActivity": datetime.now().isoformat(),
                    "errorCount": 1,
                    "confidence": 0.0,
                }
                agents.append(agent_status)

        message = {
            "type": "agent_status",
            "data": agents,
            "timestamp": datetime.now().isoformat(),
        }

        await manager.send_personal_message(json.dumps(message), websocket)

    except Exception as e:
        logger.error(f"Error sending agent status: {e}")


async def send_system_metrics(websocket: WebSocket):
    """Send system metrics to WebSocket client"""
    try:
        # Get system health check data
        health_data = await health_check()

        # Extract metrics from health check
        system_metrics = {
            "cpu": 45.5,  # Mock CPU usage
            "memory": 67.2,  # Mock memory usage
            "disk": 23.1,  # Mock disk usage
            "network": 12.8,  # Mock network usage
            "activeConnections": len(manager.active_connections),
            "timestamp": datetime.now().isoformat(),
        }

        # If we have database stats from health check, use them
        if "checks" in health_data and "database" in health_data["checks"]:
            db_stats = health_data["checks"]["database"].get("pool_stats", {})
            system_metrics["activeConnections"] = db_stats.get("checked_out", 0)

        message = {
            "type": "system_metrics",
            "data": system_metrics,
            "timestamp": datetime.now().isoformat(),
        }

        await manager.send_personal_message(json.dumps(message), websocket)

    except Exception as e:
        logger.error(f"Error sending system metrics: {e}")


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/ws/test")
async def websocket_test():
    """Test endpoint to verify WebSocket router is working"""
    return {
        "message": "WebSocket router is working",
        "timestamp": datetime.now().isoformat(),
    }
