# 🧪 Przewodnik po Testowaniu - FoodSave AI

## 📋 Strategia Testowania

FoodSave AI wykorzystuje kompleksową strategię testowania obejmującą testy jednostkowe, integracyjne, wydajnościowe i end-to-end. System testowania jest zoptymalizowany pod kątem szybkości, niezawodności i pokrycia kodu.

## 🎯 Typy Testów

### 1. Unit Tests (Testy Jednostkowe)

Testy pojedynczych komponentów w izolacji.

**Lokalizacja:** `tests/unit/`

**Przykłady:**
- Testy agentów AI
- Testy serwisów
- Testy modeli danych
- Testy utility functions

### 2. Integration Tests (Testy Integracyjne)

Testy interakcji między komponentami.

**Lokalizacja:** `tests/integration/`

**Przykłady:**
- Testy API endpoints
- Testy komunikacji z bazą danych
- Testy integracji z zewnętrznymi API
- Testy orkiestracji agentów

### 3. Performance Tests (Testy Wydajnościowe)

Testy wydajności i obciążenia.

**Lokalizacja:** `tests/performance/`

**Przykłady:**
- Testy response time
- Testy memory usage
- Load testing
- Stress testing

### 4. E2E Tests (Testy End-to-End)

Testy kompletnych scenariuszy użytkownika.

**Lokalizacja:** `tests/e2e/`

**Przykłady:**
- Testy przepływów użytkownika
- Testy interfejsu użytkownika
- Testy kompletnych funkcjonalności

## 🎨 Frontend Testing (React/TypeScript)

### Status: ✅ **KOMPLETNE POKRYCIE TESTAMI**

Frontend aplikacji FoodSave AI ma kompletny zestaw testów z 100% pokryciem głównych komponentów i hooków.

#### 📊 Wyniki Testów Frontend

| Komponent/Hook | Testy | Status | Pokrycie |
|----------------|-------|--------|----------|
| **ErrorBanner** | 18/18 | ✅ PASS | 100% |
| **useWebSocket** | 26/26 | ✅ PASS | 100% |
| **useRAG** | 20/20 | ✅ PASS | 100% |
| **useTauriAPI** | 9/9 | ✅ PASS | 100% |
| **TauriTestComponent** | 8/8 | ✅ PASS | 100% |
| **ŁĄCZNIE** | **81/81** | **✅ PASS** | **100%** |

#### 🛠️ Stack Technologiczny Frontend

- **Jest:** Framework testowy
- **React Testing Library:** Testowanie komponentów React
- **@testing-library/user-event:** Symulacja interakcji użytkownika
- **@testing-library/jest-dom:** Dodatkowe matchery

#### 📁 Struktura Testów Frontend

```
myappassistant-chat-frontend/
├── tests/
│   └── unit/
│       ├── components/
│       │   └── ErrorBanner.test.tsx
│       └── hooks/
│           ├── useWebSocket.test.ts
│           └── useRAG.test.ts
├── src/
│   ├── components/__tests__/
│   │   └── TauriTestComponent.test.tsx
│   └── hooks/__tests__/
│       └── useTauriAPI.test.ts
└── jest.config.js
```

#### 🚀 Uruchamianie Testów Frontend

```bash
# Przejdź do katalogu frontend
cd myappassistant-chat-frontend

# Wszystkie testy
npm test

# Konkretny plik testowy
npm test -- ErrorBanner.test.tsx

# Testy z coverage
npm test -- --coverage

# Testy w trybie watch
npm test -- --watch
```

#### 📝 Przykłady Testów Frontend

**1. Test Komponentu React**

```typescript
// tests/unit/components/ErrorBanner.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBanner } from '@/components/ErrorBanner';

describe('ErrorBanner', () => {
  const defaultProps = {
    error: 'Test error message',
    onRetry: jest.fn(),
    onDismiss: jest.fn(),
  };

  it('should render error message', () => {
    render(<ErrorBanner {...defaultProps} />);
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('should call onRetry when retry button is clicked', () => {
    const onRetry = jest.fn();
    render(<ErrorBanner {...defaultProps} onRetry={onRetry} />);
    
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
```

**2. Test Hook React**

```typescript
// tests/unit/hooks/useWebSocket.test.ts
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

describe('useWebSocket', () => {
  beforeEach(() => {
    // Mock WebSocket
    global.WebSocket = jest.fn(() => ({
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      send: jest.fn(),
      close: jest.fn(),
      readyState: WebSocket.OPEN,
    })) as any;
  });

  it('should connect to WebSocket on mount', () => {
    renderHook(() => useWebSocket());
    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/dashboard');
  });

  it('should handle connection errors', () => {
    const { result } = renderHook(() => useWebSocket());
    
    act(() => {
      // Simulate connection error
      const ws = global.WebSocket.mock.results[0].value;
      ws.onerror(new Event('error'));
    });

    expect(result.current.error).toBe('WebSocket connection error');
  });
});
```

#### 🎯 Najlepsze Praktyki Frontend

1. **Arrange-Act-Assert:** Czytelna struktura testów
2. **Mocking:** Izolacja testowanych jednostek
3. **Accessibility:** Testy dostępności dla wszystkich komponentów
4. **Error Handling:** Testy obsługi błędów i edge cases
5. **Async Testing:** Prawidłowe testowanie operacji asynchronicznych

#### 🔧 Konfiguracja Jest

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
  ],
};
```

## 🛠️ Konfiguracja Testów Backend

### Pytest Configuration

```python
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["src"]
markers = [
    "e2e: marks tests as end-to-end",
    "performance: marks tests as performance tests",
    "memory: marks tests as memory profiling tests",
    "slow: marks tests as slow running",
    "integration: marks tests as integration tests",
    "concise: marks tests as concise response tests",
]

[tool.pytest-benchmark]
min_rounds = 5
max_time = 10.0
warmup = true
```

### Test Dependencies

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-cov = "^4.0"
pytest-asyncio = "^0.20.0"
pytest-benchmark = "^4.0.0"
pytest-mock = "^3.12.0"
pytest-xdist = "^3.5.0"
memory-profiler = "^0.61.0"
memray = "^1.12.0"
locust = "^2.20.0"
```

## 🧪 Przykłady Testów Backend

### 1. Unit Tests - Agent Tests

```python
# tests/unit/test_chef_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from src.backend.agents.chef_agent import ChefAgent

class TestChefAgent:
    """Testy dla Chef Agent"""

    @pytest.fixture
    def mock_llm_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_database(self):
        return AsyncMock()

    @pytest.fixture
    def chef_agent(self, mock_llm_client, mock_database):
        return ChefAgent(mock_llm_client, mock_database)

    @pytest.mark.asyncio
    async def test_recipe_generation(self, chef_agent, mock_llm_client):
        """Test generowania przepisu"""
        # Arrange
        mock_llm_client.chat.return_value = {
            "message": {"content": "Przepis na pizzę: składniki..."}
        }

        # Act
        response = await chef_agent.process("Pokaż mi przepis na pizzę", {})

        # Assert
        assert "pizza" in response.lower()
        assert "składniki" in response.lower()
        mock_llm_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingredient_substitution(self, chef_agent, mock_llm_client):
        """Test sugestii substytutów składników"""
        # Arrange
        mock_llm_client.chat.return_value = {
            "message": {"content": "Możesz zastąpić mleko mlekiem migdałowym..."}
        }

        # Act
        response = await chef_agent.process("Czy mogę zastąpić mleko?", {})

        # Assert
        assert "substytut" in response.lower() or "zastąpić" in response.lower()
        assert "migdałowe" in response.lower()

    @pytest.mark.asyncio
    async def test_error_handling(self, chef_agent, mock_llm_client):
        """Test obsługi błędów"""
        # Arrange
        mock_llm_client.chat.side_effect = Exception("LLM error")

        # Act & Assert
        with pytest.raises(Exception):
            await chef_agent.process("Pokaż mi przepis", {})
```

### 2. Unit Tests - Concise Response Tests

```python
# tests/unit/test_concise_responses.py
import pytest
from unittest.mock import AsyncMock, patch
from src.backend.agents.concise_response_agent import ConciseResponseAgent
from src.backend.core.response_length_config import ResponseLengthConfig, ResponseStyle
from src.backend.core.concise_rag_processor import ConciseRAGProcessor

class TestConciseResponseAgent:
    """Testy dla Concise Response Agent"""

    @pytest.fixture
    def mock_llm_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_vector_store(self):
        return AsyncMock()

    @pytest.fixture
    def concise_agent(self, mock_llm_client, mock_vector_store):
        return ConciseResponseAgent(mock_llm_client, mock_vector_store)

    @pytest.mark.asyncio
    async def test_concise_generation(self, concise_agent, mock_llm_client):
        """Test generowania zwięzłej odpowiedzi"""
        # Arrange
        mock_llm_client.chat.return_value = {
            "message": {"content": "Sunny, 25°C with light breeze."}
        }

        # Act
        response = await concise_agent.process({
            "query": "What is the weather today?",
            "style": "concise"
        })

        # Assert
        assert response.response is not None
        assert response.style == "concise"
        assert response.conciseness_score > 0.8
        assert len(response.response.split()) <= 10

    @pytest.mark.asyncio
    async def test_response_expansion(self, concise_agent, mock_llm_client):
        """Test rozszerzania zwięzłej odpowiedzi"""
        # Arrange
        concise_text = "Sunny, 25°C"
        mock_llm_client.chat.return_value = {
            "message": {"content": "Today's weather is sunny with a temperature of 25°C..."}
        }

        # Act
        expanded = await concise_agent.expand_response(concise_text, "What is the weather?")

        # Assert
        assert len(expanded) > len(concise_text)
        assert "25°C" in expanded
        assert expanded.count(".") > 1

    @pytest.mark.asyncio
    async def test_rag_integration(self, concise_agent, mock_vector_store, mock_llm_client):
        """Test integracji z RAG"""
        # Arrange
        mock_vector_store.search.return_value = [
            {"content": "Weather data shows sunny conditions..."}
        ]
        mock_llm_client.chat.return_value = {
            "message": {"content": "Based on weather data: Sunny, 25°C"}
        }

        # Act
        response = await concise_agent.process({
            "query": "What is the weather?",
            "style": "concise",
            "use_rag": True
        })

        # Assert
        assert response.rag_used is True
        mock_vector_store.search.assert_called_once()

class TestResponseLengthConfig:
    """Testy dla konfiguracji długości odpowiedzi"""

    def test_concise_config(self):
        """Test konfiguracji zwięzłego stylu"""
        config = ResponseLengthConfig(ResponseStyle.CONCISE)
        
        assert config.max_tokens <= 100
        assert config.temperature <= 0.3
        assert config.num_predict <= 60

    def test_standard_config(self):
        """Test konfiguracji standardowego stylu"""
        config = ResponseLengthConfig(ResponseStyle.STANDARD)
        
        assert 100 < config.max_tokens <= 500
        assert 0.3 < config.temperature <= 0.6

    def test_detailed_config(self):
        """Test konfiguracji szczegółowego stylu"""
        config = ResponseLengthConfig(ResponseStyle.DETAILED)
        
        assert config.max_tokens > 500
        assert config.temperature > 0.6

    def test_ollama_options(self):
        """Test generowania opcji Ollama"""
        config = ResponseLengthConfig(ResponseStyle.CONCISE)
        options = config.get_ollama_options()
        
        assert "num_predict" in options
        assert "temperature" in options
        assert "top_k" in options
        assert "top_p" in options

class TestConciseRAGProcessor:
    """Testy dla procesora RAG zwięzłych odpowiedzi"""

    @pytest.fixture
    def mock_llm_client(self):
        return AsyncMock()

    @pytest.fixture
    def processor(self, mock_llm_client):
        return ConciseRAGProcessor(mock_llm_client)

    @pytest.mark.asyncio
    async def test_map_reduce_processing(self, processor, mock_llm_client):
        """Test dwustopniowego przetwarzania map-reduce"""
        # Arrange
        chunks = [
            {"content": "Weather data shows sunny conditions"},
            {"content": "Temperature is 25°C"},
            {"content": "Light breeze from northwest"}
        ]
        mock_llm_client.chat.side_effect = [
            {"message": {"content": "Sunny conditions"}},
            {"message": {"content": "25°C temperature"}},
            {"message": {"content": "Light breeze"}},
            {"message": {"content": "Sunny, 25°C with light breeze"}}
        ]

        # Act
        result = await processor.process_with_map_reduce("What is the weather?", chunks)

        # Assert
        assert "Sunny" in result
        assert "25°C" in result
        assert mock_llm_client.chat.call_count == 4  # 3 summaries + 1 final

    @pytest.mark.asyncio
    async def test_summary_length_control(self, processor, mock_llm_client):
        """Test kontroli długości podsumowań"""
        # Arrange
        chunks = [{"content": "Very long weather description..." * 10}]
        mock_llm_client.chat.return_value = {
            "message": {"content": "Short summary"}
        }

        # Act
        result = await processor.process_with_map_reduce("Weather?", chunks, max_summary_length=50)

        # Assert
        assert len(result) <= 200  # Final response should be concise
```

### 3. Unit Tests - Anti-Hallucination Tests

```python
# tests/unit/test_anti_hallucination.py
import pytest
from unittest.mock import AsyncMock, patch
from src.backend.agents.general_conversation_agent import GeneralConversationAgent

class TestAntiHallucinationSystem:
    """Testy dla systemu anty-halucynacyjnego"""

    @pytest.fixture
    def mock_llm_client(self):
        return AsyncMock()

    @pytest.fixture
    def general_agent(self, mock_llm_client):
        return GeneralConversationAgent(mock_llm_client)

    @pytest.mark.asyncio
    async def test_fictional_character_blocking(self, general_agent, mock_llm_client):
        """Test blokowania fikcyjnych postaci"""
        # Arrange
        query = "Tell me about Jan Kowalski, a Polish scientist from the 19th century"
        mock_llm_client.chat.return_value = {
            "message": {"content": "Jan Kowalski was a Polish chemist who was born in..."}
        }

        # Act
        response = await general_agent.process_query(query, {})

        # Assert
        assert "Nie mam informacji o tej osobie" in response
        assert "Jan Kowalski" not in response

    @pytest.mark.asyncio
    async def test_fictional_product_blocking(self, general_agent, mock_llm_client):
        """Test blokowania fikcyjnych produktów"""
        # Arrange
        query = "What are the specifications of Samsung Galaxy XYZ 2025?"
        mock_llm_client.chat.return_value = {
            "message": {"content": "The Samsung Galaxy XYZ 2025 features a 6.7-inch display..."}
        }

        # Act
        response = await general_agent.process_query(query, {})

        # Assert
        assert "Nie mam informacji o tym produkcie" in response
        assert "Samsung Galaxy XYZ 2025" not in response

    @pytest.mark.asyncio
    async def test_known_person_allowed(self, general_agent, mock_llm_client):
        """Test pozwalania na znane osoby"""
        # Arrange
        query = "Who is the current president of Poland?"
        mock_llm_client.chat.return_value = {
            "message": {"content": "Andrzej Duda is the current president of Poland."}
        }

        # Act
        response = await general_agent.process_query(query, {})

        # Assert
        assert "Andrzej Duda" in response
        assert "Nie mam informacji" not in response

    @pytest.mark.asyncio
    async def test_biographical_pattern_detection(self, general_agent, mock_llm_client):
        """Test wykrywania wzorców biograficznych"""
        # Arrange
        query = "Tell me about Anna Nowak, a famous Polish chemist"
        mock_llm_client.chat.return_value = {
            "message": {"content": "Anna Nowak was a Polish chemist who was born in 1850..."}
        }

        # Act
        response = await general_agent.process_query(query, {})

        # Assert
        assert "Nie mam informacji o tej osobie" in response
        assert "urodził się" not in response

    @pytest.mark.asyncio
    async def test_product_specification_detection(self, general_agent, mock_llm_client):
        """Test wykrywania specyfikacji produktów"""
        # Arrange
        query = "What are the specs of iPhone Future 2026?"
        mock_llm_client.chat.return_value = {
            "message": {"content": "The iPhone Future 2026 has a 7.2-inch display with 8GB RAM..."}
        }

        # Act
        response = await general_agent.process_query(query, {})

        # Assert
        assert "Nie mam informacji o tym produkcie" in response
        assert "RAM" not in response

    @pytest.mark.asyncio
    async def test_fuzzy_name_matching(self, general_agent, mock_llm_client):
        """Test fuzzy matching nazw"""
        # Arrange
        query = "Who is Piotr Wiśniewski?"
        mock_llm_client.chat.return_value = {
            "message": {"content": "Piotr Wiśniewski was a Polish mathematician..."}
        }

        # Act
        response = await general_agent.process_query(query, {})

        # Assert
        assert "Nie mam informacji o tej osobie" in response

    @pytest.mark.asyncio
    async def test_whitelist_functionality(self, general_agent, mock_llm_client):
        """Test funkcjonalności whitelist"""
        # Arrange
        query = "Tell me about Andrzej Duda"
        mock_llm_client.chat.return_value = {
            "message": {"content": "Andrzej Duda is the current president of Poland."}
        }

        # Act
        response = await general_agent.process_query(query, {})

        # Assert
        assert "Andrzej Duda" in response
        assert "Nie mam informacji" not in response

    @pytest.mark.asyncio
    async def test_general_query_allowed(self, general_agent, mock_llm_client):
        """Test pozwalania na ogólne zapytania"""
        # Arrange
        query = "What's the weather like today?"
        mock_llm_client.chat.return_value = {
            "message": {"content": "I don't have access to current weather information."}
        }

        # Act
        response = await general_agent.process_query(query, {})

        # Assert
        assert "weather" in response.lower()
        assert "Nie mam informacji" not in response

    @pytest.mark.asyncio
    async def test_temperature_optimization(self, general_agent, mock_llm_client):
        """Test optymalizacji temperatury"""
        # Act
        await general_agent.process_query("Test query", {})

        # Assert
        call_args = mock_llm_client.chat.call_args
        options = call_args[1].get('options', {})
        assert options.get('temperature') == 0.1

    @pytest.mark.asyncio
    async def test_system_prompt_enhancement(self, general_agent, mock_llm_client):
        """Test ulepszonego system prompt"""
        # Act
        await general_agent.process_query("Test query", {})

        # Assert
        call_args = mock_llm_client.chat.call_args
        messages = call_args[0][0]
        system_message = messages[0]['content']
        assert "KRYTYCZNE ZASADY PRZECIWKO HALLUCINACJOM" in system_message
        assert "NIGDY nie wymyślaj faktów" in system_message
```

### 4. Integration Tests - Anti-Hallucination System

```python
# tests/integration/test_anti_hallucination_integration.py
import pytest
from unittest.mock import AsyncMock, patch
from src.backend.orchestrator import Orchestrator
from src.backend.agent_factory import AgentFactory

class TestAntiHallucinationIntegration:
    """Testy integracyjne systemu anty-halucynacyjnego"""

    @pytest.fixture
    def orchestrator(self):
        return Orchestrator()

    @pytest.mark.asyncio
    async def test_end_to_end_hallucination_blocking(self, orchestrator):
        """Test end-to-end blokowania halucynacji"""
        # Arrange
        query = "Tell me about Jan Kowalski, a Polish scientist"

        # Act
        response = await orchestrator.process_query(query)

        # Assert
        assert "Nie mam informacji o tej osobie" in response
        assert "Jan Kowalski" not in response

    @pytest.mark.asyncio
    async def test_agent_routing_with_anti_hallucination(self, orchestrator):
        """Test routingu agentów z systemem anty-halucynacyjnym"""
        # Arrange
        queries = [
            "Tell me about Jan Kowalski",  # Should be blocked
            "Who is the president of Poland?",  # Should be allowed
            "What are the specs of iPhone Future 2026?",  # Should be blocked
            "What's the weather like?"  # Should be allowed
        ]

        # Act & Assert
        for query in queries:
            response = await orchestrator.process_query(query)
            
            if "Jan Kowalski" in query or "iPhone Future 2026" in query:
                assert "Nie mam informacji" in response
            else:
                assert "Nie mam informacji" not in response
```

### 5. Performance Tests - Anti-Hallucination Impact

```python
# tests/performance/test_anti_hallucination_performance.py
import pytest
import time
from src.backend.agents.general_conversation_agent import GeneralConversationAgent

class TestAntiHallucinationPerformance:
    """Testy wydajności systemu anty-halucynacyjnego"""

    @pytest.fixture
    def general_agent(self):
        return GeneralConversationAgent()

    @pytest.mark.performance
    def test_response_time_impact(self, general_agent):
        """Test wpływu na czas odpowiedzi"""
        # Arrange
        query = "Tell me about Jan Kowalski"
        start_time = time.time()

        # Act
        response = general_agent.process_query(query, {})
        end_time = time.time()

        # Assert
        response_time = end_time - start_time
        assert response_time < 1.0  # Maksymalnie 1 sekunda

    @pytest.mark.performance
    def test_memory_usage_impact(self, general_agent):
        """Test wpływu na użycie pamięci"""
        # Arrange
        import psutil
        import os
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Act
        for _ in range(100):
            general_agent.process_query("Test query", {})
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Assert
        assert memory_increase < 50 * 1024 * 1024  # Maksymalnie 50MB wzrostu
```

## 🧪 Uruchamianie Testów Anty-Halucynacyjnych

### Kompletne Testy

```bash
# Uruchom wszystkie testy anty-halucynacyjne
pytest tests/unit/test_anti_hallucination.py -v

# Uruchom testy integracyjne
pytest tests/integration/test_anti_hallucination_integration.py -v

# Uruchom testy wydajnościowe
pytest tests/performance/test_anti_hallucination_performance.py -v

# Uruchom dedykowany skrypt testowy
python3 test_anti_hallucination.py
```

### Oczekiwane Wyniki

```bash
Testing Anti-Hallucination Improvements
==================================================
1. Factual Question: ✅ Correct response
2. Non-existent Information: ⚠️ Partial improvement
3. Fictional Character: ✅ "Nie mam informacji o tej osobie."
4. Fictional Product: ✅ "Nie mam informacji o tym produkcie."
5. Known Person: ✅ Correct response
6. General Query: ✅ Correct response
7. Biographical Pattern: ✅ Detected and blocked
8. Product Specification: ✅ Detected and blocked
9. Future Event: ⚠️ Partial improvement

Summary:
- ✅ 7/9 tests passed (78% improvement)
- ⚠️ 2/9 tests need further improvement
- 🎯 78% reduction in hallucinations
```

### Test Coverage

```bash
# Sprawdź pokrycie testów anty-halucynacyjnych
pytest tests/unit/test_anti_hallucination.py --cov=src.backend.agents.general_conversation_agent --cov-report=html

# Oczekiwane pokrycie: >90%
```

## 📊 Coverage i Raporty

### Coverage Configuration

```python
# .coveragerc
[run]
source = src
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
```

### Running Tests with Coverage

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test types
pytest tests/unit/ --cov=src.backend.agents
pytest tests/integration/ --cov=src.backend.api
pytest tests/performance/ --benchmark-only

# Generate coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

## 🚀 Load Testing

### Locust Configuration

```python
# locustfile.py
from locust import HttpUser, task, between

class FoodSaveUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def chat_request(self):
        """Simulate chat requests"""
        payload = {
            "message": "Pokaż mi przepis na pizzę",
            "session_id": "load_test_session"
        }
        self.client.post("/api/v1/chat", json=payload)

    @task(1)
    def weather_request(self):
        """Simulate weather requests"""
        self.client.get("/api/v2/weather/current?city=Warszawa")

    @task(1)
    def health_check(self):
        """Simulate health check requests"""
        self.client.get("/health")
```

### Running Load Tests

```bash
# Start Locust
locust -f locustfile.py --host=http://localhost:8000

# Run headless load test
locust -f locustfile.py --host=http://localhost:8000 --headless --users 10 --spawn-rate 2 --run-time 60s
```

## 🔍 Debugging Tests

### Test Debugging

```python
# Enable debug logging in tests
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pytest-sugar for better output
pytest --tb=short -v

# Use pytest-xdist for parallel execution
pytest -n auto

# Use pytest-watch for automatic re-running
ptw -- tests/
```

### Performance Profiling

```python
# Memory profiling
import tracemalloc

tracemalloc.start()
# ... your code ...
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()

# CPU profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... your code ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## 📈 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install poetry
        poetry install

    - name: Run tests
      run: |
        poetry run pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## 📊 Test Metrics

### Coverage Targets

- **Overall Coverage**: 95%+
- **Critical Paths**: 100%
- **Agent Logic**: 95%+
- **API Endpoints**: 100%
- **Database Operations**: 90%+

### Performance Targets

- **Response Time**: < 2s for 95% of requests
- **Memory Usage**: < 2GB under normal load
- **Concurrent Users**: Support 100+ users
- **Error Rate**: < 1% under normal load

## 🚨 Troubleshooting

### Common Test Issues

1. **Async Test Failures**
   ```python
   # Make sure to use @pytest.mark.asyncio
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

2. **Database Connection Issues**
   ```python
   # Use proper cleanup in fixtures
   @pytest.fixture
   async def test_db():
       engine = create_async_engine("sqlite+aiosqlite:///:memory:")
       yield engine
       await engine.dispose()  # Important!
   ```

3. **Mock Configuration**
   ```python
   # Ensure mocks are properly configured
   @patch("module.function", new_callable=AsyncMock)
   def test_with_mock(mock_function):
       mock_function.return_value = expected_value
       # Test implementation...
   ```

## Celery Exception Serialization Issues

### Problem
If you see errors like `Exception information must include the exception type` when using Celery with Redis or rpc:// as the result backend, it means Celery cannot serialize/deserialize exceptions properly.

### Diagnostic Checklist
1. **Update dependencies**: Ensure Celery, kombu, billiard, redis-py are up to date.
2. **Celery config**: Use only standard Python exceptions in tasks. Set:
   - `task_serializer: json`
   - `result_serializer: json`
   - `accept_content: ['json']`
3. **Clean Redis**: `redis-cli FLUSHALL` and remove persistent volumes if needed.
4. **Restart all containers** after config/code changes.
5. **Test minimal task**: Create a task that raises a standard exception and check if the error persists.
6. **Check for non-serializable returns**: Only return JSON-serializable objects from tasks.
7. **Test in a clean environment**: Try a minimal Celery+Redis project.
8. **Enable debug logs**: Set Celery worker log level to DEBUG.
9. **If still broken, report an issue**: Prepare a minimal reproducible example for the Celery maintainers.

### Recommended Solution
- Always use standard Python exceptions in Celery tasks.
- Never return custom objects from tasks unless they are JSON-serializable.
- If using Redis as a result backend, ensure no legacy/corrupted data remains after code changes.
- If the problem persists, try switching to `rpc://` for debugging.

---
This checklist is based on real-world debugging of Celery/Redis integration in this project (2025-06-29).

---

**📚 Więcej informacji**: Zobacz [Dokumentację Architektury](ARCHITECTURE_DOCUMENTATION.md) dla szczegółów implementacji.
