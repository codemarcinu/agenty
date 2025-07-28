# 🛠️ Stack Technologiczny - FoodSave AI

> [!WARNING] Frontend (Next.js/React/Tauri/UI) został usunięty z projektu w lipcu 2025. Poniższe sekcje frontendowe są nieaktualne i zachowane wyłącznie archiwalnie.

## Co znajdziesz w tym dokumencie?

- [x] Kompletny przegląd technologii
- [x] Wersje i zależności
- [x] Architektura techniczna
- [x] Wymagania systemowe
- [x] Linki do dokumentacji

## Spis treści
- [1. 🏗️ Architektura Ogólna](#️-architektura-ogólna)
- [2. 🔧 Backend](#-backend)
- [3. 🎨 Frontend](#-frontend)
- [4. 🤖 AI/ML](#-aiml)
- [5. 🗄️ Baza Danych](#️-baza-danych)
- [6. 🐳 Infrastruktura](#-infrastruktura)
- [7. 🧪 Testy i QA](#-testy-i-qa)
- [8. 📊 Monitoring](#-monitoring)

---

## 🏗️ Architektura Ogólna

### Wzorzec Architektoniczny
- **Backend**: FastAPI (Python) - REST API + WebSocket
- **Frontend**: React 18 + TypeScript - SPA
- **Desktop**: Tauri (Rust + Web) - Aplikacja natywna
- **AI**: Ollama + Bielik - Lokalne modele AI
- **Database**: SQLite - Persystencja + Cache
- **Infrastructure**: Docker Compose - Konteneryzacja

### Diagram Architektury
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tauri App     │    │   Next.js Web   │    │   Mobile App    │
│   (Frontend)    │    │   (Frontend)    │    │   (Future)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   Backend       │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SQLite        │    │   Redis Cache   │    │   Ollama LLM    │
│   Database      │    │                 │    │   (Local AI)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔧 Backend

### Framework i Język
- **Python**: 3.12+
- **FastAPI**: 0.104+ - Nowoczesny framework web
- **Pydantic**: 2.0+ - Walidacja danych i serializacja
- **SQLAlchemy**: 2.0+ - ORM z wsparciem async
- **Uvicorn**: 0.24+ - ASGI server

### Kluczowe Biblioteki
```python
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Data Validation
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
redis==5.0.1

# AI/ML
ollama==0.1.7
faiss-cpu==1.7.4
transformers==4.36.0

# Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Struktura Backendu
```
src/backend/
├── agents/              # Agenty AI
│   ├── base_agent.py
│   ├── ocr_agent.py
│   ├── receipt_agent.py
│   └── search_agent.py
├── api/                 # Endpointy API
│   ├── v1/
│   ├── v2/
│   └── receipts.py
├── core/                # Rdzeń systemu
│   ├── config.py
│   ├── database.py
│   └── llm_client.py
├── models/              # Modele danych
│   ├── conversation.py
│   └── receipt.py
└── services/            # Logika biznesowa
    └── receipt_service.py
```

---

## 🎨 Frontend

> [!WARNING] Frontend (Next.js/React/Tauri/UI) został usunięty z projektu w lipcu 2025. Ta sekcja jest archiwalna.

### Framework i Język
- **React**: 18.2+ - Biblioteka UI
- **TypeScript**: 5.0+ - Type-safe JavaScript
- **Next.js**: 15.0+ - React framework
- **Tailwind CSS**: 3.3+ - Utility-first CSS
- **Vite**: 5.0+ - Build tool

### Kluczowe Biblioteki
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^15.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.48.0"
  }
}
```

### Desktop App (Tauri)
- **Tauri**: 2.0+ - Framework aplikacji desktop
- **Rust**: 1.70+ - Backend aplikacji
- **WebView**: Systemowy - Renderowanie UI

### Struktura Frontendu
```
myappassistant-chat-frontend/
├── src/
│   ├── app/             # Next.js App Router
│   ├── components/      # Komponenty React
│   ├── hooks/           # Custom hooks
│   ├── stores/          # Zustand stores
│   └── types/           # TypeScript types
├── src-tauri/           # Tauri configuration
└── public/              # Static assets
```

---

## 🤖 AI/ML

### Modele Językowe
- **Bielik 4.5b v3.0**: Kategoryzacja produktów i czat
- **Bielik 11b v2.3**: Analiza paragonów
- **Ollama**: Lokalna inferencja LLM
- **FAISS**: Wyszukiwanie podobieństwa wektorów

### Konfiguracja Modeli
```yaml
# Ollama Configuration
models:
  - name: "bielik-4.5b-v3.0"
    format: "Q8_0"
    size: "5.06GB"
    purpose: "categorization"
  
  - name: "bielik-11b-v2.3"
    format: "Q8_0"
    size: "7.91GB"
    purpose: "receipt_analysis"
```

### Agenty AI
1. **OCRAgent** - Ekstrakcja tekstu z obrazów
2. **ReceiptAnalysisAgent** - Analiza paragonów
3. **ProductCategorizer** - Kategoryzacja produktów
4. **SearchAgent** - Wyszukiwanie informacji
5. **ConciseAgent** - Zwięzłe odpowiedzi

---

## 🗄️ Baza Danych

### Główna Baza Danych
- **SQLite**: lokalny plik

### Cache i Sesje
- **Redis**: 7.0+ - Cache i sesje
- **TTL**: 24h dla sesji
- **Persistence**: RDB + AOF

### Vector Store
- **FAISS**: 1.7+ - Wyszukiwanie podobieństwa
- **Embeddings**: nomic-embed-text
- **Index**: IVF100, SQ8

### Schemat Bazy
```sql
-- Główne tabele
conversations (id, user_id, title, created_at)
messages (id, conversation_id, role, content, created_at)
receipts (id, user_id, store_name, total_amount, date)
receipt_items (id, receipt_id, name, quantity, price, category)
```

---

## 🐳 Infrastruktura

### Konteneryzacja
- **Docker**: 20.10+ - Konteneryzacja
- **Docker Compose**: 2.0+ - Orchestracja
- **Multi-stage builds**: Optymalizacja obrazów
- **Health checks**: Automatyczne sprawdzanie

### Konfiguracja Docker
```yaml
# docker-compose.dev.yaml
services:
  backend:
    build: ./src
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./foodsave.db
      - REDIS_URL=redis://redis:6379
  
  frontend:
    build: ./myappassistant-chat-frontend
    ports: ["3000:3000"]
    depends_on: ["backend"]
  
  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    volumes: ["ollama_data:/root/.ollama"]
```

### Porty Systemu
- **Backend API**: 8000
- **Frontend Web**: 3000
- **Ollama**: 11434
- **SQLite**: lokalny plik
- **Redis**: 6379
- **Grafana**: 3001
- **Prometheus**: 9090

---

## 🧪 Testy i QA

### Backend Testing
- **Framework**: pytest 7.0+
- **Coverage**: pytest-cov 4.0+
- **Async**: pytest-asyncio 0.21+
- **Mocking**: pytest-mock 3.12+

### Frontend Testing
- **Framework**: Jest 29.0+
- **React Testing**: @testing-library/react 13.0+
- **E2E**: Playwright 1.40+
- **Coverage**: 100% (81/81 testów)

### Test Types
```python
# Backend Test Structure
tests/
├── unit/              # Testy jednostkowe
├── integration/       # Testy integracyjne
├── performance/       # Testy wydajnościowe
└── contract/          # Testy kontraktów API
```

---

## 📊 Monitoring

### Metryki i Logi
- **Prometheus**: Zbieranie metryk
- **Grafana**: Dashboardy i wizualizacja
- **Loki**: Agregacja logów
- **Alerting**: Automatyczne alerty

### Health Checks
```python
# Endpointy health check
GET /health              # Podstawowy status
GET /monitoring/status   # Szczegółowy status
GET /metrics            # Metryki Prometheus
```

### Dashboardy Grafana
- **System Overview**: Status wszystkich komponentów
- **AI Performance**: Wydajność modeli AI
- **API Metrics**: Metryki endpointów
- **Error Tracking**: Śledzenie błędów

---

## 📋 Wymagania Systemowe

### Minimalne Wymagania
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **CPU**: 4 cores (8 cores zalecane)
- **RAM**: 8GB (16GB zalecane)
- **Dysk**: 10GB wolnego miejsca
- **GPU**: Opcjonalne (CUDA dla przyspieszenia AI)

### Zalecane Wymagania
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Dysk**: SSD 50GB+
- **GPU**: NVIDIA RTX 3060+ (CUDA 11.8+)

---

## 🔗 Linki do Dokumentacji

### Szczegółowe Przewodniki
- [Architektura systemu](ARCHITECTURE.md) - Szczegółowa architektura
- [Dokumentacja API](API_REFERENCE.md) - Endpointy API
- [Przewodnik wdrażania](../guides/deployment/PRODUCTION.md) - Wdrażanie
- [Przewodnik testowania](../guides/development/TESTING.md) - Testy

### Konfiguracja
- [Docker Setup](../guides/deployment/DOCKER.md) - Konfiguracja Docker
- [Environment Variables](../guides/development/SETUP.md) - Zmienne środowiskowe
- [Monitoring Setup](../guides/deployment/MONITORING.md) - Monitoring

---

> **💡 Wskazówka:** Wszystkie technologie są wybrane z myślą o wydajności, skalowalności i łatwości utrzymania. System jest w pełni konteneryzowany i gotowy do wdrożenia produkcyjnego. 