# Flow Dodawania Paragonów w Czacie - Implementacja

## Przegląd

Zaimplementowano kompletny flow dodawania paragonów z poziomu czatu zgodnie z wymaganiami:

1. **Załączanie paragonu** - Upload pliku przez przycisk załącznika w czacie
2. **Generacja OCR** - Asynchroniczne przetwarzanie z progress bar
3. **Przetwarzanie przez agenta** - Analiza strukturalna danych
4. **Edycja w tabeli** - Edytowalna tabela z możliwością modyfikacji
5. **Zatwierdzenie** - Przycisk zapisu z walidacją
6. **Zapis do bazy** - Zapisywanie danych do SQLite

## Komponenty

### 1. ChatReceiptProcessor
**Plik:** `myappassistant-chat-frontend/src/components/chat/ChatReceiptProcessor.tsx`

Główny komponent obsługujący cały flow przetwarzania paragonów w czacie:

- **Stany:** `upload` → `processing` → `editing` → `saving` → `complete`/`error`
- **Polling:** Automatyczne sprawdzanie statusu zadania co 2 sekundy
- **Konwersja danych:** Transformacja wyników analizy na format ReceiptData
- **Obsługa błędów:** Retry mechanism i komunikaty błędów

### 2. ChatWindow (Zaktualizowany)
**Plik:** `myappassistant-chat-frontend/src/components/chat/ChatWindow.tsx`

Zaktualizowany komponent czatu z integracją procesora paragonów:

- **Wykrywanie typów plików:** Automatyczne rozpoznawanie paragonów (obrazy/PDF)
- **Integracja z procesorem:** Wyświetlanie ChatReceiptProcessor w wiadomościach
- **Komunikaty:** Automatyczne dodawanie wiadomości o statusie przetwarzania
- **Blokowanie UI:** Wyłączanie input podczas przetwarzania

### 3. ReceiptDataTable (Zaktualizowany)
**Plik:** `myappassistant-chat-frontend/src/components/chat/ReceiptDataTable.tsx`

Kompaktowa tabela do edycji danych paragonu:

- **Inline editing:** Kliknięcie do edycji pól
- **DatePicker:** Kompaktowy wybór dat przydatności
- **Kategorie:** Kolorowe badge'y z możliwością edycji
- **Responsywny design:** Dostosowany do czatu

### 4. DatePicker (Zaktualizowany)
**Plik:** `myappassistant-chat-frontend/src/components/chat/DatePicker.tsx`

Kompaktowy komponent wyboru daty:

- **Dwa miesiące:** Bieżący i następny miesiąc
- **Szybkie opcje:** "Jutro", "Za tydzień"
- **Walidacja:** Blokowanie dat z przeszłości
- **Responsywny:** Dostosowany do tabeli

## API Endpoints

### Backend (FastAPI)

#### 1. Przetwarzanie asynchroniczne (v3)
- **POST** `/api/v3/receipts/process` - Uruchomienie przetwarzania
- **GET** `/api/v3/receipts/status/{job_id}` - Sprawdzanie statusu
- **DELETE** `/api/v3/receipts/cancel/{job_id}` - Anulowanie zadania
- **GET** `/api/v3/receipts/health` - Status systemu

#### 2. Zapisywanie danych (v2)
- **POST** `/api/v2/receipts/save` - Zapisywanie do bazy danych
- **POST** `/api/v2/receipts/process` - Przetwarzanie synchroniczne
- **POST** `/api/v2/receipts/analyze` - Analiza tekstu OCR

### Frontend (API Client)
**Plik:** `myappassistant-chat-frontend/src/lib/api.ts`

```typescript
export const receiptAPI = {
  processReceiptAsync(file: File): Promise<any> // v3/process
  getTaskStatus(taskId: string): Promise<any>   // v3/status
  saveReceiptData(receiptData: any): Promise<any> // v2/save
  getReceiptHistory(limit: number): Promise<any> // Mockowane
  analyzeExpenses(timeRange: string): Promise<any> // Mockowane
}
```

## Flow Użytkownika

### 1. Upload Paragonu
```
Użytkownik → Kliknie przycisk załącznika → Wybiera plik → 
System wykrywa typ pliku → Jeśli paragon → Uruchamia procesor
```

### 2. Przetwarzanie OCR
```
ChatReceiptProcessor → Wyświetla progress bar → 
Uruchamia zadanie Celery → Polling statusu co 2s → 
Aktualizuje progress → Po zakończeniu → Przechodzi do edycji
```

### 3. Edycja Danych
```
ReceiptDataTable → Wyświetla dane w tabeli → 
Użytkownik edytuje pola → Inline editing → 
DatePicker dla dat przydatności → Kategorie z badge'ami
```

### 4. Zatwierdzenie i Zapis
```
Użytkownik → Kliknie "Zapisz" → Walidacja danych → 
Zapis do bazy przez API → Potwierdzenie → 
Dodanie wiadomości o sukcesie
```

## Struktura Danych

### ReceiptData (Frontend)
```typescript
interface ReceiptData {
  store_name: string;
  date: string;
  total_amount: number;
  items: ReceiptItem[];
}

interface ReceiptItem {
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  category?: string;
  expiration_date?: string;
  unit?: string;
}
```

### ShoppingTripCreate (Backend)
```python
class ShoppingTripCreate(ShoppingTripBase):
    products: List[ProductCreate] = []

class ProductCreate(ProductBase):
    name: str
    quantity: float = 1.0
    unit_price: Optional[float] = None
    expiration_date: Optional[date] = None
    is_consumed: bool = False
```

## Obsługa Błędów

### 1. Błędy Upload
- Walidacja typu pliku (JPG, PNG, WebP, PDF)
- Walidacja rozmiaru (max 10MB)
- Komunikaty błędów w UI

### 2. Błędy Przetwarzania
- Timeout OCR (90s)
- Timeout analizy (60s)
- Retry mechanism
- Fallback na synchroniczne przetwarzanie

### 3. Błędy Zapisu
- Walidacja danych przed zapisem
- Obsługa błędów bazy danych
- Rollback w przypadku błędu

## Testowanie

### Endpointy Backend
```bash
# Test health check
curl -X GET http://localhost:8000/api/v3/receipts/health

# Test upload
curl -X POST http://localhost:8000/api/v3/receipts/process \
  -F "file=@tests/fixtures/test_receipt.jpg"

# Test save
curl -X POST http://localhost:8000/api/v2/receipts/save \
  -H "Content-Type: application/json" \
  -d '{"trip_date": "2024-01-15", "store_name": "Test", "total_amount": 100, "products": []}'
```

### Frontend
```bash
# Build test
cd myappassistant-chat-frontend && npm run build

# Development server
npm run dev
```

## Wymagania Systemowe

### Backend
- Python 3.12+
- FastAPI
- SQLite
- Celery (opcjonalnie dla asynchronicznego przetwarzania)
- Redis (opcjonalnie dla Celery)

### Frontend
- Node.js 18+
- Next.js 15
- React 18
- TypeScript

## Następne Kroki

1. **Celery Workers** - Uruchomienie workers dla asynchronicznego przetwarzania
2. **Testy E2E** - Dodanie testów Playwright dla flow paragonów
3. **Optymalizacja** - Caching wyników OCR
4. **Rozszerzenia** - Obsługa wielu paragonów jednocześnie
5. **Analityka** - Dashboard z analizą wydatków

## Status Implementacji

✅ **Zakończone:**
- Kompletny flow dodawania paragonów w czacie
- Asynchroniczne przetwarzanie z progress bar
- Edytowalna tabela z DatePicker
- Zapisywanie do bazy danych
- Obsługa błędów i retry
- Responsywny design

🔄 **W trakcie:**
- Testy E2E
- Dokumentacja użytkownika

⏳ **Planowane:**
- Celery workers
- Analityka wydatków
- Dashboard paragonów 