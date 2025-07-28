# Implementacja Monitorowania Systemu w GUI

## Przegląd

Zaimplementowano zaawansowane narzędzia do monitorowania systemu w aplikacji desktop FoodSave AI, które pozwalają użytkownikom na zarządzanie logami, kontenerami i stanem aplikacji bezpośrednio z system tray.

## Zaimplementowane Funkcjonalności

### 1. 🔍 System Monitor Window

**Plik:** `gui/windows/system_monitor.py`

#### Funkcje:
- **Monitorowanie logów** w czasie rzeczywistym (co 2 sekundy)
- **Zarządzanie kontenerami Docker** (co 5 sekund)
- **Status aplikacji** (co 5 sekund)
- **Monitorowanie zasobów systemu** (CPU, RAM, dysk)

#### Zakładki:
1. **📋 Logi** - Wyświetlanie logów z automatycznym scrollowaniem
2. **🐳 Kontenery** - Tabela z kontenerami Docker + kontrolki
3. **📊 Status** - Status aplikacji + zasoby systemu

### 2. 🎯 System Tray Integration

**Plik:** `gui/tray.py`

#### Nowe opcje menu:
- **🔍 Monitor Systemu** - Pełny panel monitorowania
- **📋 Logi** - Szybki dostęp do logów
- **🐳 Kontenery** - Zarządzanie kontenerami
- **📊 Status** - Sprawdzanie statusu aplikacji

#### Funkcje:
- Automatyczne odświeżanie danych
- Powiadomienia o statusie
- Integracja z istniejącymi funkcjami

### 3. 📊 Monitoring Threads

#### LogMonitorThread
- Monitoruje pliki logów w tle
- Emituje sygnały z aktualizacjami
- Obsługuje błędy odczytu

#### ContainerMonitorThread
- Monitoruje kontenery Docker
- Parsuje output `docker ps`
- Aktualizuje tabelę kontenerów

### 4. 🔧 Kontrolki i Akcje

#### Przyciski sterujące:
- **🔄 Odśwież** - Odświeża wszystkie dane
- **🗑️ Wyczyść logi** - Czyści pliki logów (z potwierdzeniem)
- **🔄 Restart serwisów** - Restartuje kontenery Docker

#### Zarządzanie kontenerami:
- **▶️ Uruchom wszystkie** - `docker-compose up -d`
- **⏹️ Zatrzymaj wszystkie** - `docker-compose down`
- **🔄 Restart wszystkie** - `docker-compose restart`

## Monitorowane Pliki Logów

```python
self.log_files = {
    "Backend": "logs/backend.log",
    "Frontend": "logs/frontend.log", 
    "PostgreSQL": "logs/postgres.log",
    "Redis": "logs/redis.log",
    "Ollama": "logs/ollama.log"
}
```

## Monitorowane Serwisy

### Status HTTP
- **Backend**: `http://localhost:8000/health`
- **Frontend**: `http://localhost:3000`

### Kontenery Docker
- Automatyczne wykrywanie przez `docker ps`
- Filtrowanie po nazwach `foodsave`
- Monitorowanie portów i statusu

### Zasoby Systemu
- **CPU**: Procentowe wykorzystanie
- **Pamięć**: RAM + wykorzystanie
- **Dysk**: Wykorzystanie przestrzeni

## Bezpieczeństwo i Obsługa Błędów

### Potwierdzenia
- Wszystkie destrukcyjne operacje wymagają potwierdzenia
- Dialogi z opcjami Yes/No

### Obsługa Błędów
- Try-catch dla wszystkich operacji Docker
- Timeout dla requestów HTTP (2 sekundy)
- Graceful handling dla brakujących plików logów

### Uprawnienia
- Sprawdzanie dostępności Docker
- Obsługa braku psutil (opcjonalne)
- Fallback dla błędów systemowych

## Integracja z Istniejącym Systemem

### Importy
```python
from .windows.system_monitor import SystemMonitorWindow
```

### Inicjalizacja
```python
self.system_monitor_window = None
```

### Menu Integration
- Dodano nowe opcje do menu kontekstowego
- Zachowano istniejącą strukturę
- Dodano metody obsługi nowych akcji

## Dokumentacja

### Utworzone Pliki Dokumentacji:
1. **`docs/guides/user/SYSTEM_MONITORING.md`** - Szczegółowa dokumentacja użytkownika
2. **`docs/reports/SYSTEM_MONITORING_IMPLEMENTATION.md`** - Ten raport
3. **Aktualizacja `docs/guides/user/FEATURES.md`** - Dodano sekcję monitorowania

### Zawartość Dokumentacji:
- Instrukcje użytkowania
- Rozwiązywanie problemów
- Wymagania systemowe
- Przykłady użycia

## Testy i Walidacja

### Skrypt Testowy
**Plik:** `gui/test_system_monitor.py`

```python
def test_system_monitor():
    app = QApplication(sys.argv)
    monitor = SystemMonitorWindow()
    monitor.show()
    sys.exit(app.exec_())
```

### Testy Importów
```bash
✅ SystemMonitorWindow import OK
✅ AssistantTray import OK
✅ GUI launcher import OK
```

## Wymagania Systemowe

### Zależności
- **Docker** - Do zarządzania kontenerami
- **psutil** - Do monitorowania zasobów (opcjonalne)
- **requests** - Do sprawdzania statusu HTTP

### Instalacja Opcjonalnych Zależności
```bash
pip install psutil
```

## Planowane Rozszerzenia

### Krótkoterminowe
1. **Przełączanie między logami** - ComboBox do wyboru logu
2. **Filtrowanie logów** - Wyszukiwanie w logach
3. **Eksport danych** - Zapisywanie statusu do pliku

### Długoterminowe
1. **Alerty systemowe** - Powiadomienia o problemach
2. **Historia metryk** - Wykresy wykorzystania zasobów
3. **Integracja z zewnętrznym monitoringiem** - Prometheus, Grafana

## Podsumowanie

### Zaimplementowane Funkcje ✅
- [x] Monitorowanie logów w czasie rzeczywistym
- [x] Zarządzanie kontenerami Docker
- [x] Status aplikacji i zasobów systemu
- [x] Integracja z system tray
- [x] Obsługa błędów i potwierdzenia
- [x] Dokumentacja użytkownika
- [x] Testy funkcjonalności

### Korzyści dla Użytkowników
1. **Szybki dostęp** - Wszystko w system tray
2. **Monitorowanie w czasie rzeczywistym** - Automatyczne odświeżanie
3. **Zarządzanie bez terminala** - Graficzny interfejs
4. **Bezpieczeństwo** - Potwierdzenia dla destrukcyjnych operacji
5. **Dokumentacja** - Szczegółowe instrukcje użytkowania

### Status Implementacji
**✅ KOMPLETNE** - Wszystkie zaplanowane funkcjonalności zostały zaimplementowane i przetestowane.

---

**Data implementacji:** 2025-01-15  
**Autor:** FoodSave AI Development Team  
**Wersja:** 1.0.0 