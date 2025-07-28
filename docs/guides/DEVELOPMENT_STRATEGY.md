# FoodSave AI - Strategia Development

## 🎯 Praktyczne Wskazówki dla Testowania

### Kiedy warto uruchamiać aplikację lokalnie?

- **Szybkość iteracji:** Lokalny start aplikacji jest dużo szybszy, bo nie musisz budować obrazu kontenera za każdym razem
- **Debugowanie:** Łatwiejszy dostęp do debuggerów, hot-reload i bezpośrednia edycja plików
- **Prostota:** Mniej narzutów konfiguracyjnych, zwłaszcza gdy masz już zainstalowane wymagane zależności systemowe
- **Optymalizacja czasu:** Nie trać czasu na budowanie kontenerów przy każdej zmianie

### Kiedy kontenery mają sens?

- **Spójność środowiska:** Kontener gwarantuje, że masz identyczne zależności i konfigurację jak na produkcji
- **Wielousługowość:** Gdy aplikacja wymaga kilku usług (baza danych, Redis, backend, frontend)
- **Testy integracyjne/CI:** Kontenery są idealne do automatycznych testów i pipeline'ów
- **Praca w zespole:** Uniknij efektu "u mnie działa"

## 🚀 Sposoby Uruchamiania

### 1. Lokalny Development (ZALECANE dla codziennej pracy)

```bash
# Uruchom pełną aplikację lokalnie (backend + frontend)
./scripts/development/start-local.sh

# Uruchom tylko backend lokalnie
./scripts/development/start-local.sh --backend-only

# Uruchom tylko frontend lokalnie
./scripts/development/start-local.sh --frontend-only

# Sprawdź status
./scripts/development/start-local.sh --status

# Zatrzymaj wszystkie procesy
./scripts/development/start-local.sh --stop
```

**Zalety:**
- ⚡ Szybki start (bez budowania kontenerów)
- 🔧 Łatwe debugowanie
- 🔄 Hot reload dla obu aplikacji
- 💾 Mniej zużycia zasobów

### 2. Testy Integracyjne (Kontenery)

```bash
# Podstawowe testy integracyjne
./scripts/development/start-integration-tests.sh --basic

# Testy z monitoringiem
./scripts/development/start-integration-tests.sh --with-monitoring

# Testy CI/CD
./scripts/development/start-integration-tests.sh --ci-cd

# Sprawdź status
./scripts/development/start-integration-tests.sh --status

# Zatrzymaj kontenery
./scripts/development/start-integration-tests.sh --stop
```

**Uwaga:** Używamy `docker compose` (v2) zamiast `docker-compose` (v1) dla lepszej kompatybilności.

**Zalety:**
- 🐳 Środowisko identyczne z produkcją
- 🔍 Pełne testy integracyjne
- 📊 Monitoring w czasie rzeczywistym
- 🧪 Automatyzacja testów

## 📊 Porównanie Podejść

| Aspekt | Lokalnie | Kontenery |
|--------|----------|-----------|
| **Czas startu** | ⚡ 10-30 sekund | 🐌 2-5 minut |
| **Hot reload** | ✅ Natychmiastowy | ✅ Z opóźnieniem |
| **Debugowanie** | ✅ Łatwe | ⚠️ Trudniejsze |
| **Zasoby** | 💚 Niskie | 🔴 Wysokie |
| **Spójność** | ⚠️ Zależy od systemu | ✅ Gwarantowana |
| **Zespół** | ❌ "U mnie działa" | ✅ Identyczne środowisko |

## 🎯 Rekomendacje dla Różnych Sytuacji

### Codzienny Development
```bash
# Uruchom lokalnie dla szybkiego developmentu
./scripts/development/start-local.sh
```

### Testy Integracyjne
```bash
# Uruchom w kontenerach dla pełnych testów
./scripts/development/start-integration-tests.sh --basic
```

### CI/CD Pipeline
```bash
# Uruchom testy CI/CD w kontenerach
./scripts/development/start-integration-tests.sh --ci-cd
```

### Debugowanie Problemów
```bash
# Lokalnie dla łatwego debugowania
./scripts/development/start-local.sh --backend-only
```

## 🔧 Optymalizacje

### Sposoby na przyspieszenie pracy z Dockerem

1. **Wykorzystuj cache Docker build:**
   ```bash
   # Użyj cache dla szybszego budowania
   docker-compose -f docker-compose.dev.yaml build --parallel
   ```

2. **Używaj bind mountów:**
   ```yaml
   # W docker-compose.dev.yaml
   volumes:
     - ./src:/app/src  # Hot reload dla kodu
   ```

3. **Buduj tylko wtedy, gdy musisz:**
   - Do codziennej pracy używaj lokalnego developmentu
   - Kontenery buduj tylko do testów integracyjnych

### Optymalizacja Cache

```yaml
# W docker-compose.dev.yaml
build:
  context: ./src/backend
  dockerfile: Dockerfile.dev
  cache_from:
    - foodsave-backend-dev:latest
```

**Uwaga:** Używamy `docker compose` (v2) zamiast `docker-compose` (v1) dla lepszej kompatybilności.

## 📱 Dostępne Endpointy

### Lokalny Development
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Testy Integracyjne (Kontenery)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **SQLite**: lokalny plik
- **Redis**: localhost:6379
- **Ollama**: http://localhost:11434

### Monitoring (z profilem monitoring)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Loki**: http://localhost:3100

## 🛠️ Troubleshooting

### Problem z portami
```bash
# Sprawdź zajęte porty
lsof -i :8000
lsof -i :3000

# Zatrzymaj procesy na portach
./scripts/development/start-local.sh --stop
```

### Problem z Docker
```bash
# Sprawdź status Docker
docker info
docker-compose --version

# Restart Docker daemon
sudo systemctl restart docker
```

### Problem z zależnościami
```bash
# Zainstaluj zależności lokalnie
cd frontend && npm install
cd ../src/backend && pip install -r requirements.txt
```

## 📈 Metryki Wydajności

### Czas Startu
- **Lokalnie**: 10-30 sekund
- **Kontenery**: 2-5 minut

### Zużycie Zasobów
- **Lokalnie**: ~500MB RAM, ~5% CPU
- **Kontenery**: ~2GB RAM, ~15% CPU

### Hot Reload
- **Lokalnie**: Natychmiastowy (< 1 sekunda)
- **Kontenery**: 2-5 sekund

## 🎯 Podsumowanie

| Sytuacja | Najlepsze podejście |
|----------|---------------------|
| **Szybkie testy, częste zmiany** | Lokalnie (`./scripts/development/start-local.sh`) |
| **Testy integracyjne/CI** | Kontenery (`./scripts/development/start-integration-tests.sh`) |
| **Praca w zespole** | Kontenery (by uniknąć "u mnie działa") |
| **Optymalizacja czasu** | Lokalnie + tylko kluczowe buildy kontenerów |

### Rekomendacja dla Twojego przypadku

**Podczas codziennego developmentu uruchamiaj aplikację lokalnie**, by nie tracić czasu na budowanie kontenerów. **Kontenery wykorzystuj do testów integracyjnych, CI/CD oraz do sprawdzenia**, czy środowisko produkcyjne nie różni się od developerskiego.

To podejście jest zgodne z praktykami branżowymi i pozwala zoptymalizować czas pracy bez utraty jakości. 