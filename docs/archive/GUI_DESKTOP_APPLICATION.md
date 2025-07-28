# 🖥️ Aplikacja Desktop FoodSave AI

## Przegląd

FoodSave AI Desktop Application to natywna aplikacja desktop oparta na PyQt5, która zapewnia pełną integrację z systemem operacyjnym i zaawansowane narzędzia do monitorowania i zarządzania systemem FoodSave AI.

## 🚀 Szybki Start

### Uruchomienie Aplikacji

```bash
# Z katalogu głównego projektu
python gui/launcher.py

# Lub przez skrypt
./scripts/development/dev-start.sh
```

### Pierwsze Uruchomienie

1. **Ikona w system tray** - Aplikacja pojawi się w system tray
2. **Menu kontekstowe** - Kliknij prawym na ikonę
3. **Panel web** - Automatyczne otwarcie w przeglądarce
4. **Monitorowanie** - Dostęp do wszystkich funkcji monitorowania

## 🎯 Funkcje Główne

### System Tray Integration

Aplikacja działa w tle jako ikona w system tray z zaawansowanym menu:

```
🍎 FoodSave AI
├── 🌐 Panel Web
├── 🎨 Frontend
├── ──────────────────
├── ⚙️ Ustawienia
├── ℹ️ O programie
├── ──────────────────
├── 📊 Status
├── 🔍 Monitor Systemu
├── 📋 Logi
├── 🐳 Kontenery
├── ──────────────────
└── ❌ Wyjście
```

### 🔍 Monitor Systemu

#### Dostęp do Monitora
1. **Kliknij prawym** na ikonę w system tray
2. **Wybierz "🔍 Monitor Systemu"**
3. **Otworzy się okno** z trzema zakładkami

#### Zakładki Monitorowania

**📋 Zakładka Logi:**
- Monitorowanie logów w czasie rzeczywistym
- Automatyczne odświeżanie co 2 sekundy
- Auto-scroll do najnowszych wpisów
- Możliwość czyszczenia logów

**🐳 Zakładka Kontenery:**
- Tabela z kontenerami Docker
- Status, porty, obrazy
- Przyciski zarządzania:
  - ▶️ Uruchom wszystkie
  - ⏹️ Zatrzymaj wszystkie
  - 🔄 Restart wszystkie

**📊 Zakładka Status:**
- Status aplikacji (Backend, Frontend, Baza danych)
- Zasoby systemu (CPU, Pamięć, Dysk)
- Alerty i powiadomienia

### ⚙️ Ustawienia

#### Autostart
- **Włącz/Wyłącz** automatyczne uruchamianie z systemem
- **Systemd service** - Automatyczne zarządzanie
- **Desktop entry** - Integracja z menu aplikacji

#### Konfiguracja
- **Porty** - Konfiguracja portów aplikacji
- **Logi** - Poziom logowania
- **Powiadomienia** - Ustawienia powiadomień

### 📊 Status Systemu

#### Szybkie Sprawdzenie
- **Kliknij "📊 Status"** w menu kontekstowym
- **Otrzymasz powiadomienie** z aktualnym statusem
- **Szczegóły** w oknie monitora systemu

#### Monitorowane Elementy
- **Backend** - Serwer FastAPI (localhost:8000)
- **Frontend** - Aplikacja React (localhost:3000)
- **Baza danych** - lokalny plik
- **Redis** - Cache system
- **Ollama** - Modele AI

## 🔧 Zarządzanie Systemem

### Kontrolki i Akcje

#### Przyciski w Monitorze Systemu
- **🔄 Odśwież** - Odświeża wszystkie dane monitorowania
- **🗑️ Wyczyść logi** - Czyści pliki logów (z potwierdzeniem)
- **🔄 Restart serwisów** - Restartuje wszystkie kontenery Docker

#### Zarządzanie Kontenerami
- **▶️ Uruchom wszystkie** - `docker-compose up -d`
- **⏹️ Zatrzymaj wszystkie** - `docker-compose down`
- **🔄 Restart wszystkie** - `docker-compose restart`

### Bezpieczeństwo

#### Potwierdzenia
- **Wszystkie destrukcyjne operacje** wymagają potwierdzenia
- **Dialogi Yes/No** dla bezpieczeństwa
- **Informacje o konsekwencjach** przed wykonaniem

#### Obsługa Błędów
- **Try-catch** dla wszystkich operacji Docker
- **Timeout** dla requestów HTTP (2 sekundy)
- **Graceful handling** dla brakujących plików

## 📱 Dostępność i UX

### Szybki Dostęp
1. **Kliknij prawym** na ikonę w system tray
2. **Wybierz opcję** z menu kontekstowego
3. **Monitoruj w czasie rzeczywistym** - automatyczne odświeżanie

### Powiadomienia
- **Status aplikacji** - Powiadomienia o problemach
- **Alerty systemowe** - Wykorzystanie zasobów
- **Informacje o kontenerach** - Status Docker

### Integracja z Automatyzacją
- **Autostart** - Automatyczne uruchamianie z systemem
- **Skrypty deployment** - Sprawdzanie statusu po wdrożeniu
- **Monitoring zewnętrzny** - Eksport danych do systemów monitorowania

## 🛠️ Rozwiązywanie Problemów

### Typowe Problemy

#### Aplikacja nie uruchamia się
```bash
# Sprawdź zależności
pip install -r requirements.txt

# Sprawdź PyQt5
pip install PyQt5

# Sprawdź logi
python gui/launcher.py --debug
```

#### Monitor systemu nie działa
```bash
# Sprawdź Docker
docker --version
docker ps

# Sprawdź uprawnienia
sudo usermod -aG docker $USER

# Sprawdź psutil (opcjonalne)
pip install psutil
```

#### Logi nie są wyświetlane
```bash
# Sprawdź pliki logów
ls -la logs/

# Sprawdź uprawnienia
chmod 644 logs/*.log

# Sprawdź ścieżki w konfiguracji
```

### Diagnostyka

#### Sprawdzenie Statusu
1. **Otwórz Monitor Systemu**
2. **Sprawdź zakładkę Status**
3. **Zobacz szczegóły błędów**

#### Logi Diagnostyczne
```bash
# Logi aplikacji GUI
tail -f logs/gui.log

# Logi backendu
tail -f logs/backend.log

# Logi kontenerów
docker logs foodsave-backend
```

## 📊 Przykłady Użycia

### Monitorowanie w Czasie Rzeczywistym

```
🔍 Monitor Systemu - FoodSave AI

📋 Logi:
[2025-01-15 14:30:15] INFO: Backend started successfully
[2025-01-15 14:30:16] INFO: Database connection established
[2025-01-15 14:30:17] INFO: Frontend server running on port 3000

🐳 Kontenery:
✅ foodsave-backend    Up 2 hours   0.0.0.0:8000->8000/tcp
✅ foodsave-frontend   Up 2 hours   0.0.0.0:3000->3000/tcp
✅ foodsave-postgres   Up 2 hours   0.0.0.0:5432->5432/tcp

📊 Status:
✅ Backend: Działa
✅ Frontend: Działa
✅ Baza danych: 1 kontener (plik)
CPU: 15.2%
Pamięć: 45.8% (2.3GB)
Dysk: 67.1% (120.5GB)
```

### Zarządzanie Kontenerami

1. **Otwórz Monitor Systemu**
2. **Przejdź do zakładki Kontenery**
3. **Użyj przycisków:**
   - ▶️ Uruchom wszystkie - dla startu systemu
   - ⏹️ Zatrzymaj wszystkie - dla zatrzymania
   - 🔄 Restart wszystkie - dla restartu

### Konfiguracja Autostartu

1. **Otwórz Ustawienia**
2. **Znajdź sekcję Autostart**
3. **Włącz/Wyłącz opcję**
4. **Zapisz ustawienia**

## 🔗 Integracja z Systemem

### Autostart
- **Systemd service** - Automatyczne zarządzanie
- **Desktop entry** - Integracja z menu aplikacji
- **Konfiguracja GUI** - Włączanie/wyłączanie w ustawieniach

### Powiadomienia Systemowe
- **Status aplikacji** - Powiadomienia o problemach
- **Alerty systemowe** - Wykorzystanie zasobów
- **Informacje o kontenerach** - Status Docker

### Skróty Klawiszowe
- **Ctrl+Shift+T** - Otwórz panel web
- **Ctrl+Shift+M** - Otwórz monitor systemu
- **Ctrl+Shift+S** - Otwórz ustawienia

## 📚 Dokumentacja Techniczna

### Architektura
- **PyQt5** - Framework GUI
- **QSystemTrayIcon** - System tray integration
- **QThread** - Monitoring w tle
- **QTimer** - Automatyczne odświeżanie

### Pliki Główne
- **`gui/launcher.py`** - Główny launcher aplikacji
- **`gui/tray.py`** - System tray integration
- **`gui/windows/system_monitor.py`** - Monitor systemu
- **`gui/windows/settings.py`** - Ustawienia aplikacji

### Zależności
```bash
# Podstawowe zależności
PyQt5>=5.15.0
requests>=2.25.0

# Opcjonalne (dla monitorowania zasobów)
psutil>=5.8.0
```

## 🎯 Planowane Rozszerzenia

### Krótkoterminowe
1. **Przełączanie między logami** - ComboBox do wyboru logu
2. **Filtrowanie logów** - Wyszukiwanie w logach
3. **Eksport danych** - Zapisywanie statusu do pliku

### Długoterminowe
1. **Alerty systemowe** - Powiadomienia o problemach
2. **Historia metryk** - Wykresy wykorzystania zasobów
3. **Integracja z zewnętrznym monitoringiem** - Prometheus, Grafana

---

**Wersja dokumentacji:** 1.0.0  
**Ostatnia aktualizacja:** 2025-01-15  
**Autor:** FoodSave AI Development Team 

## Otwieranie linków w przeglądarce

Aplikacja otwiera panel web, monitoring oraz inne linki zawsze przez polecenie systemowe:

```bash
xdg-open URL
```

Dzięki temu otwierany jest link w domyślnej przeglądarce systemowej (Firefox, Chrome, Chromium, itp.), niezależnie od tego, czy przeglądarka jest zainstalowana jako snap, deb, AppImage czy inny wariant. Nie jest wymagany Firefox ani webbrowser w Pythonie.

- Jeśli nie masz żadnej przeglądarki graficznej, pojawi się komunikat o błędzie.
- Jeśli masz kilka przeglądarek, zostanie użyta ta ustawiona jako domyślna w systemie.

### Przykład działania

- Kliknięcie w menu "🌐 Panel Web" lub "📊 Status" otworzy odpowiedni adres w domyślnej przeglądarce przez xdg-open.
- Nie musisz instalować Firefoxa przez snap, wystarczy dowolna przeglądarka graficzna. 