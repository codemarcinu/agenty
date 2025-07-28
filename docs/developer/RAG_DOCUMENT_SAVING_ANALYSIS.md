# Analiza Problemów z Zapisywaniem Dokumentów RAG

## Problem
Dokumenty uploadowane przez API RAG nie są zapisywane w vector store. Vector store pozostaje pusty (total_documents: 0) mimo że dokumenty są przetwarzane.

## Zidentyfikowane Problemy

### 1. Problem z Embedding Generation
**Problem**: Embedding nie może być wygenerowany, ponieważ Ollama nie jest dostępny.
**Rozwiązanie**: ✅ Naprawiono - zmieniono `auto_embed=False` na `auto_embed=True` w `VectorStore.add_document()`

### 2. Problem z Vector Store Initialization
**Problem**: `rag_document_processor` tworzył nowy vector store zamiast używać globalnego.
**Rozwiązanie**: ✅ Naprawiono - zmieniono na używanie globalnego `vector_store`

### 3. Problem z Background Task Processing
**Problem**: Background task nie jest wykonywany lub nie ma dostępu do zaktualizowanego kodu.
**Status**: 🔄 W trakcie analizy

## Rozwiązania Zaimplementowane

### 1. Naprawienie Embedding Generation
```python
# W src/backend/core/vector_store.py
async def add_document(
    self, text: str, metadata: dict[str, Any], auto_embed: bool = True  # Zmieniono z False na True
) -> None:
```

### 2. Naprawienie Vector Store Usage
```python
# W src/backend/core/rag_document_processor.py
# Zmieniono z tworzenia nowego vector store na używanie globalnego
from backend.core.vector_store import vector_store as global_vector_store
self.vector_store = global_vector_store
```

### 3. Dodanie Metody add_document do EnhancedVectorStoreGPU
```python
# W src/backend/core/faiss_gpu_service.py
async def add_document(self, text: str, metadata: dict[str, Any], auto_embed: bool = False) -> None:
    """Add a single document to GPU vector store"""
    # Implementacja z automatycznym generowaniem embeddingu
```

## Testy i Wyniki

### Test Vector Store (✅ UDANY)
```bash
python test_vector_store.py
```
**Wynik**: 
- ✅ Dokument przetworzony (1 chunk)
- ✅ Dokument dodany do vector store (total_documents: 1)
- ✅ Embedding wygenerowany (dimension: 384)
- ✅ Wyszukiwanie znalazło dokument
- ✅ Indeks zapisany

### Test Backend Startup (✅ UDANY)
```bash
python test_backend_startup.py
```
**Wynik**: Wszystkie importy działają poprawnie

### Test API Upload (🔄 W TRAKCIE)
```bash
curl -X POST http://localhost:8000/api/v2/rag/upload -F "file=@test_document.txt"
```
**Status**: Upload akceptowany, ale dokumenty nie pojawiają się w vector store

## Pozostałe Problemy do Rozwiązania

### 1. Background Task Processing
**Problem**: Background task nie jest wykonywany lub nie ma dostępu do zaktualizowanego kodu.
**Możliwe przyczyny**:
- Backend nie został zrestartowany po zmianach
- Background task nie ma dostępu do globalnego vector store
- Problem z asyncio event loop w background task

### 2. Vector Store Persistence
**Problem**: Dokumenty mogą być dodawane do pamięci, ale nie zapisywane na dysk.
**Rozwiązanie**: Sprawdzić czy `save_index_async()` jest wywoływane

## Następne Kroki

1. **Zrestartować backend** z `reload=True` aby załadować zmiany
2. **Sprawdzić logi background task** aby zobaczyć czy są wykonywane
3. **Przetestować upload dokumentu** po restarcie
4. **Sprawdzić czy vector store jest zapisywany** na dysk

## Komendy do Debugowania

```bash
# Sprawdzenie czy backend odpowiada
curl -X GET http://localhost:8000/health

# Sprawdzenie statystyk vector store
curl -X GET http://localhost:8000/api/v2/rag/stats

# Upload dokumentu
curl -X POST http://localhost:8000/api/v2/rag/upload -F "file=@test_document.txt"

# Sprawdzenie logów
tail -f logs/backend.log | grep -E "(background|processing|document|RAG)"
```

## Status
- ✅ Embedding generation naprawione
- ✅ Vector store initialization naprawione
- 🔄 Background task processing - w trakcie analizy
- 🔄 Vector store persistence - do sprawdzenia 