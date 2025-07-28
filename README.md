# 🤖 Agenty Console App

**Inteligentny asystent do przetwarzania dokumentów i paragonów**

Agenty to przyjazna aplikacja konsolowa, która pomoże Ci automatycznie przetwarzać paragony, zarządzać dokumentami i rozmawiać z inteligentnym asystentem AI. Nie musisz być programistą, aby z niej korzystać!

## 🌟 Co wyróżnia Agenty?

**🚀 Proste w użyciu** - Intuicyjne menu, wszystko po polsku, bez skomplikowanych ustawień

**🤖 Inteligentny asystent** - Rozmawiaj naturalnie z AI, które pomoże Ci w każdej sytuacji  

**📄 Automatyczne OCR** - Wrzuć zdjęcie paragonu, a Agenty "przeczyta" co na nim jest

**📚 Baza wiedzy** - Dodaj swoje dokumenty i zadawaj pytania o ich zawartość

**💾 Eksport danych** - Zapisuj wyniki w Excel, CSV lub innych formatach

**🔄 Wszystko automatycznie** - Jedna komenda uruchamia cały system

## 🎯 Co potrafi Agenty?

### 📄 **Automatyczne przetwarzanie paragonów**
**Co to oznacza?** Agenty potrafi "przeczytać" twoje paragony ze zdjęć lub plików PDF i wyciągnąć z nich tekst.

**Jak to działa?**
- Wrzucasz zdjęcia paragonów do specjalnego folderu
- Agenty automatycznie rozpoznaje tekst (nawet z niewyraźnych zdjęć!)
- Poprawia jakość obrazu jeśli jest potrzebne
- Wyświetla ci cały tekst z paragonu

**Jakie pliki można przetwarzać?**
- Zdjęcia: JPG, PNG, BMP, TIFF
- Dokumenty: PDF

### 💬 **Rozmowa z inteligentnym asystentem**
**Co to oznacza?** Możesz rozmawiać z Agenty jak z prawdziwym asystentem - zadawać pytania i otrzymywać odpowiedzi.

**Przykłady rozmów:**
- "Jak przetworzyć wszystkie paragony naraz?"
- "Pokasz mi statystyki z tego miesiąca"
- "Eksportuj wyniki do Excel"
- "Pomóż mi z dodaniem dokumentów"

**Dodatkowe możliwości:**
- Asystent pamięta poprzednie rozmowy
- Podpowiada pytania na podstawie kontekstu
- Obsługuje polecenia głosowe w tekście

### 📚 **Inteligentna baza wiedzy**
**Co to oznacza?** Agenty może przechowywać twoje dokumenty i pomagać w szukaniu informacji.

**Jak to działa?**
- Dodajesz dokumenty (teksty, PDF-y) do folderu
- Agenty "czyta" i "rozumie" ich treść
- Możesz zadawać pytania o zawartość dokumentów
- System znajdzie odpowiednie fragmenty tekstu

**Przykładowe zastosowania:**
- Przechowywanie instrukcji i procedur
- Wyszukiwanie informacji w dokumentach firmowych
- Tworzenie bazy wiedzy z artykułów i poradników

### 📊 **Przegląd statystyk i wyników**
**Co to oznacza?** Agenty pokazuje ci podsumowania i statystyki swojej pracy.

**Co zobaczysz?**
- Ile paragonów zostało przetworzonych
- Które pliki miały problemy i dlaczego
- Jakie dokumenty są w bazie wiedzy
- Ogólny stan systemu

### 📤 **Eksport danych**
**Co to oznacza?** Możesz zapisać wyniki pracy Agenty w różnych formatach.

**Dostępne formaty:**
- Excel/CSV (do tabel i obliczeń)
- JSON (dla programistów)
- Zwykły tekst (do czytania)

**Co można eksportować:**
- Wyniki przetwarzania paragonów
- Rezultaty wyszukiwań w bazie wiedzy
- Statystyki i raporty

## 🧠 Jak to wszystko działa? (bez technikaliów)

**Wyobraź sobie Agenty jako inteligentnego asystenta, który składa się z kilku części:**

### 🖥️ **Interfejs (to co widzisz)**
- Proste menu z opcjami do wyboru
- Można kliknąć lub wpisać numer opcji
- Wszystko jest opisane po polsku
- Nie ma skomplikowanych ustawień

### 🤖 **Mózg AI (część inteligentna)**
- To tutaj dzieje się "myślenie"
- Rozpoznaje tekst na obrazach
- Rozumie pytania i udziela odpowiedzi
- Wyszukuje informacje w dokumentach
- Działa jak bardzo mądry asystent

### 📁 **Magazyn danych (gdzie wszystko jest przechowywane)**
- **Folder PARAGONY** - tutaj wrzucasz zdjęcia paragonów
- **Folder WIEDZA_RAG** - tutaj wrzucasz dokumenty do czytania
- **Folder exports** - tutaj znajdziesz wyeksportowane pliki
- Historia rozmów jest automatycznie zapisywana

### 🔄 **Połączenia między częściami**
Wszystkie części komunikują się ze sobą automatycznie. Ty tylko wybierasz co chcesz zrobić, a reszta dzieje się sama.

## 🚀 Jak zacząć? (krok po kroku)

### 📋 **Co będziesz potrzebować**
- Komputer z systemem Windows, Mac lub Linux
- Co najmniej 16GB pamięci RAM
- 50GB wolnego miejsca na dysku
- Połączenie z internetem (do pierwszej instalacji)

*Nie martw się - wszystko zostanie zainstalowane automatycznie!*

### 🎬 **Pierwsze uruchomienie**

**Krok 1: Pobranie Agenty**
```bash
# Skopiuj i wklej tę komendę do terminala
git clone https://github.com/codemarcinu/agenty.git
cd agenty
```

**Krok 2: Uruchomienie**
```bash
# Ta komenda uruchomi wszystko automatycznie
./start_console_app.sh
```

**Krok 3: Przygotowanie folderów**
Agenty automatycznie utworzy potrzebne foldery:
- `PARAGONY/` - wrzuć tutaj zdjęcia paragonów
- `WIEDZA_RAG/` - wrzuć tutaj dokumenty do czytania

**Krok 4: Pierwsze użycie**
1. Po uruchomieniu zobaczysz menu z opcjami
2. Wpisz numer opcji i naciśnij Enter
3. Postępuj zgodnie z wyświetlanymi instrukcjami

### 💡 **Pierwsze kroki - co warto zrobić**

**🔥 Szybkie sprawdzenie czy wszystko działa:**
1. Wrzuć jedno zdjęcie paragonu do folderu `PARAGONY/`
2. Wybierz opcję "1. Przetwarzanie paragonów"
3. Zobaczysz jak Agenty "czyta" twój paragon!

**💬 Sprawdź asystenta:**
1. Wybierz opcję "3. Chat z agentem AI"
2. Napisz: "Witaj! Jak mogę przetwarzać paragony?"
3. Asystent odpowie i podpowie co dalej

## 📁 Struktura katalogów

```
AGENTY/
├── PARAGONY/                    # Katalog z paragonami do przetworzenia
│   ├── paragon1.jpg
│   ├── paragon2.pdf
│   └── ...
├── WIEDZA_RAG/                  # Katalog z dokumentami do bazy wiedzy
│   ├── dokument1.txt
│   ├── dokument2.pdf
│   └── ...
├── agenty/                      # Kod źródłowy backendu
├── console_app/                 # Aplikacja konsolowa
├── docker-compose.console.yaml  # Konfiguracja Docker
├── Dockerfile.console          # Dockerfile dla aplikacji konsolowej
└── start_console_app.sh        # Skrypt uruchamiania
```

## 🎮 Jak korzystać z Agenty (przewodnik użytkownika)

### 📋 **Menu główne - twój panel sterowania**
```
🤖 Agenty Console App - Menu Główne
============================================================
[1] 📄 Przetwarzanie paragonów
[2] 📚 Zarządzanie bazą wiedzy RAG  
[3] 💬 Chat z agentem AI
[4] 📊 Statystyki
[5] 📤 Zarządzanie eksportami
[6] ❓ Pomoc
[7] 🚪 Wyjście
============================================================
```

**Jak używać menu:**
- Wpisz numer opcji (np. "1") i naciśnij Enter
- Zawsze możesz wrócić do menu głównego
- Jeśli się zgubisz, wybierz opcję "6" dla pomocy

### 📄 **Opcja 1: Przetwarzanie paragonów**

**Jak to działa krok po kroku:**

1. **Wrzuć paragony do folderu**
   - Otwórz folder `PARAGONY/` w swoim eksploratorze plików
   - Przeciągnij i upuść zdjęcia paragonów lub pliki PDF
   - Mogą to być zdjęcia z telefonu, skany lub pliki PDF

2. **Wybierz opcję 1 z menu**
   - Agenty automatycznie znajdzie wszystkie pliki
   - Pokaże ci ile plików znaleziono

3. **Wybierz sposób przetwarzania:**
   - **Opcja 1:** Przetwórz wszystkie naraz (szybko i wygodnie)
   - **Opcja 2:** Wybierz konkretny plik (jeśli chcesz sprawdzić tylko jeden)

4. **Obserwuj wyniki:**
   - Agenty pokaże ci postęp przetwarzania
   - Wyświetli tekst z każdego paragonu
   - Poinformuje o problemach (jeśli będą)

**Co zrobić jeśli coś nie działa:**
- Sprawdź czy zdjęcie jest wyraźne i czytelne
- Spróbuj z innym plikiem
- Użyj opcji "auto-enhancement" (włączona automatycznie)

### 📚 **Opcja 2: Zarządzanie bazą wiedzy**

**Do czego to służy:**
- Możesz "nauczyć" Agenty treści twoich dokumentów
- Później zadawać pytania o ich zawartość
- Wyszukiwać informacje bez czytania całych plików

**Jak dodać dokumenty:**

1. **Wrzuć dokumenty do folderu**
   - Otwórz folder `WIEDZA_RAG/`
   - Dodaj pliki tekstowe, PDF, Word lub inne dokumenty

2. **Wybierz opcję 2 → opcję 1**
   - Agenty automatycznie "przeczyta" wszystkie dokumenty
   - Podzieli je na mniejsze fragmenty dla lepszego wyszukiwania
   - Utworzy inteligentny indeks

3. **Wyszukaj informacje (opcja 2 → opcja 2)**
   - Wpisz pytanie, np. "Jakie są procedury bezpieczeństwa?"
   - Agenty znajdzie odpowiednie fragmenty z dokumentów
   - Pokaże ci najlepsze dopasowania

### 💬 **Opcja 3: Chat z agentem AI - twój inteligentny asystent**

**To jest najpotężniejsza funkcja Agenty!**

**Jak zacząć rozmowę:**
1. Wybierz opcję 3 z menu głównego
2. Zobaczysz ekran czatu z instrukcjami
3. Po prostu zacznij pisać i rozmawiać!

**Przykłady pytań które możesz zadać:**
- "Jak dodać nowe paragony do przetwarzania?"
- "Pokaż mi statystyki z ostatniego miesiąca"
- "Jak eksportować wyniki do Excel?"
- "Znajdź informacje o procedurach w moich dokumentach"
- "Pomóż mi zrozumieć jak działają eksporty"

**Specjalne komendy w chacie:**
- `help` - pokaże ci wszystkie dostępne komendy
- `history` - wyświetli historię waszej rozmowy
- `clear` - wyczyści historię (zacznie od nowa)
- `suggestions` - pokaże sugerowane pytania
- `exit` - wróci do menu głównego

**Dlaczego warto używać asystenta:**
- Pamięta waszą rozmowę (nie musisz powtarzać kontekstu)
- Podpowiada pytania na podstawie tego o czym rozmawiasz
- Może pomóc z każdą funkcją Agenty
- Mówi prostym językiem, bez technikaliów

### 📊 **Opcja 4: Statystyki - zobacz co się dzieje**

**Co zobaczysz:**
- Ile paragonów zostało przetworzonych (dzisiaj, w tym tygodniu, ogółem)
- Które pliki miały problemy i dlaczego
- Ile dokumentów jest w bazie wiedzy
- Ogólny stan systemu (czy wszystko działa)

**Kiedy warto sprawdzać statystyki:**
- Po przetworzeniu dużej ilości paragonów
- Gdy coś nie działa jak powinno
- Żeby zobaczyć postęp swojej pracy

### 📤 **Opcja 5: Zarządzanie eksportami**

**Do czego służy eksport:**
- Zapisanie wyników w formacie Excel/CSV (do analiz)
- Utworzenie kopii zapasowej danych
- Przesłanie wyników do innych programów

**Dostępne opcje:**
1. **Lista eksportów** - zobacz wszystkie zapisane pliki
2. **Eksport paragonów** - zapisz wyniki przetwarzania paragonów
3. **Eksport bazy wiedzy** - zapisz wyniki wyszukiwań
4. **Usuń eksport** - wyczyść niepotrzebne pliki

**Formaty eksportu:**
- **CSV/Excel** - najlepszy do tabel i obliczeń
- **JSON** - dla programistów lub zaawansowanych zastosowań
- **TXT** - zwykły tekst, łatwy do czytania

### ❓ **Opcja 6: Pomoc**

**Zawsze dostępna pomoc:**
- Szczegółowe instrukcje dla każdej funkcji
- Lista obsługiwanych formatów plików
- Wskazówki dotyczące rozwiązywania problemów
- Informacje kontaktowe

## ⚙️ Ustawienia i konfiguracja (dla zaawansowanych)

*Większość użytkowników nie musi nic zmieniać - wszystko działa automatycznie!*

### 📂 **Ważne lokalizacje**
- **Folder PARAGONY:** `/home/marcin/Dokumenty/PROJEKT/AGENTY/PARAGONY/`
- **Folder WIEDZA_RAG:** `/home/marcin/Dokumenty/PROJEKT/AGENTY/WIEDZA_RAG/`
- **Eksporty:** `/home/marcin/Dokumenty/PROJEKT/AGENTY/exports/`
- **Historia czatu:** `chat_history.json` (w folderze głównym)

### 🔧 **Podstawowe ustawienia (które możesz zmienić)**

**Język rozpoznawania tekstu:**
- Domyślnie: Polski
- Można zmienić na angielski lub inne języki

**Jakość przetwarzania:**
- Auto-enhancement: Włączony (poprawia jakość zdjęć)
- Timeout: 30 sekund na plik (można zwiększyć dla dużych plików)

**Rozmiar bazy wiedzy:**
- Maksymalny rozmiar fragmentu: 1000 znaków
- Dokładność wyszukiwania: 65% (wyżej = dokładniej, ale mniej wyników)

### 🌐 **Adresy usług (automatycznie konfigurowane)**
- Backend AI: `http://localhost:8000`
- Modele językowe: `http://localhost:11434`
- Cache: `http://localhost:6379`

*Jeśli używasz Agenty na innym komputerze w sieci, IT może zmienić te adresy.*

## 🔧 Informacje techniczne (dla IT)

*Ta sekcja jest przeznaczona dla administratorów systemów i osób technicznych.*

### 🐳 **Komponenty systemu**
Agenty składa się z kilku usług uruchamianych automatycznie:
- **Backend API** - serwis główny (port 8000)
- **Modele AI** - silnik sztucznej inteligencji (port 11434)  
- **Cache** - pamięć podręczna (port 6379)
- **Aplikacja konsolowa** - interfejs użytkownika

### 📊 **Monitoring stanu systemu**
```bash
# Sprawdzenie czy wszystko działa
curl http://localhost:8000/api/health

# Status wszystkich usług  
docker-compose -f docker-compose.console.yaml ps

# Logi w przypadku problemów
docker-compose -f docker-compose.console.yaml logs -f
```

### 🔄 **Restarty i utrzymanie**
```bash
# Restart całego systemu
docker-compose -f docker-compose.console.yaml restart

# Restart konkretnej usługi
docker-compose -f docker-compose.console.yaml restart agenty-backend

# Zatrzymanie systemu
docker-compose -f docker-compose.console.yaml down
```

## 🆘 Co robić gdy coś nie działa? (rozwiązywanie problemów)

### 🚫 **"Agenty nie uruchamia się"**

**Najczęstsze przyczyny:**
- Mało pamięci RAM (potrzeba minimum 16GB)
- Brak miejsca na dysku (potrzeba 50GB wolnego)
- Zablokowane porty przez inne programy

**Co sprawdzić:**
1. Czy masz dość pamięci: `htop` lub Menedżer zadań
2. Czy masz dość miejsca: `df -h` lub właściwości dysku
3. Uruchom ponownie komputer i spróbuj jeszcze raz

### 📄 **"Paragony nie są przetwarzane"**

**Możliwe przyczyny:**
- Zdjęcie jest niewyraźne lub za ciemne
- Plik ma nieprawidłowy format
- Paragon jest w języku obcym (ustawiony na polski)

**Co zrobić:**
1. Sprawdź czy zdjęcie jest czytelne dla oka
2. Spróbuj z innymi plikami
3. Użyj lepszego oświetlenia przy robieniu zdjęć
4. Skorzystaj z auto-enhancement (włączona automatycznie)

**Najlepsze praktyki fotografowania paragonów:**
- Dobre oświetlenie (ale bez odbłysków)
- Paragon ma być płaski (bez zagięć)
- Zdjęcie z góry, prostopadle
- Paragon ma wypełniać większość kadru

### 🤖 **"Asystent AI nie odpowiada"**

**Co sprawdzić:**
1. Czy masz połączenie z internetem
2. Poczekaj chwilę - AI czasem potrzebuje czasu na myślenie
3. Spróbuj zadać prostsze pytanie
4. Wyjdź z chatu i wejdź ponownie

**Przykłady dobrych pytań:**
- "Jak dodać nowe paragony?" ✅
- "Pokaż statystyki" ✅
- "Pomóż mi z eksportem" ✅

**Unikaj:**
- Bardzo długich pytań (ponad 500 słów)
- Pytań niezwiązanych z Agenty
- Wulgaryzmów lub nieodpowiednich treści

### 📚 **"Baza wiedzy nie znajduje informacji"**

**Najczęstsze przyczyny:**
- Dokumenty nie zostały jeszcze przetworzone
- Pytanie jest za bardzo szczegółowe
- Brak odpowiedniej treści w dokumentach

**Co zrobić:**
1. Upewnij się że dodałeś dokumenty do folderu `WIEDZA_RAG/`
2. Wybierz opcję "Dodaj dokumenty" i poczekaj na przetworzenie
3. Spróbuj innych słów kluczowych w pytaniu
4. Zadaj bardziej ogólne pytanie

### 💾 **"Eksport nie działa"**

**Sprawdź:**
- Czy masz uprawnienia do zapisu w folderze
- Czy nazwa pliku nie zawiera nieprawidłowych znaków
- Czy nie próbujesz eksportować pustych wyników

### 🔄 **"Wszystko działa wolno"**

**Możliwe przyczyny:**
- Za mało pamięci RAM
- Procesor jest przeciążony innymi programami
- Duże pliki (wielkie zdjęcia, długie dokumenty)

**Co pomaga:**
1. Zamknij inne programy
2. Użyj mniejszych plików
3. Przetwarzaj po kilka plików na raz zamiast wszystkich

### 🆘 **"Nic z powyższego nie pomaga"**

**Ostateczne rozwiązania:**
1. **Restart aplikacji:** Zamknij Agenty i uruchom ponownie
2. **Restart komputera:** Czasem to naprawia tajemnicze problemy
3. **Sprawdź logi:** Wybierz opcję "Pomoc" w menu - znajdziesz tam informacje techniczne
4. **Kontakt z pomocą:** Zobacz sekcję "Wsparcie" na końcu tego dokumentu

### 💡 **Jak uniknąć problemów**

**Dobre nawyki:**
- Regularnie restartuj Agenty po długiej sesji pracy
- Nie przetwarzaj więcej niż 50 plików naraz
- Rób kopie zapasowe ważnych wyników (eksportuj)
- Używaj zdjęć o rozsądnym rozmiarze (nie większe niż 10MB)
- Trzymaj foldery PARAGONY i WIEDZA_RAG uporządkowane

## 🚀 Planowane funkcje (co będzie w przyszłości)

### 🔮 **Wkrótce**
- **Obsługa wielu języków** - możliwość przełączania między polskim a angielskim
- **Eksport do Excel** - bezpośredni eksport do plików .xlsx
- **Historia operacji** - pełny dziennik wszystkich wykonanych akcji
- **Automatyczne kopie zapasowe** - regularne zapisywanie wyników

### 🌟 **W planach**
- **Aplikacja graficzna** - wersja z okienkami zamiast konsoli
- **Integracja z chmurą** - synchronizacja między urządzeniami
- **Rozpoznawanie głosu** - wydawanie poleceń głosowo
- **Integracja z kontami bankowymi** - automatyczne pobieranie transakcji
- **Analityka wydatków** - wykresy i raporty z paragonów

### 💭 **Pomysły na przyszłość**
- **Aplikacja mobilna** - Agenty na telefonie
- **Współpraca zespołowa** - dzielenie się bazą wiedzy w firmie
- **API dla programistów** - możliwość integracji z innymi systemami

*Masz pomysł na nową funkcję? Napisz do nas!*

## 🤝 Potrzebujesz pomocy lub masz sugestie?

### 📧 **Kontakt**
- **Email ogólny**: help@agenty.pl
- **Problemy techniczne**: support@agenty.pl
- **Sugestie funkcji**: ideas@agenty.pl

### 💬 **Społeczność**
- **Forum użytkowników**: [agenty.pl/forum](https://agenty.pl/forum)
- **GitHub Issues**: [Zgłoś problem](https://github.com/codemarcinu/agenty/issues)
- **GitHub Discussions**: [Dyskusje o funkcjach](https://github.com/codemarcinu/agenty/discussions)

### 📚 **Dodatkowe zasoby**
- **Video tutorial**: [YouTube - Jak używać Agenty](https://youtube.com/agenty-tutorial)
- **FAQ**: [Często zadawane pytania](https://agenty.pl/faq)
- **Webinary**: [Regularne szkolenia online](https://agenty.pl/webinars)

### 🐛 **Zgłaszanie problemów**
Gdy zgłaszasz problem, podaj:
1. **Co robiłeś** - jakie kroki wykonałeś
2. **Co się stało** - jaki był wynik
3. **Co się spodziewałeś** - jaki powinien być wynik
4. **Zrzut ekranu** - jeśli to możliwe
5. **Wersja systemu** - Windows/Mac/Linux

### 🌟 **Zostań częścią społeczności**
- **Beta tester** - testuj nowe funkcje przed innymi
- **Ambasador Agenty** - pomóż innym użytkownikom
- **Tłumacz** - pomóż w tłumaczeniu na inne języki

---

## ❤️ Podziękowania

**Agenty powstało dzięki:**
- Użytkownikom, którzy testowali i zgłaszali uwagi
- Społeczności open source za niesamowite narzędzia
- Wszystkim, którzy wierzą w moc AI do ułatwiania codziennej pracy

**Dziękujemy za wybór Agenty!**

---

*Ostatnia aktualizacja dokumentacji: 2025-01-28*  
*Wersja Agenty: 2.0.0 (z agentem chatowym)*

**Made with ❤️ and 🤖 AI by Agenty Team** 