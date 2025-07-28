# 🛠️ Development Guide

## 🚀 Szybki start dla deweloperów

### 1. Przygotowanie środowiska

```bash
# Klonowanie repozytorium
git clone https://github.com/codemarcinu/agenty.git
cd agenty

# Utworzenie środowiska wirtualnego
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows

# Instalacja zależności
pip install -r requirements-console.txt
```

### 2. Uruchomienie w trybie deweloperskim

```bash
# Szybki start
./run_dev.sh

# Lub ręcznie
source venv/bin/activate
python -m console_app.main --debug
```

### 3. Uruchomienie testów

```bash
# Wszystkie testy
python test_app.py

# Test konkretnego modułu
python -c "from console_app.config import Config; print('Test OK')"
```

## 📁 Struktura kodu

```
console_app/
├── __init__.py              # Inicjalizacja pakietu
├── main.py                  # Główny moduł aplikacji
├── config.py                # Konfiguracja
├── receipt_processor.py     # Przetwarzanie paragonów
├── rag_manager.py           # Zarządzanie RAG
├── export_manager.py        # Eksport wyników
└── console_ui.py           # Interfejs użytkownika
```

## 🔧 Konfiguracja edytora

### VS Code
1. Zainstaluj rozszerzenie Python
2. Wybierz interpreter: `./venv/bin/python`
3. Ustawienia są w `.vscode/settings.json`

### PyCharm
1. Otwórz projekt
2. Skonfiguruj interpreter: `./venv/bin/python`
3. Ustaw PYTHONPATH: `./console_app`

### Vim/Neovim
1. Zainstaluj coc.nvim
2. Skonfiguruj Python language server
3. Ustaw PYTHONPATH: `./console_app`

## 🧪 Testowanie

### Uruchomienie testów
```bash
# Wszystkie testy
python test_app.py

# Test konkretnej funkcjonalności
python -c "
from console_app.config import Config
from console_app.console_ui import ConsoleUI
print('Test OK')
"
```

### Dodawanie nowych testów
1. Dodaj funkcję testową w `test_app.py`
2. Dodaj do listy `tests` w funkcji `main()`
3. Uruchom testy: `python test_app.py`

## 🔍 Debugging

### Logowanie
```python
import structlog
logger = structlog.get_logger()
logger.info("Informacja")
logger.error("Błąd")
```

### Debug mode
```bash
python -m console_app.main --debug
```

### Breakpoints
```python
import pdb; pdb.set_trace()  # Python debugger
# lub
import ipdb; ipdb.set_trace()  # IPython debugger
```

## 📦 Zarządzanie zależnościami

### Dodawanie nowej zależności
1. Dodaj do `requirements-console.txt`
2. Zainstaluj: `pip install -r requirements-console.txt`
3. Zaktualizuj testy w `test_app.py`

### Aktualizacja zależności
```bash
pip install --upgrade -r requirements-console.txt
pip freeze > requirements-console.txt
```

## 🐳 Docker Development

### Budowanie obrazu
```bash
docker build -f Dockerfile.console -t agenty-console .
```

### Uruchomienie kontenerów
```bash
# Wszystkie usługi
docker-compose -f docker-compose.console.yaml up -d

# Tylko aplikacja konsolowa
docker-compose -f docker-compose.console.yaml run --rm console-app
```

### Logi
```bash
# Wszystkie logi
docker-compose -f docker-compose.console.yaml logs -f

# Logi konkretnej usługi
docker-compose -f docker-compose.console.yaml logs console-app
```

## 🔧 Konfiguracja

### Zmienne środowiskowe
```bash
# Podstawowe
export BACKEND_URL=http://localhost:8000
export OLLAMA_URL=http://localhost:11434

# Katalogi
export PARAGONY_DIR=/home/marcin/Dokumenty/PROJEKT/AGENTY/PARAGONY
export WIEDZA_RAG_DIR=/home/marcin/Dokumenty/PROJEKT/AGENTY/WIEDZA_RAG

# Debug
export LOG_LEVEL=DEBUG
```

### Plik .env
```bash
# Utwórz plik .env
cp .env.example .env
# Edytuj zmienne
```

## 📝 Kodowanie

### Style guide
- Używaj `black` do formatowania
- Używaj `flake8` do lintingu
- Dodawaj type hints
- Dokumentuj funkcje

### Przykład kodu
```python
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()

def process_data(data: Dict[str, Any]) -> Optional[List[str]]:
    """
    Przetwarza dane i zwraca listę wyników.
    
    Args:
        data: Dane do przetworzenia
        
    Returns:
        Lista wyników lub None w przypadku błędu
    """
    try:
        # Logika przetwarzania
        return ["wynik1", "wynik2"]
    except Exception as e:
        logger.error(f"Błąd przetwarzania: {e}")
        return None
```

## 🚀 Deployment

### Lokalny deployment
```bash
# Uruchomienie w tle
nohup python -m console_app.main > app.log 2>&1 &

# Sprawdzenie statusu
ps aux | grep python
tail -f app.log
```

### Docker deployment
```bash
# Budowanie i uruchomienie
docker-compose -f docker-compose.console.yaml up -d

# Sprawdzenie statusu
docker-compose -f docker-compose.console.yaml ps
```

## 🔍 Troubleshooting

### Problem: Import errors
```bash
# Sprawdź środowisko wirtualne
which python
pip list

# Reinstalacja zależności
pip install --force-reinstall -r requirements-console.txt
```

### Problem: Permission denied
```bash
# Sprawdź uprawnienia
ls -la
chmod +x *.sh

# Uruchom jako użytkownik
sudo -u $USER ./run_dev.sh
```

### Problem: Port already in use
```bash
# Sprawdź używane porty
netstat -tulpn | grep :8000
lsof -i :8000

# Zabij proces
kill -9 <PID>
```

## 📚 Przydatne linki

- [Python Documentation](https://docs.python.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Structlog Documentation](https://www.structlog.org/)

## 🤝 Contributing

1. Fork repozytorium
2. Utwórz branch: `git checkout -b feature/nazwa-funkcji`
3. Commit zmiany: `git commit -am 'Dodaj funkcję'`
4. Push do branch: `git push origin feature/nazwa-funkcji`
5. Utwórz Pull Request

### Commit message format
```
feat: dodaj nową funkcjonalność
fix: napraw błąd w module X
docs: zaktualizuj dokumentację
test: dodaj testy dla funkcji Y
refactor: refaktoruj kod w module Z
```

---

**Happy coding! 🎉** 