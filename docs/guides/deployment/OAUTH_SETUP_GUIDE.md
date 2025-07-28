# Przewodnik konfiguracji OAuth 2.0 dla Gmail API

## 📧 Konfiguracja OAuth 2.0 dla Gmail Inbox Zero Agent

### 🎯 Cel
Ten przewodnik pomoże Ci skonfigurować OAuth 2.0 dla agenta Gmail Inbox Zero, aby mógł bezpiecznie uzyskać dostęp do Twojej skrzynki Gmail.

## 🚀 Szybki start

### 1. Utwórz projekt w Google Cloud Console

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Utwórz nowy projekt lub wybierz istniejący
3. Zapisz **Project ID** - będzie potrzebny później

### 2. Włącz Gmail API

1. W Google Cloud Console przejdź do **APIs & Services** > **Library**
2. Wyszukaj "Gmail API"
3. Kliknij na **Gmail API** i wybierz **Enable**

### 3. Utwórz OAuth 2.0 Client ID

1. Przejdź do **APIs & Services** > **Credentials**
2. Kliknij **Create Credentials** > **OAuth client ID**
3. Wybierz **Desktop application** jako typ aplikacji
4. Nadaj nazwę (np. "FoodSave AI Gmail Agent")
5. Kliknij **Create**

### 4. Skonfiguruj URI przekierowania

W sekcji **OAuth 2.0 Client IDs**:
1. Kliknij na utworzony Client ID
2. W sekcji **Authorized redirect URIs** dodaj:
   ```
   http://localhost:8002
   http://localhost:8003
   http://localhost:8080
   http://localhost:8081
   http://localhost:8082
   ```
3. Kliknij **Save**

### 5. Pobierz dane OAuth

1. W sekcji **OAuth 2.0 Client IDs** kliknij **Download JSON**
2. Zapisz plik jako `src/gmail_auth.json` w głównym katalogu projektu

## 🔧 Konfiguracja lokalna

### 1. Sprawdź plik konfiguracyjny

Upewnij się, że plik `src/gmail_auth.json` zawiera:

```json
{
  "web": {
    "client_id": "your-client-id.apps.googleusercontent.com",
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

### 2. Uruchom skrypt konfiguracyjny

```bash
# Sprawdź konfigurację OAuth
python scripts/fix_oauth_redirect_uri.py

# Uruchom setup OAuth
python scripts/gmail_auth_setup.py
```

### 3. Test połączenia

```bash
# Test OAuth flow
python scripts/test_oauth.py 8002

# Test agenta Gmail
python scripts/test_gmail_inbox_zero_agent.py
```

## 🛠️ Skrypty pomocnicze

### `scripts/gmail_auth_setup.py`
**Opis:** Główny skrypt konfiguracji OAuth
**Funkcje:**
- Konfiguracja OAuth 2.0 Client ID
- Test połączenia Gmail API
- Zapisywanie tokenów dostępu
- Inicjalizacja agenta Gmail

**Użycie:**
```bash
python scripts/gmail_auth_setup.py
```

### `scripts/fix_oauth_redirect_uri.py`
**Opis:** Diagnostyka problemów OAuth
**Funkcje:**
- Sprawdzanie konfiguracji OAuth
- Otwieranie Google Cloud Console
- Diagnostyka URI przekierowania
- Instrukcje naprawy

**Użycie:**
```bash
python scripts/fix_oauth_redirect_uri.py
```

### `scripts/auto_fix_oauth.py`
**Opis:** Automatyczne naprawy OAuth
**Funkcje:**
- Automatyczne znajdowanie wolnego portu
- Aktualizacja konfiguracji OAuth
- Test OAuth flow
- Instrukcje dla użytkownika

**Użycie:**
```bash
python scripts/auto_fix_oauth.py
```

### `scripts/find_and_fix_port.py`
**Opis:** Zarządzanie portami
**Funkcje:**
- Znajdowanie wolnych portów
- Aktualizacja konfiguracji
- Test połączeń
- Czyszczenie konfiguracji

**Użycie:**
```bash
python scripts/find_and_fix_port.py
```

## 🚨 Rozwiązywanie problemów

### Błąd `redirect_uri_mismatch`

**Przyczyna:** URI przekierowania w aplikacji nie pasuje do URI w Google Cloud Console.

**Rozwiązanie:**
1. Sprawdź URI w Google Cloud Console
2. Upewnij się, że port jest wolny
3. Uruchom `scripts/fix_oauth_redirect_uri.py`

```bash
# Sprawdź konfigurację
python scripts/fix_oauth_redirect_uri.py

# Znajdź wolny port
python scripts/find_and_fix_port.py

# Zaktualizuj konfigurację
python scripts/auto_fix_oauth.py
```

### Port już w użyciu

**Przyczyna:** Port używany przez OAuth callback jest zajęty.

**Rozwiązanie:**
```bash
# Znajdź proces używający portu
lsof -i :8002

# Zabij proces
kill -9 <PID>

# Lub użyj innego portu
python scripts/find_and_fix_port.py
```

### Problem z importami

**Przyczyna:** Nieprawidłowy PYTHONPATH.

**Rozwiązanie:**
```bash
# Upewnij się, że jesteś w głównym katalogu
cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO

# Uruchom z właściwym PYTHONPATH
PYTHONPATH=. python scripts/gmail_auth_setup.py
```

### Token wygasł

**Przyczyna:** Token OAuth wygasł.

**Rozwiązanie:**
```bash
# Usuń stary token
rm -f token.json

# Uruchom ponownie setup
python scripts/gmail_auth_setup.py
```

## 🔒 Bezpieczeństwo

### Najlepsze praktyki

1. **Nie udostępniaj pliku `gmail_auth.json`**
   - Dodaj do `.gitignore`
   - Nie commituj do repozytorium
   - Używaj zmiennych środowiskowych w produkcji

2. **Ogranicz uprawnienia**
   - Używaj minimalnych scope'ów Gmail API
   - Regularnie przeglądaj uprawnienia aplikacji

3. **Monitoruj dostęp**
   - Sprawdzaj logi dostępu w Google Cloud Console
   - Używaj alertów dla nietypowych działań

### Scope'y Gmail API

Agent używa następujących scope'ów:
```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Odczyt emaili
    'https://www.googleapis.com/auth/gmail.modify',    # Modyfikacja emaili
    'https://www.googleapis.com/auth/gmail.labels'     # Zarządzanie labelami
]
```

## 📊 Testowanie

### Test podstawowy

```bash
# Test OAuth flow
python scripts/test_oauth.py 8002

# Test agenta Gmail
python scripts/test_gmail_inbox_zero_agent.py
```

### Test przez API

```bash
# Test agenta przez API
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "gmail_inbox_zero", "task": "Pobierz statystyki inbox"}'
```

### Test operacji Gmail

```bash
# Test analizy emaila
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gmail_inbox_zero",
    "task": "Analizuj email",
    "operation": "analyze",
    "message_id": "email_id"
  }'
```

## 🔄 Aktualizacje

### Ostatnia aktualizacja: 2025-01-13
- ✅ Konfiguracja OAuth 2.0
- ✅ Test połączenia Gmail API
- ✅ Skrypty pomocnicze
- ✅ Rozwiązywanie problemów
- ✅ Dokumentacja bezpieczeństwa

## 📞 Wsparcie

W przypadku problemów:

1. **Sprawdź logi aplikacji**
   ```bash
   tail -f logs/app.log
   ```

2. **Uruchom skrypty diagnostyczne**
   ```bash
   python scripts/fix_oauth_redirect_uri.py
   python scripts/auto_fix_oauth.py
   ```

3. **Sprawdź konfigurację OAuth**
   - Zweryfikuj URI w Google Cloud Console
   - Sprawdź uprawnienia aplikacji
   - Upewnij się, że Gmail API jest włączone

4. **Zweryfikuj porty i połączenia**
   ```bash
   python scripts/find_and_fix_port.py
   ./scripts/utils/check-ports.sh 8002
   ```

## 📚 Dodatkowe zasoby

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Agent Gmail Inbox Zero](docs/GMAIL_INBOX_ZERO_AGENT.md)

---

**OAuth 2.0 dla Gmail API jest skonfigurowany! 🎉** 