# FoodSave AI - Aplikacja Desktopowa (GUI)

## Uruchamianie GUI

Od teraz **jedynym zalecanym sposobem uruchamiania GUI** jest:

```bash
./start_sekwencyjny.sh
```

Skrypt automatycznie uruchamia backend i GUI, kontroluje porty, sprawdza bazę danych i loguje każdy etap.

### Jak działa sekwencyjny start?
- Zamyka procesy blokujące porty 8000/8001
- Sprawdza i uruchamia PostgreSQL
- Uruchamia backend na wolnym porcie
- Czeka na healthcheck backendu
- Uruchamia GUI (jeśli plik istnieje)

### Najczęstsze błędy GUI
- **Brak pliku gui/app.py**: GUI nie zostanie uruchomione
- **Błąd importu PySide6/qasync**: Zainstaluj brakujące pakiety: `pip install PySide6 qasync`
- **Backend nie działa**: Skrypt przerywa i wyświetla komunikat o błędzie

Nie używaj już:
- `start_gui.sh`
- `run_backend.py`

---

Więcej szczegółów w pliku `start_sekwencyjny.sh` oraz w README.md. 