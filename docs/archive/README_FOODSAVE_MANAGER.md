# FoodSave Manager - Aplikacja GUI do Zarządzania Backendem

![FoodSave Manager](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-red.svg)
![Docker](https://img.shields.io/badge/Docker-Containers-blue.svg)

## 🚀 Szybki Start

```bash
# Uruchomienie aplikacji
./start_manager.sh

# Lub bezpośrednio
python foodsave_manager.py
```

## 📋 Opis

**FoodSave Manager** to aplikacja GUI napisana w Pythonie z wykorzystaniem biblioteki **Tkinter**, która umożliwia łatwe zarządzanie backendem FoodSave AI bez konieczności używania wiersza poleceń.

### ✨ Główne funkcjonalności

- 🎯 **Zarządzanie usługami backendu** - uruchamianie/zatrzymywanie FastAPI
- 📊 **Monitoring statusu** - sprawdzanie stanu wszystkich usług w czasie rzeczywistym
- 📋 **Podgląd logów** - logi backendu i kontenerów Docker
- 🧪 **Testowanie API** - automatyczne testy endpointów
- ⚙️ **Konfiguracja** - ustawianie portów, hostów, środowisk

## 🛠️ Instalacja

### Wymagania

- **Python 3.12+**
- **Tkinter** (wbudowany w Python)
- **Docker** i **Docker Compose** (opcjonalne)
- **Zainstalowane zależności backendu**

### Automatyczna instalacja

```bash
# Sprawdzenie wymagań
./start_manager.sh check

# Instalacja zależności
./start_manager.sh install

# Konfiguracja środowiska
./start_manager.sh setup

# Uruchomienie aplikacji
./start_manager.sh
```

### Ręczna instalacja

```bash
# 1. Sprawdź czy masz Python 3.12+
python3 --version

# 2. Sprawdź Tkinter
python3 -c "import tkinter; print('Tkinter OK')"

# 3. Zainstaluj zależności
pip install requests

# 4. Uruchom aplikację
python3 foodsave_manager.py
```

## 🖥️ Interfejs użytkownika

### Panel Statusu Usług

Wyświetla aktualny status wszystkich usług z wizualnymi wskaźnikami:

- ✅ **Backend (FastAPI)** - główna aplikacja
- ✅ **Ollama (AI Models)** - modele językowe  
- ✅ **PostgreSQL** - baza danych
- ✅ **Redis (Cache)** - cache i sesje

### Panel Kontroli

Przyciski do zarządzania usługami:

| Przycisk | Funkcja |
|----------|---------|
| 🚀 **Start Backend** | Uruchamia backend FastAPI |
| ⏹️ **Stop Backend** | Zatrzymuje proces backendu |
| 🔄 **Restart Backend** | Restartuje backend |
| 🐳 **Start Docker Services** | Uruchamia kontenery Docker |
| 🛑 **Stop Docker Services** | Zatrzymuje kontenery Docker |
| 📊 **Check All Services** | Sprawdza status wszystkich usług |
| 🧪 **Test API** | Testuje endpointy API |
| 📁 **Open Logs Directory** | Otwiera katalog z logami |

### Panel Logów

- **📋 Backend Logs** - logi z pliku `logs/backend/app.log`
- **🐳 Docker Logs** - logi z kontenerów Docker
- **🧹 Clear** - czyści panel logów

### Panel Konfiguracji

- **Port Backend** - port na którym działa backend (domyślnie 8000)
- **Host** - adres hosta (domyślnie 0.0.0.0)
- **Environment** - środowisko (development/production/testing)
- **⚙️ Load .env** - ładuje konfigurację z pliku .env
- **💾 Save Config** - zapisuje konfigurację do JSON
- **🔧 Setup Environment** - konfiguruje środowisko

## 📖 Przykłady użycia

### Podstawowy workflow

1. **Uruchom aplikację**:
   ```bash
   ./start_manager.sh
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

## 🔧 Konfiguracja

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

## 🐛 Rozwiązywanie problemów

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

## 📁 Struktura plików

```
foodsave-ai/
├── foodsave_manager.py          # Aplikacja GUI
├── start_manager.sh             # Skrypt uruchomieniowy
├── run_backend.py              # Skrypt uruchamiania backendu
├── src/backend/                # Kod backendu
├── logs/                       # Katalog logów
│   └── backend/
├── docker-compose.yml          # Konfiguracja Docker
└── env.dev.example            # Szablon konfiguracji
```

## 🔒 Bezpieczeństwo

- Wszystkie operacje są wykonywane w wątkach
- Bezpieczne zamykanie procesów
- Obsługa błędów i wyjątków
- Logowanie wszystkich operacji

## 📝 Logi aplikacji

Wszystkie operacje są logowane w panelu logów z timestampami:
```
[14:30:15] 🚀 Backend uruchamiany...
[14:30:16] ✅ Backend uruchomiony na http://0.0.0.0:8000
[14:30:17] 🧪 Testowanie API...
[14:30:18] ✅ Health endpoint: OK
```

## 🚀 Integracja z projektem

### Automatyzacja

Aplikacja automatycznie:
- Ustawia `PYTHONPATH`
- Konfiguruje zmienne środowiskowe
- Tworzy katalogi logów
- Kopiuje pliki konfiguracyjne

### Diagnostyka

Aplikacja automatycznie:
- Sprawdza wymagane pliki
- Weryfikuje konfigurację
- Testuje połączenia
- Wyświetla błędy w logach

## 📚 Dokumentacja

- [Przewodnik uruchamiania backendu lokalnie](docs/guides/development/BACKEND_LOCAL_SETUP.md)
- [Dokumentacja aplikacji GUI](docs/guides/development/FOODSAVE_MANAGER_GUI.md)

## 🤝 Wsparcie

### Pomoc

- Wszystkie przyciski mają opisowe etykiety
- Logi zawierają szczegółowe informacje
- Status usług jest wizualnie oznaczony
- Błędy są wyświetlane w messagebox

### Rozszerzenia

Aplikacja jest łatwo rozszerzalna:
- Dodawanie nowych usług
- Dodawanie nowych testów API
- Dodawanie nowych źródeł logów

## 📄 Licencja

Ten projekt jest częścią FoodSave AI i podlega tym samym warunkom licencyjnym.

---

**FoodSave Manager** to kompleksowe narzędzie do zarządzania backendem FoodSave AI, które upraszcza proces developmentu i deploymentu. 