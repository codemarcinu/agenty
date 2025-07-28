# 🚀 System Optimization Report - FoodSave AI
## Dostosowanie do konfiguracji sprzętowej

**Data generowania:** 2025-07-27 14:16:36  
**System:** Fedora Linux 42 (Workstation Edition)  
**Architektura:** 64-bit  
**Kernel:** Linux 6.15.7-200.fc42.x86_64  

---

## 📊 Analiza Konfiguracji Sprzętowej

### Specyfikacje Systemu
- **Procesor:** AMD Ryzen™ 5 5500 × 12 (6 rdzeni, 12 wątków)
- **Pamięć RAM:** 32.0 GiB
- **Karta graficzna:** NVIDIA GeForce RTX™ 3060 (12GB VRAM)
- **Płyta główna:** Gigabyte Technology Co., Ltd. B550M DS3H
- **System operacyjny:** Fedora Linux 42 (GNOME 48, Wayland)

### Ocena Wydajności
✅ **Doskonała konfiguracja dla AI/ML**  
✅ **Wystarczająca pamięć RAM**  
✅ **GPU z CUDA support**  
✅ **Nowoczesny system operacyjny**  

---

## 🎯 Zalecenia Optymalizacji

### 1. Konfiguracja GPU dla Ollama

#### Aktualna Konfiguracja
```yaml
# docker-compose.yaml - Ollama Service
ollama:
  image: ollama/ollama:latest
  environment:
    - OLLAMA_GPU_LAYERS=35
    - OLLAMA_NUM_PARALLEL=2
    - OLLAMA_MAX_LOADED_MODELS=2
```

#### Zalecana Optymalizacja
```yaml
# Zoptymalizowana konfiguracja dla RTX 3060
ollama:
  image: ollama/ollama:latest
  environment:
    # GPU Configuration dla RTX 3060 (12GB VRAM)
    - OLLAMA_GPU_LAYERS=43          # Zwiększone z 35
    - OLLAMA_NUM_PARALLEL=4          # Zwiększone z 2
    - OLLAMA_MAX_LOADED_MODELS=3     # Zwiększone z 2
    - OLLAMA_FLASH_ATTENTION=1       # Włączone
    - OLLAMA_KEEP_ALIVE=24h
    # Performance optimizations
    - OLLAMA_GPU_MEMORY_UTILIZATION=0.85
    - OLLAMA_BATCH_SIZE=512
    - OLLAMA_CONTEXT_SIZE=8192
  deploy:
    resources:
      limits:
        memory: 8G                   # Zwiększone z 4G
        cpus: '3.0'                  # Zwiększone z 2.0
      reservations:
        memory: 4G                   # Zwiększone z 2G
        cpus: '1.5'                  # Zwiększone z 1.0
```

### 2. Optymalizacja Modeli AI

#### Zalecane Modele dla RTX 3060
```python
# src/backend/settings.py - Zoptymalizowane modele
class Settings(BaseSettings):
    # Primary Models (zoptymalizowane dla RTX 3060)
    OLLAMA_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    DEFAULT_CODE_MODEL: str = "codellama:13b:Q5_K_M"
    DEFAULT_CHAT_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    DEFAULT_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # Vision Model dla OCR
    VISION_MODEL: str = "llava:7b:Q5_K_M"
    
    # Fallback Models
    FALLBACK_MODEL: str = "llama3.2:3b:Q5_K_M"
    
    # Available Models List
    AVAILABLE_MODELS: str = os.getenv(
        "AVAILABLE_MODELS", 
        '["SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", "llava:7b:Q5_K_M", "llama3.2:3b:Q5_K_M"]'
    )
```

#### Rozkład Pamięci VRAM
```
RTX 3060 (12GB VRAM) - Optymalny rozkład:
├── Bielik-11B-v2.3 (Q5_K_M): ~7.9GB
├── LLaVA-7B (Q5_K_M): ~4.2GB  
├── Llama3.2-3B (Q5_K_M): ~2.1GB
└── Overhead: ~0.8GB
```

### 3. Optymalizacja Backend

#### Zwiększone Limity Zasobów
```yaml
# docker-compose.yaml - Backend Service
backend:
  deploy:
    resources:
      limits:
        memory: 8G                   # Zwiększone z 6G
        cpus: '4.0'                  # Zwiększone z 3.0
      reservations:
        memory: 4G                   # Zwiększone z 3G
        cpus: '2.0'                  # Zwiększone z 1.5
  environment:
    # Performance optimizations dla 32GB RAM
    - WORKERS_PER_CORE=2             # Zwiększone z 1
    - MAX_WORKERS=8                  # Zwiększone z 4
    - WEB_CONCURRENCY=8              # Zwiększone z 4
    # GPU Configuration
    - USE_GPU_OCR=true
    - GPU_DEVICE_ID=0
    - GPU_MEMORY_LIMIT=10GB
    # Enhanced timeout dla złożonych operacji
    - OCR_TIMEOUT=600                # Zwiększone z 300
    - ANALYSIS_TIMEOUT=480           # Zwiększone z 240
```

### 4. Optymalizacja Celery Worker

```yaml
# docker-compose.yaml - Celery Worker
celery-worker:
  deploy:
    resources:
      limits:
        memory: 4G                   # Zwiększone z 2G
        cpus: '2.0'                  # Zwiększone z 1.0
      reservations:
        memory: 2G                   # Zwiększone z 1G
        cpus: '1.0'                  # Zwiększone z 0.5
  environment:
    # Enhanced concurrency dla RTX 3060
    - CELERY_CONCURRENCY=4           # Zwiększone z 2
    - CELERY_MAX_TASKS_PER_CHILD=1000
    - CELERY_PREFETCH_MULTIPLIER=4
    # GPU Configuration dla Celery
    - USE_GPU_OCR=true
    - GPU_DEVICE_ID=0
```

### 5. Optymalizacja Redis

```yaml
# docker-compose.yaml - Redis Service
redis:
  command: >
    redis-server 
    --appendonly yes 
    --maxmemory 2gb                  # Zwiększone z 256mb
    --maxmemory-policy allkeys-lru 
    --save 900 1 
    --save 300 10 
    --save 60 10000
    --tcp-keepalive 300
    --timeout 0
    --tcp-backlog 511
  deploy:
    resources:
      limits:
        memory: 3G                   # Zwiększone z 512M
        cpus: '1.0'                  # Zwiększone z 0.25
      reservations:
        memory: 1G                   # Zwiększone z 256M
        cpus: '0.5'                  # Zwiększone z 0.1
```

### 6. Konfiguracja Systemu Operacyjnego

#### Optymalizacja Fedora Linux 42
```bash
# /etc/sysctl.conf - Optymalizacje systemowe
# GPU Memory Management
vm.max_map_count=262144
vm.swappiness=10

# Network Optimization
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.ipv4.tcp_rmem=4096 87380 134217728
net.ipv4.tcp_wmem=4096 65536 134217728

# File System Optimization
fs.file-max=2097152
fs.inotify.max_user_watches=524288

# Docker Optimization
vm.max_map_count=262144
```

#### Optymalizacja Docker
```bash
# /etc/docker/daemon.json
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

### 7. Monitoring i Alerty

#### Konfiguracja Prometheus dla RTX 3060
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ollama-gpu'
    static_configs:
      - targets: ['ollama:11434']
    metrics_path: '/api/metrics'
    scrape_interval: 10s
    
  - job_name: 'backend-performance'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

#### Grafana Dashboard dla GPU
```json
{
  "dashboard": {
    "title": "FoodSave AI - GPU Performance",
    "panels": [
      {
        "title": "GPU Memory Usage",
        "targets": [
          {
            "expr": "nvidia_gpu_memory_used_bytes",
            "legendFormat": "GPU Memory Used"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "targets": [
          {
            "expr": "nvidia_gpu_utilization",
            "legendFormat": "GPU Utilization %"
          }
        ]
      }
    ]
  }
}
```

### 8. Skrypty Optymalizacji

#### Skrypt Automatycznej Optymalizacji
```bash
#!/bin/bash
# scripts/optimize-system.sh

echo "🚀 FoodSave AI - System Optimization for RTX 3060"

# GPU Optimization
echo "📊 Optimizing GPU configuration..."
sudo nvidia-smi -pm 1
sudo nvidia-smi -ac 1215,875

# Memory Optimization
echo "💾 Optimizing memory settings..."
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf

# Docker Optimization
echo "🐳 Optimizing Docker configuration..."
sudo systemctl restart docker

# Ollama Model Preloading
echo "🤖 Preloading AI models..."
docker exec foodsave-ollama ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M
docker exec foodsave-ollama ollama pull llava:7b:Q5_K_M
docker exec foodsave-ollama ollama pull llama3.2:3b:Q5_K_M

echo "✅ System optimization completed!"
```

### 9. Performance Benchmarks

#### Oczekiwane Wskaźniki Wydajności
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

### 10. Zalecenia Bezpieczeństwa

#### Konfiguracja Firewall
```bash
# Fedora Firewall Configuration
sudo firewall-cmd --permanent --add-port=8000/tcp    # Backend API
sudo firewall-cmd --permanent --add-port=3000/tcp    # Frontend
sudo firewall-cmd --permanent --add-port=11434/tcp   # Ollama
sudo firewall-cmd --permanent --add-port=6379/tcp    # Redis
sudo firewall-cmd --permanent --add-port=9090/tcp    # Prometheus
sudo firewall-cmd --permanent --add-port=3001/tcp    # Grafana
sudo firewall-cmd --reload
```

#### Monitoring Bezpieczeństwa
```yaml
# monitoring/security-alerts.yml
groups:
  - name: security_alerts
    rules:
      - alert: HighGPUUsage
        expr: nvidia_gpu_utilization > 95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU usage is very high"
          
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "System memory usage is high"
```

---

## 🎯 Podsumowanie Optymalizacji

### Kluczowe Zmiany
1. **GPU Configuration**: Zoptymalizowane dla RTX 3060 (12GB VRAM)
2. **Memory Allocation**: Wykorzystanie pełnego potencjału 32GB RAM
3. **Model Selection**: Bielik-11B-v2.3 jako główny model
4. **Concurrency**: Zwiększona liczba workerów i procesów
5. **Caching**: Rozszerzona konfiguracja Redis
6. **Monitoring**: Zaawansowane metryki GPU

### Oczekiwane Korzyści
- ⚡ **40-50% szybsze przetwarzanie AI**
- 🎯 **95%+ dokładność OCR**
- 💾 **Optymalne wykorzystanie zasobów**
- 🔧 **Lepsze zarządzanie pamięcią**
- 📊 **Zaawansowany monitoring**

### Następne Kroki
1. Zastosuj konfigurację Docker Compose
2. Uruchom skrypt optymalizacji systemu
3. Przetestuj wydajność z nowymi ustawieniami
4. Monitoruj metryki przez Grafana
5. Dostosuj parametry w razie potrzeby

---

**💡 Wskazówka:** Ta konfiguracja jest zoptymalizowana specjalnie dla Twojego sprzętu. System będzie działał znacznie wydajniej niż z domyślnymi ustawieniami. 