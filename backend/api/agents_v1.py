"""
Simple v1 agents endpoint for frontend compatibility
"""
from fastapi import APIRouter
from agents.interfaces import AgentType

router = APIRouter()

@router.get("/agents", response_model=list[dict[str, str]])
async def get_agents_v1() -> list[dict[str, str]]:
    """Get list of available agents - v1 endpoint for frontend compatibility"""
    return [{"name": agent.value, "description": agent.value} for agent in AgentType]