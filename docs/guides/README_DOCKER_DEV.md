# FoodSave AI - Docker Development Environment

## 🚀 Szybki Start

### Wymagania
- Docker Engine 19.03.0+
- Docker Compose V2
- Minimum 8GB RAM
- Minimum 20GB wolnego miejsca na dysku
- (Opcjonalnie) NVIDIA GPU z zainstalowanym NVIDIA Container Toolkit

### Uruchomienie środowiska development

```bash
# 1. Przejdź do katalogu projektu
cd myappassistant

# 2. Uruchom środowisko development
./foodsave-dev.sh start

# 3. Sprawdź status
./foodsave-dev.sh status
```

### Dostępne serwisy

Po uruchomieniu środowiska, serwisy będą dostępne pod następującymi adresami:

| Serwis | URL | Port | Opis |
|--------|-----|------|------|
| **Frontend** | http://localhost:5173 | 5173 | React/Vite aplikacja |
| **Backend API** | http://localhost:8000 | 8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | 8000 | Swagger UI |
| **Ollama** | http://localhost:11434 | 11434 | Modele językowe |
| **SQLite** | lokalny plik | lokalny plik | Baza danych |
| **Redis** | localhost:6379 | 6379 | Cache |
| **Prometheus** | http://localhost:9090 | 9090 | Metryki |
| **Grafana** | http://localhost:3001 | 3001 | Dashboardy (admin/admin) |
| **Loki** | http://localhost:3100 | 3100 | Logi |

## 📋 Zarządzanie środowiskiem

### Podstawowe komendy

```bash
# Uruchomienie
./foodsave-dev.sh start              # Wszystkie serwisy
./foodsave-dev.sh start minimal      # Tylko podstawowe serwisy
./foodsave-dev.sh start monitoring   # Z monitoringiem
./foodsave-dev.sh start proxy        # Z nginx proxy

# Zatrzymanie
./foodsave-dev.sh stop

# Status
./foodsave-dev.sh status

# Logi
./foodsave-dev.sh logs               # Wszystkie logi
./foodsave-dev.sh logs backend       # Logi backendu
./foodsave-dev.sh logs frontend      # Logi frontendu

# Restart
./foodsave-dev.sh restart

# Budowanie konkretnego serwisu
./foodsave-dev.sh build backend
./foodsave-dev.sh build frontend

# Czyszczenie
./foodsave-dev.sh clean              # Usuń wszystko
```

### Opcje uruchomienia

#### Minimal (podstawowe serwisy)
```bash
./foodsave-dev.sh start minimal
```
Uruchamia tylko:
- Ollama (modele AI)
- SQLite (baza danych)
- Redis (cache)
- Backend (FastAPI)
- Frontend (React/Vite)

#### Z monitoringiem
```bash
./foodsave-dev.sh start monitoring
```
Dodatkowo uruchamia:
- Prometheus (metryki)
- Grafana (dashboardy)
- Loki (agregacja logów)
- Promtail (zbieranie logów)

#### Z proxy
```bash
./foodsave-dev.sh start proxy
```
Dodatkowo uruchamia:
- Nginx (reverse proxy na portach 80/443)

## 🔧 Konfiguracja

### Zmienne środowiskowe

Plik `.env` jest automatycznie tworzony z `env.dev.example` przy pierwszym uruchomieniu.

Kluczowe zmienne:
```bash
# Baza danych
DATABASE_URL=sqlite+aiosqlite:///./data/foodsave.db

# Ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=gemma3:12b

# Frontend
VITE_API_URL=http://localhost:8000

# Logowanie
LOG_LEVEL=DEBUG
```

### Struktura katalogów

```
myappassistant/
├── docker-compose.dev.yaml          # Konfiguracja Docker Compose
├── foodsave-dev.sh                  # Skrypt zarządzania
├── logs/                            # Logi aplikacji
│   ├── backend/
│   ├── frontend/
│   ├── ollama/
│   ├── postgres/
│   └── redis/
├── data/                            # Dane aplikacji
│   ├── vector_store/
│   └── backups/
├── monitoring/                      # Konfiguracja monitoring
│   ├── prometheus.dev.yml
│   ├── grafana/
│   └── loki-config.yaml
└── scripts/
    └── init-db.sql                  # Inicjalizacja bazy danych
```

## 🐛 Debugowanie

### Logi w czasie rzeczywistym

```bash
# Wszystkie logi
./foodsave-dev.sh logs

# Konkretny serwis
./foodsave-dev.sh logs backend
./foodsave-dev.sh logs frontend
./foodsave-dev.sh logs ollama

# Logi Docker Compose
docker compose -f docker-compose.dev.yaml logs -f
```

### Dostęp do kontenerów

```bash
# Shell w kontenerze backendu
docker exec -it foodsave-backend-dev bash

# Shell w kontenerze frontendu
docker exec -it foodsave-frontend-dev sh

# Shell w bazie danych
docker exec -it foodsave-postgres-dev psql -U foodsave -d foodsave_dev
```

### Sprawdzanie statusu serwisów

```bash
# Status wszystkich kontenerów
docker compose -f docker-compose.dev.yaml ps

# Health checks
docker compose -f docker-compose.dev.yaml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

## 📊 Monitoring

### Grafana Dashboardy

1. Otwórz http://localhost:3001
2. Zaloguj się: `admin/admin`
3. Przejdź do folderu "FoodSave AI"

Dostępne dashboardy:
- **FoodSave AI Dashboard** - główne metryki aplikacji
- **System Metrics** - metryki systemowe

### Prometheus Metryki

- URL: http://localhost:9090
- Endpoint metryk backendu: http://localhost:8000/metrics

### Loki Logi

- URL: http://localhost:3100
- Logi wszystkich serwisów w jednym miejscu

## 🔄 Hot Reload

### Backend (FastAPI)
- Kod źródłowy jest mapowany jako volume
- Uvicorn uruchomiony z `--reload`
- Zmiany w kodzie automatycznie restartują serwer

### Frontend (React/Vite)
- Kod źródłowy jest mapowany jako volume
- Vite dev server z hot reload
- Zmiany w kodzie automatycznie odświeżają przeglądarkę

## 🗄️ Baza danych

### Inicjalizacja
Baza danych jest automatycznie inicjalizowana przy pierwszym uruchomieniu:
- Tworzenie tabel
- Indeksy dla wydajności
- Dane testowe

### Dane testowe
```sql
-- Użytkownik testowy
Username: test_user
Email: test@foodsave.ai
Password: test123

-- Produkty w spiżarni
- Mleko (2l, wygasa za 7 dni)
- Chleb (1szt, wygasa za 3 dni)
- Jabłka (2.5kg, wygasa za 14 dni)
```

### Backup i restore
```bash
# Backup
docker exec foodsave-postgres-dev pg_dump -U foodsave foodsave_dev > backup.sql

# Restore
docker exec -i foodsave-postgres-dev psql -U foodsave foodsave_dev < backup.sql
```

## 🚨 Rozwiązywanie problemów

### Problem z portami
```bash
# Sprawdź zajęte porty
netstat -tulpn | grep :8000
netstat -tulpn | grep :5173

# Zatrzymaj i uruchom ponownie
./foodsave-dev.sh stop
./foodsave-dev.sh start
```

### Problem z pamięcią
```bash
# Sprawdź użycie pamięci
docker stats

# Zatrzymaj niepotrzebne serwisy
./foodsave-dev.sh start minimal
```

### Problem z GPU (Ollama)
```bash
# Sprawdź NVIDIA Container Toolkit
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Uruchom bez GPU
# Edytuj docker-compose.dev.yaml i usuń sekcję deploy dla ollama
```

### Problem z bazą danych
```bash
# Sprawdź logi SQLite
./foodsave-dev.sh logs postgres

# Resetuj bazę danych
docker volume rm foodsave-postgres-data-dev
./foodsave-dev.sh start
```

### Problem z logami
```bash
# Sprawdź uprawnienia
ls -la logs/

# Utwórz katalogi ponownie
mkdir -p logs/{backend,frontend,ollama,postgres,redis}
chmod 755 logs/
```

## 🔧 Zaawansowana konfiguracja

### Modyfikacja Dockerfile'ów

#### Backend
```dockerfile
# src/backend/Dockerfile.dev
FROM python:3.12-slim as base
# ... konfiguracja
```

#### Frontend
```dockerfile
# myappassistant-chat-frontend/Dockerfile.dev
FROM node:18-alpine
# ... konfiguracja
```

### Dodanie nowego serwisu

1. Dodaj serwis do `docker-compose.dev.yaml`
2. Dodaj do skryptu `foodsave-dev.sh`
3. Utwórz katalog logów
4. Dodaj health check

### Customizacja monitoring

#### Prometheus
Edytuj `monitoring/prometheus.dev.yml`

#### Grafana
Edytuj dashboardy w `monitoring/grafana/dashboards/`

#### Loki
Edytuj `monitoring/loki-config.yaml`

## 📝 Przydatne komendy

### Docker
```bash
# Lista kontenerów
docker ps -a --filter "name=foodsave-"

# Lista wolumenów
docker volume ls --filter "name=foodsave-"

# Lista sieci
docker network ls --filter "name=foodsave-"

# Czyszczenie
docker system prune -a
docker volume prune
```

### Logi
```bash
# Ostatnie 100 linii
docker compose -f docker-compose.dev.yaml logs --tail=100

# Logi z timestamp
docker compose -f docker-compose.dev.yaml logs -t

# Logi od konkretnego czasu
docker compose -f docker-compose.dev.yaml logs --since="2024-01-01T00:00:00"
```

### Metryki
```bash
# Statystyki kontenerów
docker stats

# Użycie zasobów
docker system df
```

## 🤝 Contributing

### Dodawanie nowych funkcji

1. Zmodyfikuj kod w odpowiednim katalogu
2. Zmiany automatycznie się załadują (hot reload)
3. Przetestuj funkcjonalność
4. Commituj zmiany

### Debugowanie

1. Użyj `./foodsave-dev.sh logs` do sprawdzenia logów
2. Użyj Grafana do analizy metryk
3. Użyj `docker exec` do dostępu do kontenerów
4. Sprawdź health checks

### Testowanie

```bash
# Uruchom testy backendu
docker exec foodsave-backend-dev python -m pytest

# Uruchom testy frontendu
docker exec foodsave-frontend-dev npm test

# E2E testy
docker exec foodsave-frontend-dev npm run test:e2e
```

---

**FoodSave AI Development Environment** - Kompletne środowisko development w kontenerach Docker z pełną obsługą logów i monitoringiem. 🚀 