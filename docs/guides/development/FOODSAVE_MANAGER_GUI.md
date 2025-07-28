# FoodSave Manager - Aplikacja GUI do Zarządzania Backendem

## Opis

**FoodSave Manager** to aplikacja GUI napisana w Pythonie z wykorzystaniem biblioteki **Tkinter**, która umożliwia łatwe zarządzanie backendem FoodSave AI bez konieczności używania wiersza poleceń.

## Funkcjonalności

### 🎯 Główne możliwości

1. **Zarządzanie usługami backendu**
   - Uruchamianie/zatrzymywanie backendu FastAPI
   - Restart backendu
   - Kontrola usług Docker (PostgreSQL, Redis, Ollama)

2. **Monitoring statusu**
   - Sprawdzanie statusu wszystkich usług w czasie rzeczywistym
   - Wizualne wskaźniki stanu (✅ DZIAŁA / ❌ NIE DZIAŁA)
   - Automatyczne odświeżanie statusu

3. **Podgląd logów**
   - Logi backendu w czasie rzeczywistym
   - Logi kontenerów Docker
   - Czyszczenie logów

4. **Testowanie API**
   - Automatyczne testy endpointów
   - Sprawdzanie health check
   - Testowanie chat API

5. **Konfiguracja**
   - Ustawianie portu, hosta, środowiska
   - Ładowanie plików .env
   - Zapisywanie konfiguracji

## Instalacja i uruchomienie

### Wymagania

- Python 3.12+
- Tkinter (wbudowany w Python)
- Docker i Docker Compose
- Zainstalowane zależności backendu

### Uruchomienie

```bash
# Przejście do katalogu projektu
cd /path/to/foodsave-ai

# Uruchomienie aplikacji
python foodsave_manager.py
```

## Interfejs użytkownika

### Panel Statusu Usług

Wyświetla aktualny status wszystkich usług:
- **Backend (FastAPI)** - główna aplikacja
- **Ollama (AI Models)** - modele językowe
- **PostgreSQL** - baza danych
- **Redis (Cache)** - cache i sesje

### Panel Kontroli

Przyciski do zarządzania usługami:

#### 🚀 Start Backend
- Uruchamia backend FastAPI
- Ustawia zmienne środowiskowe
- Wyświetla logi w czasie rzeczywistym

#### ⏹️ Stop Backend
- Zatrzymuje proces backendu
- Bezpieczne zamykanie aplikacji

#### 🔄 Restart Backend
- Zatrzymuje i ponownie uruchamia backend
- Przydatne po zmianach w kodzie

#### 🐳 Start Docker Services
- Uruchamia kontenery Docker
- PostgreSQL, Redis, Ollama
- Używa docker-compose

#### 🛑 Stop Docker Services
- Zatrzymuje wszystkie kontenery
- Używa docker-compose down

#### 📊 Check All Services
- Sprawdza status wszystkich usług
- Aktualizuje wskaźniki wizualne

#### 🧪 Test API
- Testuje health endpoint
- Testuje chat endpoint
- Wyświetla wyniki w logach

#### 📁 Open Logs Directory
- Otwiera katalog z logami
- Obsługuje różne systemy operacyjne

### Panel Logów

#### 📋 Backend Logs
- Wyświetla logi z pliku `logs/backend/app.log`
- Pokazuje ostatnie wpisy

#### 🐳 Docker Logs
- Logi z kontenerów Docker
- PostgreSQL, Redis, Ollama
- Ostatnie 10 linii z każdego kontenera

#### 🧹 Clear
- Czyści panel logów
- Resetuje wyświetlacz

### Panel Konfiguracji

#### Ustawienia
- **Port Backend** - port na którym działa backend (domyślnie 8000)
- **Host** - adres hosta (domyślnie 0.0.0.0)
- **Environment** - środowisko (development/production/testing)

#### Przyciski
- **⚙️ Load .env** - ładuje konfigurację z pliku .env
- **💾 Save Config** - zapisuje konfigurację do JSON
- **🔧 Setup Environment** - konfiguruje środowisko

## Struktura aplikacji

```
foodsave_manager.py
├── FoodSaveManager (klasa główna)
│   ├── setup_ui() - konfiguracja interfejsu
│   ├── create_status_panel() - panel statusu
│   ├── create_control_panel() - panel kontroli
│   ├── create_logs_panel() - panel logów
│   ├── create_config_panel() - panel konfiguracji
│   ├── check_services_status() - sprawdzanie statusu
│   ├── start_backend() - uruchamianie backendu
│   ├── stop_backend() - zatrzymywanie backendu
│   ├── restart_backend() - restart backendu
│   ├── start_docker_services() - uruchamianie Docker
│   ├── stop_docker_services() - zatrzymywanie Docker
│   ├── test_api() - testowanie API
│   ├── show_logs() - wyświetlanie logów
│   └── setup_environment() - konfiguracja środowiska
```

## Konfiguracja

### Zmienne środowiskowe

Aplikacja automatycznie ustawia:
- `PYTHONPATH` - ścieżka do katalogu src
- `PORT` - port backendu
- `HOST` - adres hosta
- `ENVIRONMENT` - środowisko

### Plik konfiguracyjny

Konfiguracja jest zapisywana w `foodsave_manager_config.json`:
```json
{
  "port": "8000",
  "host": "0.0.0.0",
  "environment": "development"
}
```

## Rozwiązywanie problemów

### Backend się nie uruchamia

1. Sprawdź czy masz zainstalowane zależności:
   ```bash
   pip install -r src/backend/requirements.txt
   ```

2. Sprawdź czy plik `run_backend.py` istnieje

3. Sprawdź logi w panelu logów

### Docker services się nie uruchamiają

1. Sprawdź czy Docker jest uruchomiony:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Sprawdź czy plik `docker-compose.yml` istnieje

3. Sprawdź logi Docker w panelu logów

### Problem z importami

1. Upewnij się, że jesteś w katalogu głównym projektu

2. Sprawdź czy katalog `src` istnieje

3. Sprawdź czy `PYTHONPATH` jest ustawiony poprawnie

### Problem z logami

1. Sprawdź czy katalog `logs` istnieje:
   ```bash
   mkdir -p logs/backend
   ```

2. Sprawdź uprawnienia do zapisu

3. Użyj przycisku "🔧 Setup Environment"

## Przykłady użycia

### Podstawowy workflow

1. **Uruchom aplikację**:
   ```bash
   python foodsave_manager.py
   ```

2. **Sprawdź status usług**:
   - Kliknij "📊 Check All Services"

3. **Uruchom usługi Docker**:
   - Kliknij "🐳 Start Docker Services"

4. **Uruchom backend**:
   - Kliknij "🚀 Start Backend"

5. **Przetestuj API**:
   - Kliknij "🧪 Test API"

### Zaawansowane użycie

#### Konfiguracja niestandardowa

1. Kliknij "⚙️ Load .env" i wybierz plik konfiguracyjny
2. Dostosuj ustawienia w panelu konfiguracji
3. Kliknij "💾 Save Config" aby zapisać

#### Monitoring w czasie rzeczywistym

1. Uruchom backend
2. Kliknij "📋 Backend Logs" aby zobaczyć logi
3. Monitoruj status usług w panelu statusu

#### Debugowanie

1. Użyj "🐳 Docker Logs" aby zobaczyć logi kontenerów
2. Sprawdź status każdej usługi osobno
3. Użyj "🧪 Test API" aby przetestować endpointy

## Integracja z projektem

### Struktura plików

```
foodsave-ai/
├── foodsave_manager.py          # Aplikacja GUI
├── run_backend.py              # Skrypt uruchamiania backendu
├── src/backend/                # Kod backendu
├── logs/                       # Katalog logów
│   └── backend/
├── docker-compose.yml          # Konfiguracja Docker
└── env.dev.example            # Szablon konfiguracji
```

### Automatyzacja

Aplikacja automatycznie:
- Ustawia `PYTHONPATH`
- Konfiguruje zmienne środowiskowe
- Tworzy katalogi logów
- Kopiuje pliki konfiguracyjne

### Bezpieczeństwo

- Wszystkie operacje są wykonywane w wątkach
- Bezpieczne zamykanie procesów
- Obsługa błędów i wyjątków
- Logowanie wszystkich operacji

## Rozszerzenia

### Dodanie nowych usług

Aby dodać nową usługę:

1. Dodaj status w `create_status_panel()`
2. Dodaj funkcję sprawdzania w `check_services_status()`
3. Dodaj przyciski kontroli w `create_control_panel()`

### Dodanie nowych testów

Aby dodać nowy test API:

1. Dodaj funkcję testu w `test_api()`
2. Dodaj przycisk w interfejsie
3. Dodaj obsługę wyników

### Dodanie nowych logów

Aby dodać nowe źródło logów:

1. Dodaj funkcję w `show_logs()`
2. Dodaj przycisk w panelu logów
3. Dodaj obsługę różnych formatów

## Wsparcie

### Logi aplikacji

Wszystkie operacje są logowane w panelu logów z timestampami:
```
[14:30:15] 🚀 Backend uruchamiany...
[14:30:16] ✅ Backend uruchomiony na http://0.0.0.0:8000
[14:30:17] 🧪 Testowanie API...
[14:30:18] ✅ Health endpoint: OK
```

### Diagnostyka

Aplikacja automatycznie:
- Sprawdza wymagane pliki
- Weryfikuje konfigurację
- Testuje połączenia
- Wyświetla błędy w logach

### Pomoc

- Wszystkie przyciski mają opisowe etykiety
- Logi zawierają szczegółowe informacje
- Status usług jest wizualnie oznaczony
- Błędy są wyświetlane w messagebox

FoodSave Manager to kompleksowe narzędzie do zarządzania backendem FoodSave AI, które upraszcza proces developmentu i deploymentu. 