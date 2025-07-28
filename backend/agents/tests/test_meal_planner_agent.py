import pytest

from agents.interfaces import AgentResponse
from agents.meal_planner_agent import MealPlannerAgent


@pytest.mark.asyncio
async def test_meal_planner_no_products(monkeypatch):
    agent = MealPlannerAgent()

    # Mock get_available_products to return empty list
    async def mock_get_available_products(db):
        return []

    monkeypatch.setattr(
        "backend.core.crud.get_available_products", mock_get_available_products
    )

    # Create a mock database object with async execute method and scalars().all() chain
    class MockResult:
        def scalars(self):
            class All:
                def all(self):
                    return []

            return All()

    class MockDB:
        async def execute(self, stmt):
            return MockResult()

    mock_db = MockDB()
    response = await agent.process({"db": mock_db})
    assert isinstance(response, AgentResponse)
    assert response.success
    # Stream should yield a message about no products or error
    result = ""
    async for chunk in response.text_stream:
        result += chunk
    assert "błąd" in result or "plan" in result or "meal" in result
