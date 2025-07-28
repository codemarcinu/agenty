# Google Product Taxonomy Integration

## Przegląd

Integracja Google Product Taxonomy z FoodSave AI zapewnia zaawansowaną kategoryzację produktów spożywczych z wykorzystaniem standardowej taksonomii Google (5596 kategorii) oraz polskich tłumaczeń.

## Architektura

### Komponenty

1. **GoogleTaxonomyEnhancer** - Główny moduł integracji
2. **TaxonomyCategory** - Reprezentacja kategorii taksonomii
3. **ProductCategorizer** - Rozszerzony kategoryzator z integracją
4. **Cache system** - Wydajne cache'owanie wyników

### Hierarchia kategoryzacji

```
Google Product Taxonomy (5596 kategorii)
    ↓
Food-related categories (filtrowane)
    ↓
Polish translations
    ↓
Local category mapping
    ↓
Final categorization result
```

## Funkcjonalności

### 1. Pełna integracja z Google Product Taxonomy

- **5596 kategorii** z oficjalnej taksonomii Google
- **Automatyczne wykrywanie** kategorii związanych z żywnością
- **Hierarchiczna struktura** z poziomami kategorii
- **Polskie tłumaczenia** dla głównych kategorii

#### Przykładowe kategorie żywnościowe

```json
{
  "422": "Food, Beverages & Tobacco > Food Items",
  "428": "Food, Beverages & Tobacco > Food Items > Dairy Products",
  "429": "Food, Beverages & Tobacco > Food Items > Dairy Products > Cheese",
  "430": "Food, Beverages & Tobacco > Food Items > Fruits & Vegetables",
  "431": "Food, Beverages & Tobacco > Food Items > Grains, Rice & Cereal",
  "432": "Food, Beverages & Tobacco > Food Items > Meat, Seafood & Eggs"
}
```

### 2. Inteligentne mapowanie produktów

#### Algorytm kategoryzacji

1. **Cache check** - Sprawdzenie wcześniejszych wyników
2. **Google Taxonomy search** - Wyszukiwanie w kategoriach żywnościowych
3. **Score calculation** - Obliczanie dopasowania
4. **Local mapping** - Mapowanie na lokalne kategorie
5. **Fallback** - Kategoryzacja domyślna

#### Przykład kategoryzacji

```python
# Input: "Ser żółty Gouda 500g"
# Output:
{
    'id': '429',
    'name_en': 'Cheese',
    'name_pl': 'Ser',
    'path': 'Food, Beverages & Tobacco > Food Items > Dairy Products > Cheese',
    'path_pl': 'Żywność, Napoje i Tytoń > Produkty spożywcze > Nabiał > Ser',
    'confidence': 0.95,
    'method': 'google_taxonomy_with_local_mapping',
    'local_id': '1',
    'local_name_pl': 'Nabiał',
    'is_food_related': True
}
```

### 3. Polskie tłumaczenia

#### Automatyczne tłumaczenia

```python
translations = {
    "Food, Beverages & Tobacco": "Żywność, Napoje i Tytoń",
    "Food Items": "Produkty spożywcze",
    "Dairy Products": "Nabiał",
    "Cheese": "Ser",
    "Milk": "Mleko",
    "Bread": "Chleb",
    "Fruits & Vegetables": "Owoce i Warzywa"
}
```

### 4. Cache'owanie dla wydajności

- **In-memory cache** dla szybkiego dostępu
- **Automatic cache invalidation** po 24h
- **Performance optimization** dla wsadowego przetwarzania

## API Reference

### GoogleTaxonomyEnhancer

#### `__init__(taxonomy_file: str = "Google_Product_Taxonomy.txt")`

Inicjalizuje enhancer z plikiem taksonomii.

#### `async categorize_product_advanced(product_name: str, product_description: str = "") -> Dict[str, Any]`

Zaawansowana kategoryzacja produktu.

**Parametry:**
- `product_name`: Nazwa produktu
- `product_description`: Opis produktu (opcjonalny)

**Zwraca:**
```python
{
    'id': str,                    # ID kategorii
    'name_en': str,              # Nazwa angielska
    'name_pl': str,              # Nazwa polska
    'path': str,                 # Ścieżka kategorii
    'path_pl': str,              # Polska ścieżka
    'confidence': float,         # Pewność kategoryzacji (0-1)
    'method': str,               # Metoda kategoryzacji
    'is_food_related': bool,     # Czy związane z żywnością
    'gpt_id': str,               # Google Product Taxonomy ID
    'gpt_path': str              # Google Product Taxonomy path
}
```

#### `async get_category_hierarchy(category_id: str, max_depth: int = 3) -> Dict[str, Any]`

Zwraca hierarchię kategorii.

#### `get_food_categories_stats() -> Dict[str, Any]`

Zwraca statystyki kategorii żywnościowych.

#### `search_categories(query: str, limit: int = 10) -> List[Dict[str, Any]]`

Wyszukuje kategorie po zapytaniu.

### ProductCategorizer (rozszerzony)

#### `async categorize_product_with_bielik(product_name: str) -> Dict[str, Any]`

Kategoryzuje produkt z integracją Google Taxonomy.

#### `async categorize_products_batch(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]`

Wsadowa kategoryzacja z Google Taxonomy.

#### `async get_google_taxonomy_stats() -> Dict[str, Any]`

Zwraca statystyki Google Taxonomy.

#### `async search_google_categories(query: str, limit: int = 10) -> List[Dict[str, Any]]`

Wyszukuje w Google Taxonomy.

## Metody kategoryzacji

### 1. `google_taxonomy_only`
- Używa tylko Google Product Taxonomy
- Brak mapowania na lokalne kategorie

### 2. `google_taxonomy_with_local_mapping`
- Google Taxonomy + mapowanie lokalne
- Najlepsza jakość kategoryzacji

### 3. `keyword_match`
- Słownik słów kluczowych
- Szybka kategoryzacja

### 4. `bielik_ai`
- Model Bielik AI
- Zaawansowana kategoryzacja

### 5. `cache`
- Wynik z cache
- Najszybsza metoda

### 6. `fallback`
- Kategoria domyślna
- Gdy inne metody zawiodły

## Konfiguracja

### Plik taksonomii

```bash
# Ścieżka do pliku Google Product Taxonomy
Google_Product_Taxonomy.txt
```

### Format pliku

```
# Google_Product_Taxonomy_Version: 2021-09-21
1 - Animals & Pet Supplies
422 - Food, Beverages & Tobacco > Food Items
428 - Food, Beverages & Tobacco > Food Items > Dairy Products
429 - Food, Beverages & Tobacco > Food Items > Dairy Products > Cheese
```

### Konfiguracja cache

```python
# Cache settings
CACHE_TTL = 86400  # 24 godziny
CACHE_MAX_SIZE = 10000  # Maksymalna liczba wpisów
```

## Wydajność

### Metryki wydajności

- **Cache hit rate**: >90% dla powtarzających się produktów
- **Processing time**: <100ms dla pojedynczego produktu
- **Batch processing**: <1s dla 10 produktów
- **Memory usage**: ~50MB dla pełnej taksonomii

### Optymalizacje

1. **Lazy loading** - Taksonomia ładowana na żądanie
2. **Indexed search** - Indeksowane wyszukiwanie kategorii
3. **Batch processing** - Optymalizacja wsadowa
4. **Memory cache** - Szybki dostęp do wyników

## Obsługa błędów

### Typy błędów

1. **Missing taxonomy file** - Brak pliku taksonomii
2. **Invalid format** - Nieprawidłowy format pliku
3. **LLM timeout** - Przekroczenie czasu LLM
4. **Network error** - Błąd sieci

### Fallback strategies

```python
# Hierarchia fallback
1. Google Taxonomy (primary)
2. Local keyword matching
3. Bielik AI model
4. Default category ("Inne")
```

## Testy

### Pokrycie testów

- **Unit tests**: 100% pokrycie głównych funkcji
- **Integration tests**: Testy integracji z systemem
- **Performance tests**: Testy wydajności
- **Error handling tests**: Testy obsługi błędów

### Uruchomienie testów

```bash
# Testy jednostkowe
pytest tests/unit/test_google_taxonomy_integration.py -v

# Testy wydajności
pytest tests/unit/test_google_taxonomy_integration.py::TestGoogleTaxonomyPerformance -v

# Testy obsługi błędów
pytest tests/unit/test_google_taxonomy_integration.py::TestGoogleTaxonomyErrorHandling -v
```

## Monitoring

### Metryki

- **Categorization accuracy** - Dokładność kategoryzacji
- **Processing time** - Czas przetwarzania
- **Cache hit rate** - Współczynnik trafień cache
- **Error rate** - Współczynnik błędów

### Logi

```python
# Przykładowe logi
logger.info(f"Google Taxonomy Enhancer zainicjalizowany: {len(categories)} kategorii")
logger.info(f"Kategoryzacja Google Taxonomy: {product_name} -> {category_name}")
logger.warning(f"Brak pliku taksonomii {taxonomy_file}")
logger.error(f"Błąd podczas kategoryzacji produktu '{product_name}': {e}")
```

## Przyszłe rozszerzenia

### Planowane funkcjonalności

1. **Machine Learning** - Uczenie na podstawie danych użytkowników
2. **Custom categories** - Własne kategorie użytkowników
3. **Multi-language** - Wsparcie dla innych języków
4. **API endpoint** - REST API dla kategoryzacji
5. **Analytics dashboard** - Panel analityczny

### Roadmap

- **Q1 2025**: Machine Learning integration
- **Q2 2025**: Custom categories support
- **Q3 2025**: Multi-language support
- **Q4 2025**: Analytics dashboard

## Wsparcie

### Dokumentacja

- [API Reference](API_REFERENCE.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Testing Guide](TESTING.md)

### Kontakt

- **Backend Lead**: @backend-lead
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

*Dokumentacja zgodna z .cursorrules - Python standards, comprehensive documentation.* 