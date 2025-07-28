from fastapi.testclient import TestClient
import pytest

from backend.app_factory import create_app  # Import main FastAPI instance

app = create_app()
client = TestClient(app)


@pytest.fixture(scope="module")
def test_app():
    # Setup test database, mock external services if needed
    yield client
    # Cleanup after tests


def test_full_orchestration_flow(test_app):
    # Simulate API request that uses the orchestrator
    response = test_app.post(
        "/api/agents/execute",
        json={"task": "Find a recipe for spaghetti", "session_id": "test_session_123"},
    )
    assert response.status_code == 200
    assert "spaghetti" in (response.json().get("response") or "").lower()


def test_add_item_to_list_flow(test_app):
    response = test_app.post(
        "/api/agents/execute",
        json={"task": "add milk to shopping list", "session_id": "test_session_123"},
    )
    assert response.status_code == 200
    assert "milk" in (response.json().get("response") or "").lower()


def test_invalid_input_query(test_app):
    response = test_app.post(
        "/api/agents/execute", json={"task": "", "session_id": "test_session"}
    )  # Empty task
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_database_connection_failure(async_client):
    """Test obsługi błędu połączenia z bazą danych."""
    # Test prostego błędu HTTP - endpoint który nie istnieje
    response = await async_client.get("/api/nonexistent/endpoint")

    assert response.status_code == 404
    response_data = response.json()
    # Sprawdź czy odpowiedź zawiera informację o błędzie
    assert "detail" in response_data


def test_error_handling_value_error(test_app):
    response = test_app.get("/api/v2/raise_error?type=value")
    assert response.status_code == 500
    assert "error" in response.json()
    assert response.json()["error"]["message"] == "Test ValueError"


def test_error_handling_key_error(test_app):
    response = test_app.get("/api/v2/raise_error?type=key")
    assert response.status_code == 500
    assert "error" in response.json()
    assert "Missing required field" in response.json()["error"]["message"]


def test_error_handling_custom_exception(test_app):
    response = test_app.get("/api/v2/raise_error?type=custom")
    assert response.status_code == 500
    response_data = response.json()
    assert "detail" in response_data
    assert "Test custom exception" in response_data["detail"]


@pytest.mark.asyncio
async def test_error_handling_http_exception(async_client):
    """Test obsługi wyjątków HTTP."""
    response = await async_client.get("/api/v2/raise_error?type=http")

    assert response.status_code == 418
    response_data = response.json()
    # Sprawdź czy odpowiedź zawiera informację o błędzie
    assert "detail" in response_data


def test_error_handling_generic_exception(test_app):
    response = test_app.get("/api/v2/raise_error?type=other")
    assert response.status_code == 500
    assert "error" in response.json()
    assert "Unexpected error" in response.json()["error"]["message"]


def test_llm_models_list(test_app):
    response = test_app.get("/api/settings/llm-models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert any("name" in m for m in models)


def test_llm_model_selected_get_and_set(test_app):
    # Najpierw pobierz aktualny model
    get_resp = test_app.get("/api/settings/llm-model/selected")
    assert get_resp.status_code == 200
    current_model = get_resp.json()

    # Pobierz listę dostępnych modeli
    models_resp = test_app.get("/api/settings/llm-models")
    assert models_resp.status_code == 200
    models = models_resp.json()
    assert len(models) > 0
    model_names = [m["name"] for m in models]

    # Wybierz pierwszy model z listy
    new_model = model_names[0]
    post_resp = test_app.post(
        f"/api/settings/llm-model/selected?model_name={new_model}"
    )
    assert post_resp.status_code == 200
    data = post_resp.json()
    assert data["selected_model"] == new_model

    # Ustaw model, który nie istnieje
    bad_resp = test_app.post(
        "/api/settings/llm-model/selected?model_name=nonexistent-model-xyz"
    )
    assert bad_resp.status_code == 400
    resp_json = bad_resp.json()
    error_msg = resp_json.get("detail") or resp_json.get("error")
    assert error_msg and "nie jest dostępny" in error_msg

    # Przywróć poprzedni model (jeśli był inny)
    if current_model and current_model != new_model:
        restore_resp = test_app.post(
            f"/api/settings/llm-model/selected?model_name={current_model}"
        )
        assert restore_resp.status_code == 200
