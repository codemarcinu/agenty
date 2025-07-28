# 🚀 FoodSave AI - Deployment Guide for RTX 3060
## Przewodnik wdrażania dla AMD Ryzen 5 5500 + NVIDIA RTX 3060 + 32GB RAM

**System:** Fedora Linux 42 (Workstation Edition)  
**Data:** 2025-07-27  
**Wersja:** 2.0.0 (RTX 3060 Optimized)  

---

## 📋 Wymagania Wstępne

### Sprawdzenie Systemu
```bash
# Sprawdź wersję systemu
cat /etc/fedora-release

# Sprawdź GPU
nvidia-smi

# Sprawdź pamięć RAM
free -h

# Sprawdź procesor
lscpu | grep "Model name"
```

### Wymagane Pakiety
```bash
# Aktualizuj system
sudo dnf update -y

# Zainstaluj wymagane pakiety
sudo dnf install -y \
    docker \
    docker-compose \
    nvidia-container-toolkit \
    nvidia-container-runtime \
    curl \
    wget \
    git \
    python3 \
    python3-pip

# Włącz i uruchom Docker
sudo systemctl enable docker
sudo systemctl start docker

# Dodaj użytkownika do grupy docker
sudo usermod -aG docker $USER
```

---

## 🎯 Krok 1: Optymalizacja Systemu

### Uruchom Skrypt Optymalizacji
```bash
# Nadaj uprawnienia wykonywania
chmod +x scripts/optimize-system.sh

# Uruchom pełną optymalizację
./scripts/optimize-system.sh

# Lub uruchom poszczególne komponenty:
./scripts/optimize-system.sh --gpu-only      # Optymalizacja GPU
./scripts/optimize-system.sh --memory-only   # Optymalizacja pamięci
./scripts/optimize-system.sh --docker-only   # Optymalizacja Docker
./scripts/optimize-system.sh --health-check  # Sprawdzenie systemu
```

### Sprawdź Optymalizację
```bash
# Sprawdź GPU
nvidia-smi

# Sprawdź pamięć
free -h

# Sprawdź Docker
docker info

# Sprawdź firewall
sudo firewall-cmd --list-ports
```

---

## 🐳 Krok 2: Konfiguracja Docker

### Użyj Zoptymalizowanego Docker Compose
```bash
# Skopiuj zoptymalizowany plik
cp docker-compose.optimized.yaml docker-compose.yaml

# Lub użyj bezpośrednio:
docker-compose -f docker-compose.optimized.yaml up -d
```

### Sprawdź Konfigurację
```bash
# Sprawdź pliki konfiguracyjne
ls -la docker-compose*.yaml

# Sprawdź zmienne środowiskowe
cat .env
```

---

## 🤖 Krok 3: Wdrożenie Modeli AI

### Preload Modeli dla RTX 3060
```bash
# Uruchom Ollama
docker-compose -f docker-compose.optimized.yaml up -d ollama

# Poczekaj na gotowość Ollama
sleep 60

# Preload głównych modeli
docker exec foodsave-ollama ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M
docker exec foodsave-ollama ollama pull llava:7b:Q5_K_M
docker exec foodsave-ollama ollama pull llama3.2:3b:Q5_K_M
docker exec foodsave-ollama ollama pull codellama:13b:Q5_K_M
```

### Sprawdź Modele
```bash
# Sprawdź załadowane modele
docker exec foodsave-ollama ollama list

# Sprawdź użycie VRAM
nvidia-smi
```

---

## 🚀 Krok 4: Uruchomienie Systemu

### Pełne Uruchomienie
```bash
# Uruchom wszystkie serwisy
docker-compose -f docker-compose.optimized.yaml up -d

# Sprawdź status
docker-compose -f docker-compose.optimized.yaml ps

# Sprawdź logi
docker-compose -f docker-compose.optimized.yaml logs -f
```

### Sprawdź Dostępność Serwisów
```bash
# Backend API
curl -f http://localhost:8000/health

# Frontend
curl -f http://localhost:8085/

# Ollama
curl -f http://localhost:11434/api/tags

# Redis
docker exec foodsave-redis redis-cli ping
```

---

## 📊 Krok 5: Monitoring i Metryki

### Uruchom Monitoring (Opcjonalnie)
```bash
# Uruchom z monitoringiem
docker-compose -f docker-compose.optimized.yaml --profile monitoring up -d

# Sprawdź dostępność
echo "Grafana: http://localhost:3001"
echo "Prometheus: http://localhost:9090"
```

### Sprawdź Metryki GPU
```bash
# Monitoruj GPU w czasie rzeczywistym
watch -n 1 nvidia-smi

# Sprawdź użycie pamięci
htop

# Sprawdź dysk
df -h
```

---

## 🔧 Krok 6: Konfiguracja Ustawień

### Użyj Zoptymalizowanych Ustawień
```bash
# Skopiuj zoptymalizowane ustawienia
cp src/backend/settings_optimized.py src/backend/settings.py

# Lub zmodyfikuj istniejące ustawienia
# Edytuj src/backend/settings.py zgodnie z rekomendacjami
```

### Sprawdź Konfigurację
```bash
# Sprawdź ustawienia
python3 -c "from src.backend.settings import settings; print(f'Model: {settings.OLLAMA_MODEL}')"

# Sprawdź dostępność modeli
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", "prompt": "Test", "stream": false}'
```

---

## 🧪 Krok 7: Testy Wydajnościowe

### Testy Podstawowe
```bash
# Test API
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message", "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"}'

# Test OCR
curl -X POST http://localhost:8000/api/v1/ocr \
  -F "file=@paragony/20250125lidl.png"

# Test RAG
curl -X POST http://localhost:8000/api/v1/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query", "context": "test"}'
```

### Testy Wydajnościowe
```bash
# Test obciążenia API
ab -n 100 -c 10 http://localhost:8000/health

# Test GPU pod obciążeniem
stress-ng --cpu 6 --memory 16 --timeout 60s

# Monitoruj podczas testów
watch -n 1 'nvidia-smi && echo "---" && free -h'
```

---

## 📈 Krok 8: Monitoring i Alerty

### Konfiguracja Grafana
```bash
# Importuj dashboard GPU
curl -X POST http://localhost:3001/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/dashboards/gpu-performance.json
```

### Sprawdź Alerty
```bash
# Sprawdź alerty Prometheus
curl http://localhost:9090/api/v1/alerts

# Sprawdź metryki
curl http://localhost:9090/api/v1/query?query=nvidia_gpu_memory_used_bytes
```

---

## 🔍 Krok 9: Diagnostyka i Rozwiązywanie Problemów

### Sprawdź Logi
```bash
# Logi backend
docker-compose -f docker-compose.optimized.yaml logs backend

# Logi Ollama
docker-compose -f docker-compose.optimized.yaml logs ollama

# Logi Redis
docker-compose -f docker-compose.optimized.yaml logs redis
```

### Diagnostyka GPU
```bash
# Sprawdź sterowniki NVIDIA
nvidia-smi

# Sprawdź kontenery GPU
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# Sprawdź użycie VRAM
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

### Rozwiązywanie Problemów
```bash
# Resetuj kontenery
docker-compose -f docker-compose.optimized.yaml down
docker-compose -f docker-compose.optimized.yaml up -d

# Wyczyść cache
docker system prune -f

# Sprawdź miejsce na dysku
df -h
```

---

## 🎯 Oczekiwane Wskaźniki Wydajności

### Po Optymalizacji
```
RTX 3060 + 32GB RAM - Expected Performance:

📊 Model Loading Times:
├── Bielik-11B-v2.3: ~45-60s
├── LLaVA-7B: ~30-40s
└── Llama3.2-3B: ~15-20s

⚡ Inference Speed:
├── Bielik-11B-v2.3: ~15-25 tokens/s
├── LLaVA-7B: ~20-30 tokens/s
└── Llama3.2-3B: ~35-45 tokens/s

🎯 OCR Performance:
├── GPU OCR: ~2-3s per image
├── Batch Processing: ~10-15 images/min
└── Accuracy: >95%

💾 Memory Usage:
├── GPU VRAM: ~10-11GB (85-90%)
├── System RAM: ~16-20GB (50-60%)
└── Cache Hit Rate: >85%
```

---

## 🔧 Komendy Użyteczne

### Zarządzanie Systemem
```bash
# Start systemu
./scripts/main/foodsave.sh start

# Stop systemu
./scripts/main/foodsave.sh stop

# Status systemu
./scripts/main/foodsave.sh status

# Logi systemu
./scripts/main/foodsave.sh logs
```

### Monitoring
```bash
# GPU monitoring
watch -n 1 nvidia-smi

# System monitoring
htop

# Docker monitoring
docker stats

# Network monitoring
ss -tuln
```

### Backup i Restore
```bash
# Backup danych
docker exec foodsave-backend python3 -c "from src.backend.core.enhanced_backup_manager import EnhancedBackupManager; EnhancedBackupManager().create_backup()"

# Restore danych
docker exec foodsave-backend python3 -c "from src.backend.core.enhanced_backup_manager import EnhancedBackupManager; EnhancedBackupManager().restore_backup('backup_name')"
```

---

## 📞 Wsparcie i Diagnostyka

### Logi Systemowe
```bash
# Sprawdź logi systemowe
journalctl -u docker.service -f

# Sprawdź logi GPU
dmesg | grep -i nvidia

# Sprawdź logi aplikacji
tail -f logs/foodsave.log
```

### Kontakt i Wsparcie
- **Dokumentacja:** `docs/`
- **Logi:** `logs/`
- **Konfiguracja:** `src/backend/settings.py`
- **Skrypty:** `scripts/`

---

## ✅ Checklista Wdrożenia

- [ ] System wymagań spełniony
- [ ] Optymalizacja systemu wykonana
- [ ] Docker skonfigurowany
- [ ] Modele AI załadowane
- [ ] System uruchomiony
- [ ] Testy wydajnościowe wykonane
- [ ] Monitoring skonfigurowany
- [ ] Backup skonfigurowany
- [ ] Dokumentacja zaktualizowana

---

**🎉 Gratulacje!** System FoodSave AI jest teraz zoptymalizowany dla Twojej konfiguracji RTX 3060 + 32GB RAM i gotowy do użycia produkcyjnego.

**💡 Wskazówka:** Regularnie monitoruj wydajność systemu i dostosowuj parametry w razie potrzeby. 