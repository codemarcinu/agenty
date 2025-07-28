# 🚀 FoodSave AI - Instrukcja Uruchomienia

## ✅ Status: WSZYSTKIE USŁUGI DZIAŁAJĄ

### 📊 Aktualny Status:
- ✅ **Backend (FastAPI)**: `http://localhost:8000` - DZIAŁA
- ✅ **Frontend (React)**: `http://localhost:3000` - DZIAŁA  
- ✅ **SQLite**: lokalny plik - DZIAŁA
- ✅ **Redis**: Port 6379 - DZIAŁA
- ✅ **Ollama**: Port 11434 - DZIAŁA (4 modele dostępne)

---

## 🎯 Szybkie Uruchomienie

### 1. Uruchomienie Backendu
```bash
# Opcja 1: Użyj skryptu (zalecane)
./start_backend.sh

# Opcja 2: Ręczne uruchomienie
export DATABASE_URL="sqlite+aiosqlite:///./foodsave.db"
export REDIS_URL="redis://localhost:6379"
python run_backend.py

# Opcja 3: Z pliku środowiskowego
source backend.env && python run_backend.py
```

### 2. Uruchomienie Frontendu
```bash
cd frontend
./start-dev.sh
```

### 3. Sprawdzenie Statusu
```bash
# Sprawdź backend
curl http://localhost:8000/health

# Sprawdź frontend
curl http://localhost:3000

# Sprawdź wszystkie usługi
docker ps
```

---

## 🔧 Konfiguracja

### Baza Danych (SQLite)
- **Plik**: foodsave.db

### Redis
- **Host**: localhost:6379
- **Status**: DZIAŁA

### Ollama (AI Models)
Dostępne modele:
- `llama3.2:3b` (3.2B parametrów)
- `SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0` (4.8B parametrów)
- `SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M` (11.2B parametrów)
- `nomic-embed-text:latest` (embedding model)

---

## 🌐 Dostęp do Aplikacji

### Frontend (Interfejs Użytkownika)
- **URL**: http://localhost:3000
- **Opis**: Główny interfejs aplikacji

### Backend (API)
- **URL**: http://localhost:8000
- **Dokumentacja API**: http://localhost:8000/docs
- **OpenAPI**: http://localhost:8000/openapi.json

### Dostępne Endpointy:
- `/api/agents/*` - Agenty AI
- `/api/chat/*` - Czat z AI
- `/api/pantry/*` - Zarządzanie zapasami
- `/api/v2/receipts/*` - Analiza paragonów
- `/api/v2/rag/*` - System RAG
- `/auth/*` - Autoryzacja
- `/monitoring/*` - Monitoring

---

## 🛠️ Rozwiązywanie Problemów

### Problem: "No module named 'backend'"
**Rozwiązanie**: Użyj `python run_backend.py` zamiast `uvicorn`

### Problem: "password authentication failed"
**Rozwiązanie**: Nie dotyczy SQLite

### Problem: Frontend nie łączy się z backendem
**Rozwiązanie**: Sprawdź `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8000
```

### Problem: Docker containers nie działają
**Rozwiązanie**:
```bash
# Sprawdź status
docker ps

# Uruchom ponownie
docker-compose up -d postgres redis ollama
```

---

## 📝 Przydatne Komendy

### Sprawdzenie Logów
```bash
# Backend logs
tail -f logs/backend/app.log

# Docker logs
docker logs foodsave-redis
docker logs foodsave-ollama-dev
```

### Restart Usług
```bash
# Restart backend
pkill -f "python run_backend.py"
./start_backend.sh

# Restart frontend
cd frontend && npm run dev

# Restart Docker services
docker-compose restart
```

### Testowanie API
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Cześć!", "user_id": "test"}'
```

---

## 🎉 Gratulacje!

Twoja aplikacja FoodSave AI jest teraz w pełni funkcjonalna! Możesz:

1. **Otworzyć frontend** w przeglądarce: http://localhost:3000
2. **Przetestować API** w dokumentacji: http://localhost:8000/docs
3. **Rozpocząć pracę** z funkcjami AI, zarządzaniem zapasami i analizą paragonów

---

## 📞 Wsparcie

Jeśli napotkasz problemy:
1. Sprawdź logi aplikacji
2. Upewnij się, że wszystkie usługi Docker działają
3. Sprawdź konfigurację środowiska
4. Skonsultuj dokumentację w katalogu `docs/`

**Powodzenia z FoodSave AI! 🚀** 