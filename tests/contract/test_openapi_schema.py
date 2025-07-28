"""
Testy OpenAPI Schema

Zgodnie z regułami projektu:
- Walidacja poprawności OpenAPI schema
- Sprawdzenie czy wszystkie endpointy są udokumentowane
- Test konsystencji schematu
- Walidacja referencji
"""

import json

from fastapi.openapi.utils import get_openapi
from fastapi.testclient import TestClient
import pytest

from backend.main import app


class TestOpenAPISchema:
    """Testy dla OpenAPI Schema"""

    @pytest.fixture
    def client(self):
        """Fixture dla test client"""
        return TestClient(app)

    def test_openapi_schema_validity(self):
        """Test czy OpenAPI schema jest poprawna"""
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
        try:
            json.dumps(schema)
        except Exception as e:
            pytest.fail(f"OpenAPI schema is not valid JSON: {e}")

    def test_all_endpoints_documented(self):
        """Test czy wszystkie endpointy są udokumentowane w OpenAPI schema"""
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

    def test_schema_components_validity(self):
        """Test poprawności komponentów schematu"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź czy komponenty są poprawnie zdefiniowane
        if "components" in schema:
            components = schema["components"]

            # Sprawdź schemas
            if "schemas" in components:
                schemas = components["schemas"]
                assert isinstance(schemas, dict), "Schemas should be a dict"

                for schema_name, schema_def in schemas.items():
                    assert isinstance(
                        schema_def, dict
                    ), f"Schema {schema_name} should be a dict"
                    assert (
                        "type" in schema_def
                    ), f"Schema {schema_name} should have a type"

            # Sprawdź securitySchemes
            if "securitySchemes" in components:
                security_schemes = components["securitySchemes"]
                assert isinstance(
                    security_schemes, dict
                ), "SecuritySchemes should be a dict"

                for scheme_name, scheme_def in security_schemes.items():
                    assert isinstance(
                        scheme_def, dict
                    ), f"SecurityScheme {scheme_name} should be a dict"
                    assert (
                        "type" in scheme_def
                    ), f"SecurityScheme {scheme_name} should have a type"

    def test_schema_responses_validity(self):
        """Test poprawności odpowiedzi w schemacie"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź czy wszystkie endpointy mają odpowiednie odpowiedzi
        for path, path_item in schema["paths"].items():
            for method, method_item in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    assert (
                        "responses" in method_item
                    ), f"Method {method} for {path} should have responses"

                    responses = method_item["responses"]
                    assert isinstance(
                        responses, dict
                    ), f"Responses for {method} {path} should be a dict"

                    # Sprawdź czy są zdefiniowane odpowiedzi dla kodów błędów
                    error_codes = ["400", "401", "403", "404", "422", "500"]
                    for error_code in error_codes:
                        if error_code in responses:
                            error_response = responses[error_code]
                            assert (
                                "description" in error_response
                            ), f"Error response {error_code} for {method} {path} should have description"

    def test_schema_parameters_validity(self):
        """Test poprawności parametrów w schemacie"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź czy parametry są poprawnie zdefiniowane
        for path, path_item in schema["paths"].items():
            for method, method_item in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    if "parameters" in method_item:
                        parameters = method_item["parameters"]
                        assert isinstance(
                            parameters, list
                        ), f"Parameters for {method} {path} should be a list"

                        for param in parameters:
                            assert isinstance(param, dict), "Parameter should be a dict"
                            assert "name" in param, "Parameter should have a name"
                            assert "in" in param, "Parameter should have location (in)"
                            assert (
                                "required" in param
                            ), "Parameter should have required field"

    def test_schema_request_body_validity(self):
        """Test poprawności request body w schemacie"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź czy request body jest poprawnie zdefiniowane
        for path, path_item in schema["paths"].items():
            for method, method_item in path_item.items():
                if method in ["post", "put", "patch"]:
                    if "requestBody" in method_item:
                        request_body = method_item["requestBody"]
                        assert isinstance(
                            request_body, dict
                        ), f"RequestBody for {method} {path} should be a dict"
                        assert (
                            "content" in request_body
                        ), f"RequestBody for {method} {path} should have content"

                        content = request_body["content"]
                        assert isinstance(
                            content, dict
                        ), f"Content for {method} {path} should be a dict"

                        # Sprawdź czy jest zdefiniowany przynajmniej jeden content type
                        assert (
                            len(content) > 0
                        ), f"Content for {method} {path} should have at least one content type"

    def test_schema_tags_validity(self):
        """Test poprawności tagów w schemacie"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź czy tagi są poprawnie zdefiniowane
        if "tags" in schema:
            tags = schema["tags"]
            assert isinstance(tags, list), "Tags should be a list"

            for tag in tags:
                assert isinstance(tag, dict), "Tag should be a dict"
                assert "name" in tag, "Tag should have a name"
                assert "description" in tag, "Tag should have a description"

        # Sprawdź czy endpointy używają tagów
        for path, path_item in schema["paths"].items():
            for method, method_item in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    if "tags" in method_item:
                        tags = method_item["tags"]
                        assert isinstance(
                            tags, list
                        ), f"Tags for {method} {path} should be a list"
                        assert (
                            len(tags) > 0
                        ), f"Tags for {method} {path} should not be empty"

    def test_schema_operation_id_uniqueness(self):
        """Test unikalności operation IDs"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        operation_ids = []

        # Zbierz wszystkie operation IDs
        for path_item in schema["paths"].values():
            for method, method_item in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    if "operationId" in method_item:
                        operation_id = method_item["operationId"]
                        operation_ids.append(operation_id)

        # Sprawdź unikalność
        unique_operation_ids = set(operation_ids)
        assert len(operation_ids) == len(
            unique_operation_ids
        ), f"Operation IDs should be unique. Found duplicates: {[id for id in operation_ids if operation_ids.count(id) > 1]}"

    def test_schema_version_consistency(self):
        """Test konsystencji wersji w schemacie"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Sprawdź czy wersja OpenAPI jest poprawna
        assert schema["openapi"].startswith("3."), "OpenAPI version should be 3.x"

        # Sprawdź czy wersja aplikacji jest spójna
        assert (
            schema["info"]["version"] == app.version
        ), "Schema version should match app version"

    def test_schema_endpoint_coverage(self):
        """Test pokrycia endpointów w schemacie"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Pobierz wszystkie zarejestrowane endpointy
        documented_paths = set(schema["paths"].keys())

        # Sprawdź czy wszystkie endpointy v2 są udokumentowane
        v2_endpoints = [
            "/api/v2/chat",
            "/api/v2/receipts",
            "/api/v2/concise-responses/generate",
            "/api/v2/rag/upload",
            "/api/v2/backup",
            "/api/v2/users",
        ]

        missing_endpoints = []
        for endpoint in v2_endpoints:
            if not any(endpoint in path for path in documented_paths):
                missing_endpoints.append(endpoint)

        assert (
            len(missing_endpoints) == 0
        ), f"Missing endpoints in OpenAPI schema: {missing_endpoints}"

    def test_schema_validation_with_external_tools(self):
        """Test walidacji schematu z zewnętrznymi narzędziami"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Konwertuj na JSON string
        schema_json = json.dumps(schema)

        # Sprawdź czy JSON jest poprawny
        try:
            parsed_schema = json.loads(schema_json)
            assert (
                parsed_schema == schema
            ), "Schema should be serializable and deserializable"
        except json.JSONDecodeError as e:
            pytest.fail(f"Schema is not valid JSON: {e}")

        # Sprawdź czy schema ma wymagane pola dla narzędzi zewnętrznych
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            assert field in schema, f"Schema should have required field: {field}"

        # Sprawdź czy info ma wymagane pola
        info_required_fields = ["title", "version"]
        for field in info_required_fields:
            assert field in schema["info"], f"Info should have required field: {field}"
