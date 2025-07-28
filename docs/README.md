# FoodSave AI - Osobisty Asystent AI

## 🚀 Szybki start

### 1. Uruchomienie aplikacji
```bash
# Uruchom backend
python run_backend.py

# Sprawdź czy działa
curl http://localhost:8000/health
```

### 2. Dostępne agenty
```bash
# Lista agentów
curl http://localhost:8000/api/agents/agents

# Uruchom agenta
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "agent_name", "task": "zadanie"}'
```

## 📧 Agent Gmail Inbox Zero

### Konfiguracja OAuth 2.0
1. Utwórz projekt w Google Cloud Console
2. Włącz Gmail API
3. Utwórz OAuth 2.0 Client ID
4. Dodaj URI przekierowania:
   ```
   http://localhost:8002
   http://localhost:8003
   http://localhost:8080
   http://localhost:8081
   http://localhost:8082
   ```

### Test agenta Gmail
```bash
# Test podstawowy
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "gmail_inbox_zero", "task": "Pobierz statystyki inbox"}'

# Test z operacją
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "gmail_inbox_zero", "task": "Analizuj email", "operation": "analyze", "message_id": "email_id"}'
```

### Dostępne operacje Gmail:
- `analyze` - analiza emaila
- `label` - dodawanie labeli
- `archive` - archiwizacja
- `delete` - usuwanie
- `mark_read` - oznaczanie jako przeczytane
- `star` - dodawanie gwiazdki
- `learn` - uczenie się z interakcji

## 🔧 Konfiguracja

### Pliki konfiguracyjne
- `src/gmail_auth.json` - Konfiguracja OAuth 2.0
- `src/backend/config/settings.py` - Ustawienia aplikacji
- `data/config/` - Konfiguracja agentów

### Zmienne środowiskowe
```bash
# Port aplikacji
PORT=8000

# Port OAuth callback
OAUTH_PORT=8002

# Gmail API scopes
GMAIL_SCOPES="https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.labels"
```

## 🛠️ Skrypty pomocnicze

### OAuth i Gmail
- `scripts/gmail_auth_setup.py` - Konfiguracja OAuth 2.0
- `scripts/fix_oauth_redirect_uri.py` - Diagnostyka OAuth
- `scripts/auto_fix_oauth.py` - Automatyczne naprawy OAuth
- `scripts/find_and_fix_port.py` - Zarządzanie portami

### Aplikacja
- `scripts/foodsave.sh` - Główny skrypt aplikacji
- `scripts/development/dev-environment.sh` - Środowisko deweloperskie
- `scripts/deployment/build-all-containers.sh` - Budowanie kontenerów

## 📊 Monitoring

### Endpointy monitoringu
- `/health` - Status aplikacji
- `/monitoring/status` - Szczegółowy status
- `/monitoring/metrics` - Metryki Prometheus
- `/monitoring/logs` - Logi aplikacji

### Grafana
- Dashboard: http://localhost:3000
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

## 🔍 Debugowanie

### Sprawdzenie konfiguracji OAuth
```bash
python scripts/fix_oauth_redirect_uri.py
```

### Test połączenia Gmail API
```bash
python scripts/gmail_auth_setup.py
```

### Sprawdzenie portów
```bash
python scripts/find_and_fix_port.py
```

## 🚨 Rozwiązywanie problemów

### Błąd `redirect_uri_mismatch`
1. Sprawdź URI w Google Cloud Console
2. Upewnij się, że port jest wolny
3. Uruchom `scripts/fix_oauth_redirect_uri.py`

### Port już w użyciu
```bash
# Znajdź proces używający portu
lsof -i :8002

# Zabij proces
kill -9 <PID>

# Lub użyj innego portu
python scripts/find_and_fix_port.py
```

### Problem z importami
```bash
# Upewnij się, że jesteś w głównym katalogu
cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO

# Uruchom z właściwym PYTHONPATH
PYTHONPATH=. python run_backend.py
```

## 📝 Przykłady użycia

### Agent Gmail
```bash
# Analiza inbox
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "gmail_inbox_zero", "task": "Przeanalizuj moje inbox"}'

# Automatyczne labelowanie
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "gmail_inbox_zero", "task": "Dodaj labele do emaili z ostatnich 24h"}'

# Archiwizacja starych emaili
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "gmail_inbox_zero", "task": "Zarchiwizuj emaile starsze niż 30 dni"}'
```

### Inne agenty
```bash
# Agent Chef
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "Chef", "task": "Sugeruj przepis na obiad"}'

# Agent Weather
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "Weather", "task": "Pokaż pogodę w Warszawie"}'

# Agent Search
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "Search", "task": "Znajdź informacje o Python"}'
```

## 🔄 Aktualizacje

### Ostatnia aktualizacja: 2025-07-27
- ✅ Optymalizacja bazy danych z performance monitoring
- ✅ Database retry mechanism z exponential backoff
- ✅ SQLite-specific optimizations (WAL mode, cache size)
- ✅ Automatyczne tworzenie indeksów dla lepszej wydajności
- ✅ Connection pool monitoring i metryki wydajności
- ✅ Zaktualizowana dokumentacja z najnowszymi zmianami

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi aplikacji
2. Uruchom skrypty diagnostyczne
3. Sprawdź konfigurację OAuth
4. Zweryfikuj porty i połączenia

## 📚 Dokumentacja

- [Agent Gmail Inbox Zero](docs/GMAIL_INBOX_ZERO_AGENT.md)
- [Architektura](docs/core/ARCHITECTURE.md)
- [Technologie](docs/core/TECHNOLOGY_STACK.md)
- [API Reference](docs/core/API_REFERENCE.md)
- [Przewodnik deweloperski](docs/guides/development/DEVELOPMENT_STRATEGY.md)

---

**FoodSave AI - Twój osobisty asystent AI jest gotowy! 🎉** 