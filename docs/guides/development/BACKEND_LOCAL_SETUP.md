# Uruchomienie Backendu FoodSave AI Lokalnie

Oto **kompletny przewodnik uruchamiania backendu FoodSave AI bez Dockera**, bezpośrednio w środowisku Python.

## Wymagania systemowe

Backend FoodSave AI wymaga następujących komponentów:
- **Python 3.12** (zgodnie z regułami projektu)
- **PostgreSQL** (baza danych główna) lub **SQLite** (dla development)
- **Redis** (cache i sesje) - opcjonalny dla development
- **Ollama** (lokalne modele AI - Bielik 11b i 4.5b)

## Kroki instalacji i uruchomienia

### 1. Przygotowanie środowiska

```bash
# Klonowanie repozytorium
git clone https://github.com/codemarcinu/my_assistant.git
cd my_assistant

# Tworzenie środowiska wirtualnego
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate     # Windows
```

### 2. Instalacja zależności

```bash
# Instalacja zależności backendu
pip install -r src/backend/requirements.txt

# Alternatywnie, jeśli używasz Poetry:
poetry install

# Lub instalacja w trybie development:
pip install -e .
```

### 3. Konfiguracja zmiennych środowiskowych

Skopiuj plik `env.dev.example` na `.env` i skonfiguruj:

```bash
# Kopiowanie pliku konfiguracyjnego
cp env.dev.example .env

# Edycja pliku .env
nano .env  # lub vim .env
```

**Przykładowa konfiguracja .env dla development:**

```bash
# =============================================================================
# PODSTAWOWE USTAWIENIA APLIKACJI
# =============================================================================

ENVIRONMENT=development
LOG_LEVEL=DEBUG
APP_NAME=FoodSave AI
APP_VERSION=0.1.0

# =============================================================================
# KONFIGURACJA BAZY DANYCH
# =============================================================================

# SQLite dla development (prostsze)
DATABASE_URL=sqlite+aiosqlite:///./foodsave_dev.db

# Lub PostgreSQL (jeśli masz zainstalowane)
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/foodsave_db

# =============================================================================
# KONFIGURACJA REDIS (OPCJONALNE)
# =============================================================================

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_USE_CACHE=true
REDIS_URL=redis://localhost:6379

# =============================================================================
# KONFIGURACJA OLLAMA (MODELI AI)
# =============================================================================

OLLAMA_URL=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434

# Modele językowe - wybierz te które masz zainstalowane
OLLAMA_MODEL=SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0
DEFAULT_CODE_MODEL=SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0
DEFAULT_CHAT_MODEL=SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# =============================================================================
# KONFIGURACJA BEZPIECZEŃSTWA
# =============================================================================

SECRET_KEY=your-super-secret-key-for-development-only
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# =============================================================================
# CORS I BEZPIECZEŃSTWO
# =============================================================================

CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8000

# =============================================================================
# DEVELOPMENT SPECIFIC
# =============================================================================

DEBUG=true
ENABLE_DEBUG_TOOLBAR=true
ENABLE_SQL_LOGGING=true
LOAD_TEST_DATA=true
SEED_DATABASE=true
```

### 4. Uruchomienie usług pomocniczych

#### PostgreSQL (opcjonalne - dla production)
```bash
# Ubuntu/Debian
sudo systemctl start postgresql

# macOS (Homebrew)
brew services start postgresql

# Windows
# Uruchom PostgreSQL z instalatora
```

#### Redis (opcjonalne - dla cache)
```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS (Homebrew)
brew services start redis

# Windows
# Uruchom Redis z instalatora
```

#### Ollama z modelami Bielik
```bash
# Instalacja Ollama (jeśli nie masz)
curl -fsSL https://ollama.ai/install.sh | sh

# Uruchomienie Ollama
ollama serve

# W nowym terminalu - pobieranie modeli
ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0
ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M
ollama pull nomic-embed-text
```

### 5. Inicjalizacja bazy danych

```bash
# Przejście do katalogu głównego projektu
cd /path/to/my_assistant

# Ustawienie PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Inicjalizacja bazy danych (automatyczna przy pierwszym uruchomieniu)
# Baza zostanie utworzona automatycznie przy starcie aplikacji
```

### 6. Uruchomienie serwera FastAPI

Zgodnie z najlepszymi praktykami FastAPI, uruchom serwer używając uvicorn:

```bash
# Metoda 1: Bezpośrednie uruchomienie uvicorn
uvicorn src.backend.app_factory:app --reload --host 0.0.0.0 --port 8000

# Metoda 2: Przez skrypt główny
python run_backend.py

# Metoda 3: Przez skrypt backendu
cd src/backend
./start.sh

# Metoda 4: Przez FastAPI CLI (nowsze wersje)
fastapi dev src.backend.app_factory:app
```

### 7. Weryfikacja działania

Po uruchomieniu backend będzie dostępny na:
- **API**: http://localhost:8000
- **Dokumentacja Swagger**: http://localhost:8000/docs
- **Dokumentacja ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## Struktura katalogów backendu

Zgodnie z regułami projektu, struktura jest następująca:

```
src/backend/
├── api/                    # Routery API po domenach
│   ├── v1/                # API v1 endpoints
│   └── v2/                # API v2 endpoints
├── agents/                 # Agenty AI
│   ├── chef_agent.py
│   ├── weather_agent.py
│   ├── rag_agent.py
│   └── ...
├── models/                 # Modele SQLAlchemy
├── schemas/                # Pydantic schemas
├── services/               # Logika biznesowa
├── core/                   # Konfiguracja bazy danych
├── auth/                   # Autoryzacja i uwierzytelnianie
├── infrastructure/         # Infrastruktura (cache, monitoring)
├── app_factory.py          # Fabryka aplikacji FastAPI
├── main.py                 # Główny punkt wejścia
├── settings.py             # Konfiguracja ustawień
├── requirements.txt        # Zależności
└── start.sh               # Skrypt uruchomienia
```

## Rozwiązywanie problemów

### Problem z importami
Jeśli występują problemy z importami, dodaj katalog projektu do PYTHONPATH:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Problem z SQLAlchemy
Zgodnie z regułami projektu, upewnij się, że wszystkie modele używają pełnych ścieżek modułów:

```python
# Przykład poprawnej definicji modelu
class FoodItem(Base):
    __tablename__ = "food_items"
    
    donations = relationship(
        "backend.models.donation.Donation",
        back_populates="food_item"
    )
```

### Problem z agentami AI
Wszystkie typy agentów muszą być zarejestrowane w fabryce agentów:

```python
# W app_factory.py
agent_registry = AgentRegistry()
agent_factory = AgentFactory()

# Rejestracja agentów
agent_registry.register("chef", ChefAgent)
agent_registry.register("weather", WeatherAgent)
agent_registry.register("rag", RAGAgent)
```

### Problem z Ollama
Sprawdź czy Ollama działa:

```bash
# Sprawdzenie statusu Ollama
curl http://localhost:11434/api/tags

# Sprawdzenie dostępnych modeli
ollama list

# Test modelu
ollama run SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0 "Cześć!"
```

## Dodatkowe opcje uruchomienia

### Z pełną konfiguracją rozwojową
```bash
# Uruchomienie z reload i debugowaniem
uvicorn src.backend.app_factory:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level debug
```

### Z konfiguracją produkcyjną
```bash
# Uruchomienie produkcyjne
uvicorn src.backend.app_factory:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4
```

### Z monitoringiem i metrykami
```bash
# Uruchomienie z włączonym monitoringiem
ENABLE_METRICS=true \
PROMETHEUS_MULTIPROC_DIR=/tmp \
uvicorn src.backend.app_factory:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000
```

## Testowanie backendu

### Uruchomienie testów
```bash
# Wszystkie testy
pytest

# Testy z coverage
pytest --cov=src/backend

# Testy konkretnego modułu
pytest tests/unit/test_agents.py

# Testy z verbose output
pytest -v
```

### Testowanie API
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API v1
curl http://localhost:8000/api/v1/health

# Test API v2
curl http://localhost:8000/api/v2/health
```

## Monitoring i logi

### Logi aplikacji
```bash
# Logi w czasie rzeczywistym
tail -f logs/backend.log

# Logi z filtrowaniem
grep "ERROR" logs/backend.log
```

### Metryki Prometheus
```bash
# Metryki aplikacji
curl http://localhost:8000/metrics

# Health check z metrykami
curl http://localhost:8000/health
```

## Backup i restore

### Backup bazy danych
```bash
# SQLite
cp foodsave_dev.db foodsave_dev_backup_$(date +%Y%m%d_%H%M%S).db

# PostgreSQL
pg_dump -h localhost -U user -d foodsave_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore bazy danych
```bash
# SQLite
cp foodsave_dev_backup_20250107_120000.db foodsave_dev.db

# PostgreSQL
psql -h localhost -U user -d foodsave_db < backup_20250107_120000.sql
```

Backend FoodSave AI jest teraz w pełni skonfigurowany do uruchomienia lokalnego bez użycia Dockera. Wszystkie komponenty działają zgodnie z regułami projektu i standardami FastAPI.

## Przydatne komendy

```bash
# Sprawdzenie wersji Python
python --version

# Sprawdzenie zainstalowanych pakietów
pip list

# Sprawdzenie statusu Ollama
ollama list

# Sprawdzenie portów
netstat -tulpn | grep :8000

# Sprawdzenie procesów
ps aux | grep uvicorn
``` 