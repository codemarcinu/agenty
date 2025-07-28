# 🚀 FoodSave AI - Kompletne Środowisko Developerskie

> **Podsumowanie kompletnego środowiska developerskiego z pełnym logowaniem i monitoringiem**

## 📋 Przegląd

Przygotowano kompletne środowisko developerskie dla aplikacji FoodSave AI, które obejmuje:

- 🐳 **Pełną konteneryzację** z Docker Compose
- 📊 **Kompletny monitoring** (Prometheus, Grafana, Loki)
- 🔍 **Strukturalne logowanie** dla wszystkich serwisów
- ⚡ **Hot reload** dla backend i frontend
- 🧪 **Framework testowy** z coverage
- 🔧 **Automatyzację** setup i zarządzania

## 🏗️ Architektura Środowiska

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Agents     │
│   (React/Vite)  │◄──►│   (FastAPI)     │◄──►│   (Ollama)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   PostgreSQL    │◄─────────────┘
                        │   + Redis       │
                        └─────────────────┘
                                │
                        ┌─────────────────┐
                        │   Monitoring    │
                        │ Prometheus      │
                        │ + Grafana       │
                        │ + Loki          │
                        └─────────────────┘
```

## 🐳 Serwisy Docker

### Główne Serwisy Aplikacji
- **`backend`** - FastAPI backend (port 8000)
- **`frontend`** - React/Vite frontend (port 5173)
- **`ollama`** - Modele AI (port 11434)
- **`postgres`** - Baza danych (port 5433)
- **`redis`** - Cache (port 6379)

### Serwisy Monitoringu
- **`prometheus`** - Metryki (port 9090)
- **`grafana`** - Dashboardy (port 3001)
- **`loki`** - Agregacja logów (port 3100)
- **`promtail`** - Zbieranie logów
- **`nginx`** - Reverse proxy (port 80)

## 📊 Monitoring i Logi

### Struktura Katalogów
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

monitoring/
├── grafana/
│   ├── dashboards/   # Dashboardy Grafana
│   └── datasources/  # Źródła danych
└── prometheus/       # Konfiguracja Prometheus
```

### Dostęp do Monitoringu
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### Przykładowe Zapytania Loki
```logql
# Wszystkie logi backend
{job="backend_logs"}

# Logi błędów
{job="backend_logs"} |= "ERROR"

# Logi z określonego poziomu
{job="backend_logs"} | json | level="ERROR"
```

## 🔧 Konfiguracja

### Pliki Konfiguracyjne
- **`docker-compose.dev.yaml`** - Konfiguracja wszystkich serwisów
- **`env.dev.example`** - Szablon zmiennych środowiskowych
- **`monitoring/loki-config.yaml`** - Konfiguracja Loki
- **`monitoring/promtail-config.yaml`** - Konfiguracja Promtail
- **`monitoring/prometheus.dev.yml`** - Konfiguracja Prometheus

### Zmienne Środowiskowe
- **Pełne logowanie** (DEBUG level)
- **Hot reload** dla development
- **GPU support** dla Ollama
- **Strukturalne logi** (JSON format)
- **Metryki** włączone dla wszystkich serwisów

## 🚀 Szybki Start

### 1. Automatyczny Setup
```bash
# Szybki start (automatyczna konfiguracja)
./scripts/start-dev.sh
```

### 2. Ręczny Setup
```bash
# Konfiguracja początkowa
./scripts/dev-setup.sh setup

# Uruchomienie aplikacji
./scripts/dev-setup.sh start

# Sprawdzenie statusu
./scripts/dev-setup.sh status
```

## 🔄 Zarządzanie

### Podstawowe Komendy
```bash
# Uruchomienie
./scripts/dev-setup.sh start

# Zatrzymanie
./scripts/dev-setup.sh stop

# Restart
./scripts/dev-setup.sh restart

# Status
./scripts/dev-setup.sh status
```

### Zarządzanie Logami
```bash
# Wszystkie logi
./scripts/dev-setup.sh logs all

# Logi konkretnego serwisu
./scripts/dev-setup.sh logs backend
./scripts/dev-setup.sh logs frontend
./scripts/dev-setup.sh logs ollama

# Logi z określoną liczbą linii
./scripts/dev-setup.sh logs backend 100
```

### Instalacja Modeli AI
```bash
# Zainstaluj modele Ollama
./scripts/dev-setup.sh models
```

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

## 🔍 Debugowanie

### Dostęp do Kontenerów
```bash
# Shell w backend
docker-compose -f docker-compose.dev.yaml exec backend bash

# Shell w frontend
docker-compose -f docker-compose.dev.yaml exec frontend sh

# Redis CLI
docker-compose -f docker-compose.dev.yaml exec redis redis-cli

# PostgreSQL
docker-compose -f docker-compose.dev.yaml exec postgres psql -U foodsave -d foodsave_dev
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

## 📱 Dostępne Endpointy

### Aplikacja
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### AI i Modele
- **Ollama**: http://localhost:11434
- **Ollama API**: http://localhost:11434/api

### Monitoring
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### Baza Danych
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6379

### Health Checks
- **Backend Health**: http://localhost:8000/health
- **Backend Metrics**: http://localhost:8000/metrics
- **Backend Ready**: http://localhost:8000/ready

## 🛠️ Funkcje Development

### Hot Reload
- **Backend**: Automatyczny reload przy zmianach w `./src/`
- **Frontend**: Automatyczny reload przy zmianach w `./myappassistant-chat-frontend/`

### Strukturalne Logowanie
- **JSON format** dla łatwego parsowania
- **Poziomy logowania** (DEBUG, INFO, WARNING, ERROR)
- **Kontekstowe informacje** w logach
- **Rotacja logów** (max 100MB, 10 plików)

### Monitoring w Czasie Rzeczywistym
- **Metryki aplikacji** w Prometheus
- **Dashboardy** w Grafana
- **Agregacja logów** w Loki
- **Alerty** dla problemów

## 🔒 Bezpieczeństwo

### Zmienne Środowiskowe
- **Klucze szyfrowania** dla development
- **JWT tokens** z odpowiednimi czasami wygaśnięcia
- **CORS** skonfigurowany dla development
- **Rate limiting** dla API

### Baza Danych
- **PostgreSQL** z odpowiednimi uprawnieniami
- **Redis** dla cache i sesji
- **Backup** automatyczny

## 📈 Wydajność

### Optymalizacje
- **GPU acceleration** dla modeli AI (jeśli dostępne)
- **Connection pooling** dla bazy danych
- **Cache** w Redis
- **Hot reload** dla szybkiego development

### Monitoring Wydajności
- **Response times** API
- **Memory usage** wszystkich serwisów
- **CPU usage** w czasie rzeczywistym
- **Database performance** metrics

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
./scripts/dev-setup.sh cleanup
./scripts/dev-setup.sh start
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

## 📚 Dokumentacja

### Przewodniki
- **[Przewodnik Developerski](README_DEVELOPMENT.md)** - Kompletny przewodnik
- **[Dokumentacja API](docs/API_REFERENCE.md)** - Wszystkie endpointy
- **[Przewodnik Testowania](docs/TESTING_GUIDE.md)** - Strategie testowania
- **[Monitoring Guide](docs/MONITORING_TELEMETRY_GUIDE.md)** - Monitoring i telemetria

### Skrypty Pomocnicze
- **`scripts/dev-setup.sh`** - Główny skrypt zarządzania
- **`scripts/start-dev.sh`** - Szybki start
- **`scripts/fix_syntax_errors.py`** - Naprawa błędów składniowych

## 🎯 Podsumowanie Funkcji

### ✅ Zaimplementowane
- [x] Pełna konteneryzacja z Docker Compose
- [x] Kompletny monitoring (Prometheus, Grafana, Loki)
- [x] Strukturalne logowanie dla wszystkich serwisów
- [x] Hot reload dla backend i frontend
- [x] Framework testowy z coverage
- [x] Automatyzacja setup i zarządzania
- [x] GPU support dla modeli AI
- [x] Health checks dla wszystkich serwisów
- [x] Backup i recovery procedures
- [x] Security best practices

### 🚀 Korzyści
- **Szybki setup** - Jedna komenda do uruchomienia całego środowiska
- **Pełne logowanie** - Wszystkie logi w jednym miejscu
- **Monitoring w czasie rzeczywistym** - Natychmiastowe wykrywanie problemów
- **Hot reload** - Szybki development bez restartów
- **Izolacja** - Każdy developer ma identyczne środowisko
- **Skalowalność** - Łatwe dodawanie nowych serwisów

---

**🚀 FoodSave AI Development Environment** - Kompletne środowisko gotowe do rozwoju! 🎯

*Ostatnia aktualizacja: Czerwiec 2025* 