# 🤖 FoodSave AI - Prosty Manager

## 🎯 Dla kogo jest ten manager?
Ten prosty manager został zaprojektowany dla **użytkowników nietechnicznych**, którzy chcą łatwo zarządzać aplikacją FoodSave AI bez znajomości programowania czy Docker.

## 🚀 Jak uruchomić? (Wybierz najłatwiejszy sposób)

### 🖱️ Sposób 1: Ikona na pulpicie (najłatwiejszy)
1. **Znajdź ikonę** "FoodSave AI Manager" na pulpicie
2. **Kliknij dwukrotnie** na ikonę
3. **Gotowe!** Manager się uruchomi automatycznie

### ⌨️ Sposób 2: Terminal (3 proste kroki)
1. **Otwórz terminal**: Naciśnij `Ctrl + Alt + T`
2. **Przejdź do katalogu aplikacji**:
   ```bash
   cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO
   ```
3. **Uruchom manager**:
   ```bash
   ./foodsave-manager
   ```

### 🔧 Sposób 3: Instalacja skrótu (jeśli ikona nie działa)
```bash
cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO
./install_desktop_shortcut.sh
```

## 🎨 Co zobaczysz?

Manager pokazuje czytelne menu z opcjami:

```
🎯 Co chcesz zrobić?

1. 🚀 Uruchom aplikację (Start FoodSave AI)
2. 🛑 Zatrzymaj aplikację (Stop wszystkich kontenerów)
3. 🔄 Restartuj aplikację (Restart + odświeżenie)
4. 📊 Sprawdź status (Czy aplikacja działa?)
5. 🌐 Otwórz w przeglądarce (Przejdź do aplikacji)

🔧 Narzędzia i pomoc:
6. 📋 Zarządzaj logami (Podgląd, monitorowanie)
7. 🔧 Rozwiąż problemy (Automatyczna naprawa)
8. ❓ Pomoc i informacje

0. ❌ Wyjście
```

## 📋 Najważniejsze funkcje

### ✅ Automatyczne wykrywanie
- Manager automatycznie sprawdza czy system jest gotowy
- Wykrywa problemy i proponuje rozwiązania
- Pokazuje status wszystkich komponentów

### 🪟 Logi w czasie rzeczywistym
- **Opcja 6** → **Opcja 2**: Otwiera logi w nowych oknach terminala
- Każdy komponent (Frontend, Backend, Redis, Ollama) ma swoje okno
- Logi odświeżają się automatycznie

### 🔧 Automatyczne rozwiązywanie problemów
- **Opcja 7**: Sprawdza i naprawia typowe problemy
- Wykrywa zajęte porty i proponuje ich zwolnienie
- Czyści niepotrzebne pliki Docker
- Sprawdza miejsce na dysku

### 🌐 Łatwe otwieranie aplikacji
- **Opcja 5**: Automatycznie otwiera aplikację w przeglądarce
- Nie musisz pamiętać adresów URL
- Manager sprawdzi czy aplikacja działa przed otwarciem

## 🆘 Co robić w przypadku problemów?

### Problem: "Docker nie jest zainstalowany"
```bash
# Ubuntu/Debian:
sudo apt install docker.io docker-compose

# Dodaj siebie do grupy docker:
sudo usermod -aG docker $USER
```
Następnie uruchom komputer ponownie.

### Problem: "Port jest zajęty"
1. Użyj **opcji 7** (Rozwiąż problemy)
2. Manager automatycznie zaproponuje rozwiązanie
3. Potwierdź zakończenie procesów blokujących porty

### Problem: "Aplikacja nie działa"
1. **Opcja 4**: Sprawdź status systemu
2. **Opcja 6** → **Opcja 2**: Otwórz logi w czasie rzeczywistym
3. **Opcja 3**: Spróbuj restartu aplikacji

### Problem: "Brak miejsca na dysku"
1. **Opcja 7**: Uruchom diagnostykę
2. Manager pokaże ile miejsca zostało
3. Usuń niepotrzebne pliki lub stare obrazy Docker

## 🎯 Szybki start dla początkujących

1. **Pierwsze uruchomienie**:
   ```bash
   ./foodsave-manager
   # Wybierz opcję 1 (Uruchom aplikację)
   ```

2. **Sprawdź czy działa**:
   ```bash
   # Manager automatycznie sprawdzi i pokaże status
   # Aplikacja otworzy się w przeglądarce
   ```

3. **Jeśli coś nie działa**:
   ```bash
   # W managerze wybierz opcję 7 (Rozwiąż problemy)
   # Następuj instrukcjom na ekranie
   ```

## 📍 Adresy aplikacji

Gdy aplikacja działa, dostępna jest pod adresami:
- **Główna aplikacja**: http://localhost:8085
- **API Backend**: http://localhost:8000
- **Dokumentacja API**: http://localhost:8000/docs

## 🔍 Logi i monitorowanie

### Podgląd logów w czasie rzeczywistym:
1. **Opcja 6** (Zarządzaj logami)
2. **Opcja 2** (Otwórz logi w nowych oknach)
3. Manager otworzy osobne okno dla każdego komponentu

### Rodzaje logów:
- **Frontend**: Interfejs użytkownika, serwer nginx
- **Backend**: Serwer aplikacji, API, baza danych
- **Redis**: Cache i sesje użytkowników
- **Ollama**: Modele sztucznej inteligencji

## 💡 Wskazówki

- **Pierwsze uruchomienie** może potrwać 5-10 minut (pobieranie obrazów)
- **Logi pomagają** znaleźć przyczynę problemów
- **Regularnie sprawdzaj status** aplikacji (opcja 4)
- **Użyj restartu** (opcja 3) gdy coś nie działa poprawnie
- **Manager automatycznie wykrywa** większość problemów

## 🆘 Pomoc techniczna

Jeśli nadal masz problemy:
1. Użyj **opcji 8** (Pomoc i informacje) w managerze
2. Zapisz logi do pliku: **opcja 6** → **opcja 4**
3. Uruchom pełną diagnostykę: **opcja 7**

---

**🎉 Gratulacje! Teraz możesz łatwo zarządzać FoodSave AI bez znajomości technicznej!**