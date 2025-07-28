# Receipt Analysis System Guide

## Overview

The receipt analysis system provides advanced OCR and structured data extraction from Polish grocery receipts with intelligent categorization using Bielik AI models and Google Product Taxonomy.

## Architecture

### Components

1. **OCRAgent** - Extracts text from receipt images
2. **ReceiptAnalysisAgent** - Analyzes OCR text and extracts structured data
3. **ProductCategorizer** - Categorizes products using Bielik + Google Product Taxonomy
4. **StoreNormalizer** - Normalizes store names using Polish store dictionary
5. **ProductNameNormalizer** - Normalizes product names using product dictionary

### Data Flow

```
Receipt Image → OCRAgent → ReceiptAnalysisAgent → Structured Data
                                    ↓
                            ProductCategorizer (Bielik + GPT)
                            StoreNormalizer
                            ProductNameNormalizer
```

## Features

### 1. Intelligent Product Categorization

Uses a hybrid approach combining:
- **Bielik AI Model** for intelligent categorization
- **Google Product Taxonomy** for standardized categories
- **Keyword matching** for fast categorization
- **Fallback mechanisms** for unknown products

#### Categories Available

35 FMCG categories including:
- **Nabiał** (Dairy Products)
- **Pieczywo** (Bread & Bakery)
- **Mięso** (Meat & Seafood)
- **Owoce i warzywa** (Fruits & Vegetables)
- **Napoje** (Beverages)
- **Słodycze** (Candy & Chocolate)
- **Chemia domowa** (Household Supplies)
- **Kosmetyki** (Personal Care)

#### Example Categorization

```json
{
  "name": "Mleko 3.2% 1L",
  "category": "Nabiał > Mleko i śmietana",
  "category_en": "Dairy Products > Milk & Cream",
  "gpt_category": "Food, Beverages & Tobacco > Food Items > Dairy Products > Milk & Cream",
  "category_confidence": 0.9,
  "category_method": "bielik_ai"
}
```

### 2. Store Name Normalization

Normalizes store names using a comprehensive dictionary of 40+ Polish stores:

#### Store Types Supported
- **Discount stores**: Biedronka, Lidl, Aldi, Netto
- **Hypermarkets**: Carrefour, Tesco, Auchan, Kaufland
- **Convenience stores**: Żabka, ABC, Delikatesy Centrum
- **Gas stations**: Orlen, BP, Shell, Circle K
- **Drugstores**: Rossmann, Hebe, Super-Pharm
- **Electronics**: Media Markt, Saturn, RTV Euro AGD

#### Example Normalization

```json
{
  "store_name": "BIEDRONKA Sp. z o.o.",
  "normalized_store_name": "Biedronka",
  "store_chain": "Biedronka",
  "store_type": "discount_store",
  "store_confidence": 1.0,
  "store_normalization_method": "exact_match"
}
```

### 3. Product Name Normalization

Standardizes product names using a dictionary of 100+ common products:

#### Normalization Features
- Removes quantity suffixes (kg, l, szt, etc.)
- Handles Polish diacritics and variations
- Supports fuzzy matching for similar names
- Fallback to original names when no match found

#### Example Normalization

```json
{
  "original_name": "ser żółty 0.5kg",
  "normalized_name": "Ser żółty",
  "product_category": "dairy",
  "normalization_confidence": 0.8,
  "normalization_method": "keyword_match"
}
```

## API Endpoints

### Upload Receipt

```http
POST /api/v2/receipts/upload
Content-Type: multipart/form-data

file: [receipt_image]
```

**Response:**
```json
{
  "status_code": 200,
  "message": "Receipt processed successfully",
  "data": {
    "text": "Extracted OCR text",
    "message": "Pomyślnie wyodrębniono tekst z pliku",
    "metadata": {
      "file_type": "image",
      "prompts_applied": true
    }
  }
}
```

### Analyze Receipt

```http
POST /api/v2/receipts/analyze
Content-Type: application/x-www-form-urlencoded

ocr_text: [extracted_text]
```

**Response:**
```json
{
  "status_code": 200,
  "message": "Receipt analyzed successfully",
  "data": {
    "store_name": "BIEDRONKA",
    "normalized_store_name": "Biedronka",
    "store_chain": "Biedronka",
    "store_type": "discount_store",
    "store_confidence": 1.0,
    "date": "2025-06-15 00:00",
    "items": [
      {
        "name": "Mleko 3.2% 1L",
        "normalized_name": "Mleko 3.2% 1L",
        "quantity": 1.0,
        "unit_price": 4.99,
        "total_price": 4.99,
        "category": "Nabiał > Mleko i śmietana",
        "category_en": "Dairy Products > Milk & Cream",
        "gpt_category": "Food, Beverages & Tobacco > Food Items > Dairy Products > Milk & Cream",
        "category_confidence": 0.9,
        "category_method": "bielik_ai"
      }
    ],
    "total_amount": 4.99,
    "discounts": [],
    "coupons": [],
    "vat_summary": [...]
  }
}
```

## Configuration Files

### 1. Google Product Taxonomy Categories

**File:** `data/config/filtered_gpt_categories.json`

Contains 35 FMCG categories filtered from Google Product Taxonomy with Polish translations and keywords.

### 2. Polish Stores Dictionary

**File:** `data/config/polish_stores.json`

Contains 40+ Polish stores with normalized names, variations, and metadata.

### 3. Product Name Normalization

**File:** `data/config/product_name_normalization.json`

Contains 100+ product normalization rules with keywords and categories.

## Implementation Classes

### ProductCategorizer

```python
from backend.core.product_categorizer import ProductCategorizer

categorizer = ProductCategorizer()

# Categorize single product
category_info = await categorizer.categorize_product_with_bielik("Mleko 3.2%")

# Categorize batch of products
categorized_products = await categorizer.categorize_products_batch(products)
```

### StoreNormalizer

```python
from backend.core.store_normalizer import StoreNormalizer

normalizer = StoreNormalizer()

# Normalize store name
store_info = normalizer.normalize_store_name("BIEDRONKA Sp. z o.o.")

# Normalize batch of stores
normalized_stores = normalizer.normalize_stores_batch(store_names)
```

### ProductNameNormalizer

```python
from backend.core.product_name_normalizer import ProductNameNormalizer

normalizer = ProductNameNormalizer()

# Normalize product name
product_info = normalizer.normalize_product_name("ser żółty 0.5kg")

# Normalize batch of products
normalized_products = normalizer.normalize_products_batch(products)
```

## Bielik Model Integration

### Models Used

1. **Bielik 4.5b v3.0** - Product categorization
2. **Bielik 11b v2.3** - Receipt analysis

### Prompt Engineering

#### Product Categorization Prompt

```
Przypisz produkt do odpowiedniej kategorii.

Dostępne kategorie:
1. Nabiał > Mleko i śmietana (Dairy Products > Milk & Cream)
2. Nabiał > Sery (Dairy Products > Cheese)
...

Produkt: "Mleko 3.2% 1L"

Odpowiedz tylko numerem kategorii (np. "1" dla Nabiał, "35" dla Inne).
```

#### Receipt Analysis Prompt

```
Analizuj poniższy tekst paragonu i wypisz wynik w JSON:

{ocr_text}

Wyjście ma mieć dokładnie taką strukturę:
{
  "store": "",
  "address": "",
  "date": "",
  "items": [...],
  "total": 0.0
}
```

## Error Handling

### Fallback Mechanisms

1. **Product Categorization**
   - Keyword matching → Bielik AI → "Inne" category
   - Confidence thresholds for each method

2. **Store Normalization**
   - Exact match → Partial match → Fuzzy match → "Nieznany sklep"
   - Handles missing store names

3. **Product Name Normalization**
   - Exact match → Keyword match → Fuzzy match → Original name
   - Preserves original names when no match found

### Confidence Scoring

- **1.0** - Exact match
- **0.8-0.9** - High confidence (Bielik AI)
- **0.6-0.7** - Medium confidence (Partial/Fuzzy match)
- **0.1-0.5** - Low confidence (Fallback)
- **0.0** - Unknown/Error

## Performance Considerations

### Caching

- Product categorization results cached
- Store normalization cached
- Product name normalization cached

### Batch Processing

- Supports batch categorization for multiple products
- Reduces API calls to Bielik models
- Improves overall performance

### Model Selection

- Automatic model selection based on task complexity
- Fallback to smaller models if larger ones unavailable
- Graceful degradation when models are down

## Monitoring and Logging

### Metrics Tracked

- Categorization accuracy
- Normalization success rates
- Model response times
- Error rates by method

### Log Examples

```
INFO: Dokładne dopasowanie sklepu: BIEDRONKA -> Biedronka
INFO: Kategoryzacja Bielik: Mleko 3.2% -> Nabiał > Mleko i śmietana
INFO: Statystyki kategoryzacji: {'Nabiał': 3, 'Pieczywo': 2, 'Inne': 1}
```

## Future Enhancements

### Planned Features

1. **Machine Learning Training**
   - Train custom models on Polish receipt data
   - Improve categorization accuracy

2. **Dynamic Dictionaries**
   - Auto-update store and product dictionaries
   - Learn from user corrections

3. **Multi-language Support**
   - Support for other European languages
   - Localized taxonomies

4. **Advanced Analytics**
   - Spending pattern analysis
   - Nutritional information extraction
   - Budget tracking integration

## Troubleshooting

### Common Issues

1. **Model Not Available**
   - Check if Bielik models are loaded in Ollama
   - Verify model names in configuration

2. **Low Categorization Accuracy**
   - Review product names in normalization dictionary
   - Check Bielik model responses

3. **Store Not Recognized**
   - Add store to `polish_stores.json`
   - Check store name variations

### Debug Mode

Enable debug logging to see detailed categorization process:

```python
import logging
logging.getLogger('backend.core.product_categorizer').setLevel(logging.DEBUG)
logging.getLogger('backend.core.store_normalizer').setLevel(logging.DEBUG)
logging.getLogger('backend.core.product_name_normalizer').setLevel(logging.DEBUG)
``` 