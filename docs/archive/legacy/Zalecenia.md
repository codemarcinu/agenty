# Zalecenia dla Poprawek w Projekcie MyAppAssistant

## 🔴 Priorytet Wysoki

### 1. Zwiększenie Pokrycia Testami Authentication (0% → 80%)

#### Struktura Testów Autentyfikacji
Należy stworzyć kompleksowy system testów dla modułu autentyfikacji zgodnie z najlepszymi praktykami FastAPI[1][2][3].

```python
# tests/unit/test_auth.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.auth.authentication import AuthService
from app.auth.models import User

class TestAuthService:
    @pytest.fixture
    def auth_service(self):
        return AuthService()
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$hash..."
        )
    
    def test_create_salt_and_hashed_password(self, auth_service):
        """Test password hashing generates unique salts"""
        password = "test_password123"
        first_hash = auth_service.create_salt_and_hashed_password(password)
        second_hash = auth_service.create_salt_and_hashed_password(password)
        
        assert first_hash.password != second_hash.password
        assert first_hash.salt != second_hash.salt
    
    def test_verify_password_success(self, auth_service):
        """Test successful password verification"""
        password = "test_password123"
        hashed = auth_service.create_salt_and_hashed_password(password)
        
        result = auth_service.verify_password(password, hashed.password)
        assert result is True
    
    def test_verify_password_failure(self, auth_service):
        """Test failed password verification"""
        password = "test_password123"
        wrong_password = "wrong_password"
        hashed = auth_service.create_salt_and_hashed_password(password)
        
        result = auth_service.verify_password(wrong_password, hashed.password)
        assert result is False
```

#### Testy Integracyjne dla Endpointów Autentyfikacji

```python
# tests/integration/test_auth_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_auth_dependency():
    """Mock authentication for protected endpoints"""
    async def fake_authenticate():
        return {
            'user_id': 1,
            'username': 'testuser',
            'roles': ['user']
        }
    return fake_authenticate

class TestAuthFlow:
    def test_login_success(self, client):
        """Test successful login flow"""
        login_data = {
            "username": "testuser",
            "password": "correct_password"
        }
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "testuser",
            "password": "wrong_password"
        }
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/protected/endpoint")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self, client, mock_auth_dependency):
        """Test accessing protected endpoint with valid authentication"""
        app.dependency_overrides[get_current_user] = mock_auth_dependency
        
        response = client.get("/protected/endpoint")
        assert response.status_code == 200
        
        # Cleanup
        app.dependency_overrides.clear()
```

#### Mock Authentication Handler dla Testów[4][5]

```python
# tests/conftest.py
import pytest
from fastapi import HTTPException
from app.auth.models import User

class MockAuthHandler:
    """Mock authentication handler for testing"""
    
    def __init__(self, default_user_id: str = "1"):
        self.default_user_id = default_user_id
    
    async def authenticate(self, token: str = None, user_id: str = None):
        """Mock authentication method"""
        if user_id:
            return self._create_mock_user(user_id)
        return self._create_mock_user(self.default_user_id)
    
    def _create_mock_user(self, user_id: str):
        return User(
            id=int(user_id),
            username=f"user_{user_id}",
            email=f"user_{user_id}@test.com",
            roles=["user"]
        )

@pytest.fixture
def mock_auth_handler():
    return MockAuthHandler()
```

### 2. Rozszerzenie Testów RAG System (17% → 70%)

#### Testy dla Systemu RAG

```python
# tests/unit/test_rag_processing.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.rag.processor import RAGProcessor
from app.rag.vector_store import VectorStore

class TestRAGProcessor:
    @pytest.fixture
    def mock_vector_store(self):
        mock = Mock(spec=VectorStore)
        mock.is_empty = False
        mock.search.return_value = [
            {"content": "test document", "score": 0.95},
            {"content": "another document", "score": 0.88}
        ]
        return mock
    
    @pytest.fixture
    def mock_llm_client(self):
        mock = AsyncMock()
        mock.generate_response.return_value = "Generated response"
        return mock
    
    @pytest.fixture
    def rag_processor(self, mock_vector_store, mock_llm_client):
        return RAGProcessor(
            vector_store=mock_vector_store,
            llm_client=mock_llm_client
        )
    
    @pytest.mark.asyncio
    async def test_process_query_success(self, rag_processor, mock_vector_store):
        """Test successful RAG query processing"""
        query = "What is machine learning?"
        
        result = await rag_processor.process_query(query)
        
        assert result is not None
        assert "Generated response" in result
        mock_vector_store.search.assert_called_once_with(query, top_k=5)
    
    @pytest.mark.asyncio
    async def test_process_query_empty_vector_store(self, rag_processor, mock_vector_store):
        """Test RAG processing with empty vector store"""
        mock_vector_store.is_empty = True
        mock_vector_store.search.return_value = []
        
        query = "What is machine learning?"
        result = await rag_processor.process_query(query)
        
        assert "No relevant documents found" in result
```

#### Testy Integracyjne dla Vector Store

```python
# tests/integration/test_vector_store.py
import pytest
import tempfile
import os
from app.rag.vector_store import VectorStore
from app.rag.embeddings import EmbeddingService

class TestVectorStoreIntegration:
    @pytest.fixture
    def temp_vector_store(self):
        """Create temporary vector store for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = os.path.join(temp_dir, "test_store")
            embedding_service = EmbeddingService()
            vector_store = VectorStore(store_path, embedding_service)
            yield vector_store
    
    def test_add_and_search_documents(self, temp_vector_store):
        """Test adding documents and searching"""
        documents = [
            {"id": "1", "content": "Python is a programming language"},
            {"id": "2", "content": "FastAPI is a web framework for Python"},
            {"id": "3", "content": "Machine learning uses algorithms"}
        ]
        
        # Add documents
        for doc in documents:
            temp_vector_store.add_document(doc["id"], doc["content"])
        
        # Search for relevant documents
        results = temp_vector_store.search("Python programming", top_k=2)
        
        assert len(results) == 2
        assert any("Python" in result["content"] for result in results)
        assert all(result["score"] > 0.5 for result in results)
    
    def test_vector_store_persistence(self, temp_vector_store):
        """Test vector store data persistence"""
        # Add a document
        temp_vector_store.add_document("test_id", "Test content")
        
        # Save and reload
        temp_vector_store.save()
        temp_vector_store.load()
        
        # Search should still work
        results = temp_vector_store.search("Test", top_k=1)
        assert len(results) == 1
        assert "Test content" in results[0]["content"]
```

### 3. Rozwiązanie 30 Ostrzeżeń Deprecation

#### Plan Aktualizacji Zależności

```bash
# Aktualizacja głównych zależności
poetry update fastapi
poetry update pydantic
poetry update sqlalchemy
poetry update pytest-asyncio

# Sprawdzenie deprecated API calls
python -m py_compile app/ --warnings-as-errors
```

#### Przykłady Poprawek Deprecated API

```python
# Przed (deprecated)
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    
# Po (aktualny)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
```

```python
# Przed (deprecated SQLAlchemy)
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# Po (SQLAlchemy 2.0+)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

## 🟡 Priorytet Średni

### 4. Dodanie Performance Benchmarking

#### Implementacja Benchmarking Tools[6]

```python
# tests/performance/test_api_performance.py
import pytest
import time
import statistics
from fastapi.testclient import TestClient
from app.main import app

class TestAPIPerformance:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def benchmark_endpoint(self, client, endpoint, method="GET", iterations=100):
        """Benchmark API endpoint performance"""
        response_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            end_time = time.time()
            
            assert response.status_code  None:
        self.secret_key = secret_key
    
    async def authenticate_user(
        self, 
        username: str, 
        password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data if valid"""
        # Implementation here
        pass
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[int] = None
    ) -> str:
        """Create JWT access token"""
        # Implementation here
        pass
```

### 6. Rozszerzenie Testów Integracyjnych

#### API Contract Testing[9]

```python
# tests/contract/test_api_contracts.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
import jsonschema

class TestAPIContracts:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_user_creation_contract(self, client):
        """Test user creation API contract"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        
        response = client.post("/users/", json=user_data)
        
        # Verify status code
        assert response.status_code == 201
        
        # Verify response schema
        response_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "created_at": {"type": "string", "format": "date-time"}
            },
            "required": ["id", "username", "email", "created_at"]
        }
        
        jsonschema.validate(response.json(), response_schema)
    
    def test_error_response_contract(self, client):
        """Test error response contract consistency"""
        # Test various error endpoints
        error_endpoints = [
            ("/users/99999", 404),
            ("/users/", 422),  # Invalid data
        ]
        
        error_schema = {
            "type": "object",
            "properties": {
                "detail": {"type": "string"},
                "error_code": {"type": "string"},
                "timestamp": {"type": "string"}
            },
            "required": ["detail"]
        }
        
        for endpoint, expected_status in error_endpoints:
            response = client.get(endpoint)
            assert response.status_code == expected_status
            jsonschema.validate(response.json(), error_schema)
```

### 7. Dodanie API Contract Testing

#### OpenAPI Schema Validation

```python
# tests/contract/test_openapi_schema.py
import pytest
from fastapi.openapi.utils import get_openapi
from app.main import app

class TestOpenAPISchema:
    def test_openapi_schema_validity(self):
        """Test that OpenAPI schema is valid"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Verify required OpenAPI fields
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # Verify info section
        assert schema["info"]["title"] == app.title
        assert schema["info"]["version"] == app.version
    
    def test_all_endpoints_documented(self):
        """Test that all endpoints are documented in OpenAPI schema"""
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Get all registered routes
        documented_paths = set(schema["paths"].keys())
        
        # Verify critical endpoints are documented
        critical_endpoints = ["/health", "/auth/login", "/users/", "/ai/query"]
        
        for endpoint in critical_endpoints:
            assert any(endpoint in path for path in documented_paths), f"Endpoint {endpoint} not documented"
```

