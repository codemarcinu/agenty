# Dokumentacja wszystkich skryptów

## 📧 Skrypty Gmail i OAuth

### `scripts/gmail_auth_setup.py`
**Opis:** Konfiguracja OAuth 2.0 dla Gmail API
**Użycie:**
```bash
python scripts/gmail_auth_setup.py
```
**Funkcje:**
- Konfiguracja OAuth 2.0 Client ID
- Test połączenia Gmail API
- Zapisywanie tokenów dostępu
- Inicjalizacja agenta Gmail

### `scripts/fix_oauth_redirect_uri.py`
**Opis:** Diagnostyka problemów OAuth
**Użycie:**
```bash
python scripts/fix_oauth_redirect_uri.py
```
**Funkcje:**
- Sprawdzanie konfiguracji OAuth
- Otwieranie Google Cloud Console
- Diagnostyka URI przekierowania
- Instrukcje naprawy

### `scripts/auto_fix_oauth.py`
**Opis:** Automatyczne naprawy OAuth
**Użycie:**
```bash
python scripts/auto_fix_oauth.py
```
**Funkcje:**
- Automatyczne znajdowanie wolnego portu
- Aktualizacja konfiguracji OAuth
- Test OAuth flow
- Instrukcje dla użytkownika

### `scripts/find_and_fix_port.py`
**Opis:** Zarządzanie portami
**Użycie:**
```bash
python scripts/find_and_fix_port.py
```
**Funkcje:**
- Znajdowanie wolnych portów
- Aktualizacja konfiguracji
- Test połączeń
- Czyszczenie konfiguracji

### `scripts/force_port_8002.py`
**Opis:** Wymuszenie użycia portu 8002
**Użycie:**
```bash
python scripts/force_port_8002.py
```
**Funkcje:**
- Wymuszenie portu 8002
- Czyszczenie niepotrzebnych portów
- Aktualizacja konfiguracji
- Test OAuth

### `scripts/show_oauth_uris.py`
**Opis:** Wyświetlanie URI OAuth
**Użycie:**
```bash
python scripts/show_oauth_uris.py
```
**Funkcje:**
- Wyświetlanie aktualnych URI
- Instrukcje dla Google Cloud Console
- Sprawdzanie konfiguracji

### `scripts/test_gmail_inbox_zero_agent.py`
**Opis:** Test agenta Gmail Inbox Zero
**Użycie:**
```bash
python scripts/test_gmail_inbox_zero_agent.py
```
**Funkcje:**
- Test wszystkich operacji Gmail
- Sprawdzanie połączenia API
- Test funkcji AI
- Walidacja odpowiedzi

## 🚀 Skrypty aplikacji

### `scripts/foodsave.sh`
**Opis:** Główny skrypt aplikacji
**Użycie:**
```bash
./scripts/foodsave.sh [start|stop|restart|status]
```
**Funkcje:**
- Uruchamianie/zatrzymywanie aplikacji
- Sprawdzanie statusu
- Zarządzanie procesami
- Logi aplikacji

### `scripts/foodsave-all.sh`
**Opis:** Kompletny skrypt systemu
**Użycie:**
```bash
./scripts/foodsave-all.sh [start|stop|restart|status]
```
**Funkcje:**
- Zarządzanie całym systemem
- Uruchamianie wszystkich komponentów
- Monitoring systemu
- Backup i restore

## 🛠️ Skrypty deweloperskie

### `scripts/development/dev-environment.sh`
**Opis:** Środowisko deweloperskie
**Użycie:**
```bash
./scripts/development/dev-environment.sh [setup|start|stop|clean]
```
**Funkcje:**
- Konfiguracja środowiska dev
- Uruchamianie serwisów
- Czyszczenie danych testowych
- Reset środowiska

### `scripts/development/cleanup.sh`
**Opis:** Czyszczenie środowiska
**Użycie:**
```bash
./scripts/development/cleanup.sh
```
**Funkcje:**
- Usuwanie plików tymczasowych
- Czyszczenie cache
- Reset bazy danych
- Czyszczenie logów

## 🚀 Skrypty deployment

### `scripts/deployment/build-all-containers.sh`
**Opis:** Budowanie kontenerów
**Użycie:**
```bash
./scripts/deployment/build-all-containers.sh
```
**Funkcje:**
- Budowanie wszystkich kontenerów
- Optimizacja obrazów
- Test kontenerów
- Push do registry

### `scripts/deployment/deploy-to-vps.sh`
**Opis:** Deployment na VPS
**Użycie:**
```bash
./scripts/deployment/deploy-to-vps.sh
```
**Funkcje:**
- Deployment na serwer
- Konfiguracja środowiska
- Uruchamianie aplikacji
- Monitoring deployment

## 📊 Skrypty monitoringu

### `scripts/monitoring/backup_cli.py`
**Opis:** CLI do backup
**Użycie:**
```bash
python scripts/monitoring/backup_cli.py [create|list|restore|cleanup]
```
**Funkcje:**
- Tworzenie backup
- Listowanie backupów
- Przywracanie z backup
- Czyszczenie starych backupów

### `scripts/monitoring/grafana/`
**Opis:** Konfiguracja Grafana
**Zawartość:**
- Dashboards
- Datasources
- Alerty
- Konfiguracja

## 🔧 Skrypty narzędziowe

### `scripts/utils/check-ports.sh`
**Opis:** Sprawdzanie portów
**Użycie:**
```bash
./scripts/utils/check-ports.sh [port_number]
```
**Funkcje:**
- Sprawdzanie dostępności portów
- Znajdowanie wolnych portów
- Listowanie używanych portów
- Diagnostyka konfliktów

### `scripts/utils/health-check.sh`
**Opis:** Sprawdzanie zdrowia systemu
**Użycie:**
```bash
./scripts/utils/health-check.sh
```
**Funkcje:**
- Sprawdzanie statusu aplikacji
- Test endpointów
- Monitoring zasobów
- Alerty o problemach

### `scripts/utils/rag_cli.py`
**Opis:** CLI do RAG
**Użycie:**
```bash
python scripts/utils/rag_cli.py [upload|query|stats|cleanup]
```
**Funkcje:**
- Upload dokumentów
- Query RAG
- Statystyki RAG
- Czyszczenie RAG

## 🧪 Skrypty testowe

### `scripts/backend_tests/`
**Opis:** Testy backend
**Zawartość:**
- `debug_imports.py` - Debug importów
- `run_intent_tests.py` - Testy intent
- `test_import.py` - Test importów

### `scripts/test_oauth.py`
**Opis:** Test OAuth
**Użycie:**
```bash
python scripts/test_oauth.py [port]
```
**Funkcje:**
- Test OAuth flow
- Sprawdzanie portów
- Test callback
- Walidacja tokenów

## 📋 Skrypty migracji

### `scripts/migration/migrate_to_faiss_gpu.py`
**Opis:** Migracja do FAISS GPU
**Użycie:**
```bash
python scripts/migration/migrate_to_faiss_gpu.py
```
**Funkcje:**
- Migracja wektorów
- Optymalizacja GPU
- Backup danych
- Test wydajności

## 🔍 Skrypty diagnostyczne

### `scripts/analyze_and_reorganize.sh`
**Opis:** Analiza i reorganizacja
**Użycie:**
```bash
./scripts/analyze_and_reorganize.sh
```
**Funkcje:**
- Analiza struktury projektu
- Reorganizacja plików
- Optymalizacja kodu
- Generowanie raportów

## 📝 Przykłady użycia

### Konfiguracja OAuth Gmail
```bash
# 1. Sprawdź konfigurację
python scripts/fix_oauth_redirect_uri.py

# 2. Uruchom setup OAuth
python scripts/gmail_auth_setup.py

# 3. Test połączenia
python scripts/test_oauth.py 8002

# 4. Test agenta
python scripts/test_gmail_inbox_zero_agent.py
```

### Uruchomienie aplikacji
```bash
# Uruchom aplikację
./scripts/foodsave.sh start

# Sprawdź status
./scripts/foodsave.sh status

# Zatrzymaj aplikację
./scripts/foodsave.sh stop
```

### Monitoring i backup
```bash
# Sprawdź zdrowie systemu
./scripts/utils/health-check.sh

# Utwórz backup
python scripts/monitoring/backup_cli.py create

# Sprawdź porty
./scripts/utils/check-ports.sh 8000
```

## 🔄 Aktualizacje

### Ostatnia aktualizacja: 2025-01-13
- ✅ Dodano skrypty OAuth i Gmail
- ✅ Zaktualizowano dokumentację
- ✅ Dodano instrukcje konfiguracji
- ✅ Dodano przykłady użycia

## 📞 Wsparcie

W przypadku problemów z skryptami:
1. Sprawdź uprawnienia wykonywania
2. Zweryfikuj zależności
3. Sprawdź logi błędów
4. Uruchom w trybie debug

---

**Wszystkie skrypty są gotowe do użycia! 🎉** 