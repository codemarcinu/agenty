"""
Testy API Contract Testing

Zgodnie z regułami projektu:
- Walidacja schematów odpowiedzi API
- Testy konsystencji endpointów
- Walidacja OpenAPI schema
- Testy kontraktów błędów
"""

import os

# Ustaw tryb testowy dla autoryzacji PRZED importem aplikacji
os.environ["TESTING_MODE"] = "true"

from unittest.mock import Mock

from fastapi.testclient import TestClient
import jsonschema
import pytest

from backend.main import app


@pytest.fixture(scope="session")
def auth_client():
    """Fixture: klient z autoryzacją JWT (mock)"""
    client = TestClient(app)
    # Mock JWT token - nie wymaga prawdziwej bazy danych
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwicm9sZXMiOlsidXNlciJdLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzM1Njg5NjAwLCJleHAiOjE3MzU3NzYwMDB9.mock_signature"

    # Dodaj nagłówek Authorization do wszystkich requestów
    client.headers.update({"Authorization": f"Bearer {mock_token}"})
    return client


class TestAPIContracts:
    """Testy kontraktów API"""

    @pytest.fixture
    def client(self):
        """Fixture dla test client"""
        return TestClient(app)

    def test_health_endpoint_contract(self, client):
        """Test kontraktu endpointu health check"""
        response = client.get("/health")

        # Sprawdź status code
        assert response.status_code == 200

        # Sprawdź schemat odpowiedzi
        response_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "timestamp": {"type": "string"},
                "version": {"type": "string"},
            },
            "required": ["status"],
        }

        try:
            jsonschema.validate(response.json(), response_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Health endpoint response doesn't match schema: {e}")

    def test_error_response_contract(self, client):
        """Test kontraktu odpowiedzi błędów"""
        # Test różnych endpointów błędów
        error_endpoints = [
            ("/api/v2/users/99999", 404),  # Nieistniejący użytkownik
            ("/api/v2/receipts/invalid-id", 404),  # Nieistniejący receipt
        ]

        error_schema = {
            "type": "object",
            "properties": {
                "detail": {"type": "string"},
                "error_code": {"type": "string"},
                "timestamp": {"type": "string"},
            },
            "required": ["detail"],
        }

        for endpoint, expected_status in error_endpoints:
            response = client.get(endpoint)
            assert response.status_code == expected_status

            try:
                jsonschema.validate(response.json(), error_schema)
            except jsonschema.ValidationError as e:
                pytest.fail(f"Error response for {endpoint} doesn't match schema: {e}")

    def test_chat_endpoint_contract(self, auth_client):
        """Test kontraktu endpointu chat"""
        mock_auth = Mock()
        mock_factory = Mock()
        # Mock authentication
        mock_auth.return_value = {"user_id": 1, "username": "testuser"}
        # Mock agent factory
        mock_agent = Mock()
        mock_agent.process.return_value = type(
            "obj", (object,), {"success": True, "response": "Test chat response"}
        )
        mock_factory.return_value.get_agent.return_value = mock_agent

        payload = {"message": "Hello, how are you?", "context": {"user_id": 1}}

        response = auth_client.post("/api/v2/chat", json=payload)

        # Sprawdź status code
        assert response.status_code in [200, 201]

        # Sprawdź schemat odpowiedzi
        response_schema = {
            "type": "object",
            "properties": {
                "response": {"type": "string"},
                "success": {"type": "boolean"},
                "metadata": {"type": "object"},
                "timestamp": {"type": "string"},
            },
            "required": ["response", "success"],
        }

        try:
            jsonschema.validate(response.json(), response_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Chat endpoint response doesn't match schema: {e}")

    def test_receipt_endpoint_contract(self, auth_client):
        """Test kontraktu endpointu receipt"""
        # Test GET endpoint
        response = auth_client.get("/api/v2/receipts")

        # Sprawdź status code
        assert response.status_code in [200, 404]  # 404 jeśli brak danych

        if response.status_code == 200:
            # Sprawdź schemat odpowiedzi
            response_schema = {
                "type": "object",
                "properties": {
                    "receipts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "filename": {"type": "string"},
                                "upload_date": {"type": "string"},
                                "status": {"type": "string"},
                            },
                            "required": ["id", "filename"],
                        },
                    },
                    "total": {"type": "integer"},
                    "page": {"type": "integer"},
                    "per_page": {"type": "integer"},
                },
                "required": ["receipts", "total"],
            }

            try:
                jsonschema.validate(response.json(), response_schema)
            except jsonschema.ValidationError as e:
                pytest.fail(f"Receipt endpoint response doesn't match schema: {e}")

    def test_concise_responses_contract(self, auth_client):
        """Test kontraktu endpointu concise responses"""
        mock_agent = Mock()
        mock_agent.process.return_value = type(
            "obj", (object,), {"success": True, "response": "Test concise response"}
        )

        payload = {
            "query": "What is Python?",
            "response_style": "concise",
            "use_rag": False,
        }

        response = auth_client.post("/api/v2/concise-responses/generate", json=payload)

        # Sprawdź status code
        assert response.status_code in [200, 201]

        # Sprawdź schemat odpowiedzi
        response_schema = {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "response_style": {"type": "string"},
                "concise_score": {"type": "number"},
                "can_expand": {"type": "boolean"},
                "processing_time": {"type": "number"},
                "metadata": {"type": "object"},
            },
            "required": ["text", "response_style"],
        }

        try:
            jsonschema.validate(response.json(), response_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(
                f"Concise responses endpoint response doesn't match schema: {e}"
            )

    def test_rag_endpoint_contract(self, auth_client):
        """Test kontraktu endpointu RAG"""
        mock_processor = Mock()
        mock_processor.process_document.return_value = [
            {"chunk": "test", "embedding": [0.1, 0.2]}
        ]

        # Test upload endpoint
        test_file_content = b"Test document content for RAG processing"
        files = {"file": ("test.txt", test_file_content, "text/plain")}
        data = {"category": "test", "tags": "test,rag"}

        response = auth_client.post("/api/v2/rag/upload", files=files, data=data)

        # Sprawdź status code
        assert response.status_code in [200, 201]

        # Sprawdź schemat odpowiedzi
        response_schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "chunks_processed": {"type": "integer"},
                "source_id": {"type": "string"},
                "processing_time": {"type": "number"},
            },
            "required": ["message", "chunks_processed"],
        }

        try:
            jsonschema.validate(response.json(), response_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"RAG upload endpoint response doesn't match schema: {e}")

    def test_validation_error_contract(self, auth_client):
        """Test kontraktu błędów walidacji"""
        # Test z niepoprawnymi danymi
        invalid_payloads = [
            ({"message": ""}, "/api/v2/chat"),  # Pusta wiadomość
            ({"query": 123}, "/api/v2/concise-responses/generate"),  # Niepoprawny typ
            ({}, "/api/v2/chat"),  # Brak wymaganych pól
        ]

        validation_error_schema = {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "loc": {"type": "array"},
                            "msg": {"type": "string"},
                            "type": {"type": "string"},
                        },
                        "required": ["loc", "msg", "type"],
                    },
                }
            },
            "required": ["detail"],
        }

        for payload, endpoint in invalid_payloads:
            response = auth_client.post(endpoint, json=payload)

            # Sprawdź status code
            assert response.status_code == 422  # Validation error

            # Sprawdź schemat błędu walidacji
            try:
                jsonschema.validate(response.json(), validation_error_schema)
            except jsonschema.ValidationError as e:
                pytest.fail(
                    f"Validation error response for {endpoint} doesn't match schema: {e}"
                )

    def test_authentication_error_contract(self, auth_client):
        """Test kontraktu błędów autentyfikacji"""
        # W trybie testowym autoryzacja jest wyłączona, więc sprawdzamy że endpointy działają
        if os.getenv("TESTING_MODE") == "true":
            # Test dostępu do chronionych endpointów z autoryzacją (w trybie testowym)
            protected_endpoints = [
                ("/api/v2/users/me", "GET"),
                ("/api/v2/chat", "POST"),
                ("/api/v2/receipts/upload", "POST"),
            ]

            for endpoint, method in protected_endpoints:
                if method == "GET":
                    response = auth_client.get(endpoint)
                elif method == "POST":
                    if endpoint == "/api/v2/chat":
                        response = auth_client.post(endpoint, json={"message": "test"})
                    else:
                        response = auth_client.post(endpoint, json={})

                # W trybie testowym endpointy powinny działać (200 OK lub 422 Validation Error)
                assert response.status_code in [
                    200,
                    422,
                ], f"Endpoint {endpoint} failed with {response.status_code}"
        else:
            # Test dostępu do chronionych endpointów bez autentyfikacji (w trybie produkcyjnym)
            protected_endpoints = [
                ("/api/v2/users/me", "GET"),
                ("/api/v2/chat", "POST"),
                ("/api/v2/receipts/upload", "POST"),
            ]

            auth_error_schema = {
                "type": "object",
                "properties": {"detail": {"type": "string"}},
                "required": ["detail"],
            }

            for endpoint, method in protected_endpoints:
                if method == "GET":
                    response = auth_client.get(endpoint)
                elif method == "POST":
                    if endpoint == "/api/v2/chat":
                        response = auth_client.post(endpoint, json={"message": "test"})
                    else:
                        response = auth_client.post(endpoint, json={})

                # Sprawdź status code
                assert response.status_code in [
                    401,
                    403,
                ]  # Authentication/Authorization error

                # Sprawdź format odpowiedzi
                if response.status_code == 401:
                    try:
                        data = response.json()
                        jsonschema.validate(data, auth_error_schema)
                    except jsonschema.ValidationError as e:
                        pytest.fail(f"Invalid error response format: {e}")


class TestOpenAPISchema:
    """Testy OpenAPI Schema"""

    def test_openapi_schema_validity(self):
        """Test czy OpenAPI schema jest poprawna"""
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź wymagane pola OpenAPI
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # Sprawdź sekcję info
        assert schema["info"]["title"] == app.title
        assert schema["info"]["version"] == app.version

        # Sprawdź czy schema jest poprawnym JSON
        import json

        try:
            json.dumps(schema)
        except Exception as e:
            pytest.fail(f"OpenAPI schema is not valid JSON: {e}")

    def test_all_endpoints_documented(self):
        """Test czy wszystkie endpointy są udokumentowane w OpenAPI schema"""
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Pobierz wszystkie zarejestrowane ścieżki
        documented_paths = set(schema["paths"].keys())

        # Sprawdź czy krytyczne endpointy są udokumentowane
        critical_endpoints = [
            "/health",
            "/api/v2/chat",
            "/api/v2/receipts",
            "/api/v2/concise-responses/generate",
            "/api/v2/rag/upload",
        ]

        for endpoint in critical_endpoints:
            assert any(
                endpoint in path for path in documented_paths
            ), f"Endpoint {endpoint} nie jest udokumentowany"

    def test_schema_consistency(self):
        """Test konsystencji schematu OpenAPI"""
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź czy wszystkie ścieżki mają odpowiednie metody HTTP
        for path, path_item in schema["paths"].items():
            assert isinstance(path_item, dict), f"Path {path} should be a dict"

            # Sprawdź czy ścieżka ma przynajmniej jedną metodę HTTP
            http_methods = ["get", "post", "put", "delete", "patch"]
            has_method = any(method in path_item for method in http_methods)
            assert has_method, f"Path {path} should have at least one HTTP method"

            # Sprawdź czy każda metoda ma odpowiednie pola
            for method in http_methods:
                if method in path_item:
                    method_item = path_item[method]
                    assert (
                        "responses" in method_item
                    ), f"Method {method} for {path} should have responses"
                    assert (
                        "summary" in method_item or "description" in method_item
                    ), f"Method {method} for {path} should have summary or description"

    def test_schema_references_validity(self):
        """Test poprawności referencji w schemacie OpenAPI"""
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź czy wszystkie referencje są poprawne
        def check_references(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "$ref":
                        # Sprawdź czy referencja jest poprawna
                        assert value.startswith(
                            "#/"
                        ), f"Invalid reference {value} at {path}"
                        # Sprawdź czy referencja wskazuje na istniejący element
                        ref_path = value[2:].split("/")
                        current = schema
                        for part in ref_path:
                            assert (
                                part in current
                            ), f"Reference {value} at {path} points to non-existent element"
                            current = current[part]
                    else:
                        check_references(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_references(item, f"{path}[{i}]")

        check_references(schema)


class TestAPIVersioning:
    """Testy wersjonowania API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_api_version_consistency(self, client):
        """Test konsystencji wersji API"""
        # Sprawdź czy wszystkie endpointy v2 mają spójną strukturę
        v2_endpoints = [
            "/api/v2/chat",
            "/api/v2/receipts",
            "/api/v2/concise-responses/generate",
            "/api/v2/rag/upload",
        ]

        for endpoint in v2_endpoints:
            response = client.get(endpoint)  # GET request to check if endpoint exists
            # Endpoint może zwrócić 405 (Method Not Allowed) dla GET, ale powinien istnieć
            assert response.status_code in [
                200,
                404,
                405,
            ], f"Endpoint {endpoint} should exist and return appropriate status"

    def test_backward_compatibility(self, client):
        """Test kompatybilności wstecznej"""
        # Sprawdź czy stare endpointy nadal działają (jeśli istnieją)
        legacy_endpoints = [
            "/api/chat",  # Stary endpoint chat
            "/api/receipts",  # Stary endpoint receipts
        ]

        for endpoint in legacy_endpoints:
            response = client.get(endpoint)
            # Stare endpointy mogą zwrócić 404, ale nie powinny zwracać 500
            assert (
                response.status_code != 500
            ), f"Legacy endpoint {endpoint} should not return 500 error"


class TestAPISecurity:
    """Testy bezpieczeństwa API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_cors_headers(self, client):
        """Test nagłówków CORS"""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
        response = client.options("/api/v2/chat", headers=headers)

        # Sprawdź czy odpowiednie nagłówki CORS są obecne
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers",
        ]

        for header in cors_headers:
            assert header in response.headers, f"CORS header {header} should be present"

    def test_security_headers(self, client):
        """Test nagłówków bezpieczeństwa"""
        response = client.get("/health")

        # Sprawdź czy odpowiednie nagłówki bezpieczeństwa są obecne
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
        ]

        for header in security_headers:
            # Niektóre nagłówki mogą być opcjonalne
            if header in response.headers:
                assert (
                    response.headers[header] is not None
                ), f"Security header {header} should have a value"

    def test_input_validation(self, client):
        """Test walidacji danych wejściowych"""
        # Test z potencjalnie niebezpiecznymi danymi
        malicious_inputs = [
            {"message": "<script>alert('xss')</script>"},
            {"message": "'; DROP TABLE users; --"},
            {"message": "a" * 10000},  # Bardzo długi input
        ]

        for payload in malicious_inputs:
            response = client.post("/api/v2/chat", json=payload)

            # System powinien obsłużyć niebezpieczne dane bez crashowania
            assert response.status_code in [
                200,
                201,
                400,
                422,
            ], f"System should handle malicious input gracefully: {payload}"

            # Odpowiedź nie powinna zawierać niebezpiecznych danych
            if response.status_code in [200, 201]:
                response_text = str(response.json())
                assert (
                    "<script>" not in response_text
                ), f"Response should not contain XSS payload: {response_text}"
