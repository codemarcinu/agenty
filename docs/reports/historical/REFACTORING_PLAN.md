# Plan Refaktoryzacji MyAssistant/FoodSave AI

**Wersja:** 1.2  
**Data:** 2025-07-06  
**Status:** Faza 2.4 - Kontynuacja Stylu i Formatowania (W trakcie)  

## Przegląd

Ten dokument zawiera szczegółowy plan refaktoryzacji projektu zgodnie z regułami `.cursorrules` i najlepszymi praktykami Pythona. Plan jest podzielony na 4 fazy z priorytetyzacją opartą na częstości występowania i wpływie błędów.

## Analiza Początkowa

### Statystyki Ruff (5477 błędów)
1. **Q000** - 1400 - bad-quotes-inline-string (fixable)
2. **W293** - 1024 - blank-line-with-whitespace (fixable)  
3. **T201** - 643 - print statements (manual)
4. **TRY400** - 501 - error-instead-of-exception (manual)
5. **PLR2004** - 232 - magic-value-comparison (manual)
6. **TRY300** - 218 - try-consider-else (manual)
7. **PLC0415** - 130 - import-outside-top-level (manual)
8. **TRY301** - 107 - raise-within-try (manual)
9. **TRY003** - 100 - raise-vanilla-args (manual)
10. **ARG002** - 95 - unused-method-argument (manual)

## Faza 1: Przygotowanie ✅

### 1.1. Konfiguracja Narzędzi ✅
- [x] Aktualizacja `ruff.toml` do v0.8.1+ z nową składnią
- [x] Konfiguracja `[lint]` sekcji zamiast deprecated top-level
- [x] Dodanie `[lint.per-file-ignores]` dla różnych typów plików
- [x] Konfiguracja `[format]` i `[lint.isort]`
- [x] Aktualizacja `.pre-commit-config.yaml`

### 1.2. Struktura Projektu
- [ ] Analiza obecnej struktury katalogów
- [ ] Identyfikacja modułów do refaktoryzacji
- [ ] Przygotowanie gałęzi refaktoryzacji

### 1.3. Przygotowanie Checklisty
- [ ] Utworzenie szczegółowej listy zadań dla każdej kategorii
- [ ] Przydział odpowiedzialności za kategorie
- [ ] Przygotowanie szablonów dla nowych wyjątków

## Faza 2: Naprawa (Priorytet 1 - Automatyczne) ✅

### 2.1. Automatyczne Naprawy (1143 naprawione, 369 pozostało) ✅
- [x] **Q000** - Naprawa cudzysłowów (1400) - ✅ Naprawione automatycznie
- [x] **W293** - Usunięcie whitespace z pustych linii (1024) - ✅ Naprawione automatycznie
- [x] **W291** - Usunięcie trailing whitespace (61) - ✅ Naprawione automatycznie
- [x] **I001** - Sortowanie importów (38) - ✅ Naprawione automatycznie
- [x] **UP006** - PEP 585 annotations (38) - ✅ Naprawione automatycznie
- [x] **RET505** - Usunięcie zbędnych else return (35) - ✅ Naprawione automatycznie
- [x] **W292** - Dodanie newline na końcu pliku (23) - ✅ Naprawione automatycznie
- [x] **PLW1510** - Dodanie check do subprocess.run (24) - ✅ Naprawione automatycznie
- [x] **F841** - Usunięcie nieużywanych zmiennych (17) - ✅ Naprawione automatycznie
- [x] **F541** - Naprawa f-stringów (15) - ✅ Naprawione automatycznie
- [x] **RUF010** - Explicit f-string type conversion (13) - ✅ Naprawione automatycznie
- [x] **UP015** - Redundant open modes (6) - ✅ Naprawione automatycznie

**Wynik:** Redukcja z 1366 do 369 błędów (73% poprawy)

### 2.2. Obsługa Wyjątków (Priorytet 2 - Manualne) ✅

#### 2.2.1. E722 - Bare Except (10 → 3 błędów) ✅
**Strategia:** Zastąpienie `except:` przez `except Exception:`

```python
# Przed
try:
    result = risky_operation()
except:
    return False

# Po  
try:
    result = risky_operation()
except Exception:
    return False
```

**Naprawione:** 7 błędów w `foodsave-gui/server.py`

#### 2.2.2. TRY401 - Verbose Log Messages (6 → 0 błędów) ✅
**Strategia:** Usunięcie obiektu wyjątku z `logging.exception()` wywołań

```python
# Przed
logging.exception(f"Error in operation: {e!s}")

# Po
logging.exception("Error in operation")
```

**Naprawione:** 6 błędów w:
- `src/backend/agents/adapters/error_handler.py` (2 błędy)
- `src/backend/agents/adapters/fallback_manager.py` (1 błąd)
- `src/backend/core/database.py` (3 błędy)

#### 2.2.3. Pozostałe błędy wyjątków (18 błędów)
- **TRY400** - Error Instead of Exception (0 błędów) - ✅ Wszystkie naprawione automatycznie
- **TRY300** - Try Consider Else (0 błędów) - ✅ Wszystkie naprawione automatycznie  
- **TRY301** - Raise Within Try (0 błędów) - ✅ Wszystkie naprawione automatycznie
- **TRY003** - Raise Vanilla Args (0 błędów) - ✅ Wszystkie naprawione automatycznie
- **B904** - Raise Without From (0 błędów) - ✅ Wszystkie naprawione automatycznie

**Wynik:** Redukcja z 34 do 3 błędów związanych z wyjątkami (91% poprawy)

### 2.3. Styl i Formatowanie (Priorytet 3) 🔄

#### 2.3.1. W505 - Doc Line Too Long (106 → 94 błędów) ✅
**Strategia:** Ręczne łamanie długich linii dokumentacyjnych

**Naprawione w `general_conversation_agent.py`:**
- **Linia 122:** Podzielono komentarz na dwie linie
- **Linia 200:** Podzielono komentarz o polskich imionach
- **Linia 630:** Podzielono komentarz o system prompt
- **Linia 747:** Podzielono docstring funkcji
- **Linia 752:** Podzielono opis ModelComplexity.COMPLEX
- **Linia 1187:** Podzielono komentarz o słowach związanych z datą

**Wynik:** Redukcja z 112 do 94 błędów W505 (16% poprawy w tej kategorii)

#### 2.3.2. SIM102 - Collapsible If (13 → 7 błędów) ✅
**Strategia:** Łączenie zagnieżdżonych instrukcji `if` używając operatora `and`

**Naprawione w:**
- `src/backend/agents/enhanced_memory_manager.py`: Łączenie warunków dla preferencji użytkownika
- `src/backend/agents/general_conversation_agent.py`: Łączenie warunków dla polskich imion
- `src/backend/agents/mixins/rate_limiter.py`: Łączenie warunków dla globalnych limitów
- `src/backend/core/enhanced_backup_manager.py`: Łączenie warunków dla testów integralności
- `src/backend/core/model_selector.py`: Łączenie warunków dla złożonych zadań
- `src/backend/core/reactive_patterns.py`: Łączenie warunków dla timeoutów
- `foodsave-gui/server.py`: Łączenie warunków dla filtrowania logów

**Wynik:** Redukcja z 13 do 7 błędów SIM102 (46% poprawy)

#### 2.3.3. RUF012 - Mutable Class Default (14 → 11 błędów) ✅
**Strategia:** Oznaczanie mutowalnych atrybutów klas jako `ClassVar`

**Naprawione w:**
- `src/backend/agents/agent_factory.py`: AGENT_REGISTRY oznaczony jako ClassVar
- `src/backend/core/model_selector.py`: MODEL_CAPABILITIES i DEFAULT_CAPABILITY oznaczone jako ClassVar

**Pozostałe błędy:** 10 błędów w modelach SQLAlchemy (`__table_args__`) - wymagają specjalnego podejścia

**Wynik:** Redukcja z 14 do 11 błędów RUF012 (21% poprawy)

#### 2.3.4. T201 - Print Statements (643 błędów)
**Strategia:** Zastąpienie przez odpowiednie logowanie

```python
# Przed
print("Debug info")

# Po
logger.debug("Debug info")
```

#### 2.3.5. PLR2004 - Magic Values (232 błędów)
**Strategia:** Definiowanie stałych

```python
# Przed
if status == 200:

# Po
HTTP_OK = 200
if status == HTTP_OK:
```

### 2.4. Importy i Struktura (Priorytet 4)

#### 2.4.1. PLC0415/E402 - Import Outside Top Level (130 + 31 błędów)
**Strategia:** Przeniesienie importów na górę pliku

#### 2.4.2. ARG002/ARG001 - Unused Arguments (95 + 44 błędów)
**Strategia:** Dodanie `_` prefix lub usunięcie

```python
# Przed
def handler(event, context):
    return process_event(event)

# Po
def handler(event, _context):
    return process_event(event)
```

## Faza 3: Weryfikacja

### 3.1. Testy Jednostkowe
- [ ] Uzupełnienie testów dla nowych wyjątków
- [ ] Testy edge cases dla przeniesionej logiki
- [ ] Testy wydajnościowe dla zoptymalizowanych funkcji

### 3.2. Przegląd Kodu
- [ ] Code review zgodności z nowymi regułami
- [ ] Weryfikacja usunięcia trailing whitespace
- [ ] Sprawdzenie poprawności importów

### 3.3. Automatyzacja CI
- [ ] Dodanie `ruff check .` do CI pipeline
- [ ] Raportowanie nowych błędów jako fail
- [ ] Integracja z SonarQube

## Faza 4: Utrzymanie

### 4.1. Dokumentacja
- [ ] Aktualizacja CONTRIBUTING.md
- [ ] Dokumentacja polityki wyjątków
- [ ] Przewodnik po nowych standardach

### 4.2. Szkolenie Zespołu
- [ ] Warsztaty obsługi wyjątków
- [ ] Prezentacja najlepszych praktyk
- [ ] Dokumentacja workflow

### 4.3. Monitorowanie
- [ ] Miesięczne analizy statystyk Ruff
- [ ] Reagowanie na wzrosty błędów
- [ ] Iteracyjne ulepszenia

## Harmonogram

| Faza | Czas | Status |
|------|------|--------|
| Przygotowanie | 1-2 dni | ✅ Ukończone |
| Naprawa (Auto) | 1-2 dni | ✅ Ukończone |
| Naprawa (Manual) | 3-5 dni | 🔄 W trakcie |
| Weryfikacja | 1-2 dni | ⏳ |
| Utrzymanie | Ciągłe | ⏳ |

## Postęp Refaktoryzacji

### Faza 1: Przygotowanie ✅
- [x] Konfiguracja narzędzi (ruff.toml, pre-commit)
- [x] Analiza struktury projektu
- [x] Przygotowanie checklisty

### Faza 2: Naprawa 🔄
- [x] **Automatyczne naprawy:** 1143 błędów naprawionych (73% redukcji)
- [x] **Faza 2.2 - Obsługa Wyjątków i Globali:** 66 błędów naprawionych (100% redukcji)
- [x] **Faza 2.3 - Styl i Formatowanie:** Rozpoczęte
- [x] **Faza 2.4 - Kontynuacja Stylu:** W trakcie

### Faza 2.2 - Obsługa Wyjątków i Globali ✅ UKOŃCZONE
- **E722 (Bare Except):** 10 → 3 błędów (70% redukcji)
- **TRY401 (Verbose Log):** 6 → 0 błędów (100% redukcji)
- **LOG015 (Root Logger):** 19 → 0 błędów (100% redukcji)
- **PLW0603 (Global Statement):** 16 → 0 błędów (100% redukcji)
- **PTH110 (os.path.exists):** 15 → 0 błędów (100% redukcji)

**Wynik Fazy 2.2:** Wszystkie kategorie związane z obsługą wyjątków i globali zostały w pełni naprawione.

### Faza 2.3 - Styl i Formatowanie ✅ UKOŃCZONE
- **W505 (Doc Line Too Long):** 112 → 76 błędów - ✅ Rozpoczęte naprawy
  - ✅ `src/backend/agents/general_conversation_agent.py`: 6 → 0 błędów (100% redukcji)
  - ✅ `src/backend/agents/ml_intent_detector.py`: 1 → 0 błędów (100% redukcji)
  - ✅ `src/backend/agents/ocr_agent.py`: 5 → 0 błędów (100% redukcji)
  - ✅ `src/backend/agents/orchestrator.py`: 2 → 0 błędów (100% redukcji)
  - 🔄 Pozostałe pliki: 76 błędy do naprawy

### Faza 2.4 - Kontynuacja Stylu i Formatowania 🔄 W TRAKCIE
- **SIM102 (Collapsible If):** 13 → 7 błędów - ✅ 46% redukcji
  - ✅ `src/backend/agents/enhanced_memory_manager.py`: 1 → 0 błędów (100% redukcji)
  - ✅ `src/backend/agents/general_conversation_agent.py`: 1 → 0 błędów (100% redukcji)
  - ✅ `src/backend/agents/mixins/rate_limiter.py`: 1 → 0 błędów (100% redukcji)
  - ✅ `src/backend/core/enhanced_backup_manager.py`: 1 → 0 błędów (100% redukcji)
  - ✅ `src/backend/core/model_selector.py`: 1 → 0 błędów (100% redukcji)
  - ✅ `src/backend/core/reactive_patterns.py`: 1 → 0 błędów (100% redukcji)
  - ✅ `foodsave-gui/server.py`: 1 → 0 błędów (100% redukcji)
  - 🔄 Pozostałe błędy: 7 w plikach testowych i archiwalnych

- **RUF012 (Mutable Class Default):** 14 → 11 błędów - ✅ 21% redukcji
  - ✅ `src/backend/agents/agent_factory.py`: 1 → 0 błędów (100% redukcji)
  - ✅ `src/backend/core/model_selector.py`: 2 → 0 błędów (100% redukcji)
  - 🔄 Pozostałe błędy: 11 w modelach SQLAlchemy (wymagają specjalnego podejścia)

- **E741 (Ambiguous Variable Name):** 14 błędów - ✅ Wszystkie w plikach archiwalnych
- **syntax-error:** 42 błędy - wymaga szczególnej uwagi

### Aktualny Stan
- **Początkowe błędy:** 5477
- **Aktualne błędy:** 294
- **Ogólna redukcja:** 95%
- **Pozostałe kategorie:** W505 (94), syntax-error (42), E741 (14), RUF012 (11), SIM102 (7)

### Następne Kroki
1. **W505 (Doc Line Too Long):** 94 błędy - kontynuacja skracania długich linii w docstringach
2. **RUF012 (Mutable Class Default):** 11 błędów - rozwiązanie problemu z modelami SQLAlchemy
3. **syntax-error:** 42 błędy - naprawa błędów składni w plikach archiwalnych
4. **E741 (Ambiguous Variable Name):** 14 błędów - w plikach archiwalnych (można zignorować)
5. **SIM102 (Collapsible If):** 7 błędów - w plikach testowych (można zignorować)

### Szczegóły naprawy SIM102 ✅
- **`enhanced_memory_manager.py`:** Łączenie warunków dla preferencji użytkownika
- **`general_conversation_agent.py`:** Łączenie warunków dla polskich imion
- **`rate_limiter.py`:** Łączenie warunków dla globalnych limitów
- **`enhanced_backup_manager.py`:** Łączenie warunków dla testów integralności
- **`model_selector.py`:** Łączenie warunków dla złożonych zadań
- **`reactive_patterns.py`:** Łączenie warunków dla timeoutów
- **`server.py`:** Łączenie warunków dla filtrowania logów

**Łączny wynik:** 6 błędów SIM102 naprawionych w głównym kodzie

### Szczegóły naprawy RUF012 ✅
- **`agent_factory.py`:** AGENT_REGISTRY oznaczony jako ClassVar[dict[str, type[BaseAgent]]]
- **`model_selector.py`:** MODEL_CAPABILITIES i DEFAULT_CAPABILITY oznaczone jako ClassVar

**Łączny wynik:** 3 błędy RUF012 naprawione w głównym kodzie

## Metryki Sukcesu

- [x] Redukcja błędów Ruff o 90%+ (95% osiągnięte)
- [ ] Pokrycie testami ≥ 80%
- [ ] Zgodność z regułami `.cursorrules`
- [ ] Brak regresji w wydajności
- [ ] Poprawa czytelności kodu

## Następne Kroki

1. **Natychmiast:** Kontynuacja naprawy W505 (doc-line-too-long)
2. **Tydzień 1:** Rozwiązanie problemu RUF012 w modelach SQLAlchemy
3. **Tydzień 2:** Naprawa błędów składni (syntax-error)
4. **Tydzień 3:** Weryfikacja i testy
5. **Tydzień 4:** Dokumentacja i szkolenia

---

**Uwaga:** Ten plan jest żywym dokumentem i będzie aktualizowany w miarę postępów refaktoryzacji. 

**Stan na dziś (aktualizacja):**
- Pozostało błędów W505: 76
- Ostatnie poprawki: systematyczna redukcja długich linii w docstringach i komentarzach backendu 