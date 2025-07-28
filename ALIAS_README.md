# 🤖 Alias "asystent" - Szybkie uruchamianie aplikacji

## 🚀 Instalacja aliasu

### Krok 1: Uruchom skrypt konfiguracyjny
```bash
./setup_alias.sh
```

### Krok 2: Aktywuj alias
```bash
# Opcja 1: Zrestartuj terminal
# Opcja 2: Wykonaj w bieżącej sesji
source ~/.bashrc  # dla bash
# lub
source ~/.zshrc   # dla zsh
```

### Krok 3: Sprawdź czy działa
```bash
asystent help
```

## 📋 Dostępne komendy

### Podstawowe komendy
```bash
asystent          # Menu główne (interaktywne)
asystent dev      # Tryb deweloperski (lokalnie)
asystent prod     # Tryb produkcyjny (Docker)
asystent status   # Sprawdź status usług
asystent stop     # Zatrzymaj usługi
asystent logs     # Pokaż logi
asystent test     # Uruchom testy
asystent help     # Pokaż pomoc
```

### Tryby uruchamiania

#### 🛠️ Tryb deweloperski (`asystent dev`)
- **Środowisko**: Lokalne Python + venv
- **Zalety**: Szybsze uruchamianie, łatwiejsze debugowanie
- **Wymagania**: Python 3.11+, zależności w venv
- **Użycie**: `asystent dev`

#### 🐳 Tryb produkcyjny (`asystent prod`)
- **Środowisko**: Kontenery Docker
- **Zalety**: Izolowane środowisko, pełna funkcjonalność
- **Wymagania**: Docker + Docker Compose
- **Użycie**: `asystent prod`

## 🎯 Przykłady użycia

### Szybkie uruchomienie
```bash
# Menu interaktywne
asystent

# Bezpośrednie uruchomienie w trybie deweloperskim
asystent dev

# Bezpośrednie uruchomienie w trybie produkcyjnym
asystent prod
```

### Zarządzanie usługami
```bash
# Sprawdź status
asystent status

# Zatrzymaj usługi
asystent stop

# Pokaż logi
asystent logs
```

### Testowanie
```bash
# Uruchom testy
asystent test

# Pokaż pomoc
asystent help
```

## 🔧 Konfiguracja

### Pliki konfiguracyjne
- **Bash**: `~/.bashrc`
- **Zsh**: `~/.zshrc`
- **Alias**: `alias asystent='/ścieżka/do/projektu/asystent'`

### Ścieżka projektu
Alias automatycznie wykrywa ścieżkę do projektu i dodaje ją do konfiguracji.

## 🐛 Rozwiązywanie problemów

### Problem: "command not found: asystent"
```bash
# Sprawdź czy alias jest w pliku konfiguracyjnym
grep "alias asystent" ~/.bashrc

# Aktywuj alias ręcznie
source ~/.bashrc

# Lub dodaj alias ręcznie
alias asystent='/pełna/ścieżka/do/projektu/asystent'
```

### Problem: "Permission denied"
```bash
# Nadaj uprawnienia wykonywania
chmod +x asystent
chmod +x setup_alias.sh
```

### Problem: "Docker not found"
```bash
# Zainstaluj Docker
sudo apt-get install docker.io docker-compose

# Dodaj użytkownika do grupy docker
sudo usermod -aG docker $USER

# Uruchom Docker
sudo systemctl start docker
```

## 📁 Struktura projektu

```
AGENTY/
├── asystent              # Główny skrypt aliasu
├── setup_alias.sh        # Skrypt konfiguracji aliasu
├── ALIAS_README.md       # Ta dokumentacja
├── console_app/          # Aplikacja konsolowa
├── PARAGONY/            # Katalog paragonów
├── WIEDZA_RAG/          # Katalog dokumentów RAG
├── docker-compose.console.yaml  # Konfiguracja Docker
└── requirements-console.txt     # Zależności Python
```

## 🎉 Korzyści z aliasu

### ✅ **Szybkość**
- Jedna komenda zamiast długich ścieżek
- Automatyczne wykrywanie środowiska
- Inteligentne sprawdzanie wymagań

### ✅ **Wygoda**
- Menu interaktywne
- Kolorowe komunikaty
- Automatyczne testy

### ✅ **Elastyczność**
- Dwa tryby uruchamiania
- Zarządzanie usługami
- Monitoring i logi

### ✅ **Niezawodność**
- Sprawdzanie wymagań
- Obsługa błędów
- Automatyczne naprawy

## 🔄 Aktualizacja aliasu

Jeśli przeniesiesz projekt do innej lokalizacji:

```bash
# Uruchom ponownie skrypt konfiguracyjny
./setup_alias.sh

# Lub zaktualizuj ręcznie
sed -i 's|alias asystent=.*|alias asystent="'$(pwd)'/asystent"|' ~/.bashrc
source ~/.bashrc
```

## 📞 Wsparcie

### Pomoc w aplikacji
```bash
asystent help
```

### Debugowanie
```bash
# Sprawdź czy skrypt działa
./asystent help

# Sprawdź alias
type asystent

# Sprawdź ścieżkę
which asystent
```

---

**🎯 Teraz możesz uruchomić aplikację wpisując tylko `asystent` w terminalu!** 