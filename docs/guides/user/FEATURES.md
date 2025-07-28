# 🍽️ Funkcje Systemu - FoodSave AI

> **Ostatnia aktualizacja:** 2025-07-18  
> **Powiązane dokumenty:** [TOC.md](../TOC.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Co znajdziesz w tym dokumencie?

- [x] Kompletny przegląd funkcji systemu
- [x] Instrukcje użytkowania
- [x] Przykłady użycia
- [x] Funkcje zaawansowane
- [x] Linki do szczegółowych przewodników

## Spis treści
- [1. 📸 Analiza Paragonów](#-analiza-paragonów)
- [2. 🤖 Czat z AI](#-czat-z-ai)
- [3. 📊 Zarządzanie Zapasami](#-zarządzanie-zapasami)
- [4. 🎯 Planowanie Posiłków](#-planowanie-posiłków)
- [5. 🔄 Koordynacja Darowizn](#-koordynacja-darowizn)
- [6. 📱 Aplikacja Desktop](#-aplikacja-desktop)
- [7. 🔍 Wyszukiwanie i Filtrowanie](#-wyszukiwanie-i-filtrowanie)
- [8. 🔍 Monitorowanie Systemu](#-monitorowanie-systemu)

---

## 📸 Analiza Paragonów

### Automatyczna Ekstrakcja Danych
System automatycznie analizuje zdjęcia paragonów i wyciąga:
- **Nazwa sklepu** - Automatyczna normalizacja nazw
- **Data zakupu** - Parsowanie dat z różnych formatów
- **Lista produktów** - Nazwy, ilości, ceny jednostkowe
- **Kwota całkowita** - Suma zakupów
- **VAT** - Polskie stawki podatkowe

### Przykład Analizy
```
📸 Zdjęcie paragonu z Biedronki
↓
🤖 Analiza AI (Bielik 11b)
↓
📊 Wynik:
{
  "store_name": "BIEDRONKA",
  "normalized_store": "Biedronka",
  "date": "2025-01-15 14:30",
  "items": [
    {
      "name": "Mleko 3.2% 1L",
      "quantity": 2,
      "unit_price": 4.99,
      "total_price": 9.98,
      "category": "Nabiał > Mleko i śmietana"
    }
  ],
  "total_amount": 45.67
}
```

### Obsługiwane Sklepy
- **Biedronka** - Pełna obsługa
- **Lidl** - Pełna obsługa
- **Carrefour** - Pełna obsługa
- **Auchan** - Pełna obsługa
- **Żabka** - Pełna obsługa
- **I 35+ innych sieci** - Podstawowa obsługa

---

## 🤖 Czat z AI

### Naturalna Konwersacja
System oferuje inteligentny czat z AI w języku polskim:
- **Kontekstowe odpowiedzi** - Pamięta historię rozmowy
- **Specjalizowane agenty** - Różne agenty dla różnych zadań
- **Zwięzłe odpowiedzi** - Tryb szybkiej komunikacji
- **Anty-halucynacja** - Weryfikacja informacji

### Typy Agentów
1. **General Agent** - Ogólne pytania i pomoc
2. **Receipt Agent** - Analiza paragonów
3. **Shopping Agent** - Zakupy i listy
4. **Recipe Agent** - Przepisy kulinarne
5. **Search Agent** - Wyszukiwanie informacji

### Przykłady Użycia
```
Użytkownik: "Co mogę ugotować z mlekiem i jajkami?"
AI: "Z mlekiem i jajkami możesz przygotować:
• Jajecznicę na mleku
• Omlet
• Pudding
• Krem do ciasta
• Sos beszamelowy

Który przepis Cię interesuje?"

Użytkownik: "Pokaż mi przepis na omlet"
AI: "Przepis na omlet:
Składniki:
• 2 jajka
• 50ml mleka
• Sól i pieprz
• Masło do smażenia

Przygotowanie:
1. Rozbij jajka do miseczki
2. Dodaj mleko i przyprawy
3. Rozgrzej patelnię z masłem
4. Wlej masę jajeczną
5. Smaż 2-3 minuty z każdej strony"
```

---

## 📊 Zarządzanie Zapasami

### Automatyczne Śledzenie
System automatycznie śledzi zapasy na podstawie paragonów:
- **Dodawanie produktów** - Z analizy paragonów
- **Śledzenie ilości** - Automatyczne odejmowanie
- **Daty ważności** - Predykcja na podstawie produktów
- **Alerty** - Powiadomienia o kończących się produktach

### Funkcje Zarządzania
- **Lista zakupów** - Automatyczne generowanie
- **Historia zakupów** - Analiza wzorców
- **Kategoryzacja** - Organizacja produktów
- **Statystyki** - Wydatki i trendy

### Przykład Zarządzania
```
📊 Aktualne zapasy:
• Mleko 3.2% 1L: 2 szt. (ważne do: 2025-01-20)
• Chleb: 1 szt. (ważny do: 2025-01-18)
• Jajka: 6 szt. (ważne do: 2025-01-25)

⚠️ Alerty:
• Chleb kończy się za 2 dni
• Mleko kończy się za 5 dni

🛒 Sugerowane zakupy:
• Chleb: 2 szt.
• Mleko: 2 szt.
```

---

## 🎯 Planowanie Posiłków

### Inteligentne Sugestie
System sugeruje posiłki na podstawie dostępnych składników:
- **Analiza zapasów** - Co masz w lodówce
- **Przepisy** - Dostosowane do składników
- **Planowanie** - Menu na cały tydzień
- **Lista zakupów** - Brakujące składniki

### Funkcje Planowania
- **Przepisy kulinarne** - Baza przepisów
- **Kalkulacja porcji** - Dostosowanie do liczby osób
- **Wartości odżywcze** - Informacje o kaloriach
- **Preferencje** - Diety i alergie

### Przykład Planowania
```
🎯 Plan posiłków na dziś:

Śniadanie:
• Omlet z warzywami (mleko, jajka, pomidory)
• Kawa z mlekiem

Obiad:
• Makaron z sosem pomidorowym (makaron, pomidory, cebula)
• Sałatka z ogórków (ogórki, cebula)

Kolacja:
• Kanapki z serem (chleb, ser, masło)

📝 Brakujące składniki:
• Pomidory: 4 szt.
• Makaron: 500g
• Ser: 200g
```

---

## 🔄 Koordynacja Darowizn

### Integracja z Organizacjami
System pomaga w koordynacji darowizn żywności:
- **Wykrywanie nadmiaru** - Produkty przed datą ważności
- **Organizacje charytatywne** - Lista lokalnych organizacji
- **Harmonogram odbioru** - Planowanie dostaw
- **Śledzenie darowizn** - Historia i statystyki

### Funkcje Darowizn
- **Automatyczne alerty** - Produkty do oddania
- **Kontakt z organizacjami** - Integracja z NGO
- **Optymalizacja tras** - Efektywne dostawy
- **Raporty** - Wpływ na środowisko

---

## 🔍 Monitorowanie Systemu

### Desktop Application
Aplikacja desktop FoodSave AI zawiera zaawansowane narzędzia do monitorowania systemu:

#### System Tray Integration
- **Ikona w system tray** - Szybki dostęp do funkcji
- **Menu kontekstowe** - Wszystkie opcje w jednym miejscu
- **Powiadomienia** - Status aplikacji w czasie rzeczywistym

#### Funkcje Monitorowania
- **📋 Logi** - Monitorowanie logów w czasie rzeczywistym
- **🐳 Kontenery** - Zarządzanie kontenerami Docker
- **📊 Status** - Sprawdzanie statusu aplikacji
- **🔍 Monitor Systemu** - Pełny panel monitorowania

### Monitorowanie Logów
System automatycznie monitoruje:
- **Logi Backend** - Serwer FastAPI
- **Logi Frontend** - Aplikacja React
- **Logi SQLite** - Baza danych
- **Logi Redis** - Cache
- **Logi Ollama** - Modele AI

**Funkcje:**
- Automatyczne odświeżanie co 2 sekundy
- Auto-scroll do najnowszych wpisów
- Możliwość czyszczenia logów
- Wyświetlanie w formacie monospace

### Zarządzanie Kontenerami
Panel zarządzania kontenerami Docker:
- **Tabela kontenerów** z informacjami o statusie
- **Uruchamianie/zatrzymywanie** wszystkich kontenerów
- **Restart serwisów** - Szybkie przywracanie działania
- **Monitorowanie portów** - Sprawdzanie dostępności

### Status Systemu
Monitorowanie w czasie rzeczywistym:
- **Status aplikacji** - Backend, Frontend, Baza danych
- **Zasoby systemu** - CPU, Pamięć, Dysk
- **Kontenery Docker** - Status i liczba aktywnych
- **Alerty** - Powiadomienia o problemach

### Przykład Użycia
```
🔍 Monitor Systemu - FoodSave AI

📋 Logi:
[2025-01-15 14:30:15] INFO: Backend started successfully
[2025-01-15 14:30:16] INFO: Database connection established
[2025-01-15 14:30:17] INFO: Frontend server running on port 3000

🐳 Kontenery:
✅ foodsave-backend    Up 2 hours   0.0.0.0:8000->8000/tcp
✅ foodsave-frontend   Up 2 hours   0.0.0.0:3000->3000/tcp
✅ foodsave-postgres   Up 2 hours   0.0.0.0:5432->5432/tcp

📊 Status:
✅ Backend: Działa
✅ Frontend: Działa
✅ Baza danych: 3 kontenery
CPU: 15.2%
Pamięć: 45.8% (2.3GB)
Dysk: 67.1% (120.5GB)
```

### Dostęp do Monitora
1. **Z System Tray** - Kliknij prawym na ikonę
2. **Menu kontekstowe** - Wybierz "Monitor Systemu"
3. **Szybkie opcje** - Logi, Kontenery, Status

### Integracja z Automatyzacją
Monitor systemu integruje się z:
- **Autostart** - Automatyczne uruchamianie z systemem
- **Skrypty deployment** - Sprawdzanie statusu po wdrożeniu
- **Monitoring zewnętrzny** - Eksport danych

---

## 📱 Aplikacja Desktop

### GUI Opcje

#### 🍽️ Uproszczony GUI (Nowy - Zalecany)
- **Chat-centric design** - Czat jako główny element
- **Agent selector** - Wybór agentów z dropdown
- **Quick actions** - Szybkie akcje dla typowych zadań
- **File upload** - Upload obrazów do analizy
- **Dark mode** - Przełączanie motywu
- **Responsive design** - Adaptacja do różnych rozmiarów

**Uruchomienie:**
```bash
./scripts/run_simplified_gui.sh
```

#### 🤖 Pełny GUI (Zaawansowany)
- **AI Command Center** - Zarządzanie 38 agentami
- **System monitoring** - Real-time monitoring
- **Multi-tab chat** - Wiele sesji czatu
- **Agent control panel** - Szczegółowe zarządzanie agentami

**Uruchomienie:**
```bash
./scripts/launch_scripts_gui.sh
```

### Natywna Aplikacja
System oferuje natywną aplikację desktop:
- **Tauri Framework** - Szybka i lekka aplikacja
- **Cross-platform** - Windows, macOS, Linux
- **Offline mode** - Działanie bez internetu
- **System notifications** - Powiadomienia systemowe

### Funkcje Aplikacji
- **Szybki dostęp** - Skróty klawiszowe
- **Drag & Drop** - Przeciąganie paragonów
- **System tray** - Działanie w tle
- **Auto-start** - Uruchamianie z systemem

### 🔍 System Tray Integration

#### Menu Kontekstowe
Aplikacja desktop oferuje zaawansowane menu w system tray:

```
🍎 FoodSave AI
├── 🌐 Panel Web
├── 🎨 Frontend
├── ──────────────────
├── ⚙️ Ustawienia
├── ℹ️ O programie
├── ──────────────────
├── 📊 Status
├── 🔍 Monitor Systemu
├── 📋 Logi
├── 🐳 Kontenery
├── ──────────────────
└── ❌ Wyjście
```

#### Funkcje Monitorowania
- **🔍 Monitor Systemu** - Pełny panel monitorowania z zakładkami
- **📋 Logi** - Szybki dostęp do monitorowania logów w czasie rzeczywistym
- **🐳 Kontenery** - Zarządzanie kontenerami Docker
- **📊 Status** - Sprawdzanie statusu aplikacji i zasobów

#### Automatyczne Uruchamianie
- **Autostart z systemem** - Opcja w ustawieniach
- **Systemd service** - Automatyczne zarządzanie
- **Desktop entry** - Integracja z menu aplikacji

### Integracja Systemowa
- **File associations** - Otwieranie plików
- **Context menu** - Menu kontekstowe
- **Print integration** - Drukowanie paragonów
- **Camera access** - Bezpośrednie skanowanie

### 🎯 Monitorowanie w Czasie Rzeczywistym

#### System Monitor Window
Zaawansowane okno monitorowania z trzema zakładkami:

**📋 Zakładka Logi:**
- Monitorowanie logów Backend, Frontend, PostgreSQL, Redis, Ollama
- Automatyczne odświeżanie co 2 sekundy
- Auto-scroll do najnowszych wpisów
- Możliwość czyszczenia logów

**🐳 Zakładka Kontenery:**
- Tabela z kontenerami Docker
- Status, porty, obrazy
- Przyciski: Uruchom wszystkie, Zatrzymaj wszystkie, Restart wszystkie
- Automatyczne odświeżanie co 5 sekund

**📊 Zakładka Status:**
- Status aplikacji (Backend, Frontend, Baza danych)
- Zasoby systemu (CPU, Pamięć, Dysk)
- Alerty i powiadomienia o problemach

#### Przykład Monitorowania
```
🔍 Monitor Systemu - FoodSave AI

📋 Logi:
[2025-01-15 14:30:15] INFO: Backend started successfully
[2025-01-15 14:30:16] INFO: Database connection established
[2025-01-15 14:30:17] INFO: Frontend server running on port 3000

🐳 Kontenery:
✅ foodsave-backend    Up 2 hours   0.0.0.0:8000->8000/tcp
✅ foodsave-frontend   Up 2 hours   0.0.0.0:3000->3000/tcp
✅ foodsave-postgres   Up 2 hours   0.0.0.0:5432->5432/tcp

📊 Status:
✅ Backend: Działa
✅ Frontend: Działa
✅ Baza danych: 3 kontenery
CPU: 15.2%
Pamięć: 45.8% (2.3GB)
Dysk: 67.1% (120.5GB)
```

### 🔧 Zarządzanie Systemem

#### Kontrolki i Akcje
- **🔄 Odśwież** - Odświeża wszystkie dane monitorowania
- **🗑️ Wyczyść logi** - Czyści pliki logów (z potwierdzeniem)
- **🔄 Restart serwisów** - Restartuje wszystkie kontenery Docker

#### Bezpieczeństwo
- **Potwierdzenia** dla destrukcyjnych operacji
- **Obsługa błędów** dla wszystkich operacji Docker
- **Timeout** dla requestów HTTP
- **Graceful handling** dla brakujących plików

### 📱 Dostępność i UX

#### Szybki Dostęp
1. **Kliknij prawym** na ikonę w system tray
2. **Wybierz opcję** z menu kontekstowego
3. **Monitoruj w czasie rzeczywistym** - automatyczne odświeżanie

#### Powiadomienia
- **Status aplikacji** - Powiadomienia o problemach
- **Alerty systemowe** - Wykorzystanie zasobów
- **Informacje o kontenerach** - Status Docker

#### Integracja z Automatyzacją
- **Autostart** - Automatyczne uruchamianie z systemem
- **Skrypty deployment** - Sprawdzanie statusu po wdrożeniu
- **Monitoring zewnętrzny** - Eksport danych do systemów monitorowania

---

## 🔍 Wyszukiwanie i Filtrowanie

### Zaawansowane Wyszukiwanie
System oferuje potężne narzędzia wyszukiwania:
- **Wyszukiwanie tekstowe** - W nazwach produktów
- **Filtry kategorii** - Według typów produktów
- **Filtry czasowe** - Według dat zakupów
- **Filtry cenowe** - Według przedziałów cenowych

### Funkcje Wyszukiwania
- **Fuzzy search** - Wyszukiwanie z błędami
- **Autocomplete** - Podpowiedzi podczas pisania
- **Saved searches** - Zapisywanie wyszukiwań
- **Export results** - Eksport wyników

### Przykład Wyszukiwania
```
🔍 Wyszukiwanie: "mleko"

Wyniki:
• Mleko 3.2% 1L - Biedronka (15.01.2025) - 4.99 zł
• Mleko 2% 1L - Lidl (12.01.2025) - 4.79 zł
• Mleko UHT 3.2% 1L - Carrefour (10.01.2025) - 5.29 zł

Filtry:
• Sklep: [Wszystkie] ▼
• Data: [Ostatni miesiąc] ▼
• Cena: [0-10 zł] ▼
• Kategoria: [Nabiał] ▼
```

---

## 🎮 Panel Sterowania

### Intuicyjny Interfejs
System oferuje panel sterowania dla wszystkich użytkowników:
- **Jednoklikowe operacje** - Łatwe zarządzanie
- **Status systemu** - Monitoring w czasie rzeczywistym
- **Logi systemu** - Szczegółowe informacje
- **Diagnostyka** - Automatyczne sprawdzanie

### Funkcje Panelu
```bash
./foodsave-all.sh

┌─────────────────────────────────────┐
│         FoodSave AI Panel           │
├─────────────────────────────────────┤
│ 1. 🚀 Uruchom system               │
│ 2. 🖥️ Aplikacja desktop (Tauri)    │
│ 3. 📊 Status systemu               │
│ 4. 📝 Logi systemu                 │
│ 5. 🛑 Zatrzymaj usługi             │
│ 6. 🔧 Diagnostyka                  │
│ 0. Wyjście                         │
└─────────────────────────────────────┘
```

---

## 🔗 Linki do Dokumentacji

### Szczegółowe Przewodniki
- [Szybki start](../QUICK_START.md) - Jak zacząć
- [Rozwiązywanie problemów](TROUBLESHOOTING.md) - Pomoc techniczna
- [Dokumentacja API](../core/API_REFERENCE.md) - Endpointy API
- [Przewodnik agentów](../reference/AGENTS_GUIDE.md) - Agenty AI

### Konfiguracja
- [Panel sterowania](../QUICK_START.md#-panel-sterowania) - Zarządzanie systemem
- [Monitoring](../guides/deployment/MONITORING.md) - Monitoring systemu
- [Backup](../operations/BACKUP_SYSTEM.md) - System backupów

---

## 📊 Statystyki Systemu

### Wydajność
- **Analiza paragonów**: 95% dokładność
- **Kategoryzacja produktów**: 90% dokładność
- **Czas odpowiedzi AI**: < 3 sekundy
- **Obsługa sklepów**: 40+ sieci handlowych

### Funkcje
- **Agenty AI**: 5 specjalistycznych agentów
- **Modele językowe**: Bielik 4.5b + 11b
- **Baza przepisów**: 1000+ przepisów
- **Kategorie produktów**: 35 kategorii FMCG

---

> **💡 Wskazówka:** System FoodSave AI jest zaprojektowany z myślą o łatwości użytkowania. Większość funkcji działa automatycznie - wystarczy przesłać paragon, a system zrobi resztę! 