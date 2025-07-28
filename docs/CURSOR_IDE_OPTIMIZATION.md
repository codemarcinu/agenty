# Cursor IDE Optimization Guide
## Rozwiązanie problemu "Window terminated unexpectedly"

### 🔍 **Diagnoza problemu**

Problem **"Window terminated unexpectedly (reason: 'killed', code: '61696')"** występuje gdy:
- Zbyt wiele procesów równocześnie
- Duży plik `.cursorrules` (8107 bajtów)
- Przeciążenie AI assistant w Cursor IDE

### ✅ **Zastosowane rozwiązania**

#### 1. **Optymalizacja .cursorrules**
- **Przed**: 8107 bajtów (215 linii)
- **Po**: 999 bajtów (45 linii)
- **Redukcja**: 88% mniejszy plik

```bash
# Przywróć oryginalny plik (jeśli potrzebny)
mv .cursorrules.backup .cursorrules

# Użyj zoptymalizowanej wersji
mv .cursorrules.optimized .cursorrules
```

#### 2. **Dodanie .cursorignore**
Wyklucza niepotrzebne pliki z kontekstu AI:
- `node_modules/`, `dist/`, `build/`
- `__pycache__/`, `*.pyc`
- `logs/`, `*.log`
- `temp_uploads/`, `backups/`
- `data/vector_store/` (duże pliki)

#### 3. **Zarządzanie procesami**
Zatrzymano **16 kontenerów Docker** + procesy lokalne:
- Backend (uvicorn) na porcie 8000
- Frontend (serve) na porcie 3000
- Celery workers (3 procesy)
- Monitoring stack (Grafana, Prometheus, etc.)

### 🚀 **Nowe narzędzia**

#### Skrypt zarządzania środowiskiem
```bash
# Sprawdź status
./scripts/development/dev-environment.sh status

# Uruchom tylko backend
./scripts/development/dev-environment.sh start backend

# Uruchom tylko frontend  
./scripts/development/dev-environment.sh start frontend

# Uruchom wszystko
./scripts/development/dev-environment.sh start all

# Zatrzymaj wszystko
./scripts/development/dev-environment.sh stop all
```

### 📊 **Wyniki optymalizacji**

| Metryka | Przed | Po | Zmiana |
|---------|-------|----|--------|
| **Pamięć RAM** | 6.8GB | 6.1GB | -0.7GB |
| **Plik .cursorrules** | 8107B | 999B | -88% |
| **Kontenery Docker** | 16 | 0 | -100% |
| **Procesy lokalne** | 8+ | 0 | -100% |

### 🛠️ **Workflow dla development**

#### Opcja A: Sekwencyjne uruchamianie
```bash
# 1. Uruchom tylko backend
./scripts/development/dev-environment.sh start backend

# 2. Pracuj z backendem w Cursor
# 3. Zatrzymaj backend
./scripts/development/dev-environment.sh stop backend

# 4. Uruchom tylko frontend
./scripts/development/dev-environment.sh start frontend

# 5. Pracuj z frontendem w Cursor
```

#### Opcja B: Minimalne środowisko
```bash
# Uruchom tylko niezbędne serwisy
docker run -d --name foodsave-postgres \
  -e POSTGRES_DB=foodsave \
  -p 5433:5432 \
  postgres:15-alpine

# Backend w trybie development
cd src && uvicorn backend.app_factory:app --port 8000 --reload
```

### 🔧 **Konfiguracja Cursor IDE**

#### Ustawienia AI (zalecane)
1. **Settings → AI → Disable real-time suggestions**
2. **Settings → AI → Reduce context window**
3. **Settings → AI → Limit concurrent requests**

#### Ustawienia wydajności
1. **Settings → Workbench → Limit memory usage**
2. **Settings → Extensions → Disable unused extensions**
3. **Settings → Files → Exclude patterns**:
   ```
   node_modules/**
   dist/**
   __pycache__/**
   *.log
   ```

### 🚨 **Zapobieganie problemom**

#### Monitorowanie zasobów
```bash
# Sprawdź pamięć przed uruchomieniem Cursor
free -h

# Sprawdź aktywne procesy
ps aux | grep -E "(cursor|node|python)" | head -10

# Sprawdź kontenery Docker
docker ps --format "table {{.Names}}\t{{.Status}}"
```

#### Czyszczenie cache
```bash
# Wyczyść cache Cursor
rm -rf ~/.cursor/logs/*
rm -rf ~/.cursor/CachedData/*

# Restart Cursor IDE
```

### 📋 **Checklista przed uruchomieniem Cursor**

- [ ] Sprawdź dostępną pamięć (`free -h`)
- [ ] Zatrzymaj niepotrzebne procesy
- [ ] Użyj zoptymalizowanego `.cursorrules`
- [ ] Sprawdź `.cursorignore`
- [ ] Uruchom tylko niezbędne serwisy
- [ ] Otwieraj pojedyncze pliki, nie cały projekt

### 🔄 **Przywracanie pełnego środowiska**

Jeśli potrzebujesz pełnego środowiska (wszystkie kontenery):

```bash
# Przywróć oryginalny .cursorrules
mv .cursorrules.backup .cursorrules

# Uruchom wszystkie kontenery
docker-compose up -d

# Sprawdź status
docker ps
```

### 📞 **Wsparcie**

Jeśli problem się powtórzy:
1. Sprawdź logi: `tail -f ~/.cursor/logs/*.log`
2. Restart systemu jeśli możliwe
3. Użyj VS Code jako alternatywy
4. Zgłoś problem w GitHub Issues

---

**Ostatnia aktualizacja**: 2025-01-07  
**Wersja**: 1.0  
**Autor**: AI Assistant 