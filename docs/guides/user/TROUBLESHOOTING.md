# 🔧 Przewodnik Rozwiązywania Problemów - FoodSave AI

> **Ostatnia aktualizacja:** 2025-07-18  
> **Status:** ✅ **AKTUALNY** - Wszystkie problemy z uwierzytelnianiem naprawione

## 📋 Spis Treści

- [🚀 Szybka Diagnostyka](#-szybka-diagnostyka)
- [🔐 Problemy z Uwierzytelnianiem](#-problemy-z-uwierzytelnianiem)
- [🌐 Problemy z Portami](#-problemy-z-portami)
- [🐳 Problemy z Docker](#-problemy-z-docker)
- [🗄️ Problemy z Bazą Danych](#️-problemy-z-bazą-danych)
- [🤖 Problemy z AI/Modelami](#-problemy-z-aimodelami)
- [📊 Problemy z Monitoringiem](#-problemy-z-monitoringiem)
- [🔍 Zaawansowane Debugowanie](#-zaawansowane-debugowanie)

---

## 🚀 Szybka Diagnostyka

### 1. Sprawdź Status Wszystkich Serwisów
```bash
# Sprawdź status kontenerów
docker compose ps

# Sprawdź health checks
curl http://localhost:8001/health
curl http://localhost:3000
```

### 2. Sprawdź Logi
```bash
# Wszystkie logi
docker compose logs

# Logi konkretnego serwisu
docker compose logs backend
docker compose logs frontend
# SQLite jest plikiem, nie ma logów kontenera
```

### 3. Uruchom Automatyczne Testy
```bash
# Test uwierzytelniania
./scripts/test_auth_automation.sh

# Pełne testy systemu
python3 FULL_SYSTEM_TEST.py
```

---

## 🔐 Problemy z Uwierzytelnianiem

### ✅ Status: NAPRAWIONE (2025-07-07)
Wszystkie problemy z async/greenlet zostały rozwiązane:
- Async session handling naprawione
- Eager loading dla user roles zaimplementowane
- Type conversion issues naprawione
- Database role assignments dodane

### Testowanie Uwierzytelniania

#### 1. Sprawdź Endpointy
```bash
# Test rejestracji
curl -X POST "http://localhost:8001/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "username": "testuser",
    "full_name": "Test User"
  }'

# Test logowania
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

#### 2. Sprawdź Token
```bash
# Zastąp YOUR_TOKEN otrzymanym tokenem
curl -X GET "http://localhost:8001/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Typowe Błędy i Rozwiązania

#### Błąd 500 - Internal Server Error
**Przyczyna:** Async context issues (NAPRAWIONE)
**Rozwiązanie:** Użyj najnowszej wersji kodu z eager loading

#### Błąd 401 - Unauthorized
**Przyczyna:** Nieprawidłowe dane logowania
**Rozwiązanie:** 
```bash
# Sprawdź czy użytkownik istnieje
curl -X POST "http://localhost:8001/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nowy@example.com",
    "password": "NoweHaslo123!",
    "username": "nowyuser",
    "full_name": "Nowy Użytkownik"
  }'
```

#### Błąd 400 - Bad Request
**Przyczyna:** Użytkownik już istnieje
**Rozwiązanie:** Użyj innego emaila lub zaloguj się z istniejącym kontem

---

## 🌐 Problemy z Portami

### Konfiguracja Portów
- **Backend**: 8001 (host) → 8000 (container)
- **Frontend**: 3000 (host) → 3000 (container)
- **Database**: lokalny plik
- **Redis**: 6379 (host) → 6379 (container)

### Sprawdzenie Dostępności Portów
```bash
# Sprawdź czy porty są otwarte
netstat -tulpn | grep :8001
netstat -tulpn | grep :3000
netstat -tulpn | grep :5433

# Test połączenia
curl http://localhost:8001/health
curl http://localhost:3000
```

### Konflikt Portów
**Problem:** Port już zajęty
**Rozwiązanie:**
```bash
# Znajdź proces używający port
lsof -i :8001
lsof -i :3000

# Zatrzymaj proces lub zmień port w docker-compose.yml
```

---

## 🐳 Problemy z Docker

### Sprawdzenie Środowiska Docker
```bash
# Sprawdź wersję Docker
docker --version
docker-compose --version

# Sprawdź status Docker daemon
sudo systemctl status docker

# Sprawdź dostępną pamięć
docker system df
```

### Problemy z Budowaniem
```bash
# Wyczyść cache Docker
docker system prune -a

# Przebuduj obrazy
docker compose build --no-cache

# Sprawdź logi budowania
docker compose build backend --progress=plain
```

### Problemy z Siecią
```bash
# Sprawdź sieci Docker
docker network ls

# Sprawdź połączenia sieciowe
docker network inspect aiasisstmarubo_default
```

### Problemy z Wolumenami
```bash
# Sprawdź wolumeny
docker volume ls

# Wyczyść wolumeny (UWAGA: usuwa dane)
docker compose down -v
```

---

## 🗄️ Problemy z Bazą Danych

### Sprawdzenie Połączenia z Bazą
```bash
# SQLite jest plikiem, nie ma połączenia do sprawdzenia
# Sprawdź czy plik bazy danych istnieje i jest dostępny
ls -l data/foodsave.db
```

### Problemy z Migracjami
```bash
# Migracje nie są wymagane dla SQLite, tabele są tworzone automatycznie
```

### Reset Bazy Danych
```bash
# UWAGA: Usuwa wszystkie dane
# Usuń plik bazy danych
rm data/foodsave.db
# Następnie uruchom aplikację, aby utworzyć nową bazę danych
```

---

## 🤖 Problemy z AI/Modelami

### Sprawdzenie Ollama
```bash
# Sprawdź status Ollama
curl http://localhost:11434/api/tags

# Sprawdź dostępne modele
docker compose exec ollama ollama list

# Pobierz modele
docker compose exec ollama ollama pull bielik-4.5b-v3.0
docker compose exec ollama ollama pull bielik-11b-v2.3
```

### Problemy z GPU
```bash
# Sprawdź GPU
nvidia-smi

# Sprawdź NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Problemy z Pamięcią
```bash
# Sprawdź użycie pamięci
free -h
docker stats

# Zatrzymaj niepotrzebne kontenery
docker container prune
```

---

## 📊 Problemy z Monitoringiem

### Sprawdzenie Prometheus
```bash
# Sprawdź status Prometheus
curl http://localhost:9090/-/healthy

# Sprawdź metryki
curl http://localhost:9090/api/v1/query?query=up
```

### Sprawdzenie Grafana
```bash
# Sprawdź status Grafana
curl http://localhost:3001/api/health

# Domyślne dane logowania: admin/admin
```

### Sprawdzenie Loki
```bash
# Sprawdź status Loki
curl http://localhost:3100/ready
```

---

## 🔍 Zaawansowane Debugowanie

### Debugowanie Backendu
```bash
# Sprawdź logi z debug info
docker compose logs backend --tail=100 -f

# Sprawdź zmienne środowiskowe
docker compose exec backend env

# Sprawdź procesy w kontenerze
docker compose exec backend ps aux
```

### Debugowanie Frontendu
```bash
# Sprawdź logi frontendu
docker compose logs frontend --tail=100 -f

# Sprawdź build frontendu
docker compose exec frontend npm run build
```

### Analiza Wydajności
```bash
# Sprawdź użycie zasobów
docker stats

# Sprawdź metryki systemu
htop
iotop
```

### Automatyczne Testy
```bash
# Uruchom pełne testy
./scripts/test_auth_automation.sh

# Testy jednostkowe
cd src && python -m pytest tests/ -v

# Testy integracyjne
python3 tests/integration/test_api_upload.py
```

---

## 📞 Wsparcie

### Gdzie Szukać Pomocy
1. **Logi systemu**: `docker compose logs`
2. **Status serwisów**: `docker compose ps`
3. **Testy automatyczne**: `./scripts/test_auth_automation.sh`
4. **Dokumentacja**: [docs/](TOC.md)
5. **GitHub Issues**: [Zgłoś problem](https://github.com/your-repo/issues)

### Przydatne Komendy
```bash
# Pełny restart systemu
docker compose down
docker compose up -d

# Sprawdź wszystkie endpointy
curl http://localhost:8001/health
curl http://localhost:3000
curl http://localhost:9090/-/healthy
curl http://localhost:3001/api/health

# Sprawdź połączenia sieciowe
docker compose exec backend ping postgres
docker compose exec backend ping redis
```

---

## 📈 Historia Napraw

### 2025-07-07 - Naprawy Uwierzytelniania
- ✅ Naprawione async/greenlet issues z SQLAlchemy
- ✅ Zaimplementowane eager loading dla user roles
- ✅ Naprawione problemy z konwersją typów user_id
- ✅ Dodane automatyczne przypisywanie ról użytkownikom
- ✅ Utworzony skrypt testowy `test_auth_automation.sh`

### 2025-07-06 - Optymalizacja Docker
- ✅ Zoptymalizowane Dockerfile z multi-stage builds
- ✅ Dodane health checks dla wszystkich serwisów
- ✅ Utworzony `.dockerignore` dla minimalnego build context
- ✅ Dodany skrypt `build-all-optimized.sh`

### 2025-07-05 - Inicjalizacja Projektu
- ✅ Podstawowa architektura FastAPI + React
- ✅ Integracja z Ollama i modelami Bielik
- ✅ System multi-agent z 38 wyspecjalizowanymi agentami
- ✅ Kompletny monitoring z Prometheus/Grafana/Loki 