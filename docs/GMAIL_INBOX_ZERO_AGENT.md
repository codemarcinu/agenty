# Gmail Inbox Zero Agent

## 📧 Agent do zarządzania Inbox Zero w Gmail

Agent odpowiedzialny za pomoc w uzyskaniu i utrzymaniu "Inbox Zero" w Gmailu. Uczy się na podstawie interakcji z użytkownikiem i analizuje wzorce w emailach.

## 🚀 Szybki start

### 1. Konfiguracja OAuth 2.0

**Wymagane kroki:**
1. Utwórz projekt w Google Cloud Console
2. Włącz Gmail API
3. Utwórz OAuth 2.0 Client ID
4. Dodaj URI przekierowania w Google Cloud Console

**URI przekierowania do dodania:**
```
http://localhost:8002
http://localhost:8003
http://localhost:8080
http://localhost:8081
http://localhost:8082
```

### 2. Uruchomienie aplikacji

```bash
# Uruchom backend
python run_backend.py

# Sprawdź czy działa
curl http://localhost:8000/health
```

### 3. Test agenta Gmail

```bash
# Test podstawowy
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "gmail_inbox_zero", "task": "Pobierz statystyki inbox"}'

# Test z konkretną operacją
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "gmail_inbox_zero", "task": "Analizuj email 123"}'
```

## 🔧 Konfiguracja

### Pliki konfiguracyjne

**`src/gmail_auth.json`** - Konfiguracja OAuth:
```json
{
  "web": {
    "client_id": "your-client-id",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": [
      "http://localhost:8002",
      "http://localhost:8003"
    ]
  }
}
```

### Zmienne środowiskowe

```bash
# Port dla OAuth callback
OAUTH_PORT=8002

# Gmail API scopes
GMAIL_SCOPES="https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.labels"
```

## 📋 Dostępne operacje

### 1. Analiza emaila (`analyze`)
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Analizuj email",
    "operation": "analyze",
    "message_id": "email_id"
  }'
```

### 2. Dodawanie labeli (`label`)
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Dodaj labele",
    "operation": "label",
    "message_id": "email_id",
    "labels": ["ważne", "praca"]
  }'
```

### 3. Archiwizacja (`archive`)
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Zarchiwizuj email",
    "operation": "archive",
    "message_id": "email_id"
  }'
```

### 4. Usuwanie (`delete`)
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Usuń email",
    "operation": "delete",
    "message_id": "email_id"
  }'
```

### 5. Oznaczanie jako przeczytane (`mark_read`)
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Oznacz jako przeczytane",
    "operation": "mark_read",
    "message_id": "email_id"
  }'
```

### 6. Dodawanie gwiazdki (`star`)
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Dodaj gwiazdkę",
    "operation": "star",
    "message_id": "email_id"
  }'
```

### 7. Uczenie się (`learn`)
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Ucz się z interakcji",
    "operation": "learn",
    "email_data": {...},
    "user_actions": {...}
  }'
```

## 🧠 Funkcje AI

### Analiza przez LLM
Agent używa hybrydowego klienta LLM do:
- Analizy treści emaili
- Sugerowania labeli
- Określania priorytetów
- Decydowania o archiwizacji

### Uczenie się
Agent uczy się na podstawie:
- Interakcji użytkownika
- Wzorców w emailach
- Historii decyzji
- Feedbacku użytkownika

## 📊 Statystyki i monitoring

### Pobieranie statystyk
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Pokaż statystyki inbox zero"
  }'
```

### Metryki dostępne:
- Liczba emaili w inbox
- Liczba nieprzeczytanych
- Liczba z labelami
- Procent archiwizacji
- Średni czas odpowiedzi

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

## 🛠️ Skrypty pomocnicze

### `scripts/gmail_auth_setup.py`
- Konfiguracja OAuth 2.0
- Test połączenia Gmail API
- Zapisywanie tokenów

### `scripts/fix_oauth_redirect_uri.py`
- Diagnostyka problemów OAuth
- Otwieranie Google Cloud Console
- Sprawdzanie URI przekierowania

### `scripts/auto_fix_oauth.py`
- Automatyczne znajdowanie wolnego portu
- Aktualizacja konfiguracji
- Test OAuth flow

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

### Przykład 1: Analiza inbox
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Przeanalizuj moje inbox i pokaż najważniejsze emaile"
  }'
```

### Przykład 2: Automatyczne labelowanie
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Dodaj labele do wszystkich emaili z ostatnich 24h"
  }'
```

### Przykład 3: Archiwizacja starych emaili
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Zarchiwizuj emaile starsze niż 30 dni"
  }'
```

## 🔄 Aktualizacje

### Ostatnia aktualizacja: 2025-01-13
- ✅ Konfiguracja OAuth 2.0
- ✅ Test połączenia Gmail API
- ✅ Agent zarejestrowany w systemie
- ✅ Aplikacja działa na porcie 8000
- ✅ Wszystkie operacje dostępne przez API

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi aplikacji
2. Uruchom skrypty diagnostyczne
3. Sprawdź konfigurację OAuth
4. Zweryfikuj porty i połączenia

---

**Agent Gmail Inbox Zero jest gotowy do użycia! 🎉** 