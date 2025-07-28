# 📜 Analiza i Plan Czyszczenia Skryptów FoodSave AI

**Data analizy:** 2025-07-19  
**Status:** Kompletna analiza wszystkich skryptów  
**Cel:** Archiwizacja niepotrzebnych skryptów i reorganizacja struktury  

---

## 🎯 Cele Czyszczenia

### ✅ 1. Identyfikacja Duplikatów
- [x] Znalezienie skryptów o tej samej nazwie
- [x] Analiza funkcjonalności duplikatów
- [x] Wybór najlepszej wersji do zachowania

### ✅ 2. Archiwizacja Przestarzałych Skryptów
- [x] Identyfikacja skryptów oznaczonych jako przestarzałe
- [x] Analiza skryptów nieużywanych
- [x] Przeniesienie do katalogu archive

### ✅ 3. Reorganizacja Struktury
- [x] Ujednolicenie katalogów
- [x] Standaryzacja nazewnictwa
- [x] Aktualizacja dokumentacji

---

## 📊 Analiza Skryptów

### 🔍 Znalezione Duplikaty

#### 1. **foodsave-all.sh**
- **Lokalizacje:**
  - `./scripts/main/foodsave-all.sh` ✅ **ZACHOWAĆ** (główny)
  - `./backups/documentation_update_20250713_190250/foodsave-all.sh` ❌ **ARCHIWIZOWAĆ**

#### 2. **health-check.sh**
- **Lokalizacje:**
  - `./scripts/utils/health-check.sh` ✅ **ZACHOWAĆ** (główny)
  - `./scripts/development/health-check.sh` ❌ **ARCHIWIZOWAĆ**

#### 3. **build-all-optimized.sh**
- **Lokalizacje:**
  - `./scripts/build-all-optimized.sh` ✅ **ZACHOWAĆ**
  - `./scripts/deployment/build-all-optimized.sh` ❌ **ARCHIWIZOWAĆ**

#### 4. **start.sh**
- **Lokalizacje:**
  - `./scripts/main/start.sh` ✅ **ZACHOWAĆ**
  - `./scripts/development/start.sh` ❌ **ARCHIWIZOWAĆ**

### 🗑️ Skrypty do Archiwizacji

#### 1. **Przestarzałe Skrypty**
- `scripts/install_missing_deps.sh` - Oznaczony jako przestarzały
- `scripts/start_ollama.sh` - Funkcjonalność wbudowana w główne skrypty
- `scripts/gui_refactor.sh` - Zastąpiony przez foodsave-all.sh

#### 2. **Duplikaty Funkcjonalności**
- `scripts/foodsave_manager_simple.sh` - Duplikat foodsave-all.sh
- `scripts/development/health-check.sh` - Duplikat utils/health-check.sh
- `scripts/development/start.sh` - Duplikat main/start.sh

#### 3. **Skrypty Testowe (do przeniesienia)**
- `scripts/test_*.py` - Przenieść do `tests/scripts/`
- `scripts/demo_*.py` - Przenieść do `examples/`

---

## 📁 Plan Reorganizacji

### 🏠 Główna Struktura (Zachować)

```
scripts/
├── main/                    # Główne skrypty zarządzania
│   ├── foodsave-all.sh     # Panel sterowania systemem
│   ├── foodsave.sh         # Podstawowy manager
│   ├── docker-manager.sh   # Zarządzanie Docker
│   └── manager.sh          # Zaawansowany manager
├── development/             # Skrypty deweloperskie
│   ├── dev-up.sh          # Uruchomienie środowiska dev
│   ├── dev-down.sh        # Zatrzymanie dev
│   └── cleanup.sh         # Czyszczenie systemu
├── deployment/             # Skrypty wdrażania
│   ├── build-all.sh       # Budowanie obrazów
│   └── deploy.sh          # Wdrażanie systemu
├── monitoring/             # Skrypty monitoringu
│   ├── health-check.sh    # Sprawdzanie zdrowia
│   ├── logs.sh           # Zarządzanie logami
│   └── backup.sh         # Backup systemu
├── utils/                 # Narzędzia pomocnicze
│   ├── health-check.sh   # Główny health check
│   └── check-ports.sh    # Sprawdzanie portów
└── archive/              # Zarchiwizowane skrypty
    ├── unused_scripts/   # Nieużywane skrypty
    └── deprecated/       # Przestarzałe skrypty
```

### 📦 Do Archiwizacji

#### 1. **Przestarzałe Skrypty**
```bash
# Przenieść do scripts/archive/deprecated/
scripts/install_missing_deps.sh
scripts/start_ollama.sh
scripts/gui_refactor.sh
scripts/foodsave_manager_simple.sh
```

#### 2. **Duplikaty**
```bash
# Przenieść do scripts/archive/unused_scripts/
scripts/development/health-check.sh
scripts/development/start.sh
backups/documentation_update_20250713_190250/foodsave-all.sh
```

#### 3. **Skrypty Testowe**
```bash
# Przenieść do tests/scripts/
scripts/test_*.py
scripts/demo_*.py
```

---

## 🔧 Plan Wykonania

### Faza 1: Archiwizacja (2025-07-19)

#### 1.1 Utworzenie Struktury Archiwum
```bash
mkdir -p scripts/archive/deprecated
mkdir -p scripts/archive/unused_scripts
mkdir -p tests/scripts
mkdir -p examples
```

#### 1.2 Przeniesienie Przestarzałych Skryptów
```bash
# Przestarzałe skrypty
mv scripts/install_missing_deps.sh scripts/archive/deprecated/
mv scripts/start_ollama.sh scripts/archive/deprecated/
mv scripts/gui_refactor.sh scripts/archive/deprecated/
mv scripts/foodsave_manager_simple.sh scripts/archive/deprecated/
```

#### 1.3 Przeniesienie Duplikatów
```bash
# Duplikaty
mv scripts/development/health-check.sh scripts/archive/unused_scripts/
mv scripts/development/start.sh scripts/archive/unused_scripts/
mv backups/documentation_update_20250713_190250/foodsave-all.sh scripts/archive/unused_scripts/
```

#### 1.4 Przeniesienie Skryptów Testowych
```bash
# Skrypty testowe
mv scripts/test_*.py tests/scripts/
mv scripts/demo_*.py examples/
```

### Faza 2: Reorganizacja (2025-07-19)

#### 2.1 Ujednolicenie Katalogów
```bash
# Przeniesienie skryptów do odpowiednich katalogów
mv scripts/check-ports.sh scripts/utils/
mv scripts/backup_cli.py scripts/monitoring/
mv scripts/rag_cli.py scripts/utils/
```

#### 2.2 Standaryzacja Nazewnictwa
```bash
# Zmiana nazw dla spójności
mv scripts/run_tests.sh scripts/development/test-runner.sh
mv scripts/debug.sh scripts/development/debug.sh
```

### Faza 3: Aktualizacja Dokumentacji (2025-07-19)

#### 3.1 Aktualizacja Linków
- Zaktualizować wszystkie linki w dokumentacji
- Sprawdzić poprawność ścieżek w skryptach
- Zaktualizować README.md

#### 3.2 Aktualizacja Przewodników
- Zaktualizować `docs/SCRIPTS_USER_GUIDE.md`
- Zaktualizować `docs/ALL_SCRIPTS_DOCUMENTATION.md`
- Dodać sekcję o zarchiwizowanych skryptach

---

## 📋 Lista Skryptów do Zachowania

### 🚀 Główne Skrypty (Zachować)
- `scripts/main/foodsave-all.sh` - **Główny panel sterowania**
- `scripts/main/foodsave.sh` - **Podstawowy manager**
- `scripts/main/docker-manager.sh` - **Zarządzanie Docker**
- `scripts/main/manager.sh` - **Zaawansowany manager**

### 🛠️ Development (Zachować)
- `scripts/development/dev-up.sh` - **Uruchomienie dev**
- `scripts/development/dev-down.sh` - **Zatrzymanie dev**
- `scripts/development/cleanup.sh` - **Czyszczenie**
- `scripts/development/health-check.sh` - **Health check dev**

### 🐳 Docker (Zachować)
- `scripts/deployment/build-all.sh` - **Budowanie obrazów**
- `scripts/deployment/deploy.sh` - **Wdrażanie**

### 📊 Monitoring (Zachować)
- `scripts/monitoring/health-check.sh` - **Główny health check**
- `scripts/monitoring/logs.sh` - **Zarządzanie logami**
- `scripts/monitoring/backup.sh` - **Backup systemu**

### 🔧 Utils (Zachować)
- `scripts/utils/health-check.sh` - **Główny health check**
- `scripts/utils/check-ports.sh` - **Sprawdzanie portów**

---

## 📦 Lista Skryptów do Archiwizacji

### 🗑️ Przestarzałe (Przenieść do archive/deprecated/)
- `scripts/install_missing_deps.sh` - Oznaczony jako przestarzały
- `scripts/start_ollama.sh` - Funkcjonalność wbudowana
- `scripts/gui_refactor.sh` - Zastąpiony przez foodsave-all.sh
- `scripts/foodsave_manager_simple.sh` - Duplikat funkcjonalności

### 🔄 Duplikaty (Przenieść do archive/unused_scripts/)
- `scripts/development/health-check.sh` - Duplikat utils/health-check.sh
- `scripts/development/start.sh` - Duplikat main/start.sh
- `backups/documentation_update_20250713_190250/foodsave-all.sh` - Stara wersja

### 🧪 Testowe (Przenieść do tests/scripts/)
- `scripts/test_*.py` - Skrypty testowe
- `scripts/demo_*.py` - Skrypty demonstracyjne

---

## 🔍 Kontrola Jakości

### ✅ Sprawdzenie Przed Archiwizacją
- [ ] Sprawdzenie czy skrypty nie są używane w innych miejscach
- [ ] Weryfikacja linków w dokumentacji
- [ ] Testowanie głównych skryptów po reorganizacji

### ✅ Sprawdzenie Po Archiwizacji
- [ ] Wszystkie główne skrypty działają poprawnie
- [ ] Dokumentacja jest aktualna
- [ ] Struktura jest spójna i logiczna

---

## 📞 Wsparcie

### 🆘 W przypadku problemów
1. **Sprawdź logi:** `tail -f logs/backend/server.log`
2. **Testuj skrypty:** `bash scripts/main/foodsave-all.sh --test`
3. **Przywróć z backupu:** `git checkout HEAD -- scripts/`

### 📚 Dokumentacja
- **Przewodnik skryptów:** `docs/SCRIPTS_USER_GUIDE.md`
- **Dokumentacja techniczna:** `docs/ALL_SCRIPTS_DOCUMENTATION.md`
- **Plan aktualizacji:** `docs/COMPREHENSIVE_DOCUMENTATION_PLAN.md`

---

> **💡 Wskazówka:** Po archiwizacji wszystkie główne skrypty będą w katalogu `scripts/main/` i będą miały spójną dokumentację.

> **📅 Ostatnia aktualizacja:** 2025-07-19 