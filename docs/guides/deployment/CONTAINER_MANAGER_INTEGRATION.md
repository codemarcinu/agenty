# 🔗 Integracja Container Manager z Systemem Uruchamiania FoodSave AI

## 📋 Przegląd

Container Manager został zintegrowany z nowym systemem uruchamiania FoodSave AI, zapewniając spójne zarządzanie całym systemem przez interfejs webowy.

## 🎯 Korzyści Integracji

- **Zunifikowane zarządzanie** - Wszystkie operacje przez jeden interfejs
- **Automatyczne zarządzanie portami** - Skrypty automatycznie zwalniają konfliktujące porty
- **Stabilna konfiguracja** - Zawsze te same porty dla wszystkich usług
- **Łatwe zarządzanie** - Jedna komenda do uruchomienia/zatrzymania całej aplikacji
- **Monitoring** - Status wszystkich usług w czasie rzeczywistym

## 🚀 Nowe Funkcje

### Zarządzanie Systemem FoodSave AI

Container Manager oferuje nowe funkcje do zarządzania całym systemem FoodSave AI:

#### 🎮 Przyciski w Interfejsie

- **Uruchom Cały System** - Uruchamia wszystkie usługi FoodSave AI
- **Zatrzymaj Cały System** - Zatrzymuje wszystkie usługi FoodSave AI
- **Restart Całego Systemu** - Restartuje wszystkie usługi FoodSave AI
- **Status Systemu** - Sprawdza status wszystkich usług
- **Sprawdź Porty** - Diagnostyka portów systemu FoodSave AI

#### 📊 Monitoring

- **Status Cards** - Szybki przegląd głównych serwisów
- **Tabela Kontenerów** - Szczegółowe informacje o wszystkich kontenerach
- **Zasoby Systemu** - Informacje o CPU, pamięci, dysku
- **Informacje Systemu** - Wersje Docker, liczba kontenerów

## 🔧 API Endpoints

### Zarządzanie Systemem FoodSave AI

Container Manager udostępnia nowe API endpointy:

```bash
# Uruchom cały system FoodSave AI
POST /api/v1/devops/foodsave/start

# Zatrzymaj cały system FoodSave AI
POST /api/v1/devops/foodsave/stop

# Restart całego systemu FoodSave AI
POST /api/v1/devops/foodsave/restart

# Sprawdź status systemu FoodSave AI
GET /api/v1/devops/foodsave/status

# Sprawdź porty systemu FoodSave AI
GET /api/v1/devops/foodsave/ports
```

### Przykłady Użycia

```bash
# Sprawdź status systemu
curl -s http://localhost:8080/api/v1/devops/foodsave/status | jq .

# Uruchom cały system
curl -X POST http://localhost:8080/api/v1/devops/foodsave/start

# Zatrzymaj cały system
curl -X POST http://localhost:8080/api/v1/devops/foodsave/stop

# Sprawdź porty
curl -s http://localhost:8080/api/v1/devops/foodsave/ports | jq .
```

## 🎮 Użytkowanie

### Główne Akcje

#### 🚀 Uruchomienie Systemu
1. Otwórz Container Manager: `http://localhost:8080`
2. Kliknij przycisk **"Uruchom Cały System"** w sekcji "System FoodSave AI"
3. Poczekaj na potwierdzenie (zielone powiadomienie)
4. Sprawdź status kontenerów w tabeli

#### 🛑 Zatrzymanie Systemu
1. Kliknij przycisk **"Zatrzymaj Cały System"** w sekcji "System FoodSave AI"
2. Potwierdź akcję w oknie dialogowym
3. Poczekaj na potwierdzenie zatrzymania

#### 🔄 Restart Systemu
1. Kliknij przycisk **"Restart Całego Systemu"** w sekcji "System FoodSave AI"
2. Potwierdź akcję w oknie dialogowym
3. Poczekaj na ponowne uruchomienie (2-3 minuty)

### Monitoring

#### 📊 Status Systemu
1. Kliknij przycisk **"Status Systemu"** w sekcji "System FoodSave AI"
2. Sprawdź status wszystkich usług w oknie modalnym
3. Sprawdź status portów systemowych

#### 🔍 Sprawdzanie Portów
1. Kliknij przycisk **"Sprawdź Porty"** w sekcji "System FoodSave AI"
2. Sprawdź status portów używanych przez system FoodSave AI
3. Zidentyfikuj konflikty portów

## 🔧 Konfiguracja

### Porty Systemowe

System FoodSave AI używa następujących portów:

| Usługa | Port | Opis |
|--------|------|------|
| **Backend (FastAPI)** | 8000 | Główny API serwer |
| **Frontend (Next.js)** | 3000 | Interfejs użytkownika |
| **Ollama (AI Models)** | 11434 | Modele AI |
| **Redis (Cache)** | 6379 | Cache i sesje |
| **Container Manager** | 8080 | Panel zarządzania |

### Automatyczne Zarządzanie Portami

Container Manager automatycznie:

1. **Sprawdza dostępność portów** przed uruchomieniem
2. **Zwalnia konfliktujące porty** jeśli są zajęte
3. **Uruchamia usługi** w odpowiedniej kolejności
4. **Czeka na uruchomienie** każdej usługi
5. **Sprawdza status** wszystkich usług

## 🛠️ Rozwiązywanie Problemów

### Problem: System nie uruchamia się

```bash
# Sprawdź status systemu
curl -s http://localhost:8080/api/v1/devops/foodsave/status

# Sprawdź porty
curl -s http://localhost:8080/api/v1/devops/foodsave/ports

# Sprawdź logi Container Manager
sudo journalctl -u foodsave-container-manager -f
```

### Problem: Porty są zajęte

```bash
# Sprawdź co używa portów
sudo lsof -i :8000
sudo lsof -i :3000
sudo lsof -i :11434
sudo lsof -i :6379

# Zatrzymaj procesy na portach
sudo kill -9 <PID>
```

### Problem: Container Manager nie odpowiada

```bash
# Sprawdź status Container Manager
sudo systemctl status foodsave-container-manager

# Restart Container Manager
sudo systemctl restart foodsave-container-manager

# Sprawdź logi
sudo journalctl -u foodsave-container-manager -f
```

## 📈 Monitoring i Diagnostyka

### Status Systemu

Container Manager sprawdza status:

- **Backend** - Czy odpowiada na `/health`
- **Frontend** - Czy odpowiada na główną stronę
- **Ollama** - Czy odpowiada na API
- **Redis** - Czy odpowiada na ping
- **Porty** - Czy są dostępne

### Logi i Diagnostyka

- **Logi systemu** - Dostępne przez przycisk "Pokaż Logi"
- **Logi kontenerów** - Dostępne przez przycisk "Logi" w tabeli
- **Logi w czasie rzeczywistym** - Dostępne przez przycisk "Logi Live"

## 🔒 Bezpieczeństwo

### Uwagi
- Container Manager wymaga uprawnień do Docker
- Operacje na systemie mogą wpływać na wszystkie usługi
- Zawsze potwierdzaj destrukcyjne operacje
- Regularnie sprawdzaj logi pod kątem błędów

### Rekomendacje
- Używaj Container Manager tylko w zaufanym środowisku
- Regularnie aktualizuj obrazy Docker
- Monitoruj zużycie zasobów systemu
- Twórz kopie zapasowe przed większymi operacjami

## 📊 Integracja z Istniejącymi Skryptami

Container Manager integruje się z istniejącymi skryptami:

- **`scripts/start-foodsave.sh`** - Uruchamianie całego systemu
- **`scripts/stop-foodsave.sh`** - Zatrzymywanie całego systemu
- **`scripts/main/foodsave-all.sh`** - Główny skrypt zarządzania
- **`scripts/main/docker-manager.sh`** - Zarządzanie kontenerami

### Automatyczne Zarządzanie

Container Manager automatycznie:

1. **Wykrywa skrypty** w katalogu `scripts/`
2. **Uruchamia skrypty** z odpowiednimi parametrami
3. **Sprawdza status** po wykonaniu operacji
4. **Wyświetla wyniki** w interfejsie użytkownika

## 🎉 Podsumowanie

Integracja Container Manager z systemem uruchamiania FoodSave AI zapewnia:

✅ **Zunifikowane zarządzanie** - Wszystkie operacje przez jeden interfejs  
✅ **Automatyczne zarządzanie portami** - Skrypty automatycznie zwalniają konfliktujące porty  
✅ **Stabilna konfiguracja** - Zawsze te same porty dla wszystkich usług  
✅ **Łatwe zarządzanie** - Jedna komenda do uruchomienia/zatrzymania całej aplikacji  
✅ **Monitoring** - Status wszystkich usług w czasie rzeczywistym  
✅ **Bezpieczeństwo** - Automatyczne czyszczenie procesów i portów  

### Dostępne Skrypty

- **`./scripts/start-foodsave.sh`** - Uruchom cały system
- **`./scripts/stop-foodsave.sh`** - Zatrzymaj cały system
- **`./container-manager-web/start.sh`** - Uruchom Container Manager
- **`./container-manager-web/stop.sh`** - Zatrzymaj Container Manager

### Dostępne Endpointy

- **`http://localhost:8080`** - Container Manager Web UI
- **`http://localhost:8000`** - Backend API
- **`http://localhost:3000`** - Frontend
- **`http://localhost:11434`** - Ollama API

---

**🎉 Integracja zakończona pomyślnie! Container Manager jest gotowy do zarządzania całym systemem FoodSave AI.** 