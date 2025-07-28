# 🔧 Konserwacja Systemu - FoodSave AI

> **Ostatnia aktualizacja:** 2025-07-18  
> **Powiązane dokumenty:** [TOC.md](../TOC.md), [BACKUP_SYSTEM.md](BACKUP_SYSTEM.md)

## Co znajdziesz w tym dokumencie?

- [x] Procedury konserwacji systemu
- [x] Czyszczenie i optymalizacja
- [x] Monitoring i alerty
- [x] Procedury awaryjne
- [x] Harmonogram konserwacji

## Spis treści
- [1. 📅 Harmonogram Konserwacji](#-harmonogram-konserwacji)
- [2. 🧹 Czyszczenie Systemu](#-czyszczenie-systemu)
- [3. 📊 Monitoring i Alerty](#-monitoring-i-alerty)
- [4. 🔄 Procedury Awarne](#-procedury-awarne)
- [5. 📈 Optymalizacja Wydajności](#-optymalizacja-wydajności)
- [6. 🔒 Bezpieczeństwo](#-bezpieczeństwo)

---

## 📅 Harmonogram Konserwacji

### Codzienne Zadania
- [ ] **Sprawdzenie statusu systemu** - `./foodsave-all.sh status`
- [ ] **Przegląd logów** - Sprawdzenie błędów i ostrzeżeń
- [ ] **Backup bazy danych** - Automatyczny backup
- [ ] **Monitoring metryk** - Sprawdzenie wydajności

### Cotygodniowe Zadania
- [ ] **Czyszczenie logów** - Usunięcie starych logów
- [ ] **Optymalizacja bazy danych** - VACUUM i ANALYZE
- [ ] **Aktualizacja modeli AI** - Sprawdzenie nowych wersji
- [ ] **Przegląd bezpieczeństwa** - Sprawdzenie uprawnień

### Comiesięczne Zadania
- [ ] **Pełne czyszczenie systemu** - Usunięcie cache i plików tymczasowych
- [ ] **Aktualizacja zależności** - Sprawdzenie nowych wersji
- [ ] **Testy wydajnościowe** - Benchmark systemu
- [ ] **Przegląd konfiguracji** - Optymalizacja ustawień

### Kwartalne Zadania
- [ ] **Audyt bezpieczeństwa** - Pełny przegląd bezpieczeństwa
- [ ] **Aktualizacja dokumentacji** - Aktualizacja przewodników
- [ ] **Testy odzyskiwania** - Testy procedur backup/restore
- [ ] **Planowanie pojemności** - Analiza wzrostu danych

---

## 🧹 Czyszczenie Systemu

### Czyszczenie Logów
```bash
# Czyszczenie starych logów (starszych niż 30 dni)
find logs/ -name "*.log" -mtime +30 -delete

# Czyszczenie logów Docker
docker system prune -f

# Czyszczenie logów aplikacji
rm -f logs/backend.log.*
rm -f logs/frontend.log.*
```

### Czyszczenie Cache
```bash
# Czyszczenie cache Redis
docker exec redis redis-cli FLUSHDB

# Czyszczenie cache aplikacji
rm -rf data/search_cache/*
rm -rf data/vector_store_dev/*

# Czyszczenie cache Docker
docker builder prune -f
```

### Czyszczenie Bazy Danych
```sql
-- Optymalizacja SQLite
VACUUM;
PRAGMA optimize;

-- Czyszczenie starych danych
DELETE FROM messages WHERE created_at < strftime('%Y-%m-%d %H:%M:%S', date('now', '-90 days'));
DELETE FROM conversations WHERE created_at < strftime('%Y-%m-%d %H:%M:%S', date('now', '-90 days'));
```

### Czyszczenie Plików Tymczasowych
```bash
# Usunięcie plików tymczasowych
rm -rf temp_uploads/*
rm -rf test-results/*
rm -rf coverage/
rm -rf .pytest_cache/

# Czyszczenie node_modules (jeśli nie używane)
cd myappassistant-chat-frontend
rm -rf node_modules
npm install
```

---

## 📊 Monitoring i Alerty

### Kluczowe Metryki do Monitorowania

#### Wydajność Systemu
- **CPU Usage**: < 80% średnio
- **Memory Usage**: < 85% RAM
- **Disk Usage**: < 90% pojemności
- **Network**: < 1GB/s transfer

#### Baza Danych
- **Connection Pool**: < 80% wykorzystania
- **Query Time**: < 1000ms średnio
- **Lock Time**: < 100ms
- **Cache Hit Rate**: > 90%

#### AI/ML
- **Model Response Time**: < 5s
- **Model Accuracy**: > 85%
- **GPU Usage**: < 90% (jeśli dostępne)
- **Memory Usage**: < 8GB per model

### Alerty Systemowe
```yaml
# Przykładowe alerty Prometheus
alerts:
  - name: "High CPU Usage"
    condition: "cpu_usage > 80%"
    duration: "5m"
    
  - name: "High Memory Usage"
    condition: "memory_usage > 85%"
    duration: "5m"
    
  - name: "Database Connection Pool Full"
    condition: "db_connections > 80%"
    duration: "2m"
    
  - name: "AI Model Response Time High"
    condition: "ai_response_time > 10s"
    duration: "3m"
```

### Monitoring Dashboardy
- **System Overview**: Status wszystkich komponentów
- **Performance Metrics**: Wydajność systemu
- **Error Tracking**: Śledzenie błędów
- **AI Performance**: Wydajność modeli AI

---

## 🔄 Procedury Awarne

### Procedura Restartu Systemu
```bash
# 1. Bezpieczne zatrzymanie
./foodsave-all.sh stop

# 2. Sprawdzenie procesów
ps aux | grep -E "(docker|ollama|postgres)"

# 3. Restart usług
./foodsave-all.sh dev

# 4. Sprawdzenie statusu
./foodsave-all.sh status
```

### Procedura Odzyskiwania z Backupu
```bash
# 1. Zatrzymanie systemu
./foodsave-all.sh stop

# 2. Przywrócenie bazy danych (skopiuj plik backupu do data/foodsave.db)
# cp backups/database/backup_latest.db data/foodsave.db

# 3. Przywrócenie plików
tar -xzf backup_files_latest.tar.gz -C /

# 4. Restart systemu
./foodsave-all.sh dev
```

### Procedura Awaryjna - Brak Dostępu do Systemu
```bash
# 1. Sprawdzenie zasobów systemowych
df -h
free -h
top

# 2. Sprawdzenie usług Docker
docker ps -a
docker logs <container_name>

# 3. Restart Docker
sudo systemctl restart docker

# 4. Pełny restart systemu
./foodsave-all.sh stop
docker system prune -af
./foodsave-all.sh dev
```

---

## 📈 Optymalizacja Wydajności

### Optymalizacja Bazy Danych
```sql
-- Analiza wydajności zapytań
EXPLAIN QUERY PLAN SELECT * FROM messages WHERE conversation_id = ?;

-- Optymalizacja indeksów
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_receipts_date ON receipts(date);
```

### Optymalizacja AI/ML
```python
# Optymalizacja modeli Ollama
# ollama.conf
models:
  - name: "bielik-4.5b-v3.0"
    parameters:
      num_ctx: 4096
      num_thread: 8
      num_gpu: 1  # jeśli dostępne GPU
```

### Optymalizacja Frontendu
```javascript
// Optymalizacja React
// next.config.js
module.exports = {
  experimental: {
    optimizeCss: true,
    optimizeImages: true,
  },
  compress: true,
  poweredByHeader: false,
}
```

### Optymalizacja Docker
```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
```

---

## 🔒 Bezpieczeństwo

### Regularne Sprawdzenia Bezpieczeństwa
```bash
# Sprawdzenie uprawnień plików
find . -type f -perm /u+w -ls
find . -type d -perm /u+w -ls

# Sprawdzenie procesów
ps aux | grep -E "(python|node|ollama)"

# Sprawdzenie połączeń sieciowych
netstat -tulpn | grep -E "(8000|3000|11434)"

# Sprawdzenie logów bezpieczeństwa
sudo journalctl -u docker --since "1 hour ago"
```

### Aktualizacje Bezpieczeństwa
```bash
# Aktualizacja obrazów Docker
docker pull ollama/ollama:latest
docker pull redis:7

# Aktualizacja zależności Python
pip list --outdated
pip install --upgrade <package_name>

# Aktualizacja zależności Node.js
npm audit
npm audit fix
```

### Monitoring Bezpieczeństwa
- **Failed Login Attempts**: Śledzenie prób logowania
- **Suspicious Network Activity**: Monitorowanie ruchu sieciowego
- **File System Changes**: Śledzenie zmian w plikach
- **Process Monitoring**: Monitorowanie procesów

---

## 📋 Checklista Konserwacji

### Codzienna
- [ ] Sprawdzenie statusu systemu
- [ ] Przegląd logów błędów
- [ ] Sprawdzenie metryk wydajności
- [ ] Weryfikacja backupów

### Cotygodniowa
- [ ] Czyszczenie starych logów
- [ ] Optymalizacja bazy danych
- [ ] Sprawdzenie aktualizacji
- [ ] Testy wydajnościowe

### Comiesięczna
- [ ] Pełne czyszczenie systemu
- [ ] Aktualizacja zależności
- [ ] Przegląd bezpieczeństwa
- [ ] Testy odzyskiwania

### Kwartalna
- [ ] Audyt bezpieczeństwa
- [ ] Planowanie pojemności
- [ ] Aktualizacja dokumentacji
- [ ] Przegląd architektury

---

## 🔗 Linki do Dokumentacji

### Powiązane Dokumenty
- [Backup System](BACKUP_SYSTEM.md) - System backupów
- [Security](SECURITY.md) - Bezpieczeństwo systemu
- [Monitoring](../guides/deployment/MONITORING.md) - Monitoring systemu
- [Production Deployment](../guides/deployment/PRODUCTION.md) - Wdrażanie produkcyjne

### Narzędzia
- **Panel sterowania**: `./foodsave-all.sh`
- **Monitoring**: http://localhost:3001 (Grafana)
- **Logi**: `./foodsave-all.sh logs`
- **Status**: `./foodsave-all.sh status`

---

> **💡 Wskazówka:** Regularna konserwacja systemu jest kluczowa dla stabilności i wydajności. Używaj panelu sterowania `foodsave-all.sh` do większości operacji konserwacyjnych. 