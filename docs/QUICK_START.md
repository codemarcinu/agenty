# 🚀 FoodSave AI - Szybki Start

> **Ostatnia aktualizacja:** 2025-07-18  
> **Status:** ✅ **PRODUKCYJNY** - Wszystkie systemy działają poprawnie

## 🎯 Wybór Interfejsu

FoodSave AI oferuje dwa interfejsy GUI:

### 🍽️ Uproszczony GUI (Zalecany dla większości użytkowników)
- **Chat-centric design** - Czat jako główny element
- **Szybkie akcje** - Gotowe komendy dla typowych zadań
- **Prosty interfejs** - Łatwy w użyciu
- **Responsive design** - Adaptacja do różnych rozmiarów

### 🤖 Pełny GUI (Dla zaawansowanych użytkowników)
- **AI Command Center** - Zarządzanie 38 agentami
- **System monitoring** - Real-time monitoring
- **Multi-tab chat** - Wiele sesji czatu
- **Agent control panel** - Szczegółowe zarządzanie

---

## 🚀 Szybki Start

### Opcja 1: Uproszczony GUI (Zalecane)

```bash
# Sprawdź wymagania
./scripts/run_simplified_gui.sh --check

# Uruchom uproszczony GUI
./scripts/run_simplified_gui.sh
```

### Opcja 2: Pełny GUI

```bash
# Uruchom pełny GUI
./scripts/launch_scripts_gui.sh
```

### Opcja 3: Backend + Frontend

```bash
# Uruchom backend
./scripts/main/start.sh dev

# W osobnym terminalu uruchom frontend
cd frontend && npm run dev
```

---

## 📋 Wymagania Systemowe

### Podstawowe Wymagania
- **Python 3.11+** - Główny język aplikacji
- **Docker & Docker Compose** - Kontenery aplikacji
- **Node.js 18+** - Frontend (opcjonalne)
- **4GB RAM** - Minimum dla działania
- **10GB wolnego miejsca** - Baza danych i logi

### Sprawdzenie Wymagań

```bash
# Sprawdź Python
python3 --version

# Sprawdź Docker
docker --version
docker-compose --version

# Sprawdź Node.js (opcjonalne)
node --version
npm --version
```

---

## 🔧 Instalacja

### Krok 1: Klonowanie Repozytorium

```bash
git clone https://github.com/youruser/foodsave-ai.git
cd foodsave-ai
```

### Krok 2: Konfiguracja Środowiska

```bash
# Utwórz wirtualne środowisko
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# lub
.venv\Scripts\activate  # Windows

# Zainstaluj zależności
pip install -r requirements.txt
```

### Krok 3: Konfiguracja Docker

```bash
# Sprawdź czy Docker działa
docker ps

# Przygotuj plik .env (jeśli nie istnieje)
cp .env.example .env
```

---

## 🚀 Uruchomienie

### Szybki Start z Uproszczonym GUI

```bash
# Uruchom uproszczony GUI (automatycznie sprawdzi wymagania)
./scripts/run_simplified_gui.sh
```

**Co się dzieje:**
1. ✅ Sprawdzenie wymagań systemowych
2. ✅ Automatyczna instalacja zależności (PySide6, structlog)
3. ✅ Sprawdzenie backendu
4. ✅ Uruchomienie uproszczonego GUI

### Pełny Start z Backendem

```bash
# Uruchom wszystkie serwisy
./scripts/main/start.sh dev

# W osobnym terminalu uruchom GUI
./scripts/launch_scripts_gui.sh
```

---

## 🎯 Pierwsze Użycie

### Uproszczony GUI

1. **Wybierz agenta** z dropdown menu
2. **Użyj quick actions** dla szybkich zadań:
   - 🛒 "Zrobiłem zakupy" - Analiza paragonów
   - 🌤️ "Jaka pogoda?" - Aktualna pogoda
   - 🍳 "Co na śniadanie?" - Sugestie kulinarne
3. **Wyślij wiadomość** w polu tekstowym
4. **Upload plików** dla analizy obrazów

### Pełny GUI

1. **Sprawdź status agentów** w panelu kontrolnym
2. **Otwórz chat** w centralnym panelu
3. **Wybierz agenta** z listy 38 dostępnych
4. **Monitoruj system** w prawym panelu

---

## 📊 Dostępne Endpointy

Po uruchomieniu systemu:

| Serwis | URL | Opis |
|--------|-----|------|
| **Backend API** | http://localhost:8000 | Główny API |
| **API Docs** | http://localhost:8000/docs | Dokumentacja Swagger |
| **Frontend** | http://localhost:3000 | Interfejs webowy |
| **Ollama** | http://localhost:11434 | Modele AI |
| **Grafana** | http://localhost:3001 | Monitoring (admin/admin) |
| **Prometheus** | http://localhost:9090 | Metryki |

---

## 🔧 Konfiguracja

### Plik .env

```bash
# Edytuj konfigurację
nano .env

# Główne ustawienia
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
DATABASE_URL=postgresql://user:pass@localhost:5432/foodsave
OLLAMA_URL=http://localhost:11434
```

### Ustawienia GUI

```bash
# Konfiguracja uproszczonego GUI
nano gui/core/config.py

# Główne ustawienia
backend_url = "http://localhost:8000"
backend_timeout = 30
maximized = False
```

---

## 🛠️ Rozwiązywanie Problemów

### Problem: "Backend nie działa"

```bash
# Sprawdź status backendu
./scripts/main/manager.sh status

# Uruchom backend
./scripts/main/start.sh dev

# Sprawdź logi
./scripts/main/manager.sh logs backend
```

### Problem: "GUI się nie uruchamia"

```bash
# Sprawdź wymagania
./scripts/run_simplified_gui.sh --check

# Zainstaluj zależności
pip install PySide6 structlog

# Sprawdź Python
python3 --version
```

### Problem: "Porty zajęte"

```bash
# Zwolnij porty
./scripts/free-ports.sh

# Sprawdź porty
./scripts/check-ports.sh
```

---

## 📚 Następne Kroki

### Dokumentacja
- [Funkcje systemu](guides/user/FEATURES.md) - Szczegółowy opis funkcji
- [Rozwiązywanie problemów](guides/user/TROUBLESHOOTING.md) - Pomoc techniczna
- [Dokumentacja API](core/API_REFERENCE.md) - Endpointy API
- [Przewodnik agentów](reference/AGENTS_GUIDE.md) - Agenty AI

### Rozwój
- [Konfiguracja środowiska](guides/development/SETUP.md) - Setup developerski
- [Przewodnik testowania](guides/development/TESTING.md) - Testy aplikacji
- [Zasady kontrybucji](guides/development/CONTRIBUTING.md) - Jak pomóc

### Deployment
- [Wdrażanie produkcyjne](guides/deployment/PRODUCTION.md) - Deployment
- [Monitoring](guides/deployment/MONITORING.md) - Monitoring systemu
- [Backup](operations/BACKUP_SYSTEM.md) - System backupów

---

## 🆘 Wsparcie

### Szybka Pomoc
1. **Sprawdź logi**: `./scripts/main/manager.sh logs [service]`
2. **Health check**: `./scripts/development/health-check.sh`
3. **Testy**: `./scripts/run_tests.sh`
4. **Dokumentacja**: `docs/`

### Kontakt
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Wiki**: GitHub Wiki

---

> **💡 Wskazówka:** Zacznij od uproszczonego GUI - jest łatwiejszy w użyciu i zawiera wszystkie najważniejsze funkcje! 