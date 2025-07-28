# Monitorowanie Systemu - FoodSave AI

## Przegląd

FoodSave AI Desktop Application zawiera zaawansowane narzędzia do monitorowania systemu, które pozwalają użytkownikom na:

- **Monitorowanie logów** w czasie rzeczywistym
- **Zarządzanie kontenerami Docker**
- **Sprawdzanie statusu aplikacji**
- **Monitorowanie zasobów systemu**

## Dostęp do Monitora Systemu

### Z System Tray

1. Kliknij prawym przyciskiem myszy na ikonę FoodSave AI w system tray
2. Wybierz jedną z opcji:
   - **🔍 Monitor Systemu** - pełny panel monitorowania
   - **📋 Logi** - szybki dostęp do logów
   - **🐳 Kontenery** - zarządzanie kontenerami Docker
   - **📊 Status** - sprawdzenie statusu aplikacji

### Z Menu Głównego

Monitor systemu jest również dostępny z głównego menu aplikacji.

## Funkcjonalności

### 📋 Monitorowanie Logów

**Zakładka "Logi"** zawiera:

- **Logi Backend** - logi serwera FastAPI
- **Logi Frontend** - logi aplikacji React
- **Logi SQLite** - logi bazy danych
- **Logi Redis** - logi cache
- **Logi Ollama** - logi modeli AI

**Funkcje:**
- Automatyczne odświeżanie co 2 sekundy
- Auto-scroll do najnowszych wpisów
- Możliwość czyszczenia logów
- Wyświetlanie w formacie monospace

### 🐳 Zarządzanie Kontenerami

**Zakładka "Kontenery"** zawiera:

- **Tabela kontenerów** z informacjami:
  - Nazwa kontenera
  - Status (uruchomiony/zatrzymany)
  - Porty
  - Obraz Docker

**Funkcje:**
- **▶️ Uruchom wszystkie** - uruchamia wszystkie kontenery
- **⏹️ Zatrzymaj wszystkie** - zatrzymuje wszystkie kontenery
- **🔄 Restart wszystkie** - restartuje wszystkie kontenery
- Automatyczne odświeżanie co 5 sekund

### 📊 Status Systemu

**Zakładka "Status"** zawiera:

#### Status Aplikacji
- **Backend** - status serwera FastAPI (localhost:8000)
- **Frontend** - status aplikacji React (localhost:3000)
- **Baza danych** - status kontenerów (nie dotyczy SQLite)
- **Redis** - status cache
- **Ollama** - status modeli AI

#### Zasoby Systemu
- **CPU** - procentowe wykorzystanie procesora
- **Pamięć** - wykorzystanie RAM
- **Dysk** - wykorzystanie dysku twardego

## Kontrolki

### Przyciski Sterujące

- **🔄 Odśwież** - odświeża wszystkie dane
- **🗑️ Wyczyść logi** - czyści wszystkie pliki logów
- **🔄 Restart serwisów** - restartuje wszystkie serwisy Docker

### Potwierdzenia

Wszystkie destrukcyjne operacje (czyszczenie logów, restart serwisów) wymagają potwierdzenia użytkownika.

## Wymagania Systemowe

### Zależności

Monitor systemu wymaga:

- **Docker** - do zarządzania kontenerami
- **psutil** - do monitorowania zasobów (opcjonalne)
- **requests** - do sprawdzania statusu HTTP

### Instalacja psutil (opcjonalne)

```bash
pip install psutil
```

## Rozwiązywanie Problemów

### Błędy Docker

Jeśli występują błędy z Docker:

1. Sprawdź, czy Docker jest uruchomiony:
   ```bash
   sudo systemctl status docker
   ```

2. Sprawdź uprawnienia:
   ```bash
   sudo usermod -aG docker $USER
   ```

### Błędy Monitorowania Zasobów

Jeśli nie ma informacji o zasobach systemu:

1. Zainstaluj psutil:
   ```bash
   pip install psutil
   ```

2. Sprawdź uprawnienia do `/proc`

### Błędy Logów

Jeśli logi nie są wyświetlane:

1. Sprawdź, czy pliki logów istnieją:
   ```bash
   ls -la logs/
   ```

2. Sprawdź uprawnienia do odczytu:
   ```bash
   chmod 644 logs/*.log
   ```

## Konfiguracja

### Pliki Logów

Domyślne ścieżki logów:
- `logs/backend.log`
- `logs/frontend.log`
- `logs/sqlite.log` (jeśli używane)
- `logs/redis.log`
- `logs/ollama.log`

### Interwały Odświeżania

- **Logi**: 2 sekundy
- **Kontenery**: 5 sekund
- **Status**: 5 sekund

## Bezpieczeństwo

### Uprawnienia

Monitor systemu wymaga uprawnień do:

- Odczytu plików logów
- Wykonywania komend Docker
- Dostępu do `/proc` (dla psutil)

### Rekomendacje

1. Używaj monitora tylko w środowisku deweloperskim
2. Nie udostępniaj logów zawierających dane wrażliwe
3. Regularnie czyść logi, aby nie zajmowały zbyt dużo miejsca

## Integracja z Automatyzacją

Monitor systemu może być używany z:

- **Autostart** - automatyczne uruchamianie z systemem
- **Skrypty deployment** - sprawdzanie statusu po wdrożeniu
- **Monitoring zewnętrzny** - eksport danych do systemów monitorowania

## Rozszerzenia

### Dodawanie Nowych Logów

Aby dodać nowy log do monitorowania:

1. Dodaj ścieżkę do `self.log_files` w `SystemMonitorWindow`
2. Log automatycznie pojawi się w interfejsie

### Dodawanie Nowych Kontenerów

Kontenery są automatycznie wykrywane przez komendę `docker ps`. Aby monitorować tylko określone kontenery:

1. Zmodyfikuj filtr w `ContainerMonitorThread`
2. Dostosuj format wyświetlania w tabeli

### Dodawanie Nowych Metryk

Aby dodać nowe metryki systemowe:

1. Rozszerz metodę `_update_status`
2. Dodaj nowe etykiety w `_create_status_tab`
3. Zaimplementuj logikę pobierania danych 