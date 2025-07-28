# 🐳 Docker Setup Guide - Option 3: Pełny Stack

Przewodnik uruchomienia pełnego stacku Docker z integracją mini aplikacji konsolowych.

## 🎯 Cel: Uruchomienie Option 3

```
Mini Aplikacje (host) → Backend Container → Ollama Container → Modele AI
```

---

## 📋 Krok 1: Sprawdzenie Środowiska

```bash
# Sprawdź Docker
docker --version
docker-compose --version

# Sprawdź dostępne zasoby
docker system df
docker system info | grep -E "(Total Memory|CPUs)"
```

**Minimalne wymagania:**
- Docker Desktop aktywny
- 16GB+ RAM dostępne
- 50GB+ wolnego miejsca (modele AI są duże)

---

## 🔧 Krok 2: Przygotowanie Konfiguracji

### A) Sprawdź obecną konfigurację:
```bash
cd /home/marcin/Dokumenty/PROJEKT/my_assistant

# Sprawdź docker-compose
ls -la config/docker/
cat config/docker/docker-compose.optimized.yaml | grep -A5 -B5 "OLLAMA_URL"
```

### B) Problem: Konflikt konfiguracji
```yaml
# W docker-compose.optimized.yaml (kontenery):
- OLLAMA_URL=http://ollama:11434     # ← Service name dla kontenerów

# W src/backend/settings.py (mini aplikacje):
OLLAMA_URL = "http://localhost:11434"  # ← Localhost dla hosta
```

### C) Rozwiązanie: Port forwarding
Ollama container musi być dostępny z hosta na `localhost:11434`

---

## 🚀 Krok 3: Uruchomienie Stack

```bash
cd /home/marcin/Dokumenty/PROJEKT/my_assistant

# Uruchom pełny stack
docker-compose -f config/docker/docker-compose.optimized.yaml up -d

# Sprawdź status
docker-compose -f config/docker/docker-compose.optimized.yaml ps
```

**Oczekiwany output:**
```
NAME                STATUS              PORTS
foodsave-backend    Up 2 minutes        0.0.0.0:8000->8000/tcp
foodsave-ollama     Up 2 minutes        0.0.0.0:11434->11434/tcp  ← Ważne!
foodsave-redis      Up 2 minutes        0.0.0.0:6379->6379/tcp
```

---

## 🔍 Krok 4: Weryfikacja Połączeń

### A) Test Ollama z hosta:
```bash
# Test podstawowy
curl http://localhost:11434/api/version

# Powinno zwrócić:
# {"version":"0.1.x"}
```

### B) Sprawdź dostępne modele:
```bash
# Lista modeli w kontenerze
docker exec foodsave-ollama ollama list

# Jeśli puste, załaduj modele
docker exec foodsave-ollama ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M
docker exec foodsave-ollama ollama pull llama3.2:3b
```

### C) Test modelu:
```bash
# Test inferecji z hosta
curl http://localhost:11434/api/generate -d '{
  "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
  "prompt": "Napisz krótkie podsumowanie sztucznej inteligencji",
  "stream": false
}' | jq .response
```

---

## 🎮 Krok 5: Uruchomienie Mini Aplikacji

```bash
# Powróć do głównego katalogu
cd /home/marcin/Dokumenty/PROJEKT/my_assistant

# Uruchom menedżer konsoli
python console_manager.py

# W menu wybierz:
# Opcja 11: Diagnostyka systemu (sprawdzi połączenia)
```

**Oczekiwany rezultat diagnostyki:**
```
🩺 DIAGNOSTYKA SYSTEMU
=====================
🔍 Sprawdzam dostępność skryptów...
✅ Gmail Inbox Zero Agent Test: OK
✅ General Chat & Search Agent Test: OK
✅ Anti-Hallucination System Test: OK

🔍 Sprawdzam zależności Python...
✅ asyncio: Asynchroniczne operacje
✅ json: Obsługa JSON
✅ logging: System logowania

🔍 Sprawdzam system plików...
✅ Uprawnienia zapisu: OK

📊 PODSUMOWANIE DIAGNOSTYKI:
✅ System gotowy do pracy - nie znaleziono problemów
```

---

## 🧪 Krok 6: Test Pełnej Integracji

### A) Test Gmail Inbox Zero:
```bash
# W console_manager.py wybierz opcję 1
# Następnie opcja 1: Analizuj przykładowy email
# Wybierz typ 1: Email biznesowy
```

**Oczekiwany output:**
```
🤔 Przetwarzam pytanie: [email content]

✅ Odpowiedź agenta:
Status: Sukces
Czas przetwarzania: 2.34s
Tekst: Analiza emaila zakończona. Priorytet: high
Sugerowane labele: ['Praca', 'Ważne']
Powinno być zarchiwizowane: false
Wymaga odpowiedzi: true
Priorytet: high
Pewność: 0.85
```

### B) Test General Chat:
```bash
# W console_manager.py wybierz opcję 2
# Następnie opcja 1: Zadaj pytanie ogólne
# Wpisz: "Co to jest sztuczna inteligencja?"
```

**Oczekiwany output:**
```
🤔 Przetwarzam pytanie: Co to jest sztuczna inteligencja?

✅ Odpowiedź agenta:
Status: Sukces
Czas przetwarzania: 3.12s
Tekst: [Szczegółowa odpowiedź o AI wygenerowana przez Bielik-11B]
Pewność: 0.92
Model użyty: SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M
```

---

## 🔧 Rozwiązywanie Problemów

### Problem 1: Ollama nie odpowiada
```bash
# Sprawdź logi
docker logs foodsave-ollama

# Sprawdź czy port jest otwarty
netstat -tlnp | grep 11434

# Restart Ollama
docker restart foodsave-ollama
```

### Problem 2: Model nie znaleziony
```bash
# Sprawdź modele w kontenerze
docker exec foodsave-ollama ollama list

# Załaduj model
docker exec foodsave-ollama ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M

# Sprawdź rozmiar modelu (może być duży!)
docker exec foodsave-ollama du -sh /root/.ollama/models/
```

### Problem 3: Backend nie łączy się z Ollama
```bash
# Sprawdź logi backendu
docker logs foodsave-backend | grep -i ollama

# Sprawdź sieć Docker
docker network inspect foodsave_foodsave-network

# Test połączenia z backend do ollama
docker exec foodsave-backend curl http://ollama:11434/api/version
```

### Problem 4: Import errors w mini aplikacjach
```bash
# Sprawdź czy jesteś w głównym katalogu
pwd
# Powinno być: /home/marcin/Dokumenty/PROJEKT/my_assistant

# Sprawdź strukturę
ls -la src/backend/agents/

# Sprawdź Python path
python -c "import sys; print('\n'.join(sys.path))"
```

---

## 📊 Monitoring Stack

### Sprawdź zasoby:
```bash
# CPU i RAM wszystkich kontenerów
docker stats

# Szczegóły konkretnego kontenera
docker stats foodsave-ollama --no-stream

# Logs w czasie rzeczywistym
docker logs -f foodsave-backend
```

### Health checks:
```bash
# Status wszystkich serwisów
docker-compose -f config/docker/docker-compose.optimized.yaml ps

# Health check konkretnego serwisu
docker inspect foodsave-ollama | jq '.[].State.Health'
```

---

## 🎯 Optymalizacja Wydajności

### Dla RTX 3060:
```yaml
# W docker-compose.optimized.yaml już skonfigurowane:
environment:
  - OLLAMA_GPU_LAYERS=43          # Użyj GPU
  - OLLAMA_NUM_PARALLEL=4         # 4 równoległe requesty
  - OLLAMA_MAX_LOADED_MODELS=3    # Max 3 modele w pamięci
  - OLLAMA_FLASH_ATTENTION=1      # Flash attention
  - OLLAMA_GPU_MEMORY_UTILIZATION=0.85  # 85% VRAM
```

### Monitorowanie GPU:
```bash
# Sprawdź użycie GPU
nvidia-smi

# W kontenerze Ollama
docker exec foodsave-ollama nvidia-smi
```

---

## 🔄 Kompletny Workflow

### 1. Start Stack:
```bash
cd /home/marcin/Dokumenty/PROJEKT/my_assistant
docker-compose -f config/docker/docker-compose.optimized.yaml up -d
```

### 2. Załaduj Modele:
```bash
docker exec foodsave-ollama ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M
docker exec foodsave-ollama ollama pull llama3.2:3b
```

### 3. Sprawdź Status:
```bash
docker-compose -f config/docker/docker-compose.optimized.yaml ps
curl http://localhost:11434/api/version
curl http://localhost:8000/health
```

### 4. Uruchom Mini Aplikacje:
```bash
python console_manager.py
```

### 5. Test Funkcjonalności:
- Gmail Inbox Zero (opcja 1)
- General Chat (opcja 2)  
- Anti-Hallucination (opcja 3)

### 6. Stop Stack (gdy skończysz):
```bash
docker-compose -f config/docker/docker-compose.optimized.yaml down
```

---

## 🎉 Sukces!

Po wykonaniu tych kroków będziesz miał:

✅ **Pełny stack Docker** z backend, Ollama, Redis  
✅ **Modele AI** gotowe do użycia (Bielik-11B, Llama3.2)  
✅ **Mini aplikacje** z pełną integracją AI  
✅ **GPU acceleration** dla RTX 3060  
✅ **Production-ready** konfigurację  

**Gotowe do testowania wszystkich funkcji agentowych! 🚀**