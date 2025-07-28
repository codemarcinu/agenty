# 🎯 OCR-RAG Integration Guide - FoodSave AI

## 📋 Overview

Ten przewodnik opisuje jak agenty OCR mogą wspomagać system RAG (Retrieval-Augmented Generation) w aplikacji FoodSave AI. Integracja OCR z RAG umożliwia automatyczne dodawanie przetworzonych dokumentów do bazy wiedzy, co znacznie poprawia jakość odpowiedzi AI.

## 🔍 Jak OCR Wspomaga RAG

### 1. **Automatyczne Dodawanie Dokumentów do Bazy Wiedzy**
- OCR przetwarza zeskanowane paragony, dokumenty i notatki
- Wyodrębniony tekst jest automatycznie dodawany do wektorowej bazy danych RAG
- System może później wyszukiwać i wykorzystywać te informacje

### 2. **Kontekstowe Odpowiedzi**
- Gdy użytkownik pyta o konkretne zakupy czy wydatki
- RAG może wyszukać odpowiednie paragony z bazy
- AI generuje odpowiedzi na podstawie rzeczywistych danych

### 3. **Historia Zakupów i Analiza Wydatków**
- Wszystkie przetworzone paragony są dostępne do wyszukiwania
- Można analizować trendy zakupowe
- System może odpowiadać na pytania o konkretne produkty czy sklepy

## 🏗️ Architektura Integracji

### Komponenty Systemu

#### 1. **OCRRAGIntegrationAgent** (`src/backend/agents/ocr_rag_integration_agent.py`)
```python
class OCRRAGIntegrationAgent(BaseAgent):
    """
    Agent that integrates OCR processing with RAG system.
    
    This agent:
    1. Processes images/PDFs with OCR
    2. Extracts structured data from receipts
    3. Adds extracted content to RAG knowledge base
    4. Enables future queries about shopping history
    """
```

**Kluczowe funkcjonalności:**
- ✅ Przetwarzanie plików z OCR
- ✅ Tworzenie strukturalnych dokumentów RAG
- ✅ Dodawanie do bazy wiedzy z metadanymi
- ✅ Wyszukiwanie historii paragonów
- ✅ Statystyki przetworzonych dokumentów

#### 2. **API Endpoints** (`src/backend/api/v2/endpoints/ocr_rag.py`)
```python
@router.post("/process-receipt")
@router.post("/query-history")
@router.get("/statistics")
@router.post("/demo-upload")
```

**Dostępne endpointy:**
- `/process-receipt` - Przetwarzanie paragonu z OCR i dodanie do RAG
- `/query-history` - Wyszukiwanie w historii paragonów
- `/statistics` - Statystyki przetworzonych dokumentów
- `/demo-upload` - Demo integracji OCR-RAG

## 🚀 Jak Używać Integracji OCR-RAG

### 1. **Przetwarzanie Paragonu z RAG**

```bash
# Upload paragonu z automatycznym dodaniem do RAG
curl -X POST "http://localhost:8000/api/v2/ocr-rag/process-receipt" \
  -F "file=@receipt.pdf" \
  -F "session_id=user123" \
  -F "store_name=Lidl" \
  -F "store_address=ul. Przykładowa 1, Warszawa" \
  -F "receipt_date=2025-01-25"
```

**Odpowiedź:**
```json
{
  "success": true,
  "message": "Pomyślnie przetworzono paragon receipt.pdf i dodano do bazy wiedzy",
  "data": {
    "ocr_text": "LIDL POLSKA...",
    "ocr_confidence": 0.85,
    "rag_chunks_added": 3,
    "rag_source_id": "receipt_ocr_user123_20250125_143022",
    "filename": "receipt.pdf",
    "store_info": {
      "name": "Lidl",
      "address": "ul. Przykładowa 1, Warszawa"
    },
    "receipt_date": "2025-01-25"
  }
}
```

### 2. **Wyszukiwanie w Historii Paragonów**

```bash
# Wyszukiwanie paragonów z konkretnym produktem
curl -X POST "http://localhost:8000/api/v2/ocr-rag/query-history" \
  -F "query=chleb" \
  -F "session_id=user123" \
  -F "limit=5"
```

**Odpowiedź:**
```json
{
  "success": true,
  "message": "Znaleziono 3 paragony z chlebem",
  "data": {
    "results": [
      {
        "content": "Chleb żytni 1kg - 4.50 zł",
        "metadata": {
          "store_name": "Lidl",
          "receipt_date": "2025-01-25"
        },
        "score": 0.92
      }
    ],
    "query": "chleb",
    "total_results": 3
  }
}
```

### 3. **Statystyki Przetworzonych Dokumentów**

```bash
# Pobieranie statystyk
curl "http://localhost:8000/api/v2/ocr-rag/statistics?session_id=user123"
```

**Odpowiedź:**
```json
{
  "success": true,
  "message": "Statystyki paragonów: 15 paragonów z 8 sklepów",
  "data": {
    "total_receipts": 15,
    "total_stores": 8,
    "average_ocr_confidence": 0.87,
    "date_range": {
      "from": null,
      "to": null
    },
    "session_id": "user123"
  }
}
```

## 💡 Przykłady Użycia

### 1. **Analiza Wydatków**
```
Użytkownik: "Ile wydałem na warzywa w tym miesiącu?"
System: "Na podstawie przetworzonych paragonów, wydałeś 245.30 zł na warzywa w styczniu 2025. Najczęściej kupowałeś w Lidl (120.50 zł) i Biedronka (124.80 zł)."
```

### 2. **Wyszukiwanie Produktów**
```
Użytkownik: "Gdzie kupiłem ostatnio mleko?"
System: "Ostatnio kupiłeś mleko w Lidl 23.01.2025 za 3.99 zł/l. Wcześniej kupowałeś w Biedronka 15.01.2025 za 3.79 zł/l."
```

### 3. **Trendy Zakupowe**
```
Użytkownik: "Jakie są moje ulubione sklepy?"
System: "Na podstawie historii zakupów, najczęściej robisz zakupy w Lidl (45% paragonów), Biedronka (30%), i Carrefour (25%)."
```

## 🔧 Konfiguracja i Optymalizacja

### 1. **Konfiguracja RAG**
```python
# W src/backend/core/rag_document_processor.py
class RAGDocumentProcessor:
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
    ):
```

### 2. **Optymalizacja OCR**
```python
# W src/backend/agents/ocr_rag_integration_agent.py
class OCRRAGIntegrationAgent:
    def __init__(self):
        self.ocr_agent = OCRAgent()
        self.rag_processor = RAGDocumentProcessor()
```

### 3. **Metadane dla RAG**
```python
metadata = {
    "source_type": "receipt_ocr",
    "filename": "receipt.pdf",
    "session_id": "user123",
    "store_name": "Lidl",
    "receipt_date": "2025-01-25",
    "ocr_confidence": 0.85,
    "tags": ["receipt", "ocr", "shopping", "expenses"],
    "category": "receipts"
}
```

## 📊 Korzyści Integracji OCR-RAG

### 1. **Lepsze Odpowiedzi AI**
- ✅ Kontekstowe odpowiedzi na podstawie rzeczywistych danych
- ✅ Eliminacja halucynacji AI
- ✅ Źródłowe cytowanie informacji

### 2. **Automatyczna Organizacja**
- ✅ Automatyczne kategoryzowanie paragonów
- ✅ Strukturalne metadane
- ✅ Łatwe wyszukiwanie i filtrowanie

### 3. **Analiza Wydatków**
- ✅ Trendy zakupowe
- ✅ Porównanie cen
- ✅ Historia zakupów

### 4. **Skalowalność**
- ✅ Obsługa tysięcy paragonów
- ✅ Szybkie wyszukiwanie
- ✅ Efektywne przechowywanie

## 🚀 Następne Kroki

### 1. **Rozszerzenie Funkcjonalności**
- [ ] Integracja z systemem kategoryzacji produktów
- [ ] Automatyczne wykrywanie sklepów
- [ ] Analiza trendów cenowych
- [ ] Eksport danych do analizy

### 2. **Optymalizacja Wydajności**
- [ ] Cachowanie wyników OCR
- [ ] Asynchroniczne przetwarzanie
- [ ] Kompresja embeddings
- [ ] Indeksowanie metadanych

### 3. **Interfejs Użytkownika**
- [ ] Dashboard z statystykami
- [ ] Wizualizacja trendów
- [ ] Eksport raportów
- [ ] Integracja z aplikacją mobilną

## 📝 Podsumowanie

Integracja OCR z RAG w systemie FoodSave AI zapewnia:

1. **Automatyczne przetwarzanie** paragonów i dokumentów
2. **Inteligentne wyszukiwanie** w historii zakupów
3. **Kontekstowe odpowiedzi** AI na podstawie rzeczywistych danych
4. **Analizę wydatków** i trendów zakupowych
5. **Skalowalną architekturę** dla tysięcy dokumentów

Ta integracja znacząco poprawia jakość odpowiedzi AI i umożliwia zaawansowaną analizę danych zakupowych użytkownika. 