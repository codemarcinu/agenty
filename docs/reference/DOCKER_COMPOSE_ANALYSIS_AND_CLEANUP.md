# 🔍 ANALIZA I UPORZĄDKOWANIE KONFIGURACJI DOCKER COMPOSE

## 📊 **PRZEGLĄD PLIKÓW DOCKER COMPOSE**

### **Znalezione Pliki (13 plików)**
1. `docker-compose.yml` - Podstawowa konfiguracja
2. `docker-compose.yaml` - Główna konfiguracja (nowsza)
3. `docker-compose.dev.yaml` - Środowisko deweloperskie
4. `docker-compose.prod.yaml` - Środowisko produkcyjne
5. `docker-compose.test.yaml` - Środowisko testowe
6. `docker-compose.proxy.yaml` - Konfiguracja proxy
7. `docker-compose.optimized.yml` - Zoptymalizowana wersja
8. `docker-compose.monitoring.yaml` - Monitoring
9. `docker-compose.consolidated.yaml` - Skonsolidowana wersja
10. `docker-compose.run.yml` - Uruchomienie
11. `docker-compose.cache.yaml` - Cache
12. `docker-compose.logging.yaml` - Logowanie
13. `docker-compose.backup.yaml` - Backup

---

## 🚨 **PROBLEMY ZIDENTYFIKOWANE**

### **1. DUPLIKACJA I KONFLIKTY**
- **2 główne pliki**: `docker-compose.yml` vs `docker-compose.yaml`
- **Różne mapowania portów** dla tych samych usług
- **Niespójne nazwy kontenerów** i sieci
- **Konflikty portów** między różnymi środowiskami

### **2. MAPOWANIA PORTÓW - ANALIZA**

#### **Backend (FastAPI)**
| Plik | Port Host | Port Container | Status |
|------|-----------|----------------|--------|
| `docker-compose.yml` | `8001` | `8000` | ❌ Konflikt |
| `docker-compose.yaml` | `8000` | `8000` | ✅ Standard |
| `docker-compose.dev.yaml` | `8000` | `8000` | ✅ Standard |
| `docker-compose.prod.yaml` | `8000` | `8000` | ✅ Standard |
| `docker-compose.optimized.yml` | `8001` | `8000` | ❌ Konflikt |

#### **SQLite**
| Plik | Port Host | Port Container | Status |
|------|-----------|----------------|--------|
| `docker-compose.yml` | `lokalny plik` | `lokalny plik` | ✅ Standard |
| `docker-compose.yaml` | `lokalny plik` | `lokalny plik` | ✅ Standard |
| `docker-compose.dev.yaml` | `lokalny plik` | `lokalny plik` | ✅ Standard |
| `docker-compose.prod.yaml` | `lokalny plik` | `lokalny plik` | ⚠️ Produkcja |
| `docker-compose.optimized.yml` | `lokalny plik` | `lokalny plik` | ✅ Standard |

#### **Frontend**
| Plik | Port Host | Port Container | Status |
|------|-----------|----------------|--------|
| `docker-compose.yml` | `3000` | `3000` | ✅ Standard |
| `docker-compose.optimized.yml` | `3000` | `3000` | ✅ Standard |

#### **Redis**
| Plik | Port Host | Port Container | Status |
|------|-----------|----------------|--------|
| Wszystkie pliki | `6379` | `6379` | ✅ Standard |

#### **Ollama**
| Plik | Port Host | Port Container | Status |
|------|-----------|----------------|--------|
| Wszystkie pliki | `11434` | `11434` | ✅ Standard |

---

## 🎯 **REKOMENDOWANE UPORZĄDKOWANIE**

### **1. STANDARDYZACJA PORTÓW**

#### **🔒 ZAREZERWOWANE PORTY**
```yaml
# STANDARDOWE MAPOWANIA
Backend:     8000:8000    # Główny API
Frontend:    3000:3000    # UI
SQLite: lokalny plik    # Development
SQLite: lokalny plik    # Production
Redis:       6379:6379    # Cache
Ollama:      11434:11434  # AI Models
Grafana:     3001:3000    # Monitoring
Prometheus:  9090:9090    # Metrics
Loki:        3100:3100    # Logs
```

### **2. STRUKTURA PLIKÓW**

#### **📁 REKOMENDOWANA STRUKTURA**
```
docker-compose/
├── docker-compose.yaml          # Główny (development)
├── docker-compose.prod.yaml     # Produkcja
├── docker-compose.test.yaml     # Testy
├── docker-compose.monitoring.yaml # Monitoring
└── docker-compose.override.yaml # Override (opcjonalny)
```

### **3. PROFILES SYSTEM**

#### **🎭 PROFILES DLA RÓŻNYCH ŚRODOWISK**
```yaml
# Uruchomienie z profilem
docker-compose --profile development up
docker-compose --profile production up
docker-compose --profile testing up
docker-compose --profile monitoring up
```

---

## 🛠️ **PLAN UPORZĄDKOWANIA**

### **KROK 1: USUNIĘCIE DUPLIKATÓW**
```bash
# Usuń stare pliki
rm docker-compose.yml                    # Stary format
rm docker-compose.optimized.yml          # Zduplikowany
rm docker-compose.consolidated.yaml      # Zduplikowany
rm docker-compose.cache.yaml             # Nieużywany
rm docker-compose.logging.yaml           # Nieużywany
rm docker-compose.backup.yaml            # Nieużywany
rm docker-compose.run.yml                # Nieużywany
```

### **KROK 2: STANDARDYZACJA PORTÓW**
```yaml
# docker-compose.yaml (główny)
services:
  backend:
    ports:
      - "8000:8000"  # STANDARD
  frontend:
    ports:
      - "3000:3000"  # STANDARD
  postgres:
    ports:
      - "5433:5432"  # DEVELOPMENT
  redis:
    ports:
      - "6379:6379"  # STANDARD
  ollama:
    ports:
      - "11434:11434"  # STANDARD
```

### **KROK 3: KONSOLIDACJA KONFIGURACJI**
```yaml
# docker-compose.yaml - GŁÓWNY
version: '3.8'

services:
  # Podstawowe usługi (zawsze uruchomione)
  postgres:
    profiles: [development, production, testing]
    
  redis:
    profiles: [development, production, testing]
    
  ollama:
    profiles: [development, production, testing]
    
  backend:
    profiles: [development, production, testing]
    
  celery_worker:
    profiles: [development, production]
    
  celery_beat:
    profiles: [development, production]
    
  # Monitoring (osobny profil)
  prometheus:
    profiles: [monitoring]
    
  grafana:
    profiles: [monitoring]
    
  loki:
    profiles: [monitoring]
```

---

## 📋 **DETALICZNA ANALIZA PLIKÓW**

### **1. docker-compose.yml (STARY)**
```yaml
# PROBLEMY:
- Port backend: 8001:8000 (niezgodny ze standardem)
- Brak Celery
- Brak Ollama
- Proste konfiguracje
- Brak profiles

# STATUS: DO USUNIĘCIA
```

### **2. docker-compose.yaml (GŁÓWNY)**
```yaml
# ZALETY:
+ Kompletna konfiguracja
+ Wszystkie usługi
+ Health checks
+ Proper networking
+ Volumes

# PROBLEMY:
- Brak profiles
- Brak monitoring
- Brak test environment

# STATUS: PODSTAWOWY (DO ROZSZERZENIA)
```

### **3. docker-compose.dev.yaml**
```yaml
# ZALETY:
+ Profiles system
+ Development optimizations
+ Monitoring included
+ Cache configurations

# PROBLEMY:
- Duplikacja z głównym plikiem
- Różne porty dla backend

# STATUS: DO KONSOLIDACJI
```

### **4. docker-compose.prod.yaml**
```yaml
# ZALETY:
+ Production settings
+ Resource limits
+ Security configurations
+ Proper environment variables

# PROBLEMY:
- SQLite port 5432 (może konfliktować)
- Brak profiles

# STATUS: DO POPRAWY
```

---

## 🔧 **IMPLEMENTACJA ROZWIĄZAŃ**

### **1. NOWY GŁÓWNY PLIK**
```yaml
# docker-compose.yaml
version: '3.8'

services:
  # =============================================================================
  # BAZA DANYCH - SQLITE
  # =============================================================================
  postgres:
    image: postgres:15-alpine
    container_name: foodsave-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-foodsave_dev}
      POSTGRES_USER: ${POSTGRES_USER:-foodsave}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-foodsave_dev_password}
    volumes:
      - sqlite_data:/var/lib/sqlite/data
    ports:
      - "5433:5432"  # STANDARD DEVELOPMENT PORT
    networks:
      - foodsave-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-foodsave}"]
      interval: 30s
      timeout: 10s
      retries: 3
    profiles:
      - development
      - production
      - testing

  # =============================================================================
  # CACHE - REDIS
  # =============================================================================
  redis:
    image: redis:7-alpine
    container_name: foodsave-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"  # STANDARD PORT
    networks:
      - foodsave-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    profiles:
      - development
      - production
      - testing

  # =============================================================================
  # AI MODELS - OLLAMA
  # =============================================================================
  ollama:
    image: ollama/ollama:latest
    container_name: foodsave-ollama
    restart: unless-stopped
    environment:
      OLLAMA_HOST: ${OLLAMA_HOST:-0.0.0.0}
      OLLAMA_KEEP_ALIVE: ${OLLAMA_KEEP_ALIVE:-24h}
    volumes:
      - ollama_data:/root/.ollama
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "11434:11434"  # STANDARD PORT
    networks:
      - foodsave-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "pgrep", "ollama"]
      interval: 30s
      timeout: 10s
      retries: 3
    profiles:
      - development
      - production
      - testing

  # =============================================================================
  # BACKEND - FASTAPI
  # =============================================================================
  backend:
    build:
      context: .
      dockerfile: ${BACKEND_DOCKERFILE:-src/backend/Dockerfile}
    container_name: foodsave-backend
    restart: unless-stopped
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - DATABASE_URL=${DATABASE_URL:-postgresql+asyncpg://foodsave:foodsave_dev_password@postgres:5432/foodsave_dev}
      - REDIS_URL=${REDIS_URL:-redis://redis:6379}
      - OLLAMA_URL=${OLLAMA_URL:-http://ollama:11434}
      - PORT=${PORT:-8000}
    volumes:
      - ./src:/app/src:ro
      - ./data:/app/data
      - ./logs/backend:/app/logs
      - ./temp_uploads:/app/temp_uploads
    ports:
      - "8000:8000"  # STANDARD PORT
    networks:
      - foodsave-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      ollama:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    profiles:
      - development
      - production
      - testing

  # =============================================================================
  # CELERY WORKER
  # =============================================================================
  celery_worker:
    build:
      context: .
      dockerfile: ${BACKEND_DOCKERFILE:-src/backend/Dockerfile}
    container_name: foodsave-celery-worker
    restart: unless-stopped
    command: celery -A src.backend.config.celery_config worker --loglevel=info
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - DATABASE_URL=${DATABASE_URL:-postgresql+asyncpg://foodsave:foodsave_dev_password@postgres:5432/foodsave_dev}
      - REDIS_URL=${REDIS_URL:-redis://redis:6379}
    volumes:
      - ./src:/app/src:ro
      - ./data:/app/data
      - ./logs/backend:/app/logs
    networks:
      - foodsave-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "celery -A src.backend.config.celery_config inspect ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    profiles:
      - development
      - production

  # =============================================================================
  # CELERY BEAT
  # =============================================================================
  celery_beat:
    build:
      context: .
      dockerfile: ${BACKEND_DOCKERFILE:-src/backend/Dockerfile}
    container_name: foodsave-celery-beat
    restart: unless-stopped
    command: celery -A src.backend.config.celery_config beat --loglevel=info
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - DATABASE_URL=${DATABASE_URL:-postgresql+asyncpg://foodsave:foodsave_dev_password@postgres:5432/foodsave_dev}
      - REDIS_URL=${REDIS_URL:-redis://redis:6379}
    volumes:
      - ./src:/app/src:ro
      - ./data:/app/data
      - ./logs/backend:/app/logs
    networks:
      - foodsave-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "pgrep -f 'celery.*beat'"]
      interval: 30s
      timeout: 10s
      retries: 3
    profiles:
      - development
      - production

# =============================================================================
# NETWORKS
# =============================================================================
networks:
  foodsave-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

# =============================================================================
# VOLUMES
# =============================================================================
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  ollama_data:
    driver: local
```

### **2. PLIK PRODUKCYJNY**
```yaml
# docker-compose.prod.yaml
version: '3.8'

services:
  postgres:
    ports:
      - "5432:5432"  # PRODUCTION PORT
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  backend:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
      replicas: 2

  celery_worker:
    command: celery -A src.backend.config.celery_config worker --loglevel=info --concurrency=4
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
      replicas: 2
```

### **3. PLIK MONITORING**
```yaml
# docker-compose.monitoring.yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: foodsave-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    networks:
      - foodsave-network
    profiles:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: foodsave-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - foodsave-network
    profiles:
      - monitoring

  loki:
    image: grafana/loki:latest
    container_name: foodsave-loki
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
      - ./monitoring/loki:/etc/loki
    networks:
      - foodsave-network
    profiles:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

---

## 📝 **INSTRUKCJE UŻYTKOWANIA**

### **Uruchomienie Różnych Środowisk**
```bash
# Development (domyślne)
docker-compose up

# Production
docker-compose -f docker-compose.prod.yaml up

# Testing
docker-compose --profile testing up

# Monitoring
docker-compose --profile monitoring up

# Wszystko
docker-compose --profile all up
```

### **Sprawdzanie Portów**
```bash
# Sprawdź zajęte porty
netstat -tulpn | grep -E ':(8000|3000|5433|6379|11434)'

# Sprawdź kontenery
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### **Czyszczenie**
```bash
# Zatrzymaj wszystkie kontenery
docker-compose down

# Usuń wolumeny
docker-compose down -v

# Usuń obrazy
docker-compose down --rmi all
```

---

## ✅ **CHECKLISTA UPORZĄDKOWANIA**

- [ ] Usuń duplikaty plików Docker Compose
- [ ] Ustandaryzuj mapowania portów
- [ ] Wprowadź system profiles
- [ ] Skonsoliduj konfiguracje
- [ ] Zaktualizuj dokumentację
- [ ] Przetestuj wszystkie środowiska
- [ ] Zaktualizuj skrypty uruchamiania
- [ ] Sprawdź kompatybilność z istniejącymi skryptami

---

**Ostatnia aktualizacja**: 2025-01-07
**Status**: Analiza zakończona, gotowy do implementacji 