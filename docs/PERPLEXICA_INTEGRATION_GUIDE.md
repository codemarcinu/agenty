# 🔍 Perplexica Integration Guide

## Przegląd

Ten dokument opisuje integrację Perplexica z systemem FoodSave AI.

## Konfiguracja

### 1. Zmienne środowiskowe

```bash
# Perplexica Configuration
PERPLEXICA_BASE_URL=http://perplexica:3000/api
PERPLEXICA_ENABLED=true
PERPLEXICA_TIMEOUT=30
```

### 2. Docker Compose

```bash
# Uruchom Perplexica
docker-compose -f docker-compose.perplexica.yaml up -d

# Sprawdź status
docker-compose -f docker-compose.perplexica.yaml ps
```

### 3. Health Check

```bash
# Sprawdź zdrowie Perplexica
curl http://localhost:3000/health
```

## Użycie

### Podstawowe wyszukiwanie

```python
from backend.agents.tools.search_providers import PerplexicaSearchProvider

provider = PerplexicaSearchProvider()
results = await provider.search("test query", max_results=5)
```

### Integration z SearchAgent

```python
from backend.agents.search_agent import SearchAgent

agent = SearchAgent()
response = await agent.process({
    "query": "test query",
    "use_perplexica": True
})
```

## Monitoring

### Metryki

- Response time
- Success rate
- Cache hit rate
- Error rate

### Logi

```bash
# Logi Perplexica
docker logs foodsave-perplexica

# Logi bazy danych
docker logs foodsave-perplexica-db
```

## Troubleshooting

### Problem: Perplexica nie odpowiada

1. Sprawdź czy kontener działa:
   ```bash
   docker ps | grep perplexica
   ```

2. Sprawdź logi:
   ```bash
   docker logs foodsave-perplexica
   ```

3. Sprawdź połączenie z bazą danych:
   ```bash
   docker exec -it foodsave-perplexica-db psql -U perplexica -d perplexica
   ```

### Problem: Błędy API

1. Sprawdź ustawienia:
   ```bash
   echo $PERPLEXICA_BASE_URL
   ```

2. Testuj endpoint:
   ```bash
   curl -X POST http://perplexica:3000/api/search \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}'
   ```

## Rozwój

### Dodawanie nowych providerów

1. Dodaj provider do Perplexica
2. Zaktualizuj `providers` w `search_request`
3. Dodaj testy
4. Zaktualizuj dokumentację

### Optymalizacja wydajności

1. Monitoruj metryki
2. Dostosuj cache settings
3. Optymalizuj queries
4. Scale resources
