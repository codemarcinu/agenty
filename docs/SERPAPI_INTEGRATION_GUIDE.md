# 🔍 SerpAPI Integration Guide

## Przegląd

SerpAPI został zintegrowany z systemem FoodSave AI, aby zapewnić wysokojakościowe wyniki wyszukiwania Google z zaawansowanymi funkcjami.

## Funkcjonalności

### 🎯 Typy wyszukiwania
- **Organiczne wyniki** - standardowe wyniki Google
- **Answer Box** - bezpośrednie odpowiedzi Google
- **Knowledge Graph** - graf wiedzy Google  
- **Featured Snippets** - fragmenty wyróżnione
- **Related Questions** - powiązane pytania (People Also Ask)
- **Wyszukiwanie obrazów** - Google Images
- **Wyszukiwanie wiadomości** - Google News

### 📊 Ocena jakości
- Automatyczna ocena wiarygodności źródeł
- Wskaźniki pewności na podstawie pozycji i domeny
- Priorytet dla zaufanych źródeł (Wikipedia, .gov, .edu)

## Konfiguracja

### 1. Uzyskanie klucza API

1. Zarejestruj się na [serpapi.com](https://serpapi.com/)
2. Uzyskaj darmowy klucz API (100 zapytań/miesiąc)
3. Dla większego użycia rozważ płatny plan

### 2. Konfiguracja środowiska

Dodaj do `config/environments/backend.env`:

```bash
# SerpAPI Configuration
SERPAPI_API_KEY=your_api_key_here
SERPAPI_ENABLED=true
SERPAPI_ENGINE=google
SERPAPI_LOCATION=Poland
SERPAPI_LANGUAGE=pl
```

### 3. Zmienne konfiguracyjne

| Zmienna | Opis | Domyślna wartość |
|---------|------|------------------|
| `SERPAPI_API_KEY` | Klucz API SerpAPI | `""` |
| `SERPAPI_ENABLED` | Włącz/wyłącz SerpAPI | `false` |
| `SERPAPI_ENGINE` | Silnik wyszukiwania | `"google"` |
| `SERPAPI_LOCATION` | Lokalizacja wyszukiwania | `"Poland"` |
| `SERPAPI_LANGUAGE` | Język wyników | `"pl"` |

## Użycie

### Automatyczny wybór providera

Agent automatycznie wybiera SerpAPI dla zapytań wysokiej jakości:

```python
# Te zapytania automatycznie używają SerpAPI (jeśli włączony)
"aktualności AI"
"najnowsze wiadomości"
"definicja machine learning"
"firma OpenAI"
```

### Wymuszone użycie SerpAPI

```python
# Bezpośrednie użycie SerpAPI
"serpapi:Python programming"
"google:machine learning"
```

### Wyszukiwanie specjalistyczne

```python
# Wyszukiwanie obrazów
"obrazy koty"
"images cats"

# Wyszukiwanie wiadomości  
"wiadomości technologia"
"news technology"
```

## Przykłady integracji

### Podstawowe wyszukiwanie

```python
from agents.search_agent import SearchAgent

agent = SearchAgent()

# Zapytanie wysokiej jakości - automatycznie użyje SerpAPI
response = await agent.process({
    "query": "aktualności sztuczna inteligencja",
    "max_results": 5
})

print(response.text)
```

### Bezpośrednie użycie SerpAPI

```python
from agents.tools.search_providers import SerpAPISearchProvider

provider = SerpAPISearchProvider()

if provider.is_enabled():
    # Standardowe wyszukiwanie
    results = await provider.search("Python programming")
    
    # Wyszukiwanie obrazów
    images = await provider.search_images("cats")
    
    # Wyszukiwanie wiadomości
    news = await provider.search_news("technology")
```

## Typy wyników

### Answer Box
```json
{
    "title": "Odpowiedź Google",
    "snippet": "Bezpośrednia odpowiedź na pytanie",
    "result_type": "answer_box",
    "confidence": 0.95
}
```

### Knowledge Graph
```json
{
    "title": "Wiedza Google",
    "snippet": "Informacje z grafu wiedzy",
    "result_type": "knowledge_graph", 
    "confidence": 0.90,
    "kgmid": "/m/123abc"
}
```

### Featured Snippet
```json
{
    "title": "Fragment wyróżniony",
    "snippet": "Wyróżniony fragment tekstu",
    "result_type": "featured_snippet",
    "confidence": 0.92
}
```

## Formatowanie wyników

Agent automatycznie formatuje różne typy wyników z odpowiednimi ikonami:

- 📋 **Answer Box** - Odpowiedzi Google
- 🧠 **Knowledge Graph** - Wiedza Google  
- ⭐ **Featured Snippet** - Fragment wyróżniony
- 📰 **News** - Wiadomości z datą i źródłem
- 🖼️ **Images** - Obrazy z wymiarami

## Monitoring i limity

### Sprawdzanie limitów

```python
from agents.tools.search_providers import SerpAPISearchProvider

provider = SerpAPISearchProvider()
print(f"SerpAPI enabled: {provider.is_enabled()}")
```

### Śledzenie użycia

Agent automatycznie śledzi:
- Liczbę zapytań SerpAPI
- Czas odpowiedzi
- Współczynnik sukcesu
- Wykorzystanie cache

## Troubleshooting

### Problem: SerpAPI nie działa

1. **Sprawdź konfigurację:**
   ```bash
   echo $SERPAPI_API_KEY
   echo $SERPAPI_ENABLED
   ```

2. **Sprawdź limity:**
   - Darmowy plan: 100 zapytań/miesiąc
   - Sprawdź dashboard SerpAPI

3. **Sprawdź logi:**
   ```bash
   docker logs foodsave-backend | grep -i serpapi
   ```

### Problem: Niska jakość wyników

1. **Sprawdź ustawienia lokalizacji:**
   ```bash
   SERPAPI_LOCATION=Poland
   SERPAPI_LANGUAGE=pl
   ```

2. **Użyj specyficznych zapytań:**
   ```python
   "serpapi:exact query here"
   ```

### Problem: Błędy autoryzacji

1. **Sprawdź klucz API:**
   - Logowanie na serpapi.com
   - Sprawdź czy klucz jest aktywny
   - Sprawdź limity konta

## Fallback Strategy

Jeśli SerpAPI nie jest dostępny, agent automatycznie przełącza się na:

1. **Perplexica** - dla zapytań ogólnych
2. **Wikipedia** - dla zapytań encyklopedycznych  
3. **DuckDuckGo** - dla zapytań podstawowych

## Przykłady zapytań

### Wysokiej jakości (automatycznie SerpAPI)
- "aktualności sztuczna inteligencja"
- "definicja blockchain"
- "firma Tesla najnowsze wiadomości"
- "current AI developments"

### Wymuszone SerpAPI
- "google:Python best practices"
- "serpapi:machine learning frameworks"

### Specjalistyczne
- "obrazy artificial intelligence" (obrazy)
- "wiadomości technologia 2025" (news)

## Testowanie

Uruchom test integracji:

```bash
cd /path/to/project
python test_serpapi_integration.py
```

Test sprawdzi:
- ✅ Konfigurację SerpAPI
- ✅ Bezpośrednie działanie providera  
- ✅ Integrację z SearchAgent
- ✅ Logikę wyboru providerów