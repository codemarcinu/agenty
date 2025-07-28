# 📜 Przewodnik Użytkownika - Skrypty FoodSave AI

**Data utworzenia:** 2025-07-19  
**Cel:** Przejrzysty przewodnik dla osób nietechnicznych  
**Status:** Kompletny przewodnik wszystkich skryptów  

---

## 🎯 Wprowadzenie

Ten przewodnik wyjaśnia wszystkie skrypty `.sh` w projekcie FoodSave AI w sposób przyjazny dla osób nietechnicznych. Każdy skrypt ma jasny opis tego, co robi, jak go uruchomić i jak rozwiązać typowe problemy.

### 📋 Jak korzystać z tego przewodnika

1. **Znajdź skrypt** - Użyj spisu treści poniżej
2. **Przeczytaj opis** - Dowiedz się co robi skrypt
3. **Skopiuj komendę** - Uruchom skrypt
4. **Sprawdź wyniki** - Upewnij się, że wszystko działa

---

## 📁 Spis Treści

### 🚀 Skrypty Główne (Najważniejsze)
- [foodsave-all.sh](#-foodsave-allsh---główny-panel-sterowania)
- [foodsave.sh](#-foodsavesh---podstawowy-manager)
- [start_foodsave.sh](#-start_foodsavesh---szybkie-uruchomienie)

### 🛠️ Skrypty Development
- [dev-up.sh](#-dev-upsh---środowisko-deweloperskie)
- [dev-down.sh](#-dev-downsh---zatrzymanie-dev)
- [cleanup.sh](#-cleanupsh---czyszczenie-systemu)

### 🐳 Skrypty Docker
- [docker-manager.sh](#-docker-managersh---zarządzanie-kontenerami)
- [build-all.sh](#-build-allsh---budowanie-obrazów)
- [deploy.sh](#-deploysh---wdrażanie-systemu)

### 📊 Skrypty Monitoring
- [health-check.sh](#-health-checksh---sprawdzanie-zdrowia)
- [logs.sh](#-logssh---zarządzanie-logami)
- [backup.sh](#-backupsh---backup-systemu)

### 📦 Zarchiwizowane Skrypty
- [Archiwum skryptów](#-archiwum-skryptów)

---

## 🚀 Skrypty Główne

### 📜 `foodsave-all.sh` - Główny Panel Sterowania

#### 🎯 Co robi ten skrypt?
To jest **główny panel sterowania** całego systemu FoodSave AI. Umożliwia uruchamianie, zatrzymywanie i monitorowanie wszystkich komponentów systemu przez przyjazny interfejs tekstowy.

#### 🚀 Jak uruchomić?
```bash
./scripts/main/foodsave-all.sh
```

#### ⚙️ Opcje menu
1. **🚀 Start Systemu** - Uruchom wszystkie serwisy
2. **🛑 Stop Systemu** - Zatrzymaj wszystkie serwisy
3. **📊 Status** - Sprawdź status wszystkich komponentów
4. **🔧 Konfiguracja** - Zmień ustawienia systemu
5. **💾 Backup/Restore** - Zarządzaj danymi
6. **🧪 Testy** - Sprawdź czy wszystko działa
7. **📚 Dokumentacja** - Otwórz przewodniki
8. **🔍 Diagnostyka** - Sprawdź problemy

#### 🔧 Co się dzieje w tle?
- Sprawdza czy Docker jest uruchomiony
- Weryfikuje dostępność portów
- Uruchamia kontenery z bazą danych, backendem, frontendem
- Sprawdza status wszystkich serwisów
- Wyświetla logi w czasie rzeczywistym

#### ❓ Rozwiązywanie problemów
**Problem:** Skrypt nie uruchamia się
```bash
# Sprawdź uprawnienia
chmod +x scripts/main/foodsave-all.sh

# Sprawdź czy Docker działa
docker info
```

**Problem:** Menu nie wyświetla się
```bash
# Sprawdź terminal
echo $TERM

# Uruchom w trybie interaktywnym
bash -i scripts/main/foodsave-all.sh
```

#### 📞 Wsparcie
- Dokumentacja: `docs/ALL_SCRIPTS_DOCUMENTATION.md`
- Logi: `logs/backend/server.log`

---

### 📜 `foodsave.sh` - Podstawowy Manager

#### 🎯 Co robi ten skrypt?
Prostszy manager systemu z podstawowymi funkcjami start/stop/status. Idealny dla szybkich operacji.

#### 🚀 Jak uruchomić?
```bash
./scripts/main/foodsave.sh start    # Uruchom system
./scripts/main/foodsave.sh stop     # Zatrzymaj system
./scripts/main/foodsave.sh status   # Sprawdź status
./scripts/main/foodsave.sh logs     # Wyświetl logi
```

#### ⚙️ Opcje
- `start` - Uruchom wszystkie serwisy
- `stop` - Zatrzymaj wszystkie serwisy
- `status` - Sprawdź status serwisów
- `logs` - Wyświetl logi systemu
- `backup` - Wykonaj backup
- `restore` - Przywróć z backupu

#### 🔧 Co się dzieje w tle?
- Sprawdza czy Docker działa
- Tworzy katalogi logów
- Uruchamia kontenery Docker
- Sprawdza zdrowie serwisów
- Wyświetla adresy URL

#### ❓ Rozwiązywanie problemów
**Problem:** Serwisy nie uruchamiają się
```bash
# Sprawdź Docker
docker info

# Sprawdź porty
netstat -tulpn | grep :8000
```

#### 📞 Wsparcie
- Sprawdź logi: `tail -f logs/backend/server.log`
- Dokumentacja: `docs/guides/deployment/DOCKER.md`

---

### 📜 `start_foodsave.sh` - Szybkie Uruchomienie

#### 🎯 Co robi ten skrypt?
Szybkie uruchomienie systemu bez dodatkowych opcji. Idealny dla początkujących.

#### 🚀 Jak uruchomić?
```bash
./start_foodsave.sh
```

#### ⚙️ Opcje
Brak opcji - skrypt uruchamia system z domyślnymi ustawieniami.

#### 🔧 Co się dzieje w tle?
- Sprawdza wymagania systemowe
- Uruchamia Docker Compose
- Czeka na gotowość serwisów
- Wyświetla adresy URL

#### ❓ Rozwiązywanie problemów
**Problem:** Skrypt nie kończy się
```bash
# Sprawdź logi
docker compose logs

# Sprawdź status
docker compose ps
```

#### 📞 Wsparcie
- Sprawdź status: `docker compose ps`
- Logi: `docker compose logs -f`

---

## 🛠️ Skrypty Development

### 📜 `dev-up.sh` - Środowisko Deweloperskie

#### 🎯 Co robi ten skrypt?
Uruchamia środowisko deweloperskie z hot-reload (automatyczne przeładowanie zmian) i dodatkowymi narzędziami do rozwoju.

#### 🚀 Jak uruchomić?
```bash
./scripts/development/dev-up.sh
```

#### ⚙️ Opcje
- `--monitoring` - Dodaj monitoring (Grafana, Prometheus)
- `--cache` - Włącz cache Redis
- `--logging` - Dodaj zaawansowane logowanie

#### 🔧 Co się dzieje w tle?
- Uruchamia serwisy w trybie development
- Włącza hot-reload dla frontendu
- Uruchamia debugger
- Tworzy development database
- Włącza verbose logging

#### ❓ Rozwiązywanie problemów
**Problem:** Hot-reload nie działa
```bash
# Sprawdź Node.js
node --version

# Restart frontend
docker compose restart foodsave-frontend
```

#### 📞 Wsparcie
- Dokumentacja: `docs/guides/development/SETUP.md`
- Logi dev: `logs/backend/dev.log`

---

### 📜 `dev-down.sh` - Zatrzymanie Dev

#### 🎯 Co robi ten skrypt?
Zatrzymuje środowisko deweloperskie i czyści zasoby.

#### 🚀 Jak uruchomić?
```bash
./scripts/development/dev-down.sh
```

#### ⚙️ Opcje
- `--clean` - Usuń wszystkie dane
- `--volumes` - Usuń volumes Docker

#### 🔧 Co się dzieje w tle?
- Zatrzymuje wszystkie kontenery dev
- Czyści cache
- Usuwa temporary files
- Resetuje development database

#### ❓ Rozwiązywanie problemów
**Problem:** Kontenery nie zatrzymują się
```bash
# Wymuszone zatrzymanie
docker compose down --force

# Usuń wszystkie kontenery
docker system prune -a
```

#### 📞 Wsparcie
- Sprawdź procesy: `ps aux | grep docker`

---

### 📜 `cleanup.sh` - Czyszczenie Systemu

#### 🎯 Co robi ten skrypt?
Czyści system z niepotrzebnych plików, cache i logów.

#### 🚀 Jak uruchomić?
```bash
./scripts/development/cleanup.sh
```

#### ⚙️ Opcje
- `--logs` - Usuń stare logi
- `--cache` - Wyczyść cache
- `--docker` - Wyczyść Docker
- `--all` - Pełne czyszczenie

#### 🔧 Co się dzieje w tle?
- Usuwa stare logi (>30 dni)
- Czyści cache aplikacji
- Usuwa nieużywane obrazy Docker
- Czyści temporary files
- Resetuje cache baz danych

#### ❓ Rozwiązywanie problemów
**Problem:** Brak miejsca na dysku
```bash
# Sprawdź użycie dysku
df -h

# Wyczyść Docker
docker system prune -a
```

#### 📞 Wsparcie
- Sprawdź miejsce: `df -h`
- Docker info: `docker system df`

---

## 🐳 Skrypty Docker

### 📜 `docker-manager.sh` - Zarządzanie Kontenerami

#### 🎯 Co robi ten skrypt?
Zaawansowany manager kontenerów Docker z monitoringiem i diagnostyką.

#### 🚀 Jak uruchomić?
```bash
./scripts/main/docker-manager.sh
```

#### ⚙️ Opcje menu
1. **📊 Status Kontenerów** - Sprawdź wszystkie kontenery
2. **🚀 Start/Stop** - Zarządzaj kontenerami
3. **🔍 Logi** - Wyświetl logi kontenerów
4. **🧹 Cleanup** - Wyczyść nieużywane zasoby
5. **📈 Monitoring** - Metryki kontenerów
6. **🔧 Konfiguracja** - Ustawienia Docker

#### 🔧 Co się dzieje w tle?
- Sprawdza status wszystkich kontenerów
- Monitoruje użycie zasobów
- Wyświetla logi w czasie rzeczywistym
- Wykonuje operacje Docker
- Generuje raporty

#### ❓ Rozwiązywanie problemów
**Problem:** Kontenery nie uruchamiają się
```bash
# Sprawdź Docker
docker info

# Sprawdź obrazy
docker images

# Sprawdź sieć
docker network ls
```

#### 📞 Wsparcie
- Docker docs: https://docs.docker.com/
- Sprawdź status: `docker ps -a`

---

### 📜 `build-all.sh` - Budowanie Obrazów

#### 🎯 Co robi ten skrypt?
Buduje wszystkie obrazy Docker potrzebne do uruchomienia systemu.

#### 🚀 Jak uruchomić?
```bash
./scripts/deployment/build-all.sh
```

#### ⚙️ Opcje
- `--no-cache` - Buduj bez cache
- `--push` - Wypchnij obrazy do registry
- `--optimize` - Optymalizuj rozmiar obrazów

#### 🔧 Co się dzieje w tle?
- Buduje obraz backend (Python/FastAPI)
- Buduje obraz frontend (React/Node.js)
- Buduje obraz database (PostgreSQL)
- Optymalizuje rozmiary obrazów
- Testuje obrazy

#### ❓ Rozwiązywanie problemów
**Problem:** Budowanie nie kończy się
```bash
# Sprawdź miejsce na dysku
df -h

# Wyczyść cache Docker
docker builder prune
```

#### 📞 Wsparcie
- Docker build docs: https://docs.docker.com/engine/reference/commandline/build/
- Sprawdź obrazy: `docker images`

---

### 📜 `deploy.sh` - Wdrażanie Systemu

#### 🎯 Co robi ten skrypt?
Wdraża system na serwer produkcyjny z wszystkimi ustawieniami.

#### 🚀 Jak uruchomić?
```bash
./scripts/deployment/deploy.sh
```

#### ⚙️ Opcje
- `--staging` - Wdrażaj na środowisko testowe
- `--production` - Wdrażaj na produkcję
- `--rollback` - Cofnij do poprzedniej wersji

#### 🔧 Co się dzieje w tle?
- Sprawdza wymagania serwera
- Kopiuje pliki konfiguracyjne
- Uruchamia kontenery produkcyjne
- Konfiguruje monitoring
- Testuje wdrożenie

#### ❓ Rozwiązywanie problemów
**Problem:** Wdrożenie nie działa
```bash
# Sprawdź logi
docker compose logs

# Sprawdź konfigurację
cat .env
```

#### 📞 Wsparcie
- Dokumentacja: `docs/guides/deployment/PRODUCTION.md`
- Sprawdź status: `docker compose ps`

---

## 📊 Skrypty Monitoring

### 📜 `health-check.sh` - Sprawdzanie Zdrowia

#### 🎯 Co robi ten skrypt?
Sprawdza zdrowie wszystkich komponentów systemu i wyświetla raport.

#### 🚀 Jak uruchomić?
```bash
./scripts/utils/health-check.sh
```

#### ⚙️ Opcje
- `--detailed` - Szczegółowy raport
- `--fix` - Automatyczne naprawianie problemów
- `--email` - Wyślij raport email

#### 🔧 Co się dzieje w tle?
- Sprawdza status wszystkich serwisów
- Testuje połączenia sieciowe
- Sprawdza użycie zasobów
- Weryfikuje bazy danych
- Generuje raport HTML

#### ❓ Rozwiązywanie problemów
**Problem:** Serwisy nie odpowiadają
```bash
# Sprawdź porty
netstat -tulpn

# Restart serwisów
docker compose restart
```

#### 📞 Wsparcie
- Monitoring docs: `docs/guides/deployment/MONITORING.md`
- Grafana: http://localhost:3001

---

### 📜 `logs.sh` - Zarządzanie Logami

#### 🎯 Co robi ten skrypt?
Zarządza logami systemu - wyświetla, filtruje i archiwizuje.

#### 🚀 Jak uruchomić?
```bash
./scripts/monitoring/logs.sh
```

#### ⚙️ Opcje
- `--follow` - Śledź logi w czasie rzeczywistym
- `--filter` - Filtruj logi
- `--archive` - Zarchiwizuj stare logi
- `--clean` - Wyczyść stare logi

#### 🔧 Co się dzieje w tle?
- Zbiera logi ze wszystkich serwisów
- Filtruje według poziomu (ERROR, WARNING, INFO)
- Archiwizuje stare logi
- Kompresuje pliki logów
- Wyświetla w czasie rzeczywistym

#### ❓ Rozwiązywanie problemów
**Problem:** Logi są za duże
```bash
# Wyczyść stare logi
find logs/ -name "*.log" -mtime +7 -delete

# Skompresuj logi
gzip logs/*.log
```

#### 📞 Wsparcie
- Logi backend: `logs/backend/`
- Logi frontend: `logs/frontend/`

---

### 📜 `backup.sh` - Backup Systemu

#### 🎯 Co robi ten skrypt?
Tworzy kopie zapasowe wszystkich danych systemu.

#### 🚀 Jak uruchomić?
```bash
./scripts/monitoring/backup.sh
```

#### ⚙️ Opcje
- `--full` - Pełny backup
- `--incremental` - Backup przyrostowy
- `--restore` - Przywróć z backupu
- `--schedule` - Ustaw automatyczne backupy

#### 🔧 Co się dzieje w tle?
- Tworzy backup bazy danych
- Kopiuje pliki konfiguracyjne
- Archiwizuje logi
- Kompresuje backup
- Weryfikuje integralność

#### ❓ Rozwiązywanie problemów
**Problem:** Backup nie działa
```bash
# Sprawdź miejsce na dysku
df -h

# Sprawdź uprawnienia
ls -la backups/
```

#### 📞 Wsparcie
- Backup docs: `docs/operations/BACKUP_SYSTEM.md`
- Sprawdź backupy: `ls -la backups/`

---

## 🔧 Dodatkowe Skrypty

### 📜 `test-dev-setup.sh` - Test Środowiska

#### 🎯 Co robi ten skrypt?
Testuje czy środowisko deweloperskie jest poprawnie skonfigurowane.

#### 🚀 Jak uruchomić?
```bash
bash scripts/test-dev-setup.sh
```

#### ⚙️ Opcje
Brak opcji - skrypt wykonuje pełny test środowiska.

#### 🔧 Co się dzieje w tle?
- Sprawdza wymagania systemowe
- Testuje Docker i Docker Compose
- Weryfikuje Node.js i npm
- Sprawdza porty
- Testuje połączenia sieciowe

---

### 📜 `check-ports.sh` - Sprawdzanie Portów

#### 🎯 Co robi ten skrypt?
Sprawdza czy porty używane przez system są dostępne.

#### 🚀 Jak uruchomić?
```bash
bash scripts/utils/check-ports.sh
```

#### ⚙️ Opcje
- `--fix` - Automatyczne zwolnienie portów
- `--kill` - Zatrzymaj procesy używające portów

#### 🔧 Co się dzieje w tle?
- Sprawdza porty 8000, 3000, 5432, 11434
- Identyfikuje procesy używające portów
- Sugeruje rozwiązania

---

## 📦 Zarchiwizowane Skrypty

### 🗑️ Co to są zarchiwizowane skrypty?

Zarchiwizowane skrypty to pliki, które były używane wcześniej, ale zostały zastąpione przez nowsze i lepsze wersje. Są przechowywane w katalogu `scripts/archive/` na wypadek, gdyby ktoś potrzebował przywrócić starą funkcjonalność.

### 📁 Struktura archiwum

```
scripts/archive/
├── deprecated/           # Przestarzałe skrypty
│   ├── foodsave_manager_simple.sh
│   ├── gui_refactor.sh
│   ├── install_missing_deps.sh
│   └── start_ollama.sh
├── unused_scripts/       # Nieużywane skrypty
│   ├── automation/       # Skrypty automatyzacji
│   ├── dev-setup.sh
│   ├── dev-status.sh
│   ├── dev-stop.sh
│   ├── dev-run-simple.sh
│   ├── foodsave-all.sh
│   ├── health-check.sh
│   ├── manage_app.sh
│   └── start_manager.sh
└── README.md            # Dokumentacja archiwum
```

### 🔧 Jak przywrócić zarchiwizowany skrypt?

#### 1. Sprawdź czy funkcjonalność jest dostępna
```bash
# Sprawdź czy funkcjonalność jest w głównych skryptach
./scripts/main/foodsave-all.sh --help
```

#### 2. Przywróć skrypt z archiwum
```bash
# Przykład przywrócenia skryptu
cp scripts/archive/deprecated/start_ollama.sh scripts/utils/
chmod +x scripts/utils/start_ollama.sh
```

#### 3. Przetestuj przywrócony skrypt
```bash
# Uruchom przywrócony skrypt
./scripts/utils/start_ollama.sh
```

### 📋 Lista zarchiwizowanych skryptów

#### 🗑️ Przestarzałe (deprecated/)
- **`foodsave_manager_simple.sh`** - Duplikat funkcjonalności z `foodsave-all.sh`
- **`gui_refactor.sh`** - Zastąpiony przez nowsze skrypty zarządzania
- **`install_missing_deps.sh`** - Oznaczony jako przestarzały w kodzie
- **`start_ollama.sh`** - Funkcjonalność wbudowana w główne skrypty

#### 🔄 Nieużywane (unused_scripts/)
- **`foodsave-all.sh`** - Stara wersja z backupu
- **`health-check.sh`** - Duplikat z `utils/health-check.sh`
- **`dev-setup.sh`** - Nieużywany skrypt deweloperski
- **`dev-status.sh`** - Nieużywany skrypt deweloperski
- **`dev-stop.sh`** - Nieużywany skrypt deweloperski
- **`dev-run-simple.sh`** - Nieużywany skrypt deweloperski
- **`manage_app.sh`** - Nieużywany skrypt zarządzania
- **`start_manager.sh`** - Nieużywany skrypt zarządzania

### 📞 Wsparcie dla zarchiwizowanych skryptów

#### 🆘 Potrzebujesz przywrócić skrypt?
1. Sprawdź czy funkcjonalność jest dostępna w głównych skryptach
2. Jeśli nie, przywróć z odpowiedniego katalogu archiwum
3. Zaktualizuj dokumentację
4. Przetestuj przywrócony skrypt

#### 📚 Dokumentacja archiwum
- **Dokumentacja archiwum:** `scripts/archive/README.md`
- **Plan archiwizacji:** `docs/SCRIPTS_ANALYSIS_AND_CLEANUP_PLAN.md`

---

## 📞 Wsparcie i Pomoc

### 🆘 Gdzie szukać pomocy?

1. **📚 Dokumentacja**
   - Ten przewodnik: `docs/SCRIPTS_USER_GUIDE.md`
   - Kompletna dokumentacja: `docs/ALL_SCRIPTS_DOCUMENTATION.md`
   - Spis treści: `docs/TOC.md`

2. **🐛 Problemy techniczne**
   - Sprawdź logi: `logs/backend/server.log`
   - Testy: `python scripts/test-dev-setup.sh`
   - Diagnostyka: `./scripts/main/foodsave-all.sh --diagnose`

3. **💬 Wsparcie społeczności**
   - GitHub Issues: https://github.com/your-username/foodsave-ai/issues
   - Discord: https://discord.gg/foodsave-ai
   - Email: support@foodsave-ai.com

### 🔧 Przydatne komendy

```bash
# Sprawdź status systemu
./scripts/main/foodsave-all.sh

# Wyświetl logi
tail -f logs/backend/server.log

# Sprawdź zdrowie
./scripts/utils/health-check.sh

# Backup
./scripts/monitoring/backup.sh

# Czyszczenie
./scripts/development/cleanup.sh
```

### 📋 Słownik terminów

- **Skrypt** - Plik z instrukcjami dla komputera
- **Terminal** - Okno tekstowe do wpisywania komend
- **Kontener** - Izolowane środowisko aplikacji
- **Port** - Numer używany przez aplikację do komunikacji
- **Log** - Plik z informacjami o działaniu aplikacji
- **Backup** - Kopia zapasowa danych
- **Cache** - Tymczasowe dane przyspieszające działanie
- **Archiwum** - Miejsce przechowywania starych plików

---

> **💡 Wskazówka:** Jeśli nie jesteś pewien jakiego skryptu użyć, zacznij od `foodsave-all.sh` - to główny panel sterowania całego systemu.

> **📅 Ostatnia aktualizacja:** 2025-07-19 