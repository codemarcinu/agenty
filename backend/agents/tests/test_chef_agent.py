import pytest

from agents.chef_agent import ChefAgent
from agents.interfaces import AgentResponse


@pytest.mark.asyncio
async def test_chef_agent_no_ingredients():
    agent = ChefAgent()
    response = await agent.process({"available_ingredients": []})
    assert isinstance(response, AgentResponse)
    assert not response.success
    assert "składniki" in (response.text or "")


@pytest.mark.asyncio
async def test_chef_agent_with_ingredients(monkeypatch):
    agent = ChefAgent()

    # Mock llm_client.chat to return a simple async generator
    async def mock_chat(*args, **kwargs):
        async def gen():
            yield {"message": {"content": "Przepis: Jajecznica z cebulą."}}

        return gen()

    monkeypatch.setattr(agent.llm_client, "chat", mock_chat)
    response = await agent.process({"available_ingredients": ["jajka", "cebula"]})
    assert response.success
    assert response.text_stream is not None
    # Consume the stream
    result = ""
    async for chunk in response.text_stream:
        result += chunk
    assert "Jajecznica" in result
