# 🚀 FoodSave AI - Przewodnik Developerski

> **Kompletny przewodnik uruchomienia środowiska developerskiego z pełnym logowaniem i monitoringiem**

## 📋 Spis Treści

- [🚀 Szybki Start](#-szybki-start)
- [🔧 Wymagania Systemowe](#-wymagania-systemowe)
- [📦 Instalacja i Konfiguracja](#-instalacja-i-konfiguracja)
- [🔐 Uwierzytelnianie i Testowanie](#-uwierzytelnianie-i-testowanie)
- [🔄 Zarządzanie Aplikacją](#-zarządzanie-aplikacją)
- [📊 Monitoring i Logi](#-monitoring-i-logi)
- [🧪 Testowanie](#-testowanie)
- [🔍 Debugowanie](#-debugowanie)
- [📚 Dokumentacja API](#-dokumentacja-api)
- [🛠️ Rozwój](#-rozwój)

---

## 🚀 Szybki Start

### 1. Klonowanie Repozytorium
```bash
git clone https://github.com/yourusername/foodsave-ai.git
cd foodsave-ai
```

### 2. Konfiguracja Środowiska
```bash
# Skopiuj plik konfiguracyjny
cp env.dev.example .env

# Uruchom konfigurację początkową
./scripts/dev-setup.sh setup
```

### 3. Uruchomienie Aplikacji
```bash
# Uruchom wszystkie serwisy
docker compose up -d

# Sprawdź status
docker compose ps
```

### 4. Dostęp do Aplikacji
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8001
- 📚 **API Docs**: http://localhost:8001/docs
- 🤖 **Ollama**: http://localhost:11434
- 📈 **Prometheus**: http://localhost:9090
- 📊 **Grafana**: http://localhost:3001 (admin/admin)
- 📝 **Loki**: http://localhost:3100

---

## 🔧 Wymagania Systemowe

### Podstawowe Wymagania
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **curl**: dla health checks

### Opcjonalne (Dla Lepszego Wydajności)
- **NVIDIA GPU**: z CUDA support
- **NVIDIA Container Toolkit**: dla GPU acceleration
- **Min. 8GB RAM**: dla modeli AI
- **Min. 20GB wolnego miejsca**: dla modeli i danych

### Sprawdzenie Wymagań
```bash
# Sprawdź Docker
docker --version
docker-compose --version

# Sprawdź GPU (opcjonalne)
nvidia-smi

# Sprawdź dostępną pamięć
free -h
```

---

## 📦 Instalacja i Konfiguracja

### 1. Konfiguracja Początkowa
```bash
# Uruchom pełną konfigurację
./scripts/dev-setup.sh setup
```

To polecenie:
- ✅ Sprawdza wymagania systemowe
- ✅ Tworzy plik `.env` z szablonu
- ✅ Tworzy katalogi dla logów i danych
- ✅ Sprawdza support GPU
- ✅ Konfiguruje uprawnienia

### 2. Konfiguracja GPU (Opcjonalne)
Jeśli masz NVIDIA GPU:

```bash
# Sprawdź czy GPU jest wykryty
nvidia-smi

# Jeśli tak, Ollama automatycznie użyje GPU
# Jeśli nie, sprawdź instalację NVIDIA Container Toolkit
```

### 3. Instalacja Modeli AI
```bash
# Zainstaluj modele Ollama (po uruchomieniu aplikacji)
./scripts/dev-setup.sh models
```

Dostępne modele:
- `gemma3:12b` - Główny model (zalecany)
- `gemma3:8b` - Lżejszy model
- `nomic-embed-text` - Model embeddings

---

## 🔐 Uwierzytelnianie i Testowanie

### Status Uwierzytelniania
✅ **NAPRAWIONE** - Wszystkie problemy z async/greenlet zostały rozwiązane:
- Backend działa poprawnie na porcie 8001
- Endpointy `/auth/register` i `/auth/login` działają
- Async session handling naprawione
- Eager loading dla user roles zaimplementowane

### Testowanie Uwierzytelniania

#### 1. Utworzenie Nowego Użytkownika
```bash
curl -X POST "http://localhost:8001/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "username": "testuser",
    "full_name": "Test User"
  }'
```

#### 2. Logowanie
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

#### 3. Sprawdzenie Tokenu
```bash
# Zastąp YOUR_TOKEN otrzymanym tokenem
curl -X GET "http://localhost:8001/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Automatyczne Testy
```bash
# Uruchom skrypt testowy
./scripts/test_auth_automation.sh
```

### Konfiguracja Portów
- **Backend**: Port 8001 (host) → 8000 (container)
- **Frontend**: Port 3000 (host) → 3000 (container)
- **Database**: Port 5433 (host) → 5432 (container)

---

## 🔄 Zarządzanie Aplikacją

### Podstawowe Komendy
```bash
# Uruchom aplikację
docker compose up -d

# Zatrzymaj aplikację
docker compose down

# Restartuj aplikację
docker compose restart

# Sprawdź status
docker compose ps
```

### Zarządzanie Logami
```bash
# Wszystkie logi
docker compose logs

# Logi konkretnego serwisu
docker compose logs backend
docker compose logs frontend
docker compose logs postgres
docker compose logs redis

# Logi z określoną liczbą linii
docker compose logs backend --tail=100
```

### Czyszczenie Środowiska
```bash
# Zatrzymaj i wyczyść
docker compose down -v
```

---

## 📊 Monitoring i Logi

### Struktura Katalogów Logów
```
logs/
├── backend/          # Logi FastAPI
├── frontend/         # Logi React/Vite
├── ollama/           # Logi modeli AI
├── postgres/         # Logi bazy danych
├── redis/            # Logi cache
├── grafana/          # Logi dashboardów
├── prometheus/       # Logi metryk
└── loki/             # Logi agregacji
```

### Dostęp do Logów

#### 1. Przez Skrypt
```bash
# Logi w czasie rzeczywistym
./scripts/dev-setup.sh logs backend -f

# Ostatnie 100 linii
./scripts/dev-setup.sh logs backend 100
```

#### 2. Przez Docker
```bash
# Logi kontenera
docker logs foodsave-backend-dev -f

# Logi z timestamp
docker logs foodsave-backend-dev --timestamps
```

#### 3. Przez Grafana (Loki)
- Otwórz http://localhost:3001
- Zaloguj się (admin/admin)
- Przejdź do "Explore"
- Wybierz datasource "Loki"
- Wpisz zapytanie: `{job="backend_logs"}`

### Monitoring Metryk

#### Prometheus
- **URL**: http://localhost:9090
- **Metryki**: Backend, Frontend, Ollama, PostgreSQL, Redis
- **Zapytania**: PromQL queries

#### Grafana
- **URL**: http://localhost:3001
- **Login**: admin/admin
- **Dashboardy**: Automatycznie załadowane
- **Datasources**: Prometheus, Loki

### Przykładowe Zapytania Loki
```logql
# Wszystkie logi backend
{job="backend_logs"}

# Logi błędów
{job="backend_logs"} |= "ERROR"

# Logi z określonego poziomu
{job="backend_logs"} | json | level="ERROR"

# Logi z określonego serwisu
{job="docker"} |= "foodsave-backend"
```

---

## 🧪 Testowanie

### Uruchomienie Testów
```bash
# Wszystkie testy
./scripts/dev-setup.sh test

# Testy jednostkowe
docker-compose -f docker-compose.dev.yaml exec backend poetry run pytest tests/unit/ -v

# Testy integracyjne
docker-compose -f docker-compose.dev.yaml exec backend poetry run pytest tests/integration/ -v

# Testy z coverage
docker-compose -f docker-compose.dev.yaml exec backend poetry run pytest --cov=src --cov-report=html
```

### Struktura Testów
```
tests/
├── unit/              # Testy jednostkowe
├── integration/       # Testy integracyjne
├── e2e/              # Testy end-to-end
└── fixtures/         # Dane testowe
```

### Testy Frontendu
```bash
# Przejdź do katalogu frontendu
cd myappassistant-chat-frontend

# Testy jednostkowe
npm test

# Testy e2e
npm run test:e2e
```

---

## 🔍 Debugowanie

### Debugowanie Backend
```bash
# Shell w kontenerze backend
docker-compose -f docker-compose.dev.yaml exec backend bash

# Sprawdź logi aplikacji
tail -f /app/logs/backend.log

# Sprawdź zmienne środowiskowe
env | grep FOODSAVE

# Uruchom Python debugger
poetry run python -m pdb src/backend/main.py
```

### Debugowanie Frontend
```bash
# Shell w kontenerze frontend
docker-compose -f docker-compose.dev.yaml exec frontend sh

# Sprawdź logi
tail -f /app/logs/frontend.log

# Sprawdź node_modules
ls -la node_modules/
```

### Debugowanie Bazy Danych
```bash
# Połączenie z PostgreSQL
docker-compose -f docker-compose.dev.yaml exec postgres psql -U foodsave -d foodsave_dev

# Sprawdź tabele
\dt

# Sprawdź logi
tail -f /var/log/postgresql/postgresql.log
```

### Debugowanie Redis
```bash
# Redis CLI
docker-compose -f docker-compose.dev.yaml exec redis redis-cli

# Sprawdź klucze
KEYS *

# Sprawdź logi
tail -f /var/log/redis/redis.log
```

---

## 📚 Dokumentacja API

### Swagger UI
- **URL**: http://localhost:8000/docs
- **Funkcje**: Interaktywna dokumentacja API
- **Testowanie**: Możliwość testowania endpointów

### ReDoc
- **URL**: http://localhost:8000/redoc
- **Funkcje**: Alternatywna dokumentacja API

### Endpointy Health Check
```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# Readiness
curl http://localhost:8000/ready

# Liveness
curl http://localhost:8000/live
```

---

## 🛠️ Rozwój

### Hot Reload
- **Backend**: Automatyczny reload przy zmianach w `./src/`
- **Frontend**: Automatyczny reload przy zmianach w `./myappassistant-chat-frontend/`

### Struktura Projektu
```
myappassistant/
├── src/backend/           # Backend FastAPI
├── myappassistant-chat-frontend/  # Frontend React
├── scripts/               # Skrypty automatyzacji
├── tests/                 # Testy
├── monitoring/            # Konfiguracja monitoringu
├── logs/                  # Logi aplikacji
└── data/                  # Dane aplikacji
```

### Dodawanie Nowych Serwisów
1. Dodaj serwis do `docker-compose.dev.yaml`
2. Dodaj konfigurację do `env.dev.example`
3. Zaktualizuj skrypt `dev-setup.sh`
4. Dodaj health check
5. Skonfiguruj logowanie

### Best Practices
- ✅ Zawsze używaj hot reload
- ✅ Sprawdzaj logi przed commitowaniem
- ✅ Uruchamiaj testy przed push
- ✅ Używaj pre-commit hooks
- ✅ Dokumentuj zmiany w API

---

## 🆘 Rozwiązywanie Problemów

### Częste Problemy

#### 1. Port Already in Use
```bash
# Sprawdź co używa portu
sudo lsof -i :8000

# Zatrzymaj proces
sudo kill -9 <PID>
```

#### 2. Brak Pamięci dla Modeli
```bash
# Sprawdź użycie pamięci
docker stats

# Zatrzymaj niepotrzebne kontenery
docker stop $(docker ps -q)
```

#### 3. Problemy z GPU
```bash
# Sprawdź NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Jeśli nie działa, użyj CPU
export NVIDIA_VISIBLE_DEVICES=""
```

#### 4. Problemy z Bazą Danych
```bash
# Resetuj bazę danych
docker-compose -f docker-compose.dev.yaml down -v
docker-compose -f docker-compose.dev.yaml up -d postgres
```

### Logi Debugowania
```bash
# Szczegółowe logi Docker
docker-compose -f docker-compose.dev.yaml logs --tail=100 -f

# Logi systemowe
journalctl -f

# Logi Docker daemon
sudo journalctl -u docker.service -f
```

---

## 📞 Wsparcie

### Dokumentacja
- [Główny README](../README.md)
- [Dokumentacja API](API_REFERENCE.md)
- [Przewodnik Testowania](TESTING_GUIDE.md)

### Kontakt
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**🚀 FoodSave AI Development Environment** - Gotowy do rozwoju! 🎯
