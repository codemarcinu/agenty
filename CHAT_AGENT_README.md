# 💬 Agent Chatowy - Aplikacja Konsolowa

## Opis

Agent chatowy został zaimplementowany jako nowa funkcja aplikacji konsolowej, umożliwiająca konwersację z AI w języku naturalnym. Agent obsługuje kontekst, historię rozmów oraz oferuje inteligentne sugestie.

## ✨ Funkcjonalności

### 🗣️ Konwersacja
- **Naturalny język**: Konwersacja w języku polskim i angielskim
- **Kontekst**: Agent pamięta poprzednie wiadomości w ramach sesji
- **Markdown**: Obsługa formatowania w odpowiedziach agenta

### 📚 Historia rozmów
- **Trwałość**: Historia jest zapisywana automatycznie w pliku `chat_history.json`
- **Import/Export**: Możliwość eksportu i importu historii rozmów
- **Ograniczenia**: Domyślnie przechowuje maksymalnie 50 ostatnich wiadomości

### 🤖 Inteligentne sugestie
- **Kontekstowe pytania**: Sugerowane pytania na podstawie poprzednich rozmów
- **Dynamiczne dostosowanie**: Sugestie zmieniają się w zależności od tematów
- **Kategorie**: Paragon OCR, RAG, eksporty, statystyki, pomoc

### 🛠️ Komendy specjalne
- `exit`, `quit`, `wyjście` - Wyjście z chatu
- `clear`, `wyczyść` - Wyczyszczenie historii rozmów
- `history`, `historia` - Wyświetlenie historii rozmów
- `summary`, `podsumowanie` - Podsumowanie obecnej konwersacji
- `suggestions`, `sugestie` - Wyświetlenie sugerowanych pytań
- `help`, `pomoc` - Pomoc dotycząca komend czatu

## 🚀 Uruchomienie

### Sposób 1: Skrypt startowy
```bash
./start_chat_console.sh
```

### Sposób 2: Bezpośrednio
```bash
python -m console_app.main
```

Następnie wybierz opcję **"3. 💬 Chat z agentem AI"** z menu głównego.

## 📋 Wymagania

### Podstawowe zależności
```bash
pip install aiohttp rich structlog
```

### Pełne zależności (opcjonalne)
```bash
pip install -r requirements-console.txt
```

### Backend AI
Aplikacja wymaga uruchomionego backendu AI pod adresem `http://localhost:8000`

## 🏗️ Architektura

### Klasy główne

#### `ChatAgent`
- Główna klasa agenta chatowego
- Zarządza komunikacją z backendem
- Obsługuje historię i kontekst rozmów

#### `ConversationHistory`
- Zarządzanie historią wiadomości
- Export/import do plików JSON
- Ograniczenie liczby przechowywanych wiadomości

#### `ConsoleUI.show_chat_interface()`
- Interfejs użytkownika dla chatu
- Obsługa komend specjalnych
- Wyświetlanie odpowiedzi z formatowaniem

### Struktura plików
```
console_app/
├── chat_agent.py          # Główna logika agenta
├── console_ui.py          # Interfejs chatu (show_chat_interface)
├── main.py                # Integracja z aplikacją główną
└── config.py              # Konfiguracja (BACKEND_URL)

chat_history.json          # Historia rozmów (tworzona automatycznie)
```

## 💡 Przykłady użycia

### Podstawowa konwersacja
```
Ty: Jak przetworzyć paragony wsadowo?
🤖 Agent: Możesz przetworzyć wszystkie paragony jednocześnie...
```

### Komendy specjalne
```
Ty: history
📜 Historia czatu (ostatnie 10 wiadomości):
...

Ty: clear
🧹 Historia konwersacji została wyczyszczona!
```

### Sugestie kontekstowe
Po rozmowie o paragonach, agent zasugeruje:
- "Jakiej jakości obrazy dają najlepsze wyniki OCR?"
- "Czy mogę przetworzyć paragony wsadowo?"
- "Jak poprawić dokładność rozpoznawania tekstu?"

## 🧪 Testowanie

### Uruchomienie testów
```bash
# Testy podstawowe
python test_chat_console.py

# Testy integracji
python test_chat_integration.py
```

### Pokrycie testów
- ✅ Zarządzanie historią konwersacji
- ✅ Inicjalizacja agenta chatowego
- ✅ Generowanie sugerowanych pytań
- ✅ Podsumowania konwersacji
- ✅ Komendy specjalne
- ✅ Trwałość historii
- ✅ Wykrywanie tematów

## 🔧 Konfiguracja

### Zmienne konfiguracyjne w `config.py`
```python
BACKEND_URL = "http://localhost:8000"  # Adres backendu AI
```

### Ustawienia historii
```python
ConversationHistory(max_messages=50)  # Maksymalna liczba wiadomości
```

## 🚨 Rozwiązywanie problemów

### "Brak połączenia z backendem"
- Sprawdź czy backend AI jest uruchomiony
- Zweryfikuj adres w konfiguracji (BACKEND_URL)
- Sprawdź czy port 8000 nie jest zablokowany

### "ModuleNotFoundError"
```bash
pip install aiohttp rich structlog
```

### "Historia nie jest zapisywana"
- Sprawdź uprawnienia zapisu w katalogu
- Upewnij się że `chat_history.json` nie jest tylko do odczytu

### "Sugestie nie działają"
- Sugestie są generowane na podstawie słów kluczowych
- Spróbuj użyć słów: "paragon", "rag", "eksport", "statystyki"

## 🛣️ Rozwój

### Planowane funkcje
- [ ] Eksport rozmów do różnych formatów
- [ ] Integracja z bazą wiedzy RAG
- [ ] Personalizowane sugestie
- [ ] Obsługa załączników w czacie
- [ ] Tryb głosowy (text-to-speech)

### Rozszerzenia
- Dodanie nowych komend specjalnych
- Integracja z innymi agentami systemowymi
- Wsparcie dla wielu języków
- API do zewnętrznych integracji

## 📄 Licencja

Zgodnie z licencją głównego projektu.

---

**Autor**: Claude Code Agent  
**Data**: 2025-01-28  
**Wersja**: 1.0.0