# 📋 PRZEWODNIK MIGRACJI - REORGANIZACJA DOKUMENTACJI I SKRYPTÓW

## 🎯 CEL MIGRACJI

Niniejszy dokument opisuje zmiany wprowadzone podczas reorganizacji dokumentacji i skryptów w projekcie FoodSave AI / MyAppAssistant.

**Data migracji:** 2025-07-07  
**Wersja:** 1.0  
**Branch:** `reorganization-2025-07-07`

---

## 📁 ZMIANY W STRUKTURZE SKRYPTÓW

### 🔄 **STARA STRUKTURA → NOWA STRUKTURA**

#### **Główne skrypty:**
```
STARE LOKALIZACJE                    NOWE LOKALIZACJE
├── foodsave-manager.sh              ├── scripts/main/manager.sh
├── run-dev.sh                       ├── scripts/development/dev-start.sh
├── run_dev.sh                       └── [USUNIĘTY - duplikat]
├── build-all-containers.sh          ├── scripts/deployment/build-all-containers.sh
├── build-all-optimized.sh           ├── scripts/deployment/build-all-optimized.sh
└── scripts/foodsave-manager.sh      └── [USUNIĘTY - duplikat]
```

#### **Nowa organizacja katalogów:**
```
scripts/
├── main/                    # Skrypty główne
│   ├── start.sh            # Główny skrypt uruchamiania
│   ├── stop.sh             # Główny skrypt zatrzymywania
│   └── manager.sh          # Manager aplikacji
├── development/            # Skrypty deweloperskie
│   ├── dev-start.sh        # Uruchomienie dev
│   ├── start-dev.sh        # Alternatywny start dev
│   └── start_monitoring.sh # Monitoring dev
├── deployment/             # Skrypty deploymentu
│   ├── build-all-containers.sh
│   ├── build-all-optimized.sh
│   ├── docker-setup.sh
│   └── rebuild-with-models.sh
├── automation/             # Automatyzacja
│   ├── generate_toc.sh
│   ├── update_documentation.sh
│   └── validate-links.sh   # NOWY - walidacja linków
└── utils/                  # Narzędzia pomocnicze
    ├── setup_logging.sh
    └── setup_nvidia_docker.sh
```

### 🚀 **NOWE SKRYPTY GŁÓWNE**

#### **`scripts/main/start.sh`**
```bash
# Główny punkt wejścia do aplikacji
./scripts/main/start.sh dev      # Uruchom środowisko deweloperskie
./scripts/main/start.sh prod     # Uruchom środowisko produkcyjne
./scripts/main/start.sh test     # Uruchom środowisko testowe
./scripts/main/start.sh stop     # Zatrzymaj wszystkie serwisy
./scripts/main/start.sh status   # Pokaż status serwisów
```

#### **`scripts/main/stop.sh`**
```bash
# Zatrzymanie wszystkich serwisów
./scripts/main/stop.sh
```

---

## 📚 ZMIANY W STRUKTURZE DOKUMENTACJI

### 🔄 **STARA STRUKTURA → NOWA STRUKTURA**

#### **Dokumentacja architektury:**
```
STARE LOKALIZACJE                    NOWE LOKALIZACJE
├── docs/architecture/               ├── docs/core/architecture/
│   ├── ASYNC_IMPLEMENTATION_SUMMARY.md
│   ├── GPU_SETUP.md
│   ├── MULTI_AGENT_OPTIMIZATION_PLAN.md
│   ├── OPTIMIZATION_IMPLEMENTATION.md
│   └── QUICK_START_OPTIMIZATION.md
├── docs/FRONTEND_ARCHITECTURE.md    ├── docs/core/architecture/FRONTEND_ARCHITECTURE.md
└── docs/INFORMATION_ARCHITECTURE.md └── docs/core/architecture/INFORMATION_ARCHITECTURE.md
```

#### **Nowa organizacja katalogów:**
```
docs/
├── core/                    # Dokumentacja rdzenia
│   ├── architecture/        # Architektura systemu
│   ├── api/                # Dokumentacja API
│   └── technology/         # Stack technologiczny
├── guides/                 # Przewodniki
│   ├── development/        # Rozwój
│   ├── deployment/         # Wdrażanie
│   ├── user/              # Użytkownik
│   └── troubleshooting/   # Rozwiązywanie problemów
├── reference/             # Referencje
│   ├── agents/            # Agenty AI
│   ├── database/          # Baza danych (SQLite)
│   └── integrations/      # Integracje
├── operations/            # Operacje
│   ├── security/          # Bezpieczeństwo
│   ├── monitoring/        # Monitoring
│   └── maintenance/       # Konserwacja
└── archive/               # Archiwum (przestarzałe)
```

---

## 🛠️ MAPOWANIE STARYCH → NOWYCH LOKALIZACJI

### 📋 **SKRYPTY**

| Stara lokalizacja | Nowa lokalizacja | Status |
|------------------|------------------|---------|
| `foodsave-manager.sh` | `scripts/main/manager.sh` | ✅ Przeniesiony |
| `run-dev.sh` | `scripts/development/dev-start.sh` | ✅ Przeniesiony |
| `run_dev.sh` | - | ❌ Usunięty (duplikat) |
| `build-all-containers.sh` | `scripts/deployment/build-all-containers.sh` | ✅ Przeniesiony |
| `build-all-optimized.sh` | `scripts/deployment/build-all-optimized.sh` | ✅ Przeniesiony |
| `scripts/foodsave-manager.sh` | - | ❌ Usunięty (duplikat) |

### 📚 **DOKUMENTACJA**

| Stara lokalizacja | Nowa lokalizacja | Status |
|------------------|------------------|---------|
| `docs/architecture/*` | `docs/core/architecture/*` | ✅ Przeniesiony |
| `docs/FRONTEND_ARCHITECTURE.md` | `docs/core/architecture/FRONTEND_ARCHITECTURE.md` | ✅ Przeniesiony |
| `docs/INFORMATION_ARCHITECTURE.md` | `docs/core/architecture/INFORMATION_ARCHITECTURE.md` | ✅ Przeniesiony |

---

## 🔧 INSTRUKCJE MIGRACJI

### 🚀 **DLA DEWELOPERÓW**

#### **1. Aktualizacja skryptów uruchamiania**
```bash
# STARE:
./run-dev.sh
./foodsave-manager.sh start dev

# NOWE:
./scripts/main/start.sh dev
./scripts/main/manager.sh start dev
```

#### **2. Aktualizacja CI/CD**
```bash
# Zaktualizuj ścieżki w plikach CI/CD:
- .github/workflows/*.yml
- docker-compose*.yaml
- Makefile (jeśli istnieje)
```

#### **3. Aktualizacja dokumentacji**
```bash
# Zaktualizuj linki w dokumentacji:
- README.md
- docs/TOC.md
- Wszystkie pliki .md z linkami do skryptów
```

### 📚 **DLA UŻYTKOWNIKÓW**

#### **1. Nowe komendy uruchamiania**
```bash
# Uruchomienie środowiska deweloperskiego
./scripts/main/start.sh dev

# Uruchomienie środowiska produkcyjnego
./scripts/main/start.sh prod

# Zatrzymanie wszystkich serwisów
./scripts/main/start.sh stop

# Sprawdzenie statusu
./scripts/main/start.sh status
```

#### **2. Dostęp do dokumentacji**
```bash
# Główna dokumentacja architektury
docs/core/architecture/

# Przewodniki
docs/guides/

# Referencje
docs/reference/
```

---

## 🔍 NOWE NARZĘDZIA

### 📊 **Walidacja linków**
```bash
# Sprawdzenie wszystkich linków w dokumentacji
./scripts/automation/validate-links.sh

# Generowanie szczegółowego raportu
./scripts/automation/validate-links.sh --report
```

### 📋 **Automatyzacja dokumentacji**
```bash
# Generowanie spisu treści
./scripts/automation/generate_toc.sh

# Aktualizacja dokumentacji
./scripts/automation/update_documentation.sh
```

---

## ⚠️ ZNANE PROBLEMY I ROZWIĄZANIA

### 🔗 **Uszkodzone linki**
- **Problem:** Niektóre linki w dokumentacji mogą wskazywać na stare lokalizacje
- **Rozwiązanie:** Uruchom `./scripts/automation/validate-links.sh` aby zidentyfikować problemy

### 🔄 **Skrypty zewnętrzne**
- **Problem:** Skrypty w innych katalogach mogą nadal odwoływać się do starych lokalizacji
- **Rozwiązanie:** Przeszukaj projekt za pomocą `grep -r "stara-sciezka" .`

### 📝 **Dokumentacja zewnętrzna**
- **Problem:** Dokumentacja poza projektem może zawierać nieaktualne linki
- **Rozwiązanie:** Zaktualizuj dokumentację w repozytoriach zewnętrznych

---

## 🚀 PLAN ROLLBACK

### 🔄 **Przywrócenie poprzedniej wersji**
```bash
# Przełącz na poprzedni branch
git checkout feature/tauri-implementation

# Lub przywróć konkretne pliki
git checkout feature/tauri-implementation -- stara-sciezka
```

### 📋 **Lista plików do przywrócenia**
- `run_dev.sh` (jeśli potrzebny)
- `scripts/foodsave-manager.sh` (jeśli potrzebny)
- Stara struktura katalogów `docs/architecture/`

---

## 📊 METRYKI SUKCESU

### ✅ **ZREALIZOWANE CELES**
- **Redukcja skryptów:** 64 → 58 (-9.4%)
- **Standaryzacja nazewnictwa:** 100%
- **Konsolidacja dokumentacji:** 8 dokumentów architektury → 1 katalog
- **Nowe narzędzia:** Walidacja linków, automatyzacja

### 📈 **OCZEKIWANE KORZYŚCI**
- **Łatwiejsze zarządzanie:** Spójna struktura katalogów
- **Lepsza dokumentacja:** Centralizacja dokumentów architektury
- **Automatyzacja:** Walidacja linków i generowanie dokumentacji
- **Standaryzacja:** Spójne nazewnictwo i organizacja

---

## 📞 WSPARCIE

### 🆘 **W przypadku problemów**
1. Sprawdź sekcję "Znane problemy i rozwiązania"
2. Uruchom walidację linków: `./scripts/automation/validate-links.sh`
3. Sprawdź logi w katalogu `logs/`
4. Skontaktuj się z zespołem deweloperskim

### 📧 **Kontakt**
- **Branch:** `reorganization-2025-07-07`
- **Data migracji:** 2025-07-07
- **Wersja:** 1.0

---

**Status migracji:** ✅ Zakończona  
**Następny krok:** Testowanie nowej struktury w środowisku deweloperskim 