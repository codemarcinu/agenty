# 🚀 Przewodnik Optymalizacji Perplexica dla FoodSave AI

## 📊 **ANALIZA AKTUALNEGO STANU**

### **Kontenery Perplexica**
- **perplexica-docker-app-1**: 142.3MB RAM (0.45% CPU) - **bardzo niskie wykorzystanie**
- **perplexica-docker-searxng-1**: 125.7MB RAM (0.39% CPU) - **bardzo niskie wykorzystanie**

### **Status Integracji**
- ✅ Kontenery uruchomione i działają
- ⚠️ Brak integracji z głównym systemem FoodSave AI
- ⚠️ Niskie wykorzystanie zasobów
- ⚠️ Brak aktywnych zapytań wyszukiwania

---

## 🎯 **PLAN OPTYMALIZACJI**

### **1. Integracja z Głównym Systemem**

#### **A) Aktualizacja Docker Compose**
```yaml
# docker-compose.perplexica.yaml
services:
  perplexica-app:
    networks:
      - foodsave-network  # Główna sieć FoodSave
    depends_on:
      perplexica-searxng:
        condition: service_healthy
      ollama:
        condition: service_healthy
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/"]
```

#### **B) Aktualizacja Ustawień Backendu**
```python
# src/backend/settings.py
PERPLEXICA_BASE_URL: str = "http://perplexica-app:3000/api"
PERPLEXICA_SEARXNG_URL: str = "http://perplexica-searxng:8080"
PERPLEXICA_HEALTH_CHECK_ENABLED: bool = True
```

### **2. Optymalizacja Wykorzystania Zasobów**

#### **A) Limity Zasobów**
```yaml
deploy:
  resources:
    limits:
      memory: 512M  # Perplexica App
      memory: 256M  # SearxNG
    reservations:
      memory: 256M  # Perplexica App
      memory: 128M  # SearxNG
```

#### **B) Health Checks**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### **3. Integracja z SearchAgent**

#### **A) Primary Provider**
```python
# src/backend/agents/search_agent.py
self.search_providers = {
    "perplexica": PerplexicaSearchProvider(),  # Primary
    "wikipedia": WikipediaSearchProvider(),    # Fallback
    "duck": DuckDuckGoSearchProvider(),       # Emergency
}
self.default_provider = "perplexica"
```

#### **B) Hybrydowe Wyszukiwanie**
```python
async def search_with_fallback(self, query: str) -> list[dict]:
    # Try Perplexica first
    try:
        results = await self.perplexica_provider.search(query)
        if results:
            return results
    except Exception as e:
        logger.warning(f"Perplexica failed: {e}")
    
    # Fallback to other providers
    return await self.fallback_search(query)
```

---

## 🔧 **IMPLEMENTACJA KROK PO KROKU**

### **Krok 1: Aktualizacja Konfiguracji**
```bash
# Uruchom skrypt optymalizacji
./scripts/optimize_perplexica.sh

# Zatrzymaj obecne kontenery
docker-compose -f docker-compose.perplexica.yaml down

# Uruchom z nową konfiguracją
docker-compose -f docker-compose.perplexica.yaml up -d
```

### **Krok 2: Test Integracji**
```bash
# Test połączenia
curl http://localhost:3000/
curl http://localhost:4000/

# Test wyszukiwania przez API
curl -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Adam Mickiewicz", "use_perplexica": true}'
```

### **Krok 3: Monitoring Wydajności**
```bash
# Sprawdź wykorzystanie zasobów
docker stats perplexica-docker-app-1 perplexica-docker-searxng-1

# Sprawdź logi
docker logs perplexica-docker-app-1 --tail 50

# Test health checks
curl -f http://localhost:3000/ || echo "Health check failed"
```

---

## 📈 **OCZEKIWANE KORZYŚCI**

### **Wydajność**
- **Lepsze wyniki wyszukiwania**: AI-powered search engine
- **Szybsze odpowiedzi**: Lokalne przetwarzanie
- **Większa dokładność**: Multi-provider aggregation

### **Koszty**
- **Redukcja kosztów API**: Brak zewnętrznych płatnych API
- **Optymalizacja zasobów**: Lepsze wykorzystanie pamięci i CPU
- **Skalowalność**: Możliwość dostosowania do potrzeb

### **Funkcjonalność**
- **Offline capability**: Praca bez internetu
- **Privacy**: Wszystkie dane lokalnie
- **Customization**: Pełna kontrola nad konfiguracją

---

## 🛠️ **NARZĘDZIA MONITORINGU**

### **Skrypt Optymalizacji**
```bash
# Pełna analiza
./scripts/optimize_perplexica.sh

# Sprawdź status
docker ps | grep perplexica

# Sprawdź zasoby
docker stats --no-stream perplexica-docker-app-1
```

### **Grafana Dashboard**
```yaml
# monitoring/grafana/dashboards/perplexica-dashboard.json
{
  "title": "Perplexica Performance",
  "panels": [
    {
      "title": "Memory Usage",
      "targets": ["perplexica-app", "perplexica-searxng"]
    },
    {
      "title": "Search Response Time",
      "targets": ["perplexica-search-latency"]
    },
    {
      "title": "Search Success Rate",
      "targets": ["perplexica-success-rate"]
    }
  ]
}
```

---

## 🚨 **TROUBLESHOOTING**

### **Problem: Niskie wykorzystanie zasobów**
**Rozwiązanie:**
1. Sprawdź czy SearchAgent używa Perplexica
2. Testuj wyszukiwania przez API
3. Sprawdź logi kontenerów

### **Problem: Brak połączenia z backendem**
**Rozwiązanie:**
1. Sprawdź sieć Docker: `docker network ls`
2. Testuj połączenie: `curl http://perplexica-app:3000/`
3. Sprawdź ustawienia w `settings.py`

### **Problem: Wolne odpowiedzi**
**Rozwiązanie:**
1. Sprawdź wykorzystanie CPU: `docker stats`
2. Zoptymalizuj konfigurację Ollama
3. Rozważ cache'owanie wyników

---

## 📊 **METRYKI SUKCESU**

### **Wydajność**
- [ ] Wykorzystanie pamięci > 50% (obecnie ~0.4%)
- [ ] Czas odpowiedzi < 2s
- [ ] Success rate > 95%

### **Integracja**
- [ ] SearchAgent używa Perplexica jako primary
- [ ] Health checks przechodzą
- [ ] Fallback strategy działa

### **Funkcjonalność**
- [ ] AI-powered search działa
- [ ] Multi-provider aggregation
- [ ] Offline capability

---

## 🎯 **NASTĘPNE KROKI**

1. **Implementacja optymalizacji** (1-2 dni)
2. **Testy integracyjne** (1 dzień)
3. **Monitoring wydajności** (ciągły)
4. **Dostrajanie konfiguracji** (1 tydzień)
5. **Dokumentacja użytkownika** (1 dzień)

**Szacowany czas implementacji: 1-2 tygodnie**
**Oczekiwane korzyści: 10x lepsze wykorzystanie zasobów** 