# 🚀 Ewoluowany System Agentowy AI

## 📋 Przegląd

Ten system implementuje zaawansowaną architekturę agentową z **planistą-egzekutorem-syntezatorem**, która zastępuje prosty router intencji. System oferuje:

- **Inteligentne planowanie** zadań wieloetapowych
- **Efektywną pamięć konwersacji** z podsumowaniami
- **Niezawodne wykonanie** z obsługą błędów
- **Spójne odpowiedzi** syntetyzowane z wyników kroków
- **Rozszerzalne narzędzia** z centralnym rejestrem

## 🏗️ Architektura

### Faza 1: Fundamenty ✅
- [x] Pamięć podsumowująca konwersacje
- [x] Refaktoryzacja agentów na narzędzia
- [x] Centralny rejestr narzędzi z dekoratorami

### Faza 2: Rdzeń Inteligencji ✅
- [x] **Planner** - tworzy wieloetapowe plany JSON
- [x] **Executor** - wykonuje kroki sekwencyjnie z streamingiem
- [x] **Synthesizer** - generuje spójne odpowiedzi

### Faza 3: Niezawodność i Zaufanie 🚧
- [ ] **Critic** - weryfikacja faktów i samokorekta
- [ ] Pętle samokorekty
- [ ] Metryki jakości odpowiedzi

### Faza 4: Integracja Frontend 🚧
- [ ] Streaming myśli agentów
- [ ] Widoczność kroków wykonania
- [ ] Interfejs użytkownika

## 🚀 Szybki Start

### Uruchomienie w Kontenerach (Zalecane)

```bash
# 1. Uruchom cały system
chmod +x run_system.sh
./run_system.sh

# 2. Uruchom testy
chmod +x test_in_container.sh
./test_in_container.sh
```

### Uruchomienie Lokalne

```bash
# 1. Zainstaluj zależności
pip install -r src/backend/requirements.txt
pip install aiosqlite celery

# 2. Uruchom migracje bazy danych (dla SQLite niepotrzebne, tabele tworzone automatycznie)
cd src

# 3. Uruchom testy
cd ..
python test_evolved_agent_system.py
```

## 📊 Komponenty Systemu

### 1. Planner (Planista)
```python
from backend.agents.planner import Planner

planner = Planner()
plan = await planner.create_plan("Znajdź przepis na kurczaka i sprawdź pogodę")
# Zwraca ExecutionPlan z krokami JSON
```

### 2. Executor (Egzekutor)
```python
from backend.agents.executor import Executor

executor = Executor()
result = await executor.execute_plan(plan)
# Wykonuje kroki sekwencyjnie z streamingiem statusu
```

### 3. Synthesizer (Syntezator)
```python
from backend.agents.synthesizer import Synthesizer

synthesizer = Synthesizer()
response = await synthesizer.generate_response(result, original_query)
# Łączy wyniki w spójną odpowiedź
```

### 4. Memory Manager (Menedżer Pamięci)
```python
from backend.agents.memory_manager import MemoryManager

memory = MemoryManager()
context = await memory.get_optimized_context(session_id, max_tokens=4000)
# Automatycznie kompresuje kontekst z podsumowaniami
```

### 5. Tool Registry (Rejestr Narzędzi)
```python
from backend.agents.tools.registry import register_tool

@register_tool(
    name="get_weather",
    description="Get weather forecast",
    required_args=["location"]
)
async def get_weather(location: str) -> str:
    return f"Weather for {location}: sunny"
```

## 🔧 Konfiguracja

### Zmienne Środowiskowe

```bash
# Baza danych
DATABASE_URL=sqlite+aiosqlite:///./foodsave.db

# Redis dla Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Ollama LLM
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=bielik:11b-q4_k_m

# System agentowy
USE_PLANNER_EXECUTOR=true
ENABLE_CONVERSATION_SUMMARY=true
```

### Konfiguracja Celery

```python
# backend/config/celery_config.py
celery_config = {
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'timezone': 'Europe/Warsaw',
    'task_time_limit': 30 * 60,
}
```

## 🧪 Testowanie

### Testy Komponentów

```bash
# Test planisty
python -c "
import asyncio
from backend.agents.planner import Planner
planner = Planner()
plan = asyncio.run(planner.create_plan('Test query'))
print(f'Plan: {plan.steps}')
"

# Test egzekutora
python -c "
import asyncio
from backend.agents.executor import Executor
executor = Executor()
result = asyncio.run(executor.execute_plan(plan))
print(f'Result: {result.success}')
"

# Test syntezatora
python -c "
import asyncio
from backend.agents.synthesizer import Synthesizer
synthesizer = Synthesizer()
response = asyncio.run(synthesizer.generate_response(result, 'Test query'))
print(f'Response: {response.text}')
"
```

### Testy Integracyjne

```bash
# Pełny test systemu
python test_evolved_agent_system.py

# Test w kontenerze
docker-compose exec backend python test_evolved_agent_system.py
```

## 📈 Metryki i Monitorowanie

### Metryki Systemu

```python
# Statystyki pamięci
stats = memory_manager.get_memory_stats()
print(f"Konteksty: {stats['total_contexts']}")
print(f"Kompresja: {stats['compression_ratio']:.2f}")

# Statystyki wykonania
print(f"Czas wykonania: {execution_result.total_execution_time:.2f}s")
print(f"Kroki udane: {len([r for r in execution_result.step_results if r.success])}")
```

### Logi

```bash
# Logi systemu
docker-compose logs -f backend

# Logi Celery
docker-compose logs -f celery_worker

# Logi z błędami
docker-compose logs | grep -i error
```

## 🔄 Migracje Bazy Danych

```bash
# Uruchom migracje (dla SQLite niepotrzebne)

# Sprawdź schemat (dla SQLite użyj sqlite3)
```

## 🛠️ Rozszerzanie Systemu

### Dodawanie Nowych Narzędzi

```python
# backend/agents/tools/custom_tools.py
from backend.agents.tools.registry import register_tool

@register_tool(
    name="custom_tool",
    description="Custom tool description",
    required_args=["param1"],
    optional_args=["param2"],
    return_type="str"
)
async def custom_tool(param1: str, param2: str = "default") -> str:
    # Implementacja narzędzia
    return f"Result: {param1} + {param2}"
```

### Dodawanie Nowych Agentów

```python
# backend/agents/custom_agent.py
from backend.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def process(self, input_data: dict) -> dict:
        # Implementacja agenta
        return {"result": "custom response"}
```

## 🚨 Rozwiązywanie Problemów

### Częste Problemy

1. **Błąd połączenia z bazą danych (SQLite)**
   ```bash
   # Sprawdź DATABASE_URL
   echo $DATABASE_URL
   ```

2. **Błąd Celery**
   ```bash
   # Sprawdź Redis
   redis-cli ping
   
   # Sprawdź worker
   docker-compose logs celery_worker
   ```

3. **Błąd Ollama**
   ```bash
   # Sprawdź Ollama
   curl http://localhost:11434/api/tags
   
   # Sprawdź modele
   ollama list
   ```

### Debugowanie

```bash
# Włącz debug mode
export DEBUG=true

# Szczegółowe logi
export LOG_LEVEL=DEBUG

# Test pojedynczego komponentu
python -c "
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

# Test komponentu
"
```

## 📚 Dokumentacja API

### Endpointy

- `POST /api/agents/query` - Zapytanie do systemu agentowego
- `GET /api/agents/status` - Status systemu
- `POST /api/agents/stream` - Streaming odpowiedzi
- `GET /health` - Health check

### Przykłady Użycia

```python
import aiohttp
import json

async def query_agent(query: str, session_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/api/agents/query', 
                               json={'query': query, 'session_id': session_id}) as response:
            return await response.json()

# Użycie
result = await query_agent("What's the weather like?", "session_123")
print(result['text'])
```

## 🤝 Wkład w Projekt

1. Fork projektu
2. Utwórz branch feature (`git checkout -b feature/amazing-feature`)
3. Commit zmiany (`git commit -m 'Add amazing feature'`)
4. Push do branch (`git push origin feature/amazing-feature`)
5. Otwórz Pull Request

## 📄 Licencja

Ten projekt jest licencjonowany pod MIT License - zobacz plik [LICENSE](LICENSE) dla szczegółów.

## 🆘 Wsparcie

- 📧 Email: support@foodsave-ai.com
- 💬 Discord: [FoodSave AI Community](https://discord.gg/foodsave-ai)
- 📖 Dokumentacja: [docs.foodsave-ai.com](https://docs.foodsave-ai.com)
- 🐛 Issues: [GitHub Issues](https://github.com/foodsave-ai/makeit/issues)

---

**🎉 Dziękujemy za używanie ewoluowanego systemu agentowego AI!** 