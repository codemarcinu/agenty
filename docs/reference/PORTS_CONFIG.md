# 🔧 KONFIGURACJA PORTÓW - REZERWACJA NA SZTYWNO

## 📋 Przydzielone Porty

### 🎯 **Główne Aplikacje**
| Usługa | Port Host | Port Container | Status | Opis |
|--------|-----------|----------------|--------|------|
| **Backend (FastAPI)** | `8000` | `8000` | 🔒 ZAREZERWOWANY | Główny serwer API |
| **Frontend (Vite/React)** | `3000` | `3000` | 🔒 ZAREZERWOWANY | Interfejs użytkownika |
| **GUI (PyQt5)** | `8000` | `8000` | 🔒 ZAREZERWOWANY | Desktop application |

### 🗄️ **Bazy Danych**
| Usługa | Port Host | Port Container | Status | Opis |
|--------|-----------|----------------|--------|------|
| **SQLite** | `lokalny plik` | `lokalny plik` | 🔒 ZAREZERWOWANY | Główna baza danych |
| **Redis** | `6379` | `6379` | 🔒 ZAREZERWOWANY | Cache i sesje |

### 🤖 **AI & Monitoring**
| Usługa | Port Host | Port Container | Status | Opis |
|--------|-----------|----------------|--------|------|
| **Ollama** | `11434` | `11434` | 🔒 ZAREZERWOWANY | Modele AI |
| **Grafana** | `3001` | `3000` | 🔒 ZAREZERWOWANY | Monitoring dashboard |
| **Prometheus** | `9090` | `9090` | 🔒 ZAREZERWOWANY | Metryki |
| **Loki** | `3100` | `3100` | 🔒 ZAREZERWOWANY | Logi |

### 🧪 **Testy**
| Usługa | Port Host | Port Container | Status | Opis |
|--------|-----------|----------------|--------|------|
| **SQLite Test** | `lokalny plik` | `lokalny plik` | 🔒 ZAREZERWOWANY | Testowa baza danych |
| **Redis Test** | `6380` | `6379` | 🔒 ZAREZERWOWANY | Testowy cache |
| **Ollama Test** | `11435` | `11434` | 🔒 ZAREZERWOWANY | Testowe modele AI |
| **Backend Test** | `8001` | `8001` | 🔒 ZAREZERWOWANY | Testowy backend |

## 🐳 **KONFIGURACJA DOCKER**

### **Mapowanie Portów w Kontenerach**
```yaml
# docker-compose.yml
services:
  postgres:
    ports:
      - "5433:5432"  # Host:Container
  redis:
    ports:
      - "6379:6379"  # Host:Container
  backend:
    ports:
      - "8000:8000"  # Host:Container
  frontend:
    ports:
      - "3000:3000"  # Host:Container
  ollama:
    ports:
      - "11434:11434"  # Host:Container
```

### **Różne Środowiska**
| Środowisko | Backend Port | Frontend Port | Database (SQLite) |
|------------|--------------|---------------|---------------|
| **Development** | `8000` | `3000` | `lokalny plik` |
| **Production** | `8000` | `3000` | `lokalny plik` |
| **Testing** | `8001` | `3001` | `lokalny plik` |
| **Monitoring** | `8000` | `3000` | `5433` |

## 🔧 **SKRYPTY ZARZĄDZANIA**

### **Sprawdzanie Portów (Lokalne + Kontenery)**
```bash
./scripts/check-ports.sh
```

### **Zwalnianie Portów (Lokalne + Kontenery)**
```bash
./scripts/free-ports.sh
```

### **Sprawdzanie Kontenerów**
```bash
./scripts/check-containers.sh
```

## 🚨 **KONFLIKTY PORTÓW**

### **Typowe Konflikty**
1. **Port 8000**: Backend lokalny vs Backend kontener
2. **Port 3000**: Frontend lokalny vs Frontend kontener
3. **Port 5433**: PostgreSQL lokalny vs PostgreSQL kontener

### **Rozwiązania**
1. **Użyj różnych portów dla lokalnych i kontenerowych usług**
2. **Zatrzymaj lokalne usługi przed uruchomieniem kontenerów**
3. **Użyj skryptów zarządzania portami**

## 📊 **MONITORING PORTÓW**

### **Automatyczne Sprawdzanie**
- Sprawdzanie przed uruchomieniem aplikacji
- Wykrywanie konfliktów portów
- Automatyczne zwalnianie zajętych portów

### **Logi Portów**
- Rejestrowanie użycia portów
- Śledzenie konfliktów
- Raporty dostępności

## 🔒 **BEZPIECZEŃSTWO**

### **Ograniczenia Dostępu**
- Porty dostępne tylko lokalnie (127.0.0.1)
- Firewall dla portów produkcyjnych
- Szyfrowanie komunikacji

### **Audyt Portów**
- Regularne sprawdzanie otwartych portów
- Wykrywanie nieautoryzowanych usług
- Raporty bezpieczeństwa

## 📝 **INSTRUKCJE UŻYTKOWANIA**

### **Uruchomienie z Rezerwacją Portów**
```bash
# 1. Sprawdź dostępność portów
./scripts/check-ports.sh

# 2. Zwalnij zajęte porty (jeśli potrzebne)
./scripts/free-ports.sh

# 3. Uruchom aplikację
./scripts/start-all.sh
```

### **Sprawdzanie Statusu**
```bash
# Sprawdź wszystkie porty
./scripts/check-ports.sh

# Sprawdź kontenery
docker ps

# Sprawdź logi
docker logs <container-name>
```

## 🛠️ **TROUBLESHOOTING**

### **Port Zajęty**
```bash
# Znajdź proces używający portu
lsof -i :8000

# Zatrzymaj proces
kill -9 <PID>

# Lub użyj skryptu
./scripts/free-ports.sh
```

### **Kontener Nie Uruchamia Się**
```bash
# Sprawdź logi kontenera
docker logs <container-name>

# Sprawdź konflikty portów
./scripts/check-ports.sh

# Restartuj kontenery
docker compose down && docker compose up -d
```

## 📈 **MONITORING I ALERTY**

### **Automatyczne Alerty**
- Powiadomienia o zajętych portach
- Alerty o nieudanych uruchomieniach
- Raporty wydajności

### **Metryki**
- Czas odpowiedzi usług
- Użycie zasobów
- Liczba połączeń

---

**Ostatnia aktualizacja**: 2025-01-07
**Wersja**: 2.0 (z obsługą kontenerów) 