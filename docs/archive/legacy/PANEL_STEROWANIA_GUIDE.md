# 🎮 Panel Sterowania FoodSave AI - Przewodnik Użytkownika

## 📋 Przegląd

Panel sterowania `foodsave-all.sh` to intuicyjny skrypt zarządzania systemem FoodSave AI, zaprojektowany zarówno dla użytkowników nietechnicznych, jak i deweloperów. Oferuje przyjazny interfejs do zarządzania wszystkimi komponentami systemu.

**Ostatnia aktualizacja**: 2025-01-27  
**Wersja**: 1.0.0  
**Status**: Gotowy do produkcji ✅

## 🚀 Szybki Start

### Uruchomienie Panelu
```bash
# Przejdź do katalogu projektu
cd AIASISSTMARUBO

# Uruchom panel sterowania
./foodsave-all.sh
```

### Bezpośrednie Komendy
```bash
# Tryb deweloperski
./foodsave-all.sh dev

# Tryb produkcyjny
./foodsave-all.sh prod

# Status systemu
./foodsave-all.sh status

# Zatrzymaj usługi
./foodsave-all.sh stop

# Sprawdź środowisko
./foodsave-all.sh check
```

## 🎯 Funkcje Panelu

### 1. 🚀 Uruchom System (Tryb Deweloperski)
**Dla**: Programistów i testowania nowych funkcji

**Funkcje**:
- Automatyczne przeładowanie przy zmianach w kodzie
- Szczegółowe logi i komunikaty błędów
- Wolniejszy, ale bardziej elastyczny
- Idealny do debugowania

**Proces uruchamiania**:
1. Sprawdzenie środowiska
2. Uruchomienie backendu (serwer API)
3. Uruchomienie frontendu (interfejs web)
4. Sprawdzenie modelu AI (Ollama)

### 2. 🏭 Uruchom System (Tryb Produkcyjny)
**Dla**: Użytkowników końcowych

**Funkcje**:
- Zoptymalizowany i stabilny
- Szybsze działanie
- Mniej szczegółowych logów
- Gotowy do użytku produkcyjnego

**Proces uruchamiania**:
1. Sprawdzenie środowiska
2. Uruchomienie backendu
3. Budowanie i uruchomienie frontendu
4. Sprawdzenie modelu AI

### 3. 🖥️ Uruchom Aplikację Desktop (Tauri)
**Dla**: Użytkowników preferujących aplikacje desktop

**Wymagania**:
- Wcześniejsze zbudowanie aplikacji
- Działający backend

**Funkcje**:
- Natywna aplikacja dla systemu
- Działa bez przeglądarki
- Pełna funkcjonalność systemu

### 4. 🔨 Zbuduj Aplikację Desktop
**Dla**: Deweloperów i użytkowników końcowych

**Proces**:
1. Sprawdzenie Node.js
2. Instalacja zależności (jeśli potrzebne)
3. Budowanie frontendu dla Tauri
4. Budowanie aplikacji Tauri
5. Sprawdzenie wynikowego pliku

**Wynik**: Plik `FoodSave AI_1.0.0_amd64.AppImage`

### 5. 📊 Sprawdź Status Systemu
**Dla**: Wszystkich użytkowników

**Informacje wyświetlane**:
- Status backendu (serwer API)
- Status frontendu (interfejs web)
- Status modelu AI (Ollama)
- Status kontenerów Docker
- Status bazy danych
- Przydatne linki
- Statystyki systemu

### 6. 📝 Pokaż Logi
**Dla**: Deweloperów i rozwiązywania problemów

**Dostępne logi**:
- **Logi backendu**: Informacje o żądaniach API, błędy serwera
- **Logi frontendu**: Błędy JavaScript, problemy z ładowaniem
- **Logi Docker**: Status kontenerów, problemy z uruchamianiem
- **Logi Ollama**: Status modelu AI, błędy przetwarzania
- **Wszystkie logi**: Podsumowanie wszystkich logów
- **Szukaj w logach**: Wyszukiwanie konkretnych błędów

### 7. 🛑 Zatrzymaj Wszystkie Usługi
**Dla**: Wszystkich użytkowników

**Proces zatrzymywania**:
1. Sprawdzenie aktywnych procesów
2. Zatrzymanie kontenerów Docker
3. Zatrzymanie procesów frontendu
4. Zatrzymanie aplikacji desktop

**Rezultat**: Bezpieczne zwolnienie wszystkich zasobów

### 8. 🔧 Sprawdź Środowisko
**Dla**: Diagnostyki problemów

**Sprawdzane elementy**:
1. **Docker**: Instalacja, wersja, status
2. **Docker Compose**: Instalacja, wersja
3. **Node.js**: Instalacja, wersja, kompatybilność
4. **npm**: Instalacja, wersja
5. **curl**: Instalacja, wersja
6. **Porty**: Dostępność portów 3000, 8000, 5432, 11434
7. **Pliki konfiguracyjne**: Istnienie wymaganych plików
8. **Uprawnienia**: Uprawnienia do zapisu, grupa docker

### 9. ❓ Pomoc i Informacje
**Dla**: Wszystkich użytkowników

**Zawartość**:
- Szczegółowe wyjaśnienia funkcji
- Rozwiązywanie problemów
- Przydatne linki i wskazówki

## 🔧 Diagnostyka i Rozwiązywanie Problemów

### Sprawdzanie Środowiska
```bash
# Uruchom pełną diagnostykę
./foodsave-all.sh

# Wybierz opcję 8: Sprawdź środowisko
```

### Typowe Problemy i Rozwiązania

#### Problem: Docker nie działa
**Objawy**: Błąd "Docker nie jest uruchomiony"
**Rozwiązanie**:
```bash
# Ubuntu/Debian
sudo systemctl start docker
sudo usermod -aG docker $USER

# macOS
open -a Docker
```

#### Problem: Port 3000 zajęty
**Objawy**: Błąd "Port 3000 jest zajęty"
**Rozwiązanie**:
```bash
# Sprawdź co używa portu
sudo netstat -tulpn | grep :3000

# Zatrzymaj proces
sudo kill -9 <PID>
```

#### Problem: Node.js nie zainstalowany
**Objawy**: Błąd "Node.js nie jest zainstalowany"
**Rozwiązanie**:
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node
```

#### Problem: Ollama nie działa
**Objawy**: Ostrzeżenie "Model AI nie jest dostępny"
**Rozwiązanie**:
```bash
# Uruchom Ollama
ollama serve

# Pobierz modele
ollama pull bielik-4.5b-v3.0
ollama pull bielik-11b-v2.3
```

### Sprawdzanie Logów
```bash
# Uruchom panel
./foodsave-all.sh

# Wybierz opcję 6: Pokaż logi
# Wybierz odpowiedni typ logów
```

## 📊 Monitoring i Status

### Sprawdzanie Statusu Systemu
```bash
# Szybkie sprawdzenie
./foodsave-all.sh status

# Szczegółowy status
./foodsave-all.sh
# Wybierz opcję 5: Sprawdź status systemu
```

### Przydatne Linki
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Ollama API**: http://localhost:11434

### Metryki Systemu
Panel wyświetla:
- Użycie zasobów Docker
- Ostatnie logi systemu
- Status wszystkich komponentów
- Statystyki błędów i ostrzeżeń

## 🔒 Bezpieczeństwo

### Bezpieczne Zatrzymywanie
```bash
# Zawsze używaj opcji zatrzymania
./foodsave-all.sh stop

# Lub przez menu
./foodsave-all.sh
# Wybierz opcję 7: Zatrzymaj wszystkie usługi
```

### Sprawdzanie Uprawnień
Panel automatycznie sprawdza:
- Uprawnienia do zapisu w katalogu
- Przynależność do grupy docker
- Uprawnienia do uruchamiania kontenerów

## 📚 Integracja z Dokumentacją

### Powiązane Dokumenty
- **[README.md](../README.md)** - Główny przewodnik projektu
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Przewodnik wdrażania
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Przewodnik testowania
- **[ARCHITECTURE_DOCUMENTATION.md](ARCHITECTURE_DOCUMENTATION.md)** - Architektura systemu

### Szybkie Linki
- [Główna dokumentacja](README_MAIN.md)
- [API Reference](API_REFERENCE.md)
- [Rozwiązywanie problemów](TESTING_GUIDE.md)

## 🎯 Najlepsze Praktyki

### Dla Użytkowników Nietechnicznych
1. **Zawsze używaj menu interaktywnego**: `./foodsave-all.sh`
2. **Sprawdzaj status przed uruchomieniem**: Opcja 5
3. **Używaj diagnostyki przy problemach**: Opcja 8
4. **Bezpiecznie zatrzymuj system**: Opcja 7

### Dla Deweloperów
1. **Używaj trybu deweloperskiego**: Opcja 1
2. **Monitoruj logi**: Opcja 6
3. **Sprawdzaj środowisko**: Opcja 8
4. **Używaj bezpośrednich komend** dla automatyzacji

### Dla Administratorów
1. **Regularnie sprawdzaj status**: Opcja 5
2. **Monitoruj logi**: Opcja 6
3. **Używaj trybu produkcyjnego**: Opcja 2
4. **Sprawdzaj metryki systemu**

## 🔄 Aktualizacje i Wersjonowanie

### Sprawdzanie Wersji
```bash
# Sprawdź wersję skryptu
head -5 foodsave-all.sh

# Sprawdź wersje komponentów
./foodsave-all.sh status
```

### Historia Wersji
- **v1.0.0** (2025-01-27): Pierwsza wersja produkcyjna
  - Interaktywne menu
  - Diagnostyka środowiska
  - Zarządzanie logami
  - Bezpieczne zatrzymywanie

## 🤝 Wsparcie

### Rozwiązywanie Problemów
1. Uruchom diagnostykę: `./foodsave-all.sh` → Opcja 8
2. Sprawdź logi: `./foodsave-all.sh` → Opcja 6
3. Sprawdź status: `./foodsave-all.sh` → Opcja 5
4. Zobacz dokumentację: [docs/](.)

### Kontakt
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Dokumentacja**: [docs/](.)
- **Status**: Użyj opcji "Sprawdź status systemu"

---

**Panel Sterowania FoodSave AI** - Intuicyjne zarządzanie systemem AI 🎮🤖 