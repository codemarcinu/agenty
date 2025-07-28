# Gmail Inbox Zero Container Guide

## Przegląd

Ten przewodnik opisuje jak uruchomić ulepszony system Gmail Inbox Zero w kontenerach Docker z wszystkimi nowymi funkcjonalnościami.

## 🚀 Nowe Funkcjonalności

### Backend Ulepszenia
- **SmartCache**: Inteligentne cache'owanie z metadanymi i LRU
- **EnhancedRateLimiter**: Adaptacyjne rate limiting z exponential backoff
- **EnhancedPrefilterEngine**: ML-based klasyfikacja emaili
- **BatchProcessor**: Przetwarzanie wsadowe operacji Gmail
- **Asynchroniczne operacje**: Szybsze przetwarzanie z retry logic

### Frontend Ulepszenia
- **Batch Mode**: Masowe operacje na emailach
- **Keyboard Shortcuts**: Skróty klawiszowe (Ctrl+A, Ctrl+B, Space, Escape)
- **Gamification**: System poziomów, XP, odznaki
- **Responsive Design**: Pełna responsywność
- **Progress Tracking**: Śledzenie postępów w czasie rzeczywistym

## 📋 Wymagania

### System
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM (minimum)
- 4 CPU cores (minimum)
- 20GB wolnego miejsca

### GPU (Opcjonalne)
- NVIDIA GPU z 12GB+ VRAM
- CUDA 11.8+
- nvidia-docker2

## 🛠️ Instalacja

### 1. Szybki Start

```bash
# Uruchom system w trybie production
./scripts/deployment/start-gmail-inbox-zero.sh

# Lub w trybie development
./scripts/deployment/start-gmail-inbox-zero.sh development
```

### 2. Ręczna Instalacja

```bash
# Stwórz katalogi
mkdir -p data/gmail_cache data/gmail_logs data/gmail_batch_operations

# Uruchom kontenery
docker-compose up -d

# Sprawdź status
docker-compose ps
```

## 🔧 Konfiguracja

### Zmienne Środowiskowe Backend

| Zmienna | Opis | Domyślna Wartość |
|---------|------|------------------|
| `GMAIL_INBOX_ZERO_ENABLED` | Włącz/wyłącz system | `true` |
| `GMAIL_CACHE_TTL_HOURS` | Czas życia cache | `24` |
| `GMAIL_RATE_LIMIT_PER_SECOND` | Limit requestów na sekundę | `10` |
| `GMAIL_BATCH_SIZE` | Rozmiar batch'a | `100` |
| `GMAIL_PREFILTER_ENABLED` | Włącz prefilter | `true` |
| `GMAIL_SMART_CACHE_SIZE` | Rozmiar smart cache | `1000` |
| `GMAIL_EXPONENTIAL_BACKOFF_MAX_RETRIES` | Maksymalne retry | `3` |
| `GMAIL_QUOTA_EXCEEDED_BACKOFF_MULTIPLIER` | Mnożnik backoff | `1.5` |
| `GMAIL_ADAPTIVE_RATE_LIMITING` | Adaptacyjne rate limiting | `true` |
| `GMAIL_SUCCESS_RATE_THRESHOLD` | Próg sukcesu | `0.95` |
| `GMAIL_FAILURE_RATE_THRESHOLD` | Próg porażki | `0.8` |
| `GMAIL_BATCH_PROCESSING_ENABLED` | Włącz batch processing | `true` |
| `GMAIL_CONCURRENT_SEMAPHORE_LIMIT` | Limit concurrent requests | `5` |
| `GMAIL_PREFILTER_CONFIDENCE_THRESHOLD` | Próg pewności prefilter | `0.8` |
| `GMAIL_ML_CLASSIFIER_ENABLED` | Włącz ML classifier | `true` |

### Zmienne Środowiskowe Frontend

| Zmienna | Opis | Domyślna Wartość |
|---------|------|------------------|
| `NEXT_PUBLIC_GMAIL_INBOX_ZERO_ENABLED` | Włącz system | `true` |
| `NEXT_PUBLIC_GMAIL_BATCH_MODE_ENABLED` | Włącz batch mode | `true` |
| `NEXT_PUBLIC_GMAIL_KEYBOARD_SHORTCUTS_ENABLED` | Włącz skróty | `true` |
| `NEXT_PUBLIC_GMAIL_GAMIFICATION_ENABLED` | Włącz gamification | `true` |
| `NEXT_PUBLIC_GMAIL_PROGRESS_TRACKING_ENABLED` | Włącz tracking | `true` |
| `NEXT_PUBLIC_GMAIL_RESPONSIVE_DESIGN_ENABLED` | Włącz responsive | `true` |
| `NEXT_PUBLIC_GMAIL_PERFORMANCE_METRICS_ENABLED` | Włącz metryki | `true` |

## 🎮 Użycie

### 1. Dostęp do Interfejsu

```
Frontend: http://localhost:8085
Gmail Inbox Zero: http://localhost:8085/gmail-inbox-zero
Backend API: http://localhost:8000
```

### 2. Skróty Klawiszowe

| Skrót | Akcja |
|-------|-------|
| `Ctrl+A` | Zaznacz wszystkie emaile |
| `Ctrl+B` | Przełącz tryb batch |
| `Space` | Zaznacz/odznacz email w trybie batch |
| `Escape` | Wyjdź z trybu batch |
| `Ctrl+Enter` | Wykonaj operacje batch |
| `Ctrl+Z` | Cofnij ostatnią operację |

### 3. Batch Operations

1. **Włącz tryb batch**: `Ctrl+B` lub przycisk "Batch Mode"
2. **Zaznacz emaile**: Kliknij lub użyj `Space`
3. **Wybierz operację**: Archive, Delete, Label, Mark Read
4. **Wykonaj**: `Ctrl+Enter` lub przycisk "Execute Batch"

### 4. Gamification

- **Poziomy**: Zdobywaj XP za operacje
- **Odznaki**: Unlockuj odznaki za osiągnięcia
- **Streaks**: Utrzymuj codzienne sesje
- **Efficiency**: Śledź efektywność

## 📊 Monitoring

### 1. Logi

```bash
# Wszystkie logi
./scripts/deployment/start-gmail-inbox-zero.sh logs

# Logi konkretnego serwisu
docker-compose logs backend
docker-compose logs frontend
```

### 2. Status Serwisów

```bash
# Status wszystkich serwisów
./scripts/deployment/start-gmail-inbox-zero.sh status

# Szczegółowy status
docker-compose ps
```

### 3. Metryki Wydajności

```bash
# Sprawdź użycie zasobów
docker stats

# Sprawdź cache hit rate
curl http://localhost:8000/api/v1/gmail/cache/stats
```

## 🧪 Testowanie

### 1. Uruchom Testy

```bash
# Wszystkie testy Gmail Inbox Zero
./scripts/deployment/start-gmail-inbox-zero.sh test

# Konkretne testy
docker-compose exec backend python -m pytest tests/unit/test_gmail_inbox_zero_agent.py -v
```

### 2. Testy Wydajnościowe

```bash
# Test cache performance
docker-compose exec backend python -m pytest tests/performance/test_gmail_cache_performance.py

# Test rate limiting
docker-compose exec backend python -m pytest tests/performance/test_gmail_rate_limiting.py
```

## 🔧 Troubleshooting

### 1. Problemy z Uruchomieniem

```bash
# Sprawdź logi
docker-compose logs

# Restart serwisów
./scripts/deployment/start-gmail-inbox-zero.sh restart

# Clean restart
./scripts/deployment/start-gmail-inbox-zero.sh clean
./scripts/deployment/start-gmail-inbox-zero.sh start
```

### 2. Problemy z Gmail API

```bash
# Sprawdź konfigurację Gmail
docker-compose exec backend python -c "from src.backend.agents.gmail_inbox_zero_agent import GmailInboxZeroAgent; print('Gmail config OK')"

# Test Gmail API connection
curl http://localhost:8000/api/v1/gmail/test
```

### 3. Problemy z Cache

```bash
# Wyczyść cache
docker-compose exec redis redis-cli FLUSHALL

# Sprawdź cache stats
curl http://localhost:8000/api/v1/gmail/cache/stats
```

### 4. Problemy z Rate Limiting

```bash
# Sprawdź rate limiter stats
curl http://localhost:8000/api/v1/gmail/rate-limiter/stats

# Reset rate limiter
curl -X POST http://localhost:8000/api/v1/gmail/rate-limiter/reset
```

## 📈 Optymalizacja

### 1. Production Settings

```yaml
# docker-compose.yaml
environment:
  - GMAIL_RATE_LIMIT_PER_SECOND=10
  - GMAIL_BATCH_SIZE=100
  - GMAIL_SMART_CACHE_SIZE=1000
  - GMAIL_CONCURRENT_SEMAPHORE_LIMIT=5
```

### 2. Development Settings

```yaml
# docker-compose.dev.yaml
environment:
  - GMAIL_RATE_LIMIT_PER_SECOND=5
  - GMAIL_BATCH_SIZE=10
  - GMAIL_SMART_CACHE_SIZE=100
  - GMAIL_CONCURRENT_SEMAPHORE_LIMIT=2
  - GMAIL_DEBUG_MODE=true
```

### 3. Resource Limits

```yaml
deploy:
  resources:
    limits:
      memory: 6G
      cpus: '3.0'
    reservations:
      memory: 3G
      cpus: '1.5'
```

## 🔒 Bezpieczeństwo

### 1. Gmail API Credentials

```bash
# Stwórz plik credentials
mkdir -p config
touch config/gmail_credentials.json

# Dodaj credentials do .gitignore
echo "config/gmail_credentials.json" >> .gitignore
```

### 2. Environment Variables

```bash
# Stwórz .env file
cp .env.example .env

# Edytuj zmienne
nano .env
```

### 3. Network Security

```yaml
# docker-compose.yaml
networks:
  foodsave-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 📚 Dodatkowe Zasoby

### 1. Dokumentacja API

- [Gmail Inbox Zero API Reference](../reference/GMAIL_INBOX_ZERO_API.md)
- [Agent Configuration Guide](../reference/AGENTS_GUIDE.md)

### 2. Development

- [Development Setup Guide](../development/BACKEND_LOCAL_SETUP.md)
- [Testing Strategy](../development/TESTING_STRATEGY.md)

### 3. Deployment

- [Production Deployment](../deployment/PRODUCTION_DEPLOYMENT.md)
- [Monitoring Setup](../deployment/MONITORING_SETUP.md)

## 🤝 Wsparcie

### 1. Logi i Debugging

```bash
# Szczegółowe logi
docker-compose logs -f backend

# Debug mode
docker-compose exec backend python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

### 2. Kontakt

- **Issues**: GitHub Issues
- **Documentation**: `/docs` folder
- **Tests**: `/tests` folder

---

*Ostatnia aktualizacja: 2025-01-21*
*Wersja: 2.0.1 - Enhanced Gmail Inbox Zero* 