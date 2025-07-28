# 🔧 AUTOMATYCZNA CHECKLISTA NAPRAW BŁĘDÓW TESTÓW

**Data utworzenia:** 2025-07-07 16:30  
**Status:** W TRAKCIE WYKONYWANIA  
**Priorytet:** KRYTYCZNY

---

## 📋 OGÓLNY PLAN NAPRAW

### **PRIORYTET 1 - BŁĘDY KRYTYCZNE (NAPRAWIONE ✅)**
- [x] **1.1** Naprawić AttributeError w testach RAG/vector store
- [x] **1.2** Naprawić błędy fallback/cache w testach search agent
- [x] **1.3** Naprawić flow agentów/modeli w testach integracyjnych

### **PRIORYTET 2 - BŁĘDY WAŻNE (W TRAKCIE)**
- [ ] **2.1** Naprawić błędy OpenAPI schema (ForwardRef)
- [ ] **2.2** Naprawić błędy OCR i preprocessing
- [ ] **2.3** Naprawić błędy HybridLLMClient
- [ ] **2.4** Naprawić błędy bazy danych (name resolution)

### **PRIORYTET 3 - BŁĘDY ŚREDNIE**
- [ ] **3.1** Naprawić błędy ResponseLengthConfig
- [ ] **3.2** Naprawić błędy PerformanceMonitoring
- [ ] **3.3** Naprawić błędy ErrorHandling

---

## 🔍 SZCZEGÓŁOWA ANALIZA BŁĘDÓW

### **1. RAG/Vector Store (NAPRAWIONE ✅)**
**Status:** Wszystkie testy RAG przechodzą
**Naprawy:** 
- ✅ Naprawiono testy orchestrator
- ✅ Naprawiono testy search agent
- ✅ Naprawiono testy integracyjne

### **2. OpenAPI Schema (BŁĄD KRYTYCZNY)**
**Problem:** ForwardRef w schematach Pydantic
**Lokalizacja:** `tests/contract/test_openapi_schema.py`
**Błąd:** `TypeAdapter[typing.Annotated[ForwardRef('shopping_schemas.ShoppingTripCreate'), Body(PydanticUndefined)]]`
**Naprawy:**
- [x] Dodano `from __future__ import annotations`
- [x] Zmieniono `list[ProductCreate]` na `list["ProductCreate"]`
- [x] Dodano `model_rebuild()`
- [ ] **POTRZEBNE:** Naprawić `Body(...)` w API endpoints

### **3. OCR i Preprocessing (BŁĄD WAŻNY)**
**Problem:** Brakujące metody w OCRProcessor
**Lokalizacja:** `tests/unit/test_ocr_advanced_preprocessing.py`
**Błędy:**
- `AttributeError: 'OCRProcessor' object has no attribute '_correct_perspective'`
- `AttributeError: 'OCRProcessor' object has no attribute '_apply_adaptive_thresholding'`
- `AttributeError: 'OCRProcessor' object has no attribute '_enhance_contrast'`

### **4. HybridLLMClient (BŁĄD WAŻNY)**
**Problem:** Niepoprawne mocki i asercje
**Lokalizacja:** `tests/unit/test_hybrid_llm_client.py`
**Błędy:**
- `AssertionError: assert <MagicMock> == 'Remote response'`
- `AssertionError: assert 'user' == 'system'`

### **5. Baza danych (BŁĄD KRYTYCZNY)**
**Problem:** Network connectivity
**Błąd:** `socket.gaierror: [Errno -3] Temporary failure in name resolution`
**Wpływa na:** testy entity_extraction

---

## 🛠️ NASTĘPNE KROKI

### **KROK 1: Naprawić OpenAPI Schema**
1. Sprawdzić wszystkie użycia `Body(...)` w API
2. Naprawić ForwardRef w schematach
3. Przetestować OpenAPI schema

### **KROK 2: Naprawić OCR**
1. Dodać brakujące metody do OCRProcessor
2. Naprawić konfigurację Tesseract
3. Przetestować preprocessing

### **KROK 3: Naprawić HybridLLMClient**
1. Poprawić mocki w testach
2. Naprawić asercje
3. Przetestować fallback

### **KROK 4: Naprawić bazy danych**
1. Sprawdzić konfigurację bazy danych
2. Naprawić network connectivity
3. Przetestować entity extraction

---

## 📊 POSTĘP

**Zaliczonych testów:** 355/412 (86.2%)
**Błędów:** 49
**Ostrzeżeń:** 68
**Status:** W TRAKCIE NAPRAW

---

**Ostatnia aktualizacja:** 2025-07-07 16:45 