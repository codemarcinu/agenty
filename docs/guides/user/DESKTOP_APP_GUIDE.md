# 🖥️ FoodSave AI Desktop Application - Przewodnik Użytkownika

## 📋 Przegląd

FoodSave AI Desktop Application to natywna aplikacja desktopowa, która łączy wygodę GUI z mocą backendu FastAPI oraz frontendu Next.js. Aplikacja działa w zasobniku systemowym (tray) i uruchamia lokalny serwer API oraz może uruchamiać frontend.

## 🚀 Szybkie Uruchomienie

### Metoda 1: Skrypt Uruchamiający (Zalecane)

```bash
./run_desktop.sh
```

### Metoda 2: Ręczne Uruchomienie

```bash
# Aktywuj virtual environment
source .venv/bin/activate

# Ustaw zmienne środowiskowe
export PYTHONPATH="$(pwd)/src"
export QT_QPA_PLATFORM_PLUGIN_PATH="$(pwd)/.venv/lib/python3.12/site-packages/PyQt5/Qt5/plugins"
export QT_DEBUG_PLUGINS=0

# Uruchom aplikację
python3 -m gui.launcher
```

## 🎯 Funkcje Aplikacji

### System Tray (Zasobnik Systemowy)

Po uruchomieniu aplikacji, ikona FoodSave AI pojawi się w zasobniku systemowym. Kliknij prawym przyciskiem myszy, aby otworzyć menu:

- **🌐 Panel Web** - Otwiera panel web (Swagger UI) w przeglądarce
- **🎨 Frontend** - Uruchamia/zatrzymuje frontend Next.js
- **⚙️ Ustawienia** - Konfiguracja aplikacji
- **ℹ️ O programie** - Informacje o aplikacji
- **📊 Status** - Sprawdź status backendu i frontendu
- **❌ Wyjście** - Zamknij aplikację

### Panel Web (Backend)

Panel web jest dostępny pod adresem: `http://127.0.0.1:8000/docs`

Zawiera:
- Dokumentację API (Swagger UI)
- Interaktywne testy endpointów
- Schemat OpenAPI

### Frontend Next.js

Frontend jest dostępny pod adresem: `http://localhost:3000`

Zawiera:
- Nowoczesny interfejs użytkownika
- Dashboard z statystykami
- Analizę paragonów
- Zarządzanie zapasami
- Chat z AI
- Monitoring systemu

## ⚙️ Konfiguracja

### Wymagania dla Frontendu

Aby uruchomić frontend z aplikacji desktopowej, potrzebujesz:

1. **Node.js 18+** - Sprawdź czy jest zainstalowany:
   ```bash
   node --version
   ```

2. **Zależności frontendu** - Zainstaluj je w katalogu `frontend/`:
   ```bash
   cd frontend
   npm install
   ```

### Ustawienia Aplikacji

W oknie **Ustawienia** możesz skonfigurować:

- **Host i Port** - Adres backendu (domyślnie: 127.0.0.1:8000)
- **Motyw** - Jasny/Ciemny
- **Język** - Polski/Angielski
- **Powiadomienia** - Włącz/Wyłącz
- **Autostart** - Uruchom przy starcie systemu
- **Logowanie** - Poziom logów

### Zmienne Środowiskowe

Możesz ustawić następujące zmienne środowiskowe:

```bash
export PYTHONPATH="/ścieżka/do/projektu/src"
export QT_QPA_PLATFORM_PLUGIN_PATH="/ścieżka/do/.venv/lib/python3.12/site-packages/PyQt5/Qt5/plugins"
export QT_DEBUG_PLUGINS=0
```

## 🔧 Rozwiązywanie Problemów

### Problem: "Could not load the Qt platform plugin"

**Rozwiązanie:**
```bash
# Zainstaluj wymagane biblioteki systemowe
sudo apt update
sudo apt install libxcb-xinerama0 libxcb-xinerama0-dev libxkbcommon-x11-0 libxcb1 libxcb-util1 libgl1-mesa-glx libglib2.0-0 qtbase5-dev qtbase5-dev-tools

# Ustaw zmienne środowiskowe
export QT_QPA_PLATFORM_PLUGIN_PATH="$(pwd)/.venv/lib/python3.12/site-packages/PyQt5/Qt5/plugins"
```

### Problem: Backend nie odpowiada

**Sprawdź:**
1. Czy port 8000 jest wolny: `netstat -tlnp | grep 8000`
2. Czy backend się uruchomił: `curl http://127.0.0.1:8000/health`
3. Logi aplikacji w terminalu

### Problem: Frontend nie uruchamia się

**Sprawdź:**
1. Czy Node.js jest zainstalowany: `node --version`
2. Czy zależności są zainstalowane: `cd frontend && npm install`
3. Czy port 3000 jest wolny: `netstat -tlnp | grep 3000`
4. Logi w terminalu aplikacji

### Problem: Ikona nie pojawia się w tray

**Sprawdź:**
1. Czy środowisko graficzne działa
2. Czy nie uruchamiasz przez SSH bez X11 forwarding
3. Czy masz uprawnienia do wyświetlania ikon w tray

## 📁 Struktura Plików

```
gui/
├── launcher.py          # Główny plik uruchamiający
├── tray.py              # System tray i menu
├── windows/
│   ├── about.py         # Okno "O programie"
│   └── settings.py      # Okno ustawień
├── icons/
│   └── assist.svg       # Ikona aplikacji
└── resources.qrc        # Zasoby Qt

frontend/                 # Frontend Next.js
├── package.json         # Zależności Node.js
├── src/                 # Kod źródłowy React
└── ...

run_desktop.sh           # Skrypt uruchamiający
requirements-desktop.txt  # Zależności dla aplikacji desktopowej
```

## 🛠️ Rozwój

### Dodawanie Nowych Okien

1. Utwórz nowy plik w `gui/windows/`
2. Dziedzicz po `QDialog`
3. Dodaj do menu w `gui/tray.py`

### Modyfikacja Menu

Edytuj `gui/tray.py` w metodzie `_create_menu()`.

### Zmiana Ikony

Zastąp `gui/icons/assist.svg` i zaktualizuj `gui/resources.qrc`.

### Rozwój Frontendu

```bash
# Uruchom frontend w trybie deweloperskim
cd frontend
npm run dev

# Lub uruchom przez aplikację desktopową
# Kliknij prawym przyciskiem na ikonę w tray → 🎨 Frontend
```

## 📞 Wsparcie

W przypadku problemów:

1. Sprawdź logi w terminalu
2. Uruchom z debugowaniem: `export QT_DEBUG_PLUGINS=1`
3. Sprawdź status systemu: Kliknij prawym na ikonę → 📊 Status

## 🔄 Aktualizacje

Aby zaktualizować aplikację:

```bash
git pull
pip install -r requirements-desktop.txt
cd frontend && npm install
./run_desktop.sh
```

---

**FoodSave AI Desktop Application** - Łączy wygodę natywnego GUI z mocą nowoczesnego web development! 🖥️🌐 