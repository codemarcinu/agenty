# FoodSave AI - Dokumentacja Skryptów

## 🚀 GUI Scripts Launcher (Dla Osób Nietechnicznych)

### Szybki Start
```bash
# Uruchom przyjazny interfejs graficzny
./scripts/launch_scripts_gui.sh
```

### Funkcje GUI
- **Kategoryzowane skrypty** - podzielone na logiczne grupy
- **Opisy każdego skryptu** - jasne wyjaśnienie co robi
- **Output w czasie rzeczywistym** - widzisz co się dzieje
- **Możliwość zatrzymywania** - bezpieczne przerwanie skryptów
- **Przyjazny interfejs** - ikony i intuicyjny design

### Szczegółowa Dokumentacja
Zobacz: [GUI Scripts Launcher Documentation](GUI_SCRIPTS_LAUNCHER.md)

---

## 🍽️ Uproszczony GUI (Nowy)

### Szybki Start
```bash
# Uruchom uproszczony interfejs GUI
./scripts/run_simplified_gui.sh
```

### Funkcje Uproszczonego GUI
- **Chat-centric design** - Czat jako główny element
- **Agent selector** - Wybór agentów z dropdown
- **Quick actions** - Szybkie akcje dla typowych zadań
- **File upload** - Upload obrazów do analizy
- **Dark mode** - Przełączanie motywu
- **Responsive design** - Adaptacja do różnych rozmiarów

### Szczegółowa Dokumentacja
Zobacz: [Uproszczony GUI Design](SIMPLIFIED_GUI_DESIGN.md)

---

## 📋 Spis treści

1. [Główne skrypty uruchomieniowe](#główne-skrypty-uruchomieniowe)
2. [Skrypty developmentowe](#skrypty-developmentowe)
3. [Skrypty deploymentowe](#skrypty-deploymentowe)
4. [Skrypty automatyzacji](#skrypty-automatyzacji)
5. [Skrypty monitoringu](#skrypty-monitoringu)
6. [Skrypty testowe](#skrypty-testowe)
7. [Narzędzia pomocnicze](#narzędzia-pomocnicze)
8. [GUI Skrypty](#gui-skrypty)
9. [Troubleshooting](#troubleshooting)

---

## 🚀 Główne skrypty uruchomieniowe

### `scripts/main/start.sh` - Główny skrypt uruchamiania

**Opis:** Centralny punkt uruchamiania aplikacji z różnymi środowiskami.

**Użycie:**
```bash
./scripts/main/start.sh [OPCJA]
```

**Opcje:**
- `dev` - Uruchom środowisko deweloperskie
- `prod` - Uruchom środowisko produkcyjne  
- `test` - Uruchom środowisko testowe
- `stop` - Zatrzymaj wszystkie serwisy
- `restart` - Restartuj serwisy
- `status` - Pokaż status serwisów
- `logs` - Pokaż logi
- `help` - Pokaż pomoc

**Przykłady:**
```bash
./scripts/main/start.sh dev      # Uruchom development
./scripts/main/start.sh prod     # Uruchom production
./scripts/main/start.sh stop     # Zatrzymaj wszystko
./scripts/main/start.sh status   # Sprawdź status
```

**Funkcje:**
- Sprawdza wymagania systemowe (Docker, Docker Compose)
- Przekierowuje do odpowiednich skryptów w zależności od środowiska
- Zapewnia spójny interfejs dla wszystkich operacji

---

### `scripts/main/manager.sh` - Zaawansowany manager aplikacji

**Opis:** Kompleksowy skrypt zarządzania projektem z obsługą wielu środowisk i serwisów.

**Użycie:**
```bash
./scripts/main/manager.sh [KOMENDA] [ŚRODOWISKO]
```

**Komendy:**
- `start [env]` - Uruchom serwisy w określonym środowisku
- `stop` - Zatrzymaj wszystkie serwisy
- `restart` - Restartuj serwisy
- `status` - Pokaż status wszystkich serwisów
- `logs [service]` - Pokaż logi serwisu
- `clean` - Wyczyść wszystkie kontenery i dane
- `build` - Zbuduj obrazy Docker
- `health` - Sprawdź zdrowie aplikacji

**Środowiska:**
- `dev` - Development (domyślne)
- `test` - Testing
- `prod` - Production

**Przykłady:**
```bash
./scripts/main/manager.sh start dev      # Uruchom development
./scripts/main/manager.sh start prod     # Uruchom production
./scripts/main/manager.sh stop           # Zatrzymaj wszystko
./scripts/main/manager.sh status         # Sprawdź status
./scripts/main/manager.sh logs backend   # Logi backendu
./scripts/main/manager.sh clean          # Wyczyść wszystko
```

**Funkcje:**
- Zarządzanie wieloma środowiskami (dev/test/prod)
- Automatyczne sprawdzanie portów i konfliktów
- Monitoring zdrowia serwisów
- Logowanie wszystkich operacji
- Obsługa różnych wersji Docker Compose

---

### `scripts/main/stop.sh` - Skrypt zatrzymywania

**Opis:** Bezpieczne zatrzymanie wszystkich komponentów aplikacji.

**Użycie:**
```bash
./scripts/main/stop.sh
```

**Funkcje:**
- Zatrzymuje wszystkie kontenery Docker
- Kończy sesje tmux
- Sprawdza zwolnienie portów
- Loguje wszystkie operacje

---

## 🔧 Skrypty developmentowe

### `scripts/development/start-dev.sh` - Szybki start development

**Opis:** Szybki skrypt do uruchomienia środowiska developerskiego z Docker Compose.

**Użycie:**
```bash
./scripts/development/start-dev.sh
```

**Funkcje:**
- Tworzy plik `.env` z szablonu jeśli nie istnieje
- Tworzy wymagane katalogi (logs, data, monitoring)
- Uruchamia kontenery Docker w trybie development
- Wyświetla dostępne endpointy po uruchomieniu

**Endpointy po uruchomieniu:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Ollama: http://localhost:11434
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)
- Loki: http://localhost:3100

---

### `scripts/development/start-local.sh` - Lokalny development (bez Docker)

**Opis:** Uruchomienie aplikacji lokalnie bez kontenerów Docker (szybsze iteracje).

**Użycie:**
```bash
./scripts/development/start-local.sh
```

**Funkcje:**
- Sprawdza wymagania systemowe (Python, Node.js, Docker)
- Przygotowuje środowisko (katalogi, pliki konfiguracyjne)
- Uruchamia bazę danych w Docker (SQLite, Redis, Ollama)
- Uruchamia backend lokalnie (FastAPI + uvicorn)
- Uruchamia frontend lokalnie (React + Vite)
- Zwalnia zajęte porty automatycznie
- Sprawdza zdrowie serwisów

**Zalety:**
- Szybsze uruchamianie i restart
- Łatwiejsze debugowanie
- Mniejsze zużycie zasobów
- Hot reload dla kodu

---

### `scripts/development/dev-environment.sh` - Manager środowiska developerskiego

**Opis:** Zaawansowany manager dla środowiska developerskiego z kontrolą poszczególnych komponentów.

**Użycie:**
```bash
./scripts/development/dev-environment.sh [KOMENDA] [KOMPONENT]
```

**Komendy:**
- `start [component]` - Uruchom komponent
- `stop [component]` - Zatrzymaj komponent
- `status` - Pokaż status wszystkich komponentów
- `restart [component]` - Restartuj komponent

**Komponenty:**
- `backend` - Backend FastAPI
- `frontend` - Frontend React
- `all` - Wszystkie komponenty

**Przykłady:**
```bash
./scripts/development/dev-environment.sh start backend    # Uruchom tylko backend
./scripts/development/dev-environment.sh start frontend   # Uruchom tylko frontend
./scripts/development/dev-environment.sh start all        # Uruchom wszystko
./scripts/development/dev-environment.sh stop backend     # Zatrzymaj backend
./scripts/development/dev-environment.sh status           # Sprawdź status
```

**Funkcje:**
- Kontrola poszczególnych komponentów
- Automatyczne sprawdzanie portów
- Zarządzanie procesami (PID tracking)
- Sprawdzanie zależności i pamięci
- Docker dla bazy danych

---

### `scripts/development/health-check.sh` - Sprawdzenie zdrowia aplikacji

**Opis:** Kompleksowe sprawdzenie zdrowia wszystkich komponentów aplikacji.

**Użycie:**
```bash
./scripts/development/health-check.sh [KOMPONENT]
```

**Komponenty:**
- `backend` - Sprawdź backend API
- `frontend` - Sprawdź frontend
- `database` - Sprawdź bazę danych
- `ollama` - Sprawdź Ollama
- `all` - Sprawdź wszystko (domyślne)

**Funkcje:**
- Sprawdza dostępność endpointów HTTP
- Testuje połączenia z bazą danych
- Sprawdza status kontenerów Docker
- Weryfikuje modele Ollama
- Generuje raport zdrowia

---

### `scripts/development/cleanup.sh` - Czyszczenie środowiska

**Opis:** Bezpieczne czyszczenie środowiska developerskiego.

**Użycie:**
```bash
./scripts/development/cleanup.sh [OPCJA]
```

**Opcje:**
- `containers` - Usuń kontenery Docker
- `volumes` - Usuń wolumeny Docker
- `logs` - Wyczyść logi
- `all` - Wyczyść wszystko (domyślne)

**Funkcje:**
- Zatrzymuje i usuwa kontenery
- Usuwa wolumeny Docker
- Czyści pliki logów
- Resetuje środowisko do stanu początkowego

---

## 🚀 Skrypty deploymentowe

### `scripts/deployment/build-all-containers.sh` - Budowanie wszystkich kontenerów

**Opis:** Buduje wszystkie obrazy Docker dla aplikacji.

**Użycie:**
```bash
./scripts/deployment/build-all-containers.sh [OPCJA]
```

**Opcje:**
- `--no-cache` - Buduj bez cache
- `--push` - Pushuj obrazy do registry
- `--latest` - Taguj jako latest

**Funkcje:**
- Buduje obrazy dla wszystkich serwisów
- Optymalizuje rozmiar obrazów
- Sprawdza bezpieczeństwo obrazów
- Generuje raport budowania

---

### `scripts/deployment/build-all-optimized.sh` - Zoptymalizowane budowanie

**Opis:** Buduje zoptymalizowane obrazy Docker z wieloetapowym buildem.

**Użycie:**
```bash
./scripts/deployment/build-all-optimized.sh
```

**Funkcje:**
- Multi-stage builds dla mniejszych obrazów
- Optymalizacja dla produkcji
- Security scanning
- Dependency caching

---

### `scripts/deployment/docker-setup.sh` - Konfiguracja Docker

**Opis:** Konfiguruje środowisko Docker dla projektu.

**Użycie:**
```bash
./scripts/deployment/docker-setup.sh [OPCJA]
```

**Opcje:**
- `install` - Zainstaluj Docker
- `configure` - Skonfiguruj Docker
- `test` - Przetestuj instalację

**Funkcje:**
- Instalacja Docker i Docker Compose
- Konfiguracja uprawnień użytkownika
- Testowanie instalacji
- Optymalizacja dla Linux

---

## 🤖 Skrypty automatyzacji

### `scripts/automation/reset_qt_python_env.sh` - Reset środowiska Qt/Python

**Opis:** Automatyczny reset środowiska Qt/Python i uruchomienie GUI.

**Użycie:**
```bash
sudo ./scripts/automation/reset_qt_python_env.sh
```

**Funkcje:**
- Zabija wszystkie procesy python/Qt użytkownika i root
- Aktywuje wirtualne środowisko Python
- Uruchamia GUI aplikacji
- Rozwiązuje problem "QApplication instance already exists"

**Wymagania:**
- Uruchomienie z sudo (dla zabicia procesów root)
- Aktywne wirtualne środowisko Python

---

### `scripts/automation/full_documentation_update_2025_07_13.sh` - Aktualizacja dokumentacji

**Opis:** Automatyczna aktualizacja całej dokumentacji projektu.

**Użycie:**
```bash
./scripts/automation/full_documentation_update_2025_07_13.sh
```

**Funkcje:**
- Generuje spis treści dla wszystkich dokumentów
- Aktualizuje daty w dokumentacji
- Weryfikuje linki
- Organizuje strukturę dokumentów

---

### `scripts/automation/organize_scripts.sh` - Organizacja skryptów

**Opis:** Organizuje i kategoryzuje skrypty w projekcie.

**Użycie:**
```bash
./scripts/automation/organize_scripts.sh
```

**Funkcje:**
- Kategoryzuje skrypty według funkcji
- Tworzy dokumentację skryptów
- Weryfikuje uprawnienia wykonywania
- Generuje spis wszystkich skryptów

---

### `scripts/automation/cleanup_unnecessary_files.sh` - Czyszczenie niepotrzebnych plików

**Opis:** Usuwa niepotrzebne pliki z projektu.

**Użycie:**
```bash
./scripts/automation/cleanup_unnecessary_files.sh
```

**Funkcje:**
- Usuwa pliki tymczasowe
- Czyści cache
- Usuwa duplikaty
- Optymalizuje rozmiar projektu

---

## 📊 Skrypty monitoringu

### `scripts/development/start_monitoring.sh` - Uruchomienie monitoringu

**Opis:** Uruchamia system monitoringu (Prometheus, Grafana, Loki).

**Użycie:**
```bash
./scripts/development/start_monitoring.sh
```

**Funkcje:**
- Uruchamia Prometheus
- Uruchamia Grafana
- Uruchamia Loki
- Konfiguruje dashboards
- Ustawia alerty

---

### `scripts/monitoring/grafana/` - Konfiguracja Grafana

**Opis:** Skrypty konfiguracyjne dla Grafana.

**Zawartość:**
- Dashboards JSON
- Datasources konfiguracja
- Alert rules

---

## 🧪 Skrypty testowe

### `scripts/run_tests.sh` - Uruchomienie testów

**Opis:** Uruchamia wszystkie testy aplikacji.

**Użycie:**
```bash
./scripts/run_tests.sh [OPCJA]
```

**Opcje:**
- `unit` - Testy jednostkowe
- `integration` - Testy integracyjne
- `e2e` - Testy end-to-end
- `all` - Wszystkie testy (domyślne)

---

### `scripts/test_*.py` - Różne testy funkcjonalne

**Opis:** Specjalistyczne testy dla różnych funkcjonalności.

**Dostępne testy:**
- `test_auth_automation.sh` - Testy autoryzacji
- `test_clean_docker.sh` - Testy czyszczenia Docker
- `test_general_chat.sh` - Testy czatu
- `test_intent_routing.py` - Testy routingu intencji
- `test_rag_system.py` - Testy systemu RAG

---

## 🛠️ Narzędzia pomocnicze

### `scripts/check-ports.sh` - Sprawdzenie portów

**Opis:** Sprawdza dostępność portów używanych przez aplikację.

**Użycie:**
```bash
./scripts/check-ports.sh
```

**Funkcje:**
- Sprawdza wszystkie porty aplikacji
- Identyfikuje konflikty
- Sugeruje rozwiązania

---

### `scripts/free-ports.sh` - Zwolnienie portów

**Opis:** Automatycznie zwalnia zajęte porty.

**Użycie:**
```bash
./scripts/free-ports.sh [PORT]
```

---

### `scripts/check-containers.sh` - Sprawdzenie kontenerów

**Opis:** Sprawdza status kontenerów Docker.

**Użycie:**
```bash
./scripts/check-containers.sh
```

---

### `scripts/backup_cli.py` - CLI do backupów

**Opis:** Interfejs wiersza poleceń do zarządzania backupami.

**Użycie:**
```bash
python scripts/backup_cli.py [KOMENDA]
```

---

### `scripts/rag_cli.py` - CLI do RAG

**Opis:** Interfejs wiersza poleceń do systemu RAG.

**Użycie:**
```bash
python scripts/rag_cli.py [KOMENDA]
```

---

## 🖥️ GUI Skrypty

### `scripts/run_simplified_gui.sh` - Uproszczony GUI Launcher

**Opis:** Uruchamia uproszczony interfejs GUI skupiony na czacie.

**Użycie:**
```bash
./scripts/run_simplified_gui.sh [OPCJA]
```

**Opcje:**
- `--help, -h` - Pokaż pomoc
- `--check` - Sprawdź wymagania bez uruchamiania GUI
- `--backend` - Sprawdź tylko backend

**Przykłady:**
```bash
./scripts/run_simplified_gui.sh              # Uruchom GUI
./scripts/run_simplified_gui.sh --check      # Sprawdź wymagania
./scripts/run_simplified_gui.sh --backend    # Sprawdź backend
```

**Funkcje:**
- Sprawdza wymagania systemowe (Python, PySide6, structlog)
- Automatyczna instalacja zależności
- Sprawdzanie backendu
- Uruchamianie uproszczonego GUI

**Wymagania:**
- Python 3.11+
- PySide6 (automatyczna instalacja)
- structlog (automatyczna instalacja)
- Backend FastAPI (opcjonalne)

**Funkcje GUI:**
- Chat interface jako główny element
- Agent selector w dropdown (8 głównych agentów)
- Quick actions dla szybkich akcji
- File upload dla obrazów
- Dark mode toggle
- Connection status

---

## 🔧 Troubleshooting

### Problem: "QApplication instance already exists"

**Rozwiązanie:**
```bash
sudo ./scripts/automation/reset_qt_python_env.sh
```

### Problem: Porty zajęte

**Rozwiązanie:**
```bash
./scripts/free-ports.sh
./scripts/check-ports.sh
```

### Problem: Kontenery nie uruchamiają się

**Rozwiązanie:**
```bash
./scripts/check-containers.sh
./scripts/development/health-check.sh
```

### Problem: Brak pamięci

**Rozwiązanie:**
```bash
./scripts/development/cleanup.sh all
```

### Problem: Błędy w testach

**Rozwiązanie:**
```bash
./scripts/run_tests.sh unit
./scripts/run_tests.sh integration
```

---

## 📝 Najlepsze praktyki

1. **Development:** Używaj `start-local.sh` dla szybkiego developmentu
2. **Testy:** Uruchamiaj testy przed commitem
3. **Monitoring:** Uruchamiaj monitoring w osobnym środowisku
4. **Backup:** Regularnie twórz backup bazy danych
5. **Logs:** Monitoruj logi aplikacji i kontenerów
6. **Cleanup:** Regularnie czyść środowisko developerskie

---

## 🔄 Migracja z starych skryptów

Stare skrypty są zachowane, ale zalecane jest używanie:
- `scripts/main/start.sh` - główny skrypt uruchamiania
- `scripts/main/manager.sh` - zaawansowany manager
- `scripts/development/start-local.sh` - lokalny development
- `scripts/automation/` - automatyzacja

---

## 📞 Support

W przypadku problemów:
1. Sprawdź logi: `./scripts/main/manager.sh logs [service]`
2. Sprawdź health check: `./scripts/development/health-check.sh`
3. Sprawdź dokumentację w `docs/`
4. Uruchom testy: `./scripts/run_tests.sh` 