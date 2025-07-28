# 🍽️ FoodSave AI - Aliasy Systemowe

Dokumentacja aliasów do zarządzania systemem FoodSave AI.

## 📋 Dostępne Aliasy

### 🖥️ `app` - GUI Panel Sterowania
**Opis**: Uruchamia intuicyjny interfejs graficzny dla użytkowników nietechnicznych

**Użycie**:
```bash
app
```

**Co robi**:
- Przechodzi do katalogu GUI
- Uruchamia serwer Flask na porcie 8080
- Otwiera przeglądarkę automatycznie
- Wyświetla status wszystkich komponentów systemu

**Dostęp**: http://localhost:8080

---

### 🛑 `app-stop` - Zatrzymanie GUI
**Opis**: Bezpiecznie zatrzymuje panel sterowania GUI

**Użycie**:
```bash
app-stop
```

**Co robi**:
- Zatrzymuje serwer Flask
- Zwolnienie portu 8080
- Usunięcie plików tymczasowych

---

### 🖥️ `food` - Konsolowy Panel Sterowania
**Opis**: Oryginalny konsolowy skrypt zarządzania systemem

**Użycie**:
```bash
food
```

**Co robi**:
- Uruchamia interaktywne menu konsolowe
- Dostęp do wszystkich funkcji systemu
- Szczegółowe logi i diagnostyka

## 🚀 Szybki Start

### Dla użytkowników nietechnicznych:
```bash
# Uruchom intuicyjne GUI
app

# Zatrzymaj GUI
app-stop
```

### Dla programistów i zaawansowanych użytkowników:
```bash
# Uruchom konsolowy panel
food
```

## 🎯 Kiedy Używać Którego Aliasu

### Użyj `app` gdy:
- ✅ Jesteś użytkownikiem nietechnicznym
- ✅ Chcesz intuicyjny interfejs graficzny
- ✅ Pracujesz na komputerze z przeglądarką
- ✅ Chcesz szybko sprawdzić status systemu
- ✅ Potrzebujesz łatwego dostępu do wszystkich funkcji

### Użyj `food` gdy:
- ✅ Jesteś programistą lub zaawansowanym użytkownikiem
- ✅ Pracujesz przez SSH lub terminal
- ✅ Potrzebujesz szczegółowych logów
- ✅ Chcesz pełną kontrolę nad systemem
- ✅ Debugujesz problemy

### Użyj `app-stop` gdy:
- ✅ Chcesz zatrzymać GUI
- ✅ Port 8080 jest zajęty
- ✅ Masz problemy z GUI
- ✅ Chcesz zwolnić zasoby systemu

## 🔧 Instalacja i Konfiguracja

### Automatyczna instalacja:
Aliasy są automatycznie dodawane do pliku `~/.bashrc` podczas pierwszej konfiguracji.

### Ręczna instalacja:
```bash
# Dodaj aliasy do ~/.bashrc
echo "alias app='cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-gui && ./start-gui.sh'" >> ~/.bashrc
echo "alias app-stop='cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-gui && ./stop-gui.sh'" >> ~/.bashrc

# Załaduj nowe aliasy
source ~/.bashrc
```

### Sprawdzenie instalacji:
```bash
# Sprawdź czy aliasy są dostępne
alias | grep -E "(food|app)"

# Sprawdź czy skrypty istnieją
ls -la /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-gui/*.sh
```

## 📊 Porównanie Interfejsów

| Funkcja | GUI (`app`) | Konsola (`food`) |
|---------|-------------|------------------|
| **Uruchomienie** | `app` | `food` |
| **Zatrzymanie** | `app-stop` | Ctrl+C |
| **Status systemu** | Wizualny (karty) | Tekstowy |
| **Logi** | W przeglądarce | W terminalu |
| **Responsywność** | Tak (mobile) | Nie |
| **Dostępność** | Przeglądarka | Terminal |
| **Łatwość użycia** | Bardzo łatwe | Zaawansowane |
| **Szczegółowość** | Podstawowa | Pełna |

## 🔍 Rozwiązywanie Problemów

### Alias `app` nie działa:
```bash
# Sprawdź czy alias istnieje
alias app

# Sprawdź czy skrypt istnieje
ls -la /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-gui/start-gui.sh

# Sprawdź uprawnienia
chmod +x /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-gui/start-gui.sh
```

### Port 8080 zajęty:
```bash
# Zatrzymaj GUI
app-stop

# Lub wymuś zwolnienie portu
lsof -ti:8080 | xargs kill -9
```

### Błędy Python:
```bash
# Zainstaluj wymagane pakiety
pip3 install flask flask-cors psutil requests

# Sprawdź wersję Python
python3 --version
```

## 📱 Użycie na Różnych Urządzeniach

### Desktop/Laptop:
```bash
app  # Otwiera GUI w przeglądarce
```

### Tablet/Telefon:
```bash
app  # GUI jest responsywne
# Następnie otwórz http://localhost:8080 na urządzeniu
```

### Serwer/SSH:
```bash
food  # Użyj konsolowego interfejsu
```

## 🎨 Personalizacja

### Zmiana aliasów:
Edytuj plik `~/.bashrc`:
```bash
# Zmień nazwę aliasu
alias myapp='cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-gui && ./start-gui.sh'
```

### Dodanie nowych aliasów:
```bash
# Dodaj własny alias
echo "alias foodsave-status='curl -s http://localhost:8080/health'" >> ~/.bashrc
source ~/.bashrc
```

## 📚 Przydatne Komendy

### Sprawdzenie statusu:
```bash
# Sprawdź czy GUI działa
curl -s http://localhost:8080/health

# Sprawdź procesy
ps aux | grep "python3.*server.py"
```

### Logi:
```bash
# Logi GUI
tail -f /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-gui/gui.log

# Logi systemu
food  # Opcja 6 - Pokaż logi
```

### Porty:
```bash
# Sprawdź zajęte porty
lsof -i :8080
lsof -i :3000
lsof -i :8000
```

---

## 🎉 Podsumowanie

**Aliasy FoodSave AI** zapewniają łatwy dostęp do wszystkich funkcji systemu:

- **`app`** - Intuicyjne GUI dla każdego
- **`app-stop`** - Bezpieczne zatrzymanie GUI  
- **`food`** - Zaawansowany panel konsolowy

Wybierz interfejs odpowiedni do swoich potrzeb i umiejętności! 🍽️✨ 