# 🚀 FoodSave AI - Szybki Start

## 📱 Dla użytkowników nietechnicznych

### 🎯 **Jak uruchomić aplikację w 10 sekund:**

1. **🖱️ Kliknij dwukrotnie** ikonę "FoodSave AI Manager" na pulpicie
2. **⌨️ Wpisz "1"** i naciśnij Enter
3. **🎉 Gotowe!** Aplikacja otworzy się w przeglądarce

---

### 🔧 **Jeśli coś nie działa:**

1. **🖱️ Kliknij dwukrotnie** ikonę "FoodSave AI Manager" na pulpicie  
2. **⌨️ Wpisz "7"** (Rozwiąż problemy) i naciśnij Enter
3. **👀 Przeczytaj** komunikaty i potwierdź naprawy
4. **🔄 Spróbuj** ponownie opcji "1"

---

### 📋 **Podstawowe opcje managera:**

| Opcja | Co robi | Kiedy używać |
|-------|---------|--------------|
| **1** | 🚀 Uruchom aplikację | Pierwszy raz lub po restarcie komputera |
| **2** | 🛑 Zatrzymaj aplikację | Przed wyłączeniem komputera |
| **3** | 🔄 Restartuj aplikację | Gdy aplikacja nie odpowiada |
| **4** | 📊 Sprawdź status | Czy wszystko działa? |
| **5** | 🌐 Otwórz w przeglądarce | Szybki dostęp do aplikacji |
| **6** | 📋 Pokaż logi | Gdy szukasz przyczyny problemów |
| **7** | 🔧 Napraw problemy | Automatyczna diagnostyka |
| **8** | ❓ Pomoc | Szczegółowe instrukcje |

---

### 🌐 **Adresy aplikacji:**
- **Główna aplikacja**: http://localhost:8085
- **Dokumentacja API**: http://localhost:8000/docs

---

### ⚡ **Najczęstsze problemy i rozwiązania:**

#### Problem: "Port jest zajęty"
- **Rozwiązanie**: Opcja "7" → Potwierdź zakończenie blokujących procesów

#### Problem: "Docker nie działa"  
- **Rozwiązanie**: `sudo systemctl start docker` w terminalu

#### Problem: "Aplikacja nie otwiera się"
- **Rozwiązanie**: Opcja "3" (Restart) → Opcja "5" (Otwórz przeglądarkę)

#### Problem: "Brak ikony na pulpicie"
- **Terminal**: `cd projekt && ./install_desktop_shortcut.sh`

---

### 🧪 **Test systemu:**
```bash
./test_manager.sh
```

---

**💡 Wskazówka**: Jeśli to pierwsze uruchomienie, poczekaj 5-10 minut na pobranie wszystkich komponentów.