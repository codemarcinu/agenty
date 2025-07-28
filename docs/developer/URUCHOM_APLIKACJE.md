# 🚀 Jak uruchomić FoodSave AI - Przewodnik dla każdego

## 📱 Najłatwiejsze sposoby uruchomienia

### 🎯 Opcja 1: Skrypt Bash (Linux/Mac) - NAJŁATWIEJSZE
```bash
# Nadaj uprawnienia wykonywania
chmod +x start_foodsave.sh

# Uruchom aplikację
./start_foodsave.sh
```

### 🎯 Opcja 2: Python - Prosty uruchamiacz
```bash
python3 start_foodsave.py
```

### 🎯 Opcja 3: Python - Pełny manager (dla zaawansowanych)
```bash
python3 foodsave_console_manager.py
```

---

## 🔧 Co się dzieje podczas uruchamiania?

1. **Sprawdzanie wymagań** - Python, Node.js, NPM
2. **Uruchamianie backend** - API na porcie 8000
3. **Uruchamianie frontend** - GUI na porcie 1420  
4. **Otwieranie przeglądarki** - automatyczne otwarcie aplikacji

---

## 🌐 Gdzie znajdę aplikację?

Po uruchomieniu aplikacja będzie dostępna pod adresami:

- **🖥️ Interface użytkownika**: http://localhost:1420
- **🔧 API Backend**: http://localhost:8000
- **📊 Dokumentacja API**: http://localhost:8000/docs

---

## ❓ Problemy z uruchomieniem?

### 🔍 Sprawdź wymagania:
```bash
# Python 3.8+
python3 --version

# Node.js 16+  
node --version

# NPM
npm --version
```

### 🛠️ Instalacja wymagań (Ubuntu/Debian):
```bash
# Python
sudo apt update
sudo apt install python3 python3-pip

# Node.js i NPM
sudo apt install nodejs npm

# Git (jeśli potrzebujesz)
sudo apt install git
```

### 🍎 Instalacja wymagań (macOS):
```bash
# Zainstaluj Homebrew jeśli nie masz
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python
brew install python

# Node.js i NPM
brew install node
```

### 🪟 Windows:
1. Pobierz Python z https://python.org
2. Pobierz Node.js z https://nodejs.org
3. Użyj PowerShell lub Command Prompt:
```cmd
python start_foodsave.py
```

---

## 🎮 Jak używać aplikacji?

### 1. 💬 Chat z AI
- Otwórz http://localhost:1420
- Wpisz wiadomość w pole tekstowe
- Wybierz agenta (Analizator Paragonów, Doradca Żywienia, itp.)
- Kliknij wyślij lub naciśnij Enter

### 2. 📄 Dodawanie paragonów
- Kliknij przycisk "Skanuj Paragon"
- Wybierz zdjęcie paragonu
- AI automatycznie przeanalizuje produkty

### 3. 📦 Zarządzanie spiżarnią
- Kliknij "Moja Spiżarnia"
- Zobacz swoje produkty
- Dodaj nowe produkty przyciskiem "Dodaj Zakupy"

### 4. 🔍 Ustawienia RAG
- Kliknij "RAG Settings" w prawym górnym rogu
- Przeglądaj dokumenty w systemie
- Dodawaj nowe dokumenty do wyszukiwania

---

## 🛑 Jak zatrzymać aplikację?

### Skrypt Bash:
- Naciśnij `Ctrl+C` w terminalu

### Python:
- Naciśnij `Ctrl+C` w terminalu
- Lub zamknij okno terminala

### Ręcznie:
```bash
# Zatrzymaj wszystkie procesy
pkill -f uvicorn
pkill -f "npm.*dev"
pkill -f vite
```

---

## 🧹 Rozwiązywanie problemów

### Problem: "Port already in use"
```bash
# Sprawdź co używa portów
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :1420

# Zatrzymaj proces
sudo kill -9 [PID]
```

### Problem: "Module not found"
```bash
# Zainstaluj zależności Python
pip3 install -r requirements.txt

# Zainstaluj zależności Node.js
cd gui_refactor
python3 -m http.server 8080
```

### Problem: "Permission denied"
```bash
# Nadaj uprawnienia
chmod +x start_foodsave.sh
chmod +x *.py
```

### Problem: Frontend nie uruchamia się
```bash
cd gui_refactor
python3 -m http.server 8080
```

### Problem: Backend nie uruchamia się
```bash
cd src/backend
pip3 install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📋 Manager aplikacji - zaawansowane opcje

Jeśli potrzebujesz więcej kontroli, użyj pełnego managera:

```bash
python3 foodsave_console_manager.py
```

**Dostępne opcje:**
1. 🚀 Uruchom całą aplikację
2. 🖥️ Otwórz aplikację w przeglądarce  
3. 🔧 Zarządzaj usługami
4. 📊 Sprawdź szczegółowy status
5. 🔍 Zobacz logi aplikacji
6. 🧹 Napraw problemy
7. 🛑 Zatrzymaj wszystko
8. ❓ Pomoc i instrukcje

---

## 💡 Wskazówki

### ⚡ Szybkie uruchomienie codzienne:
```bash
# Utwórz alias w ~/.bashrc
echo 'alias foodsave="cd /ścieżka/do/foodsave && ./start_foodsave.sh"' >> ~/.bashrc
source ~/.bashrc

# Teraz wystarczy:
foodsave
```

### 🖥️ Uruchomienie w tle:
```bash
# Uruchom w tle
nohup ./start_foodsave.sh > foodsave.log 2>&1 &

# Sprawdź status
ps aux | grep -E "(uvicorn|vite|npm)"
```

### 🔄 Auto-restart po reboot:
```bash
# Dodaj do crontab
crontab -e

# Dodaj linię:
@reboot cd /ścieżka/do/foodsave && ./start_foodsave.sh
```

---

## 📞 Potrzebujesz pomocy?

1. **Sprawdź logi** - `python3 foodsave_console_manager.py` → opcja 5
2. **Szczegółowy status** - `python3 foodsave_console_manager.py` → opcja 4  
3. **Automatyczne naprawy** - `python3 foodsave_console_manager.py` → opcja 6
4. **Dokumentacja** - folder `docs/`
5. **GitHub Issues** - jeśli znalazłeś błąd

---

## 🎉 Gotowe!

Twoja aplikacja FoodSave AI powinna teraz działać na:
- http://localhost:1420 (interface użytkownika)
- http://localhost:8000 (API)

**Ciesz się inteligentnym zarządzaniem spiżarnią! 🍽️**