# 🚀 Przewodnik Uruchamiania FoodSave AI

## 📋 Przegląd

Ten przewodnik opisuje jak uruchomić całą aplikację FoodSave AI za pomocą zunifikowanych skryptów, które automatycznie zarządzają portami i usługami.

## 🎯 Korzyści

- **Automatyczne zarządzanie portami** - Skrypty automatycznie zwalniają konfliktujące porty
- **Stabilna konfiguracja** - Zawsze te same porty dla wszystkich usług
- **Łatwe zarządzanie** - Jedna komenda do uruchomienia/zatrzymania całej aplikacji
- **Monitoring** - Status wszystkich usług w czasie rzeczywistym
- **Bezpieczeństwo** - Automatyczne czyszczenie procesów i portów

## 🔧 Konfiguracja Portów

Aplikacja używa następujących portów:

| Usługa | Port | Opis |
|--------|------|------|
| **Backend (FastAPI)** | 8000 | Główny API serwer |
| **Frontend (Next.js)** | 3000 | Interfejs użytkownika |
| **Ollama** | 11434 | Serwer modeli AI |
| **Redis** | 6379 | Baza danych cache |

## 🚀 Uruchamianie

### Szybkie Uruchomienie

```bash
# Z głównego katalogu projektu
./scripts/start-foodsave.sh
```

### Szczegółowe Uruchomienie

```bash
# 1. Zatrzymaj wszystkie usługi (jeśli uruchomione)
./scripts/stop-foodsave.sh

# 2. Uruchom całą aplikację
./scripts/start-foodsave.sh

# 3. Sprawdź status
./scripts/start-foodsave.sh status
```

## 🛑 Zatrzymywanie

### Zatrzymanie Wszystkich Usług

```bash
./scripts/stop-foodsave.sh
```

### Restart Aplikacji

```bash
./scripts/start-foodsave.sh restart
```

## 📊 Monitoring

### Sprawdzenie Statusu

```bash
./scripts/start-foodsave.sh status
```

### Sprawdzenie Portów

```bash
# Sprawdź które porty są zajęte
lsof -i :8000 :3000 :11434 :6379

# Sprawdź procesy
ps aux | grep -E "(uvicorn|next|ollama|redis)" | grep -v grep
```

### Logi w Czasie Rzeczywistym

```bash
# Logi backendu
tail -f logs/backend.log

# Logi frontendu
tail -f logs/frontend.log

# Logi systemowe
journalctl -f
```

## 🔧 Rozwiązywanie Problemów

### Problem: Port Zajęty

```bash
# Sprawdź co używa portu
lsof -i :8000

# Zatrzymaj proces
kill -9 <PID>

# Lub użyj skryptu zatrzymania
./scripts/stop-foodsave.sh
```

### Problem: Backend Nie Odpowiada

```bash
# Sprawdź czy backend działa
curl http://localhost:8000/health

# Sprawdź logi
tail -f logs/backend.log

# Restart backendu
./scripts/start-foodsave.sh restart
```

### Problem: Frontend Nie Łączy się z Backendem

```bash
# Sprawdź CORS
curl -X OPTIONS http://localhost:8000/api/v1/upload \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Sprawdź konfigurację API
echo $NEXT_PUBLIC_API_URL
```

### Problem: Ollama Nie Działa

```bash
# Sprawdź status Ollama
curl http://localhost:11434/api/tags

# Uruchom Ollama ręcznie
ollama serve &

# Sprawdź modele
ollama list
```

## 🏗️ Architektura

### Struktura Procesów

```
FoodSave AI
├── Backend (FastAPI) - Port 8000
│   ├── API Endpoints
│   ├── Authentication
│   ├── Database
│   └── AI Agents
├── Frontend (Next.js) - Port 3000
│   ├── React Components
│   ├── API Integration
│   └── UI/UX
├── Ollama - Port 11434
│   ├── AI Models
│   └── Model Management
└── Redis - Port 6379
    ├── Cache
    └── Session Storage
```

### Komunikacja

```
Frontend (3000) ←→ Backend (8000)
Backend (8000) ←→ Ollama (11434)
Backend (8000) ←→ Redis (6379)
```

## 🔒 Bezpieczeństwo

### Ograniczenia Portów

- Backend: `0.0.0.0:8000` (dostępny z zewnątrz)
- Frontend: `localhost:3000` (tylko lokalnie)
- Ollama: `localhost:11434` (tylko lokalnie)
- Redis: `localhost:6379` (tylko lokalnie)

### Autoryzacja

- Endpoint `/api/v1/upload` jest wykluczony z autoryzacji
- Pozostałe endpointy wymagają JWT token
- CORS skonfigurowany dla `http://localhost:3000`

## 📝 Konfiguracja Środowiska

### Zmienne Środowiskowe

```bash
# Backend
export PYTHONPATH=/path/to/project
export DATABASE_URL=postgresql://user:pass@localhost:5432/foodsave
export REDIS_URL=redis://localhost:6379

# Frontend
export NEXT_PUBLIC_API_URL=http://localhost:8000
export NODE_ENV=development

# Ollama
export OLLAMA_HOST=localhost:11434
```

### Pliki Konfiguracyjne

```
foodsave-ai/
├── .env                    # Zmienne środowiskowe
├── modern-frontend/
│   ├── .env.local         # Frontend config
│   └── next.config.js     # Next.js config
└── src/backend/
    ├── config/
    │   └── settings.py    # Backend config
    └── auth/
        └── auth_middleware.py  # Auth config
```

## 🚀 Deployment

### Development

```bash
# Uruchom w trybie development
./scripts/start-foodsave.sh

# Dostępne usługi:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Ollama: http://localhost:11434
```

### Production

```bash
# Uruchom w trybie production
NODE_ENV=production ./scripts/start-foodsave.sh

# Lub użyj Docker
docker-compose up -d
```

## 📚 Dodatkowe Komendy

### Diagnostyka

```bash
# Sprawdź wszystkie porty
netstat -tulpn | grep -E ":(8000|3000|11434|6379)"

# Sprawdź procesy
ps aux | grep -E "(uvicorn|next|ollama|redis)"

# Sprawdź logi
tail -f logs/*.log
```

### Czyszczenie

```bash
# Zatrzymaj wszystkie usługi
./scripts/stop-foodsave.sh

# Wyczyść cache
rm -rf modern-frontend/.next
rm -rf logs/*.log

# Restart
./scripts/start-foodsave.sh
```

### Backup

```bash
# Backup danych
./scripts/backup-data.sh

# Restore danych
./scripts/restore-data.sh
```

## 🆘 Wsparcie

### Przydatne Komendy

```bash
# Pełny status
./scripts/start-foodsave.sh status

# Szczegółowe logi
tail -f logs/backend.log logs/frontend.log

# Sprawdź zdrowie usług
curl http://localhost:8000/health
curl http://localhost:3000
curl http://localhost:11434/api/tags
```

### Dokumentacja

- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000
- **Ollama:** http://localhost:11434

### Kontakt

W przypadku problemów:
1. Sprawdź logi: `tail -f logs/*.log`
2. Sprawdź status: `./scripts/start-foodsave.sh status`
3. Sprawdź porty: `lsof -i :8000 :3000 :11434 :6379`
4. Utwórz issue w repozytorium projektu

---

**🎉 FoodSave AI - Intelligent Food Management System** 