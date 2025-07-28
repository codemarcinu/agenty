

## Reset środowiska Qt/Python (problem z QApplication)

Jeśli podczas uruchamiania GUI pojawia się komunikat:

```
QApplication instance already exists. Exiting.
```

wykonaj automatyczny reset środowiska:

1. Zamknij wszystkie terminale, IDE, Jupyter itp.
2. Otwórz nowy terminal w katalogu projektu.
3. Uruchom skrypt:
   ```bash
   sudo ./scripts/automation/reset_qt_python_env.sh
   ```
   - Skrypt zabije wszystkie procesy python/Qt użytkownika i root.
   - Aktywuje venv.
   - Uruchomi GUI (`gui/app.py`) jako Twój użytkownik.

Jeśli problem nie ustąpi – zrestartuj komputer i uruchom GUI ponownie. 