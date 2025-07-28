import pytest

from agents.weather_agent import WeatherAgent


@pytest.mark.asyncio
async def test_weather_agent_stream(monkeypatch):
    agent = WeatherAgent()

    # Mock llm_client.chat to return a simple async generator
    async def mock_chat(*args, **kwargs):
        async def gen():
            yield {"message": {"content": "Pogoda: słonecznie."}}

        return gen()

    monkeypatch.setattr(agent.llm_client, "chat", mock_chat)
    # Test streaming response
    async for chunk in agent._stream_weather_response("model", "prompt"):
        assert "Pogoda" in chunk or "słonecznie" in chunk
