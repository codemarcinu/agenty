# FoodSave AI - Instalacja i Uruchamianie

## Instalacja

### Opcja 1: Instalacja w trybie deweloperskim (zalecane)

```bash
# Sklonuj repozytorium
git clone https://github.com/foodsave-ai/foodsave-ai.git
cd foodsave-ai

# Utwórz środowisko wirtualne
python3 -m venv .venv
source .venv/bin/activate

# Zainstaluj pakiet w trybie deweloperskim
pip install -e .

# Lub z dodatkowymi zależnościami GUI
pip install -e ".[gui]"
```

### Opcja 2: Instalacja z pliku requirements

```bash
# Zainstaluj podstawowe zależności
pip install -r requirements.txt

# Zainstaluj zależności GUI
pip install -r requirements-desktop.txt
```

### Opcja 3: Instalacja z PyPI (gdy będzie dostępne)

```bash
pip install foodsave-ai[gui]
```

## Uruchamianie

### GUI Application

```bash
# Uruchom GUI (automatycznie uruchomi backend)
foodsave-gui

# Lub bezpośrednio
python -m gui.app
```

### Backend Only

```bash
# Uruchom tylko backend
foodsave-backend

# Lub bezpośrednio
python -m src.backend.main
```

### Skrypt sekwencyjny (zalecany)

```bash
# Uruchom pełną aplikację z automatycznym zarządzaniem
./start_sekwencyjny.sh
```

## Struktura pakietu

Po instalacji w trybie deweloperskim (`pip install -e .`), Python automatycznie znajdzie wszystkie moduły:

```
foodsave-ai/
├── src/                    # Backend modules
│   ├── backend/
│   ├── api/
│   └── core/
├── gui/                    # GUI modules
│   ├── app.py             # Main GUI entry point
│   ├── core/
│   └── windows/
└── tests/                  # Test modules
```

## Rozwiązywanie problemów

### Problem: "Module not found"

Jeśli pojawi się błąd `ModuleNotFoundError`, upewnij się, że:

1. Pakiet jest zainstalowany w trybie deweloperskim:
   ```bash
   pip install -e .
   ```

2. Środowisko wirtualne jest aktywne:
   ```bash
   source .venv/bin/activate
   ```

3. Python może znaleźć pakiet:
   ```bash
   python -c "import gui; print('GUI package found')"
   ```

### Problem: Brak zależności GUI

```bash
# Zainstaluj zależności GUI
pip install PySide6 qasync httpx

# Lub użyj extras
pip install -e ".[gui]"
```

### Problem: Błędy Qt

```bash
# Sprawdź czy Qt jest zainstalowane
python -c "from PySide6.QtWidgets import QApplication; print('Qt OK')"

# Jeśli nie, zainstaluj systemowe zależności Qt
sudo apt install qt6-base-dev  # Ubuntu/Debian
sudo dnf install qt6-qtbase-devel  # Fedora
```

## Konfiguracja środowiska

### Zmienne środowiskowe

```bash
# Backend URL
export FOODSAVE_BACKEND_URL=http://localhost:8000

# Log level
export FOODSAVE_LOG_LEVEL=INFO

# GUI theme
export FOODSAVE_GUI_THEME=auto
```

### Plik konfiguracyjny

Konfiguracja GUI jest zapisywana w:
```
~/.config/foodsave-ai/gui_config.json
```

## Development

### Instalacja zależności deweloperskich

```bash
pip install -e ".[dev]"
```

### Uruchamianie testów

```bash
# Wszystkie testy
pytest

# Tylko testy jednostkowe
pytest tests/unit/

# Testy GUI
pytest tests/e2e/test_gui_e2e.py
```

### Formatowanie kodu

```bash
# Formatowanie z black
black .

# Linting z ruff
ruff check .

# Type checking z mypy
mypy .
```

## Pakowanie aplikacji

### Desktop application

```bash
# Zainstaluj zależności pakowania
pip install -e ".[desktop]"

# Utwórz aplikację desktopową
pyinstaller --onefile gui/app.py
```

### Docker

```bash
# Zbuduj obraz Docker
docker build -t foodsave-ai .

# Uruchom kontener
docker run -p 8000:8000 foodsave-ai
```

## Migracja z poprzednich wersji

Jeśli używasz starszej wersji z manipulacją `sys.path`:

1. Usuń wszystkie linie `sys.path.insert()` z kodu
2. Zainstaluj pakiet w trybie deweloperskim
3. Użyj importów względnych lub bezwzględnych

Przykład migracji:
```python
# PRZED (stary sposób)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from gui.core.config import get_config

# PO (nowy sposób)
from gui.core.config import get_config
```

## Wsparcie

- **Dokumentacja**: `docs/`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions 