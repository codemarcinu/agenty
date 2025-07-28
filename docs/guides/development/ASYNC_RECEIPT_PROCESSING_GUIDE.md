# Asynchroniczne Przetwarzanie Paragonów - API v3

## Przegląd

API v3 wprowadza fundamentalną zmianę w architekturze przetwarzania paragonów z synchronicznego na asynchroniczny, wykorzystując Celery do zadań w tle. To rozwiązuje problemy z blokowaniem użytkownika i zapewnia lepszą skalowalność.

## Architektura

### Komponenty

1. **Celery Worker** - Przetwarza zadania w tle
2. **Redis** - Broker wiadomości i backend wyników
3. **FastAPI Endpoints** - API do zarządzania zadaniami
4. **WebSocket** - Powiadomienia w czasie rzeczywistym (opcjonalne)

### Przepływ Przetwarzania

```
1. Upload → 2. Task Creation → 3. Background Processing → 4. Status Updates → 5. Result Delivery
```

## Endpointy API v3

### POST `/api/v3/receipts/process`

Przyjmuje plik paragonu i tworzy zadanie w tle.

**Request:**
```http
POST /api/v3/receipts/process
Content-Type: multipart/form-data

file: [receipt_image]
user_id: [optional_user_id]
```

**Response (202 Accepted):**
```json
{
  "status_code": 202,
  "message": "Receipt processing started",
  "data": {
    "job_id": "task-uuid-123",
    "filename": "receipt.jpg",
    "file_size": 1024000,
    "submitted_at": "2025-06-28T10:30:00Z",
    "status": "PENDING"
  }
}
```

### GET `/api/v3/receipts/status/{job_id}`

Sprawdza status zadania przetwarzania.

**Response:**
```json
{
  "status_code": 200,
  "message": "Task status retrieved successfully",
  "data": {
    "job_id": "task-uuid-123",
    "status": "PROGRESS",
    "step": "OCR",
    "progress": 25,
    "message": "Przetwarzanie OCR",
    "filename": "receipt.jpg",
    "timestamp": "2025-06-28T10:30:05Z"
  }
}
```

**Możliwe statusy:**
- `PENDING` - Zadanie oczekuje na wykonanie
- `STARTED` - Zadanie zostało rozpoczęte
- `PROGRESS` - Zadanie w trakcie wykonywania (z dodatkowymi informacjami o postępie)
- `SUCCESS` - Zadanie zakończone pomyślnie
- `FAILURE` - Zadanie zakończone błędem
- `RETRY` - Zadanie w trakcie ponawiania

### DELETE `/api/v3/receipts/cancel/{job_id}`

Anuluje zadanie przetwarzania.

**Response:**
```json
{
  "status_code": 200,
  "message": "Task cancellation requested",
  "data": {
    "job_id": "task-uuid-123",
    "cancelled_at": "2025-06-28T10:30:10Z"
  }
}
```

### GET `/api/v3/receipts/health`

Sprawdza stan systemu przetwarzania.

**Response:**
```json
{
  "status_code": 200,
  "message": "Receipt processing system health check",
  "data": {
    "status": "healthy",
    "timestamp": "2025-06-28T10:30:00Z",
    "active_receipt_tasks": 2,
    "workers_available": true,
    "tasks_registered": true
  }
}
```

## Zadania Celery

### process_receipt_task

Główne zadanie przetwarzania paragonu.

**Parametry:**
- `file_path` - Ścieżka do zapisanego pliku
- `original_filename` - Oryginalna nazwa pliku
- `user_id` - ID użytkownika (opcjonalne)

**Kroki przetwarzania:**
1. **Inicjalizacja** (5%) - Walidacja pliku
2. **Walidacja** (10%) - Sprawdzenie rozmiaru i typu
3. **OCR** (25%) - Rozpoznawanie tekstu
4. **Kontrola jakości OCR** (40%) - Sprawdzenie wyników
5. **Analiza AI** (60%) - Strukturalna analiza
6. **Walidacja danych** (80%) - Sprawdzenie wyników analizy
7. **Zapis** (90%) - Zapis do bazy danych
8. **Finalizacja** (100%) - Czyszczenie i zwrócenie wyniku

### cleanup_temp_files

Zadanie czyszczenia starych plików tymczasowych (uruchamiane okresowo).

### health_check

Zadanie sprawdzania stanu workera.

## Konfiguracja

### Zmienne środowiskowe

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND_URL=redis://redis:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=Europe/Warsaw
CELERY_ENABLE_UTC=True
CELERY_TASK_TRACK_STARTED=True
CELERY_TASK_TIME_LIMIT=30*60  # 30 minut
CELERY_TASK_SOFT_TIME_LIMIT=25*60  # 25 minut
CELERY_WORKER_CONCURRENCY=2
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
```

### Docker Compose

```yaml
services:
  celery_worker:
    build:
      context: .
      dockerfile: src/backend/Dockerfile.dev
    container_name: foodsave-celery-worker-dev
    command: celery -A src.worker.celery_app worker --loglevel=info --concurrency=2
    volumes:
      - ./:/app
      - temp_uploads:/app/temp_uploads
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND_URL=redis://redis:6379/0
    depends_on:
      - redis
      - backend
```

## Użycie w Frontend

### Przykład z JavaScript

```javascript
// 1. Upload pliku i otrzymanie job_id
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/v3/receipts/process', {
  method: 'POST',
  body: formData
});

const { data: { job_id } } = await response.json();

// 2. Polling statusu zadania
const checkStatus = async () => {
  const statusResponse = await fetch(`/api/v3/receipts/status/${job_id}`);
  const statusData = await statusResponse.json();
  
  switch (statusData.data.status) {
    case 'PENDING':
      console.log('Zadanie oczekuje...');
      break;
    case 'PROGRESS':
      console.log(`Postęp: ${statusData.data.progress}% - ${statusData.data.message}`);
      break;
    case 'SUCCESS':
      console.log('Zakończono!', statusData.data.result);
      return statusData.data.result;
    case 'FAILURE':
      console.error('Błąd:', statusData.data.error);
      return null;
  }
  
  // Kontynuuj polling
  setTimeout(checkStatus, 2000);
};

// 3. Rozpocznij polling
checkStatus();
```

### Przykład z WebSocket (opcjonalne)

```javascript
// Połączenie WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event_type === 'receipt_processed' && data.data.task_id === job_id) {
    console.log('Paragon przetworzony!', data.data.receipt);
  }
};
```

## Obsługa błędów

### Typy błędów

1. **Błędy walidacji** (400) - Nieprawidłowy typ pliku, brak Content-Type
2. **Plik za duży** (413) - Przekroczenie limitu 10MB
3. **Błędy przetwarzania** (422) - Błędy OCR lub analizy AI
4. **Błędy systemu** (500) - Błędy wewnętrzne

### Mechanizm ponawiania

Zadania automatycznie ponawiają próby w przypadku przejściowych błędów:
- Maksymalnie 3 próby
- Opóźnienie 60 sekund między próbami
- Rate limiting: 10 zadań na minutę

### Monitorowanie

```bash
# Sprawdź status workera
docker-compose exec celery_worker celery -A src.worker.celery_app inspect ping

# Sprawdź aktywne zadania
docker-compose exec celery_worker celery -A src.worker.celery_app inspect active

# Sprawdź statystyki
docker-compose exec celery_worker celery -A src.worker.celery_app inspect stats
```

## Migracja z API v2

### Zmiany w przepływie

**API v2 (Synchroniczne):**
```
Upload → OCR → Analysis → Response (blokujące)
```

**API v3 (Asynchroniczne):**
```
Upload → Job ID → Background Processing → Status Polling → Result
```

### Kompatybilność

- API v2 pozostaje dostępne dla kompatybilności wstecznej
- API v3 jest nowym, zalecanym podejściem
- Można używać obu wersji równolegle

## Testowanie

### Uruchomienie testów

```bash
# Testy integracyjne API v3
pytest tests/integration/test_receipt_v3_async.py -v

# Testy jednostkowe zadań Celery
pytest tests/unit/test_celery_tasks.py -v
```

### Testowanie lokalne

```bash
# Uruchom system z Celery
docker-compose -f docker-compose.dev.yaml up -d

# Sprawdź logi workera
docker-compose logs -f celery_worker

# Test endpointu
curl -X POST http://localhost:8000/api/v3/receipts/process \
  -F "file=@test_receipt.jpg"
```

## Wydajność

### Zalety asynchronicznego przetwarzania

1. **Lepsze UX** - Użytkownik nie jest blokowany
2. **Skalowalność** - Można skalować workery niezależnie
3. **Niezawodność** - Mechanizm ponawiania i circuit breaker
4. **Monitorowanie** - Szczegółowe śledzenie postępu
5. **Anulowanie** - Możliwość anulowania długich zadań

### Metryki

- **Czas odpowiedzi API**: < 100ms (vs 30s+ w v2)
- **Przetwarzanie w tle**: 30-60s (zależnie od złożoności)
- **Współbieżność**: 2 zadania na worker (konfigurowalne)
- **Rate limiting**: 10 zadań/minutę na użytkownika

## Rozwój

### Dodawanie nowych zadań

```python
@celery_app.task(bind=True, max_retries=3)
def my_new_task(self, param1, param2):
    try:
        # Logika zadania
        self.update_state(state='PROGRESS', meta={'progress': 50})
        result = process_data(param1, param2)
        return result
    except Exception as e:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {'error': str(e)}
```

### Rozszerzanie API

```python
@router.post("/my-endpoint")
async def my_endpoint(file: UploadFile = File(...)):
    # Walidacja
    # Utworzenie zadania
    task = my_new_task.delay(param1, param2)
    
    return JSONResponse(
        status_code=202,
        content={"job_id": task.id}
    )
```

## Wnioski

API v3 wprowadza nowoczesne, skalowalne podejście do przetwarzania paragonów, które znacząco poprawia doświadczenie użytkownika i niezawodność systemu. Asynchroniczne przetwarzanie z wykorzystaniem Celery zapewnia lepszą wydajność i możliwość obsługi większej liczby użytkowników jednocześnie. 