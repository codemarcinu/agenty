# 🚀 FoodSave AI GUI Autostart Guide

## 📋 Przegląd

FoodSave AI Desktop Application oferuje kompletną funkcjonalność automatycznego uruchamiania ze startem systemu. Aplikacja może być skonfigurowana do uruchamiania automatycznie przy starcie sesji graficznej.

## 🎯 Metody Autostartu

### 1. **Desktop Entry (Zalecane)**
- Tworzy plik `.desktop` w `~/.config/autostart/`
- Działa z większością środowisk graficznych (GNOME, KDE, XFCE)
- Najprostsza metoda dla użytkowników

### 2. **Systemd User Service**
- Tworzy service systemd dla użytkownika
- Lepsze zarządzanie i monitoring
- Zaawansowana opcja dla administratorów

## 🖥️ Zarządzanie przez GUI

### Uruchomienie GUI
```bash
# Uruchom aplikację GUI
python3 -m gui.launcher

# Lub przez skrypt
./gui/autostart.sh
```

### Konfiguracja w GUI
1. **Otwórz aplikację** - ikona pojawi się w zasobniku systemowym
2. **Kliknij prawym przyciskiem** na ikonę
3. **Wybierz "⚙️ Ustawienia"**
4. **Przejdź do zakładki "Ogólne"**
5. **Zarządzaj autostartem**:
   - ✅ **Włącz autostart** - aplikacja będzie uruchamiana automatycznie
   - ❌ **Wyłącz autostart** - aplikacja nie będzie uruchamiana automatycznie
   - 📊 **Status** - sprawdź aktualny stan autostartu

## 💻 Zarządzanie przez CLI

### Skrypt Bash
```bash
# Włącz autostart
./gui/autostart.sh enable

# Wyłącz autostart
./gui/autostart.sh disable

# Sprawdź status
./gui/autostart.sh status

# Szczegółowe informacje
./gui/autostart.sh info

# Pomoc
./gui/autostart.sh help
```

### Python CLI
```bash
# Włącz autostart (desktop entry)
python3 gui/autostart_cli.py enable

# Włącz autostart (systemd service)
python3 gui/autostart_cli.py enable --systemd

# Wyłącz autostart
python3 gui/autostart_cli.py disable

# Sprawdź status
python3 gui/autostart_cli.py status

# Szczegółowe informacje
python3 gui/autostart_cli.py info
```

## 🔧 Konfiguracja Ręczna

### Desktop Entry
```bash
# Utwórz katalog autostart
mkdir -p ~/.config/autostart

# Utwórz plik desktop entry
cat > ~/.config/autostart/foodsave-ai.desktop << EOF
[Desktop Entry]
Type=Application
Name=FoodSave AI
Comment=Inteligentny Asystent Żywności
Exec=/home/user/path/to/AIASISSTMARUBO/gui/launcher.py
Icon=/home/user/path/to/AIASISSTMARUBO/gui/icons/assist.svg
Terminal=false
Type=Application
Categories=Utility;Food;AI;
X-GNOME-Autostart-enabled=true
Hidden=false
NoDisplay=false
EOF

# Nadaj uprawnienia wykonywania
chmod +x ~/.config/autostart/foodsave-ai.desktop
```

### Systemd User Service
```bash
# Utwórz katalog systemd user
mkdir -p ~/.config/systemd/user

# Utwórz service file
cat > ~/.config/systemd/user/foodsave-ai.service << EOF
[Unit]
Description=FoodSave AI Desktop Application
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=/home/user/path/to/AIASISSTMARUBO/gui/launcher.py
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority

[Install]
WantedBy=graphical-session.target
EOF

# Włącz service
systemctl --user enable foodsave-ai.service
```

## 📊 Monitoring i Diagnostyka

### Sprawdzenie Statusu
```bash
# Sprawdź czy autostart jest włączony
./gui/autostart.sh status

# Sprawdź szczegółowe informacje
./gui/autostart.sh info

# Sprawdź pliki autostartu
ls -la ~/.config/autostart/
ls -la ~/.config/systemd/user/
```

### Logi Systemowe
```bash
# Sprawdź logi systemd (jeśli używasz systemd service)
journalctl --user -u foodsave-ai.service -f

# Sprawdź logi aplikacji
tail -f logs/gui.log
```

## 🛠️ Troubleshooting

### Problem: Aplikacja nie uruchamia się automatycznie
**Rozwiązania:**
1. **Sprawdź uprawnienia**:
   ```bash
   ls -la ~/.config/autostart/foodsave-ai.desktop
   chmod +x ~/.config/autostart/foodsave-ai.desktop
   ```

2. **Sprawdź ścieżkę**:
   ```bash
   # Upewnij się, że ścieżka w Exec= jest poprawna
   cat ~/.config/autostart/foodsave-ai.desktop
   ```

3. **Sprawdź środowisko**:
   ```bash
   # Upewnij się, że Python i zależności są dostępne
   python3 -c "import PyQt5; print('PyQt5 OK')"
   ```

### Problem: Błąd "Permission denied"
**Rozwiązania:**
1. **Sprawdź uprawnienia katalogu**:
   ```bash
   ls -la ~/.config/autostart/
   chmod 755 ~/.config/autostart/
   ```

2. **Sprawdź uprawnienia pliku**:
   ```bash
   chmod +x ~/.config/autostart/foodsave-ai.desktop
   ```

### Problem: Aplikacja uruchamia się w terminalu
**Rozwiązania:**
1. **Sprawdź ustawienie Terminal=false** w pliku .desktop
2. **Upewnij się, że Exec= wskazuje na launcher.py**

## 🔒 Bezpieczeństwo

### Uwagi Bezpieczeństwa
- ✅ Autostart używa tylko katalogów użytkownika (`~/.config/`)
- ✅ Nie wymaga uprawnień administratora
- ✅ Można łatwo wyłączyć przez GUI lub CLI
- ✅ Pliki są tworzone z odpowiednimi uprawnieniami

### Sprawdzenie Bezpieczeństwa
```bash
# Sprawdź uprawnienia plików autostartu
ls -la ~/.config/autostart/foodsave-ai.desktop

# Sprawdź zawartość pliku
cat ~/.config/autostart/foodsave-ai.desktop

# Sprawdź czy plik jest wykonywalny
file ~/.config/autostart/foodsave-ai.desktop
```

## 📋 Checklist Konfiguracji

### Przed Włączeniem Autostartu
- [ ] Aplikacja GUI działa poprawnie
- [ ] Backend uruchamia się bez błędów
- [ ] Wszystkie zależności są zainstalowane
- [ ] Ścieżki w konfiguracji są poprawne

### Po Włączeniu Autostartu
- [ ] Sprawdź status: `./gui/autostart.sh status`
- [ ] Przetestuj restart systemu
- [ ] Sprawdź czy aplikacja uruchamia się automatycznie
- [ ] Sprawdź logi pod kątem błędów

### Regularne Sprawdzanie
- [ ] Sprawdź status autostartu co miesiąc
- [ ] Sprawdź logi aplikacji
- [ ] Zaktualizuj konfigurację po zmianach w aplikacji

## 🎯 Podsumowanie

Funkcjonalność autostartu FoodSave AI GUI zapewnia:

1. **Łatwość użycia** - konfiguracja przez GUI lub CLI
2. **Elastyczność** - desktop entry lub systemd service
3. **Bezpieczeństwo** - tylko katalogi użytkownika
4. **Monitoring** - szczegółowe informacje o statusie
5. **Troubleshooting** - narzędzia diagnostyczne

Aplikacja będzie uruchamiana automatycznie przy starcie systemu, zapewniając ciągłą dostępność FoodSave AI. 