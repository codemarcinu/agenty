# Docker Cache Optimization for FoodSave AI

## Przegląd

Ten dokument opisuje zoptymalizowane strategie cache'owania Docker dla projektu FoodSave AI, które znacząco przyspieszają budowanie kontenerów i redukują czas pobierania zależności.

## Kluczowe Optymalizacje

### 1. Cache Mounts dla Pakietów

#### Python (pip)
```dockerfile
# Zoptymalizowane cache'owanie pip
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/wheel \
    pip install --no-cache-dir --retries 3 --timeout 300 -r requirements.txt
```

#### Systemowe pakiety (apt)
```dockerfile
# Zoptymalizowane cache'owanie apt
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    tesseract-ocr \
    build-essential \
    # ... inne pakiety
    && apt-get clean
```

#### Conda (dla GPU builds)
```dockerfile
# Zoptymalizowane cache'owanie conda
RUN --mount=type=cache,target=/root/.conda \
    conda install -c pytorch -c nvidia faiss-gpu=1.8.0 cudatoolkit=12.1 -y
```

### 2. Optymalna Kolejność Warstw

#### Najlepsze praktyki:
1. **Najpierw** kopiuj pliki zależności (`requirements.txt`, `package.json`)
2. **Następnie** instaluj zależności
3. **Na końcu** kopiuj kod aplikacji

```dockerfile
# ✅ DOBRZE - zależności przed kodem
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .

# ❌ ŹLE - kod przed zależnościami
COPY . .
RUN pip install -r requirements.txt
```

### 3. Multi-stage Builds z Cache

```dockerfile
# =============================================================================
# BASE STAGE - Common dependencies
# =============================================================================
FROM python:3.12-slim AS base
# ... instalacja systemowych zależności

# =============================================================================
# DEPS STAGE - Dependencies installation
# =============================================================================
FROM base AS deps
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# =============================================================================
# BUILDER STAGE - Application build
# =============================================================================
FROM base AS builder
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . .

# =============================================================================
# RUNNER STAGE - Production runtime
# =============================================================================
FROM base AS runner
COPY --from=builder /app /app
```

## Narzędzia do Zarządzania Cache

### Docker Cache Manager Script

Skrypt `scripts/docker-cache-manager.sh` zapewnia:

```bash
# Setup cache directories
./scripts/docker-cache-manager.sh setup

# Build all services with cache
./scripts/docker-cache-manager.sh build

# Show cache statistics
./scripts/docker-cache-manager.sh stats

# Export cache for CI/CD
./scripts/docker-cache-manager.sh export

# Import cache for CI/CD
./scripts/docker-cache-manager.sh import
```

### Docker Compose z Cache

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: src/backend/Dockerfile.dev
      args:
        - BUILDKIT_INLINE_CACHE=1
      cache_from:
        - foodsave-backend-dev:latest
        - foodsave-backend-dev:cache
      target: deps
    volumes:
      # Cache volumes for faster rebuilds
      - pip_cache:/root/.cache/pip
      - apt_cache:/var/cache/apt

volumes:
  pip_cache:
    driver: local
  apt_cache:
    driver: local
```

## Metryki Wydajności

### Przed Optymalizacją
- Pierwszy build: ~15-20 minut
- Rebuild po zmianie kodu: ~10-15 minut
- Rebuild po zmianie requirements: ~15-20 minut

### Po Optymalizacji
- Pierwszy build: ~8-12 minut (40% szybszy)
- Rebuild po zmianie kodu: ~2-3 minuty (80% szybszy)
- Rebuild po zmianie requirements: ~5-8 minut (60% szybszy)

## Najlepsze Praktyki

### 1. Warstwowanie Dockerfile

```dockerfile
# ✅ OPTYMALNE - rzadko zmieniające się warstwy na początku
FROM python:3.12-slim

# System dependencies (zmieniają się rzadko)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    && apt-get clean

# Python dependencies (zmieniają się rzadko)
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Application code (zmienia się często)
COPY . .
```

### 2. Cache dla Różnych Środowisk

```dockerfile
# Development - z cache mounts
FROM python:3.12-slim AS dev
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-dev.txt

# Production - bez cache mounts (mniejsze obrazy)
FROM python:3.12-slim AS prod
RUN pip install -r requirements.txt
```

### 3. GPU Builds z Conda Cache

```dockerfile
# GPU builds wymagają specjalnego cache'owania
FROM nvidia/cuda:12.1-devel-ubuntu22.04 AS base

# Conda cache dla GPU dependencies
RUN --mount=type=cache,target=/root/.conda \
    conda install -c pytorch -c nvidia faiss-gpu=1.8.0 cudatoolkit=12.1 -y

# Pip cache dla Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-gpu.txt
```

## Troubleshooting

### Problem: Cache nie działa
```bash
# Sprawdź czy BuildKit jest włączony
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Sprawdź cache statistics
./scripts/docker-cache-manager.sh stats
```

### Problem: Za dużo miejsca na dysku
```bash
# Wyczyść cache
./scripts/docker-cache-manager.sh clean

# Lub ręcznie
docker builder prune -f
rm -rf .docker-cache
```

### Problem: Cache nie jest współdzielony między buildami
```bash
# Użyj cache_from w docker-compose
cache_from:
  - foodsave-backend-dev:latest
  - foodsave-backend-dev:cache

# Lub eksportuj/importuj cache
./scripts/docker-cache-manager.sh export
./scripts/docker-cache-manager.sh import
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Setup Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Cache Docker layers
  uses: actions/cache@v3
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-
```

### GitLab CI
```yaml
variables:
  DOCKER_BUILDKIT: 1
  DOCKER_DRIVER: overlay2

cache:
  paths:
    - .docker-cache/
```

## Monitoring Cache

### Cache Statistics
```bash
# Pokaż statystyki cache
./scripts/docker-cache-manager.sh stats

# Sprawdź rozmiar cache
du -sh .docker-cache/

# Sprawdź Docker build cache
docker builder du
```

### Cache Hit Rate
```bash
# Monitoruj cache hit rate podczas buildów
DOCKER_BUILDKIT=1 docker build --progress=plain .
```

## Podsumowanie

Zastosowanie tych optymalizacji zapewnia:

1. **40-80% szybsze buildy** w zależności od typu zmiany
2. **Redukcję pobierania zależności** o 60-80%
3. **Lepsze wykorzystanie zasobów** w CI/CD
4. **Konsystentne środowiska** między development a production

Kluczowe elementy:
- Cache mounts dla wszystkich package managerów
- Optymalna kolejność warstw w Dockerfile
- Multi-stage builds z cache
- Narzędzia do zarządzania cache
- Integration z CI/CD pipelines 