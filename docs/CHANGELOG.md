# 📝 Changelog - FoodSave AI

> **Ostatnia aktualizacja:** 2025-07-27

## 🆕 [2025-07-27] - Bielik-11B-v2.3 Integration & Documentation Overhaul

### ✨ Major Updates
- **[Comprehensive Changelog](CHANGELOG_2025-07-27.md)** - Detailed changelog for version 2.1.0
- **[Project Status Report](PROJECT_STATUS_2025-07-27.md)** - Complete project overview
- **Bielik-11B-v2.3 Integration** - Primary Polish language model with 32k context window
- **Modular Cursor Rules** - Split `.cursorrules` into specialized files for better maintainability

### 🛠️ Technical Improvements
- **AI Model Optimizations** - Multi-model fusion with confidence scoring
- **System Architecture** - Planner-Executor-Synthesizer pattern
- **Code Quality** - Enhanced type hints and docstring coverage
- **Performance** - Improved response times and resource usage

### 📚 Documentation
- **Project Status** - Comprehensive system overview
- **Architecture Guide** - Detailed system architecture
- **API Reference** - Complete API documentation
- **Development Guide** - Enhanced setup instructions

### 🎯 Key Changes
- **Primary Model**: Upgraded to `SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M`
- **Context Window**: Expanded to 32,768 tokens
- **Polish Optimization**: Enhanced Polish language processing with 95%+ confidence
- **Performance**: Improved response times and resource utilization

---

## 🆕 [2025-07-27] - Aktualizacja dokumentacji i optymalizacja bazy danych

### ✨ Nowe Funkcje
- **📊 Optymalizacja bazy danych** - Ulepszone zarządzanie połączeniami SQLite
  - Performance monitoring dla zapytań
  - Retry mechanism z exponential backoff
  - Connection pool monitoring
  - SQLite-specific optimizations (WAL mode, cache size)
- **🔍 Database indexes** - Automatyczne tworzenie indeksów dla lepszej wydajności
- **📈 Performance metrics** - Monitoring wydajności bazy danych

### 🛠️ Ulepszenia
- **Dokumentacja** - Zaktualizowano datę ostatniej aktualizacji
- **Database connection handling** - Lepsze zarządzanie połączeniami
- **Error handling** - Ulepszone obsługiwanie błędów bazy danych
- **Monitoring** - Dodano szczegółowe metryki wydajności

### 📚 Dokumentacja
- **Zaktualizowano CHANGELOG.md** - Nowa data aktualizacji
- **Zaktualizowano README.md** - Aktualizacja daty
- **Database performance monitoring** - Nowe funkcje monitoringu

### 🎯 Kluczowe Zmiany
- **Database retry mechanism** - Automatyczne ponowne próby przy błędach połączenia
- **SQLite optimizations** - WAL mode, cache size, page size optimizations
- **Performance tracking** - Śledzenie czasu wykonywania zapytań
- **Connection pool monitoring** - Monitoring puli połączeń

---

## 🆕 [2025-07-15] - Uproszczony GUI

### ✨ Nowe Funkcje
- **🍽️ Uproszczony GUI** - Nowy interfejs skupiony na czacie
  - Chat-centric design jako główny element
  - Agent selector w dropdown (8 głównych agentów)
  - Quick actions dla szybkich zadań
  - File upload dla obrazów
  - Dark mode toggle
  - Responsive design
- **📋 Automatyczna instalacja zależności** - PySide6, structlog
- **🔍 Sprawdzanie wymagań** - Automatyczna walidacja systemu
- **📱 Responsive layout** - Adaptacja do różnych rozmiarów okna

### 🛠️ Ulepszenia
- **Dokumentacja** - Zaktualizowano TOC, README, QUICK_START
- **Skrypty uruchomieniowe** - Nowy skrypt `run_simplified_gui.sh`
- **Analiza GUI** - Szczegółowa analiza obecnego GUI i propozycje uproszczenia

### 📚 Dokumentacja
- **SIMPLIFIED_GUI_DESIGN.md** - Szczegółowy design uproszczonego GUI
- **GUI_SIMPLIFICATION_ANALYSIS.md** - Analiza obecnego GUI i propozycje
- **Zaktualizowano TOC.md** - Dodano nowe dokumenty
- **Zaktualizowano SCRIPTS_DOCUMENTATION.md** - Dodano sekcję GUI skryptów
- **Zaktualizowano QUICK_START.md** - Nowy przewodnik z opcjami GUI
- **Zaktualizowano FEATURES.md** - Dodano sekcję GUI opcji

### 🎯 Kluczowe Zmiany
- **Chat jako główny element** - 75% szerokości okna
- **2-panelowy layout** - Sidebar + Chat zamiast 3 paneli
- **Dropdown agent selector** - Zamiast 38 kart agentów
- **Quick actions** - Szybkie akcje dla typowych zadań
- **Collapsible sidebar** - Możliwość ukrycia panelu bocznego

### 🚀 Uruchomienie
```bash
# Uproszczony GUI (zalecane)
./scripts/run_simplified_gui.sh

# Pełny GUI (zaawansowany)
./scripts/launch_scripts_gui.sh
```

---

## 🔄 [2025-07-02] - Monitoring & MMLW Naprawy

### 🛠️ Naprawy
- **Monitoring systemu** - Status "healthy" opiera się na krytycznych komponentach
- **Perplexity API** - Usunięte z oceny statusu, traktowane jako opcjonalne
- **MMLW Embeddings** - Zawsze inicjalizowane jeśli włączone w ustawieniach
- **Testy GUI** - 100% PASSING dla jednostkowych i E2E testów

### 📊 Status
- **Testy Jednostkowe**: 11/11 testów przechodzi
- **Testy E2E**: Wszystkie krytyczne testy przechodzą
- **Czas wykonania**: ~18s (jednostkowe), ~86s (E2E)

---

## 🔄 [2025-06-15] - Refaktoryzacja i Optymalizacja

### 🏗️ Architektura
- **Refaktoryzacja agentów** - Nowa architektura agentów
- **Optymalizacja wydajności** - Szybsze działanie systemu
- **Poprawa stabilności** - Mniej błędów i crashów

### 📚 Dokumentacja
- **Aktualizacja dokumentacji** - Nowe przewodniki
- **Przykłady użycia** - Więcej przykładów
- **Troubleshooting** - Rozszerzona sekcja pomocy

---

## 🔄 [2025-05-20] - Nowe Funkcje

### ✨ Funkcje
- **System RAG** - Retrieval-Augmented Generation
- **Analiza paragonów** - Automatyczna analiza
- **Kategoryzacja produktów** - Inteligentna kategoryzacja
- **Monitoring systemu** - Real-time monitoring

### 🛠️ Ulepszenia
- **GUI improvements** - Lepszy interfejs użytkownika
- **Performance optimization** - Szybsze działanie
- **Error handling** - Lepsze obsługiwanie błędów

---

## 🔄 [2025-04-10] - Pierwsza Wersja

### 🎯 Funkcje Podstawowe
- **Backend FastAPI** - REST API
- **Frontend React** - Interfejs webowy
- **Baza danych SQLite** - Przechowywanie danych
- **Agenty AI** - Inteligentne asystenty

### 📦 Deployment
- **Docker support** - Kontenery aplikacji
- **Monitoring** - Prometheus + Grafana
- **Logging** - Strukturalne logi

---

## 📋 Planowane Funkcje

### 🔮 Roadmap
- **Mobile app** - Aplikacja mobilna
- **Voice interface** - Interfejs głosowy
- **Advanced analytics** - Zaawansowana analityka
- **Multi-language support** - Wsparcie wielu języków

### 🎯 Priorytety
1. **Stabilność** - Poprawa stabilności systemu
2. **Wydajność** - Optymalizacja wydajności
3. **UX** - Lepsze doświadczenie użytkownika
4. **Dokumentacja** - Rozszerzenie dokumentacji

---

## 📞 Kontakt

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Wiki**: GitHub Wiki

---

> **💡 Wskazówka:** Sprawdź [QUICK_START.md](QUICK_START.md) dla najnowszych instrukcji uruchamiania! 