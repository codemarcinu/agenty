# 🔧 Przewodnik Naprawy Błędu OAuth redirect_uri_mismatch

## ❌ Problem

Błąd `400: redirect_uri_mismatch` występuje, gdy aplikacja próbuje użyć URI przekierowania, które nie jest skonfigurowane w Google Cloud Console.

```
Błąd 400: redirect_uri_mismatch
Nie możesz zalogować się w tej aplikacji, ponieważ jest ona niezgodna z zasadami Google dotyczącymi protokołu OAuth 2.0.
```

## ✅ Rozwiązanie

### 1. Sprawdź Aktualną Konfigurację

Uruchom skrypt diagnostyczny:
```bash
python scripts/fix_oauth_redirect_uri.py
```

### 2. Dodaj URI Przekierowania w Google Cloud Console

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Wybierz projekt: `email-categorization-project`
3. Przejdź do: **APIs & Services** > **Credentials**
4. Znajdź aplikację OAuth 2.0 Client ID
5. Kliknij na nazwę aplikacji (ikona ołówka)
6. W sekcji **Authorized redirect URIs** dodaj następujące URI:

```
http://localhost:8000/auth/callback
http://localhost:8000/
http://127.0.0.1:8000/auth/callback
http://127.0.0.1:8000/
http://localhost:8080/
http://127.0.0.1:8080/
http://localhost:8081/
http://127.0.0.1:8081/
http://localhost:57605/
http://127.0.0.1:57605/
```

7. Kliknij **Save**
8. Poczekaj 5-10 minut na propagację zmian

### 3. Testowanie Konfiguracji

Uruchom skrypt testowy:
```bash
python test_oauth.py
```

### 4. Aktualizacja Pliku Konfiguracyjnego

Plik `src/gmail_auth.json` został zaktualizowany z odpowiednimi URI:

```json
{
  "web": {
    "client_id": "YOUR_CLIENT_ID_HERE",
    "project_id": "email-categorization-project",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET_HERE",
    "redirect_uris": [
      "http://localhost:8000/auth/callback",
      "http://localhost:8000/",
      "http://127.0.0.1:8000/auth/callback",
      "http://127.0.0.1:8000/",
      "http://localhost:8080/",
      "http://127.0.0.1:8080/",
      "http://localhost:8081/",
      "http://127.0.0.1:8081/"
    ]
  }
}
```

## 🔧 Rozwiązywanie Problemów

### Problem: Port jest zajęty
```bash
❌ Błąd autoryzacji: [Errno 98] Address already in use
```

**Rozwiązanie:**
1. Sprawdź jakie porty są zajęte:
   ```bash
   netstat -tlnp | grep -E ":(8000|8080|8081)"
   ```

2. Użyj wolnego portu w skrypcie testowym:
   ```python
   creds = flow.run_local_server(port=8081)  # Zmień na wolny port
   ```

3. Dodaj URI dla nowego portu w Google Cloud Console:
   ```
   http://localhost:8081/
   http://127.0.0.1:8081/
   ```

### Problem: Zmiany nie działają
**Rozwiązanie:**
1. Poczekaj 5-10 minut na propagację zmian
2. Wyczyść cache przeglądarki
3. Spróbuj w trybie incognito
4. Sprawdź czy wszystkie URI zostały dodane poprawnie

### Problem: Błąd nadal występuje
**Rozwiązanie:**
1. Sprawdź czy aplikacja używa odpowiedniego portu
2. Upewnij się, że nie ma dodatkowych spacji w URI
3. Sprawdź czy protokół to `http://` (nie `https://`)
4. Sprawdź czy konto Google ma włączone API Gmail

## 📋 Lista Kontrolna

- [ ] Dodano wszystkie URI przekierowania w Google Cloud Console
- [ ] Poczekano 5-10 minut na propagację zmian
- [ ] Przetestowano konfigurację za pomocą `python test_oauth.py`
- [ ] Sprawdzono czy aplikacja używa odpowiedniego portu
- [ ] Wyczyszczono cache przeglądarki
- [ ] Sprawdzono czy konto Google ma włączone API Gmail

## 🚀 Następne Kroki

Po naprawie błędu OAuth:

1. **Uruchom agenta Gmail:**
   ```bash
   python scripts/gmail_auth_setup.py
   ```

2. **Przetestuj z rzeczywistymi emailami:**
   ```bash
   python scripts/test_gmail_inbox_zero_agent.py
   ```

3. **Sprawdź API endpoints:**
   - Dokumentacja API: `http://localhost:8000/docs`
   - Endpointy Gmail: `/api/v2/gmail/*`

## 📞 Wsparcie

Jeśli problem nadal występuje:

1. Sprawdź logi aplikacji
2. Sprawdź czy wszystkie URI zostały dodane w Google Cloud Console
3. Sprawdź czy aplikacja używa odpowiedniego portu
4. Sprawdź czy konto Google ma włączone API Gmail

## 🔗 Przydatne Linki

- [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- [Dokumentacja Gmail API](https://developers.google.com/workspace/gmail/api/reference/rest)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2) 