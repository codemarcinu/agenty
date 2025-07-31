# 🤖 AGENTY - Aplikacja Konsolowa

Zaawansowana aplikacja konsolowa do zarządzania agentami AI z pełnym interfejsem UX/UI.

## 📋 Spis treści

- [🚀 Szybki start](#szybki-start)
- [✨ Funkcjonalności](#funkcjonalności)
- [🔧 Instalacja](#instalacja)
- [💻 Użytkowanie](#użytkowanie)
- [🛠️ Rozwiązywanie problemów](#rozwiązywanie-problemów)
- [📚 Szczegółowa dokumentacja](#szczegółowa-dokumentacja)

## 🚀 Szybki start

### 1. Uruchom backend (jeśli nie jest uruchomiony)
```bash
cd agenty/backend
python main.py
```

### 2. Uruchom aplikację konsolową
```bash
./start_agenty_console.sh
```

Lub bezpośrednio:
```bash
python console_agenty_enhanced.py
```

## ✨ Funkcjonalności

### 🎯 Menu główne
- **Lista Agentów** - Zarządzanie dostępnymi agentami AI
- **Chat Interaktywny** - Rozmowa z agentami w czasie rzeczywistym
- **Dashboard** - Monitor systemu z danymi na żywo
- **Konfiguracja** - Ustawienia aplikacji i systemu
- **Statystyki** - Analiza wydajności i użycia
- **System pomocy** - Komprehensywna dokumentacja

### 🤖 Obsługiwane agenty

| Agent | Typ | Opis |
|-------|-----|------|
| **Chef Agent** | 🍳 | Planowanie posiłków, przepisy, dieta |
| **Weather Agent** | 🌤️ | Prognoza pogody, informacje klimatyczne |
| **RAG Agent** | 🔍 | Wyszukiwanie w dokumentach, Q&A |
| **OCR Agent** | 📖 | Rozpoznawanie tekstu z obrazów |
| **Search Agent** | 🔍 | Wyszukiwanie informacji online |
| **Analytics Agent** | 📊 | Analiza danych i statystyki |

### 🎨 Zaawansowany interfejs

#### Progress indicators i feedback
- ⏳ Animowane wskaźniki postępu
- 🔄 Spinnery dla długotrwałych operacji
- ✅ Komunikaty sukcesu/błędu z kolorami
- 📊 Real-time status bar

#### Hierarchiczne menu
- 📋 Intuicyjna nawigacja numeryczna
- ⌨️ Skróty klawiszowe
- 🔙 Nawigacja breadcrumb
- 💡 Kontekstowa pomoc

#### Tryb interaktywny
- 💬 Chat z agentami w naturalnym języku
- 🔄 Zachowanie kontekstu rozmowy
- 📝 Komendy specjalne (`/help`, `/clear`, `/status`)
- 🎯 Auto-wykrywanie typu zapytania

## 🔧 Instalacja

### Wymagania
- Python 3.8+
- Backend AGENTY uruchomiony na porcie 8000

### Zależności
```bash
pip install -r requirements-console.txt
```

Lub ręcznie:
```bash
pip install rich==13.7.0 textual==0.81.0 httpx==0.25.2 prompt-toolkit==3.0.43
```

### Sprawdzenie instalacji
```bash
python test_console.py
```

## 💻 Użytkowanie

### Nawigacja w menu
- Użyj numerów **1-6** do wyboru opcji
- **0** - wyjście z aplikacji/powrót
- **Ctrl+C** - przerwanie operacji
- **Ctrl+Q** - szybkie wyjście

### Tryb chat
```
💬 Przykłady zapytań:
• "Jaka będzie pogoda jutro w Warszawie?" 
• "Zaproponuj przepis na obiad dla 4 osób"
• "Wyszukaj informacje o AI"
• "Przeanalizuj ten dokument"
```

#### Dostępne komendy chat:
- `/help` - szczegółowa pomoc
- `/clear` - wyczyść ekran
- `/status` - status systemu  
- `/agents` - lista agentów
- `/exit` - zakończ chat

### Dashboard na żywo
- 📊 Metryki systemu w czasie rzeczywistym
- 🤖 Status wszystkich agentów
- 🌐 Monitor endpointów API
- ⚡ Czas odpowiedzi i wydajność

### Konfiguracja systemu
- 🔄 Regeneracja ID sesji
- 🌐 Test połączenia z backendem
- 📊 Szczegółowe informacje systemowe
- 💾 Eksport konfiguracji

## 🛠️ Rozwiązywanie problemów

### ❌ Backend niedostępny
```bash
# Sprawdź czy backend działa
curl http://localhost:8000/api/health

# Uruchom backend
cd agenty/backend && python main.py
```

### ❌ Błędy importu
```bash
# Zainstaluj brakujące zależności
pip install -r requirements-console.txt

# Sprawdź instalację Pythona
python --version
```

### ❌ Agenci nie odpowiadają
1. Sprawdź status w Dashboard (opcja 3)
2. Zrestartuj backend
3. Sprawdź logi serwera

### ❌ Aplikacja działa wolno
1. Sprawdź obciążenie systemu
2. Zamknij inne aplikacje
3. Sprawdź połączenie internetowe

## 📚 Szczegółowa dokumentacja

### Architektura aplikacji

```
console_agenty_enhanced.py     # Główna aplikacja
├── console/
│   ├── api_client.py         # Klient API z fallback
│   └── ui_components.py      # Komponenty interfejsu
├── test_console.py           # Testy aplikacji
└── start_agenty_console.sh   # Skrypt startowy
```

### API Client
- **Automatyczne wykrywanie endpointów** - próbuje v1, v2, fallback
- **Obsługa błędów** - graceful degradation 
- **Timeout handling** - konfigurowalne limity czasowe
- **Mock responses** - działanie offline

### UI Components
- **MenuRenderer** - renderowanie menu i tabel
- **ProgressManager** - wskaźniki postępu
- **DialogManager** - dialogi i input
- **DashboardRenderer** - dashboard i metryki
- **HelpSystem** - system pomocy

### Status indicators
- 🟢 **Online** - pełna funkcjonalność
- 🟡 **Limited** - ograniczone API, mock responses
- 🔴 **Offline** - brak połączenia z backend

## 🎯 Przykłady użycia

### 1. Szybka rozmowa z agentem
```bash
./start_agenty_console.sh
# Wybierz opcję 2 (Chat Interaktywny)
# Wpisz zapytanie np. "Jaka pogoda dziś?"
```

### 2. Monitoring systemu
```bash
./start_agenty_console.sh  
# Wybierz opcję 3 (Dashboard)
# Obserwuj metryki w czasie rzeczywistym
```

### 3. Test wszystkich agentów
```bash
./start_agenty_console.sh
# Wybierz opcję 1 (Lista Agentów)
# Wybierz opcję 2 (Test agenta)
```

## 🔗 Dodatkowe zasoby

- **Backend API**: http://localhost:8000/docs
- **Status serwera**: http://localhost:8000/api/health
- **GitHub**: https://github.com/codemarcinu/agenty
- **Dokumentacja backend**: `agenty/docs/`

## 🤝 Wsparcie

W przypadku problemów:

1. **Sprawdź logi** - aplikacja wyświetla szczegółowe komunikaty
2. **Użyj trybu debug** - uruchom z flagą `-v` jeśli dostępna
3. **Sprawdź status** - użyj Dashboard lub `/status` w chat
4. **Restart** - zrestartuj aplikację i backend

---

**🎉 Gotowe! Aplikacja konsolowa AGENTY z pełnym interfejsem UX/UI jest gotowa do użycia.**

*Stworzone zgodnie z najlepszymi praktykami UX/UI dla aplikacji konsolowych.*