# 🔍 Analiza Integracji Perplexica z FoodSave AI

## 📋 Przegląd

### Perplexica - Open Source Alternative to Perplexity AI
- **Opis**: Perplexica to open-source'owa alternatywa dla Perplexity AI
- **Technologia**: TypeScript, Next.js, React
- **Kluczowe funkcje**: AI-powered search engine, multi-provider support
- **Architektura**: Modularna z supportem dla różnych LLM providers

### Obecny stan FoodSave AI Search
- **SearchAgent**: Zaimplementowany z supportem dla Wikipedia i DuckDuckGo
- **Perplexity Client**: Istniejący klient dla Perplexity API
- **Web Search Integration**: Zaawansowany system z weryfikacją wiedzy
- **Cache System**: Zoptymalizowany cache dla wyników wyszukiwania

## 🎯 Możliwości Integracji

### 1. **Bezpośrednia Integracja Perplexica jako Sidecar**

#### Zalety:
- ✅ **Pełna kontrola**: Własny serwer search engine
- ✅ **Offline capability**: Możliwość pracy bez zewnętrznych API
- ✅ **Customization**: Pełna możliwość dostosowania do potrzeb FoodSave
- ✅ **Privacy**: Wszystkie dane pozostają lokalnie
- ✅ **Cost reduction**: Brak kosztów zewnętrznych API

#### Wady:
- ❌ **Complexity**: Dodatkowa infrastruktura do zarządzania
- ❌ **Resource usage**: Większe zużycie zasobów
- ❌ **Maintenance**: Dodatkowy komponent do utrzymania

#### Implementacja:
```yaml
# docker-compose.perplexica.yaml
services:
  perplexica:
    image: perplexica/perplexica:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/perplexica
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - perplexica_data:/app/data
    depends_on:
      - db
      - ollama
```

### 2. **Hybrydowe Rozwiązanie - Perplexica + Obecny System**

#### Architektura:
```
FoodSave AI Backend
├── SearchAgent (obecny)
│   ├── WikipediaSearchProvider
│   ├── DuckDuckGoSearchProvider
│   └── PerplexicaSearchProvider (nowy)
├── PerplexityClient (obecny)
└── WebSearchClient (obecny)
```

#### Implementacja:
```python
# src/backend/agents/tools/search_providers.py
class PerplexicaSearchProvider(SearchProvider):
    """Provider for Perplexica searches"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "http://perplexica:3000/api"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search using Perplexica API"""
        try:
            response = await self.client.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "max_results": max_results,
                    "providers": ["wikipedia", "duckduckgo", "searxng"]
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result["snippet"],
                    "source": "perplexica",
                    "confidence": result.get("confidence", 0.8)
                }
                for result in data["results"]
            ]
        except Exception as e:
            logger.error(f"Perplexica search error: {e}")
            return []
```

### 3. **API Gateway Pattern**

#### Architektura:
```
Client Request
    ↓
API Gateway (FastAPI)
    ↓
Search Orchestrator
    ├── Perplexica (primary)
    ├── Perplexity API (fallback)
    └── DuckDuckGo (emergency)
```

#### Implementacja:
```python
# src/backend/core/search_orchestrator.py
class SearchOrchestrator:
    """Orchestrates search across multiple providers"""
    
    def __init__(self):
        self.providers = {
            "perplexica": PerplexicaClient(),
            "perplexity": PerplexityClient(),
            "duckduckgo": DuckDuckGoSearchProvider()
        }
        self.priority_order = ["perplexica", "perplexity", "duckduckgo"]
    
    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        """Search with fallback strategy"""
        for provider_name in self.priority_order:
            try:
                provider = self.providers[provider_name]
                results = await provider.search(query, max_results)
                if results:
                    return SearchResponse(
                        results=results,
                        provider=provider_name,
                        success=True
                    )
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        return SearchResponse(
            results=[],
            provider="none",
            success=False,
            error="All providers failed"
        )
```

## 🚀 Plan Implementacji

### Faza 1: Analiza i Przygotowanie (1-2 tygodnie)

#### 1.1 Analiza Perplexica
- [ ] **Klonowanie i analiza kodu**: `git clone https://github.com/ItzCrazyKns/Perplexica.git`
- [ ] **Analiza architektury**: Zrozumienie struktury i API
- [ ] **Testowanie lokalne**: Uruchomienie Perplexica w kontenerze
- [ ] **Dokumentacja API**: Analiza dostępnych endpointów

#### 1.2 Przygotowanie Infrastruktury
- [ ] **Docker Compose**: Dodanie Perplexica do stacku
- [ ] **Network configuration**: Konfiguracja komunikacji między serwisami
- [ ] **Health checks**: Dodanie monitoringu dla Perplexica
- [ ] **Environment variables**: Konfiguracja zmiennych środowiskowych

### Faza 2: Implementacja Podstawowa (2-3 tygodnie)

#### 2.1 Perplexica Provider
```python
# src/backend/agents/tools/search_providers.py
class PerplexicaSearchProvider(SearchProvider):
    """Provider for Perplexica searches with advanced features"""
    
    def __init__(self):
        super().__init__()
        self.base_url = settings.PERPLEXICA_BASE_URL
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": settings.USER_AGENT}
        )
    
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Enhanced search with Perplexica"""
        try:
            # Prepare search request
            search_request = {
                "query": query,
                "max_results": max_results,
                "providers": ["wikipedia", "duckduckgo", "searxng"],
                "focus": "comprehensive",
                "include_sources": True
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/search",
                json=search_request
            )
            response.raise_for_status()
            data = response.json()
            
            # Process and validate results
            results = []
            for result in data.get("results", []):
                if self._validate_result(result):
                    results.append({
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"],
                        "source": "perplexica",
                        "confidence": result.get("confidence", 0.8),
                        "knowledge_verified": result.get("verified", False),
                        "providers_used": result.get("providers", [])
                    })
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Perplexica search error: {e}")
            return []
    
    def _validate_result(self, result: dict) -> bool:
        """Validate search result quality"""
        required_fields = ["title", "url", "snippet"]
        return all(field in result for field in required_fields)
```

#### 2.2 Integration z SearchAgent
```python
# src/backend/agents/search_agent.py
class SearchAgent(BaseAgent):
    def __init__(self, config: dict[str, Any] | None = None, **kwargs) -> None:
        super().__init__(name="SearchAgent", **kwargs)
        self.search_providers = {
            "perplexica": PerplexicaSearchProvider(),  # Nowy provider
            "wikipedia": WikipediaSearchProvider(),
            "duck": DuckDuckGoSearchProvider(),
        }
        self.default_provider = "perplexica"  # Zmiana domyślnego providera
        # ... reszta implementacji
```

### Faza 3: Zaawansowane Funkcje (3-4 tygodnie)

#### 3.1 Multi-Provider Search
```python
# src/backend/core/multi_provider_search.py
class MultiProviderSearch:
    """Advanced multi-provider search with result aggregation"""
    
    def __init__(self):
        self.providers = {
            "perplexica": PerplexicaSearchProvider(),
            "perplexity": PerplexityClient(),
            "wikipedia": WikipediaSearchProvider(),
            "duckduckgo": DuckDuckGoSearchProvider()
        }
    
    async def search_with_aggregation(
        self, 
        query: str, 
        max_results: int = 5,
        strategy: str = "parallel"
    ) -> AggregatedSearchResponse:
        """Search across multiple providers with result aggregation"""
        
        if strategy == "parallel":
            return await self._parallel_search(query, max_results)
        elif strategy == "fallback":
            return await self._fallback_search(query, max_results)
        else:
            return await self._smart_search(query, max_results)
    
    async def _parallel_search(self, query: str, max_results: int) -> AggregatedSearchResponse:
        """Search all providers in parallel and aggregate results"""
        tasks = []
        for provider_name, provider in self.providers.items():
            task = asyncio.create_task(
                provider.search(query, max_results),
                name=f"search_{provider_name}"
            )
            tasks.append((provider_name, task))
        
        # Wait for all searches to complete
        results = {}
        for provider_name, task in tasks:
            try:
                results[provider_name] = await task
            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                results[provider_name] = []
        
        # Aggregate and rank results
        aggregated_results = self._aggregate_results(results, max_results)
        
        return AggregatedSearchResponse(
            results=aggregated_results,
            provider_results=results,
            query=query
        )
    
    def _aggregate_results(
        self, 
        provider_results: dict[str, list], 
        max_results: int
    ) -> list[dict[str, Any]]:
        """Aggregate and rank results from multiple providers"""
        all_results = []
        
        for provider_name, results in provider_results.items():
            for result in results:
                result["provider"] = provider_name
                all_results.append(result)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Rank results by confidence and provider priority
        ranked_results = sorted(
            unique_results,
            key=lambda x: (
                x.get("confidence", 0),
                self._get_provider_priority(x.get("provider", ""))
            ),
            reverse=True
        )
        
        return ranked_results[:max_results]
    
    def _get_provider_priority(self, provider: str) -> int:
        """Get provider priority for ranking"""
        priorities = {
            "perplexica": 4,  # Highest priority
            "perplexity": 3,
            "wikipedia": 2,
            "duckduckgo": 1
        }
        return priorities.get(provider, 0)
```

#### 3.2 Enhanced Caching
```python
# src/backend/core/enhanced_search_cache.py
class EnhancedSearchCache:
    """Enhanced caching with provider-specific strategies"""
    
    def __init__(self):
        self.cache = {}
        self.provider_caches = {
            "perplexica": SearchCache(ttl=3600),  # 1 hour
            "perplexity": SearchCache(ttl=1800),  # 30 minutes
            "wikipedia": SearchCache(ttl=7200),   # 2 hours
            "duckduckgo": SearchCache(ttl=900)    # 15 minutes
        }
    
    async def get_cached_results(
        self, 
        query: str, 
        provider: str
    ) -> list[dict[str, Any]] | None:
        """Get cached results for specific provider"""
        cache_key = f"{provider}:{self._normalize_query(query)}"
        return self.provider_caches[provider].get(cache_key)
    
    async def cache_results(
        self, 
        query: str, 
        provider: str, 
        results: list[dict[str, Any]]
    ) -> None:
        """Cache results for specific provider"""
        cache_key = f"{provider}:{self._normalize_query(query)}"
        self.provider_caches[provider].set(cache_key, results)
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent caching"""
        return query.lower().strip()
```

### Faza 4: Monitoring i Optymalizacja (1-2 tygodnie)

#### 4.1 Performance Monitoring
```python
# src/backend/core/search_monitoring.py
class SearchMonitoring:
    """Monitor search performance and provider health"""
    
    def __init__(self):
        self.metrics = {
            "provider_response_times": {},
            "provider_success_rates": {},
            "cache_hit_rates": {},
            "query_volumes": {}
        }
    
    async def track_search_performance(
        self, 
        provider: str, 
        query: str, 
        response_time: float, 
        success: bool
    ) -> None:
        """Track search performance metrics"""
        # Update response times
        if provider not in self.metrics["provider_response_times"]:
            self.metrics["provider_response_times"][provider] = []
        self.metrics["provider_response_times"][provider].append(response_time)
        
        # Update success rates
        if provider not in self.metrics["provider_success_rates"]:
            self.metrics["provider_success_rates"][provider] = {"success": 0, "total": 0}
        
        self.metrics["provider_success_rates"][provider]["total"] += 1
        if success:
            self.metrics["provider_success_rates"][provider]["success"] += 1
    
    def get_provider_health(self, provider: str) -> dict[str, Any]:
        """Get health metrics for specific provider"""
        response_times = self.metrics["provider_response_times"].get(provider, [])
        success_rates = self.metrics["provider_success_rates"].get(provider, {"success": 0, "total": 0})
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        success_rate = (success_rates["success"] / success_rates["total"] * 100) if success_rates["total"] > 0 else 0
        
        return {
            "provider": provider,
            "avg_response_time": avg_response_time,
            "success_rate": success_rate,
            "total_requests": success_rates["total"],
            "healthy": success_rate > 80 and avg_response_time < 5.0
        }
```

## 📊 Porównanie Rozwiązań

| Kryterium | Obecny System | Perplexica Integration | Hybrydowe Rozwiązanie |
|-----------|---------------|------------------------|----------------------|
| **Koszt** | Średni (API keys) | Niski (self-hosted) | Średni |
| **Kontrola** | Ograniczona | Pełna | Wysoka |
| **Złożoność** | Niska | Wysoka | Średnia |
| **Wydajność** | Dobra | Bardzo dobra | Doskonała |
| **Offline** | Nie | Tak | Częściowo |
| **Maintenance** | Niska | Wysoka | Średnia |

## 🎯 Rekomendacje

### Krótkoterminowe (1-2 miesiące)
1. **Implementacja Perplexica Provider**: Dodanie jako dodatkowego providera
2. **Hybrydowe wyszukiwanie**: Fallback strategy z obecnymi providerami
3. **Enhanced caching**: Provider-specific cache strategies
4. **Monitoring**: Podstawowe metryki wydajności

### Długoterminowe (3-6 miesięcy)
1. **Full Perplexica Integration**: Pełna integracja jako primary search engine
2. **Advanced Features**: Multi-provider aggregation, smart routing
3. **Offline Capability**: Lokalne wyszukiwanie bez zewnętrznych API
4. **Custom Models**: Integracja z lokalnymi modelami Ollama

## 🚀 Następne Kroki

### 1. Proof of Concept
- [ ] Uruchomienie Perplexica w kontenerze
- [ ] Testowanie API i funkcjonalności
- [ ] Benchmarking wydajności
- [ ] Analiza integracji z obecnym systemem

### 2. Implementacja Fazy 1
- [ ] Dodanie PerplexicaSearchProvider
- [ ] Integration z SearchAgent
- [ ] Podstawowe testy funkcjonalności
- [ ] Dokumentacja API

### 3. Rozwój Funkcji
- [ ] Multi-provider search
- [ ] Enhanced caching
- [ ] Performance monitoring
- [ ] Health checks

## 📝 Podsumowanie

Integracja Perplexica z FoodSave AI oferuje znaczące korzyści:

✅ **Lepsza kontrola**: Własny search engine
✅ **Redukcja kosztów**: Brak zależności od płatnych API
✅ **Większa prywatność**: Lokalne przetwarzanie
✅ **Elastyczność**: Możliwość dostosowania do specyficznych potrzeb
✅ **Offline capability**: Praca bez internetu

Zalecane podejście to **hybrydowe rozwiązanie** z Perplexica jako primary provider i obecnymi providerami jako fallback, co zapewni najlepszą równowagę między funkcjonalnością, kontrolą i złożonością utrzymania. 

## ✅ ZAKOŃCZONA INTEGRACJA WEATHER AGENT

### Implementacja Weather Support w Perplexica

Weather agent został **pomyślnie zintegrowany** z Perplexica jako moduł wyszukiwania:

#### 🔧 Zmiany Implementacyjne

1. **PerplexicaSearchProvider** - rozszerzony o weather support:
   - Automatyczne wykrywanie weather queries
   - Integracja z `/api/weather` endpoint
   - Fallback na standardowe wyszukiwanie

2. **SearchAgent** - zaktualizowany:
   - Weather keywords detection
   - Special formatting dla weather results
   - Perplexica jako primary provider

3. **Usunięcie autonomicznego WeatherAgent**:
   - Usunięty z agent_factory.py
   - Usunięty z agent_registry.py
   - Usunięty z agent_config.json
   - Weather queries obsługiwane przez PerplexicaSearchProvider

#### 🌤️ Weather API Integration

```python
# Automatyczne wykrywanie weather queries
weather_keywords = {
    "pogoda", "weather", "temperatura", "temperature", "deszcz", "rain",
    "śnieg", "snow", "wiatr", "wind", "wilgotność", "humidity", "słońce", "sun",
    "chmury", "clouds", "burza", "storm", "mgła", "fog", "grad", "hail"
}

# Weather API call
response = await self.client.post(
    f"{self.base_url}/weather",
    json={"lat": 52.2297, "lng": 21.0122}
)
```

#### 📊 Testy i Wyniki

✅ **Weather API działa**: `{"temperature":24.1,"condition":"Cloudy","humidity":54,"windSpeed":7.2,"icon":"cloudy-1-day"}`

✅ **Weather query detection**: "pogoda w warszawie" → Perplexica weather endpoint

✅ **Weather formatting**: 
```
🌤️ **Pogoda w Warszawa**

🌡️ **Temperatura:** 24.1°C
☁️ **Warunki:** Cloudy
💧 **Wilgotność:** 54%
💨 **Wiatr:** 7.2 km/h
🎯 **Ikona:** cloudy-1-day
```

✅ **Fallback strategy**: Perplexica → Wikipedia → DuckDuckGo

#### 🎯 Korzyści Integracji

1. **Uproszczenie architektury**: Jeden agent zamiast dwóch
2. **Lepsza integracja**: Weather jako część search engine
3. **Automatyczne fallback**: Jeśli weather API niedostępne, używa standardowego wyszukiwania
4. **Spójny interfejs**: Wszystkie queries przez SearchAgent
5. **Lepsze zarządzanie**: Wszystko przez GUI (opcja 11)

#### 🔧 Zarządzanie

- **GUI**: Menu główne → Zarządzaj Perplexica → Weather API test (opcja 6)
- **CLI**: `curl -X POST http://localhost:3000/api/weather -H "Content-Type: application/json" -d '{"lat": 52.2297, "lng": 21.0122}'`
- **Status**: Perplexica działa na porcie 3000 z weather support

### 🎉 Podsumowanie

Weather agent został **pomyślnie zintegrowany** z Perplexica jako moduł wyszukiwania. System automatycznie wykrywa weather queries i kieruje je do weather API, z fallbackiem na standardowe wyszukiwanie. Architektura została uproszczona, a funkcjonalność zachowana.

**Status: ✅ ZAKOŃCZONE** 

## 🎉 PODSUMOWANIE ZAKOŃCZONEJ INTEGRACJI

### ✅ Status: ZAKOŃCZONE POMYŚLNIE

Weather agent został **w pełni zintegrowany** z Perplexica jako moduł wyszukiwania. Wszystkie testy przechodzą, a funkcjonalność została zweryfikowana.

#### 🔧 Zaimplementowane Funkcje

1. **Weather Query Detection**:
   - Automatyczne wykrywanie słów kluczowych pogodowych
   - Obsługa polskich i angielskich terminów
   - Kierowanie do weather API Perplexica

2. **Weather API Integration**:
   - Integracja z `/api/weather` endpoint
   - Pobieranie danych pogodowych w czasie rzeczywistym
   - Formatowanie wyników z emoji i strukturą

3. **Fallback Strategy**:
   - Perplexica (primary) → Wikipedia → DuckDuckGo
   - Automatyczne przełączanie przy błędach
   - Zachowanie funkcjonalności wyszukiwania

4. **GUI Integration**:
   - Zarządzanie przez `gui_refactor.sh` (opcja 11)
   - Weather API test (opcja 6)
   - Status, logi, health-check

#### 📊 Testy i Weryfikacja

✅ **Weather API**: `{"temperature":24.1,"condition":"Cloudy","humidity":54,"windSpeed":7.2,"icon":"cloudy-1-day"}`

✅ **Weather Query**: "pogoda w warszawie" → Perplexica weather endpoint

✅ **Weather Formatting**: 
```
🌤️ **Pogoda w Warszawa**

🌡️ **Temperatura:** 24.1°C
☁️ **Warunki:** Cloudy
💧 **Wilgotność:** 54%
💨 **Wiatr:** 7.2 km/h
🎯 **Ikona:** cloudy-1-day
```

✅ **Fallback**: Perplexica → Wikipedia → DuckDuckGo

✅ **Testy**: 7/7 testów przechodzi

#### 🎯 Korzyści Zrealizowane

1. **Uproszczenie architektury**: Jeden agent zamiast dwóch
2. **Lepsza integracja**: Weather jako część search engine
3. **Automatyczne fallback**: Jeśli weather API niedostępne, używa standardowego wyszukiwania
4. **Spójny interfejs**: Wszystkie queries przez SearchAgent
5. **Lepsze zarządzanie**: Wszystko przez GUI (opcja 11)

#### 🔧 Zarządzanie

- **GUI**: Menu główne → Zarządzaj Perplexica → Weather API test (opcja 6)
- **CLI**: `curl -X POST http://localhost:3000/api/weather -H "Content-Type: application/json" -d '{"lat": 52.2297, "lng": 21.0122}'`
- **Status**: Perplexica działa na porcie 3000 z weather support

### 🚀 Następne Kroki

1. **Monitoring**: Dodanie metryk wydajności weather API
2. **Caching**: Implementacja cache dla weather queries
3. **Geolokalizacja**: Automatyczne wykrywanie lokalizacji użytkownika
4. **Prognozy**: Rozszerzenie o długoterminowe prognozy

### 📝 Dokumentacja

- **README.md**: Zaktualizowany o weather support
- **GUI**: Zaktualizowany o weather management
- **Testy**: Wszystkie testy przechodzą
- **Konfiguracja**: Weather keywords i API endpoints

**Status: ✅ ZAKOŃCZONE POMYŚLNIE** 