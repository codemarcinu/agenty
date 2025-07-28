# 🔓 Development Authentication Guide

## Przegląd

Ten dokument opisuje implementację trybu deweloperskiego z wyłączoną autoryzacją w projekcie FoodSave AI. Rozwiązanie pozwala na szybki development bez konieczności zarządzania tokenami autoryzacyjnymi.

## 🎯 Cel Rozwiązania

### Problem
- Autoryzacja blokuje szybki development
- Trudność w testowaniu endpointów
- Konieczność zarządzania tokenami podczas programowania

### Rozwiązanie
- **Tryb deweloperski** z wyłączoną autoryzacją
- **Zmienne środowiskowe** do kontroli trybu
- **Bezpieczne przełączanie** między trybami
- **Zachowanie bezpieczeństwa** w produkcji

## 🛠️ Implementacja

### 1. Middleware Autoryzacji

Zmodyfikowany `AuthMiddleware` w `src/backend/auth/auth_middleware.py`:

```python
class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths: list[str] | None = None) -> None:
        super().__init__(app)
        
        # Development mode configuration
        self.disable_auth = os.getenv("DISABLE_AUTH", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "production")
        
        if self.disable_auth and self.environment == "development":
            logger.info("🔓 Development mode: Authentication disabled")
        else:
            logger.info("🔒 Production mode: Authentication enabled")

    async def dispatch(self, request: Request, call_next) -> Response:
        # 🔓 DEVELOPMENT MODE: Disable authentication
        if self.disable_auth and self.environment == "development":
            logger.debug(f"🔓 Development mode: Bypassing auth for {path}")
            # Set mock user for development
            request.state.user = {
                "sub": "dev_user",
                "email": "dev@foodsave.ai",
                "roles": ["admin", "user"],
                "dev_mode": True
            }
            request.state.user_id = "dev_user"
            request.state.user_roles = ["admin", "user"]
            return await call_next(request)
        
        # 🔒 PRODUCTION MODE: Normal authentication
        # ... normal auth logic
```

### 2. Konfiguracja Środowiska

#### Zmienne środowiskowe:

```bash
# Development mode
DISABLE_AUTH=true
ENVIRONMENT=development

# Production mode
DISABLE_AUTH=false
ENVIRONMENT=production
```

#### Plik `env.dev.example`:

```bash
# =============================================================================
# AUTHENTICATION SETTINGS
# =============================================================================
DISABLE_AUTH=true
ENVIRONMENT=development

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
APP_NAME=FoodSave AI (Development)
APP_VERSION=2.0.0-dev
DEBUG=true
LOG_LEVEL=DEBUG
```

### 3. Docker Compose

Aktualizacja `docker-compose.dev.yaml`:

```yaml
services:
  backend:
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - DISABLE_AUTH=${DISABLE_AUTH:-true}
      - LOG_LEVEL=${LOG_LEVEL:-DEBUG}
      # ... other settings
```

### 4. GUI Client

Zmodyfikowany `BackendClient` w `gui/core/backend_client.py`:

```python
class BackendClient(QObject):
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        # Development mode configuration
        self.is_dev_mode = os.getenv("DISABLE_AUTH", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "production")
        
        if self.is_dev_mode and self.environment == "development":
            self.logger.info("🔓 Development mode: Authentication disabled")
        else:
            self.logger.info("🔒 Production mode: Authentication enabled")

    def _get_headers(self) -> dict[str, str]:
        """Get headers for requests, including authentication if needed"""
        headers = {
            "User-Agent": "FoodSave-AI-GUI/2.0.0",
            "Accept": "application/json",
        }
        
        # Add authentication headers only in production mode
        if not (self.is_dev_mode and self.environment == "development"):
            # TODO: Add token-based authentication when implemented
            pass
            
        return headers
```

## 🚀 Uruchomienie

### Szybki Start

1. **Skopiuj konfigurację:**
   ```bash
   cp env.dev.example .env
   ```

2. **Uruchom w trybie deweloperskim:**
   ```bash
   ./scripts/development/start-dev-mode.sh
   ```

### Ręczne Uruchomienie

1. **Ustaw zmienne środowiskowe:**
   ```bash
   export DISABLE_AUTH=true
   export ENVIRONMENT=development
   export PYTHONPATH="$(pwd)/src:$(pwd)"
   ```

2. **Uruchom backend:**
   ```bash
   cd src/backend
   python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Uruchom GUI:**
   ```bash
   python3 gui/simplified_chat_app.py
   ```

## 🔧 Konfiguracja

### Tryby Pracy

#### 🔓 Development Mode
```bash
DISABLE_AUTH=true
ENVIRONMENT=development
```

**Zalety:**
- ✅ Szybki development
- ✅ Brak konieczności tokenów
- ✅ Automatyczny mock user
- ✅ Pełny dostęp do API

#### 🔒 Production Mode
```bash
DISABLE_AUTH=false
ENVIRONMENT=production
```

**Zalety:**
- ✅ Pełne bezpieczeństwo
- ✅ Autoryzacja JWT
- ✅ Kontrola dostępu
- ✅ Audit logging

### Endpointy Publiczne

Następujące endpointy są zawsze dostępne (bez autoryzacji):

```python
exclude_paths = [
    "/docs",           # Swagger UI
    "/redoc",          # ReDoc
    "/openapi.json",   # OpenAPI schema
    "/health",         # Health check
    "/ready",          # Readiness probe
    "/metrics",        # Prometheus metrics
    "/auth/login",     # Login endpoint
    "/auth/register",  # Registration
    "/auth/refresh",   # Token refresh
    # ... WebSocket endpoints
    "/ws/dashboard",
    "/ws/status",
    # ... API v2 endpoints
    "/api/v2/weather",
    "/api/v2/receipts",
    "/api/v2/inventory",
    "/api/v2/chat",
]
```

## 🔍 Monitoring i Logowanie

### Logi Development

```python
# W trybie deweloperskim
logger.info("🔓 Development mode: Authentication disabled")
logger.debug(f"🔓 Development mode: Bypassing auth for {path}")
```

### Logi Production

```python
# W trybie produkcyjnym
logger.info("🔒 Production mode: Authentication enabled")
logger.debug(f"Authenticated user {payload.get('sub')} for {request.url.path}")
```

### Mock User w Development

```python
request.state.user = {
    "sub": "dev_user",
    "email": "dev@foodsave.ai",
    "roles": ["admin", "user"],
    "dev_mode": True
}
```

## 🛡️ Bezpieczeństwo

### Środki Bezpieczeństwa

1. **Walidacja środowiska:**
   ```python
   if self.disable_auth and self.environment == "development":
       # Tylko w development
   ```

2. **Logowanie prób dostępu:**
   ```python
   logger.debug(f"🔓 Development mode: Bypassing auth for {path}")
   ```

3. **Dokumentacja endpointów:**
   - Oznaczone endpointy publiczne
   - Dokumentacja wymagań autoryzacji

4. **Kontrola wdrożenia:**
   - Automatyczne sprawdzanie zmiennych
   - Ostrzeżenia w logach

### Checklist Bezpieczeństwa

- [ ] `DISABLE_AUTH=true` tylko z `ENVIRONMENT=development`
- [ ] Logowanie wszystkich prób dostępu
- [ ] Dokumentacja endpointów
- [ ] Testy bezpieczeństwa
- [ ] Monitoring prób dostępu

## 🧪 Testowanie

### Testy Development Mode

```python
def test_development_mode():
    """Test development mode authentication bypass"""
    os.environ["DISABLE_AUTH"] = "true"
    os.environ["ENVIRONMENT"] = "development"
    
    # Test that auth is bypassed
    response = client.get("/api/agents")
    assert response.status_code == 200
```

### Testy Production Mode

```python
def test_production_mode():
    """Test production mode authentication"""
    os.environ["DISABLE_AUTH"] = "false"
    os.environ["ENVIRONMENT"] = "production"
    
    # Test that auth is required
    response = client.get("/api/agents")
    assert response.status_code == 401
```

## 📊 Monitoring

### Metryki

- **Auth bypass count:** Liczba pominiętych autoryzacji
- **Dev mode usage:** Czas w trybie deweloperskim
- **Security events:** Próby dostępu bez autoryzacji

### Alerty

- **Development mode in production**
- **Auth bypass in production**
- **Unauthorized access attempts**

## 🔄 Migracja

### Z Development do Production

1. **Zmiana zmiennych:**
   ```bash
   DISABLE_AUTH=false
   ENVIRONMENT=production
   ```

2. **Testowanie autoryzacji:**
   ```bash
   # Test login
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"password"}'
   ```

3. **Weryfikacja endpointów:**
   ```bash
   # Test protected endpoint
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/agents
   ```

## 🚨 Troubleshooting

### Problem: Backend nie startuje

**Rozwiązanie:**
```bash
# Sprawdź zmienne środowiskowe
echo $DISABLE_AUTH
echo $ENVIRONMENT

# Uruchom z debug
DISABLE_AUTH=true ENVIRONMENT=development python3 -m uvicorn backend.main:app --reload
```

### Problem: GUI nie łączy się z backendem

**Rozwiązanie:**
```bash
# Sprawdź czy backend działa
curl http://localhost:8000/health

# Sprawdź logi
tail -f logs/backend/backend_dev.log
```

### Problem: Autoryzacja nadal wymagana

**Rozwiązanie:**
```bash
# Sprawdź zmienne środowiskowe
export DISABLE_AUTH=true
export ENVIRONMENT=development

# Restart backend
pkill -f uvicorn
python3 -m uvicorn backend.main:app --reload
```

## 📚 Dodatkowe Zasoby

### Dokumentacja

- [FastAPI Authentication](https://fastapi.tiangolo.com/tutorial/security/)
- [Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
- [Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

### Przykłady

- [Development Setup](scripts/development/start-dev-mode.sh)
- [Environment Config](env.dev.example)
- [Docker Config](docker-compose.dev.yaml)

### Narzędzia

- **Skrypt uruchamiania:** `./scripts/development/start-dev-mode.sh`
- **Konfiguracja:** `env.dev.example`
- **Docker:** `docker-compose.dev.yaml`

## 🎯 Podsumowanie

### Zalety Rozwiązania

✅ **Szybkość developmentu** - Brak blokad autoryzacyjnych  
✅ **Bezpieczeństwo produkcyjne** - Autoryzacja w produkcji  
✅ **Elastyczność** - Łatwe przełączanie trybów  
✅ **Zgodność z najlepszymi praktykami** - Zmienne środowiskowe  
✅ **Monitoring** - Logowanie i metryki  
✅ **Dokumentacja** - Kompletna dokumentacja  

### Użycie

```bash
# Development
./scripts/development/start-dev-mode.sh

# Production
DISABLE_AUTH=false ENVIRONMENT=production python3 -m uvicorn backend.main:app
```

To rozwiązanie zapewnia optymalne doświadczenie developmentu przy zachowaniu pełnego bezpieczeństwa w środowisku produkcyjnym. 