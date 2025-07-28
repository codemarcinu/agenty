# KRYTYCZNE NAPRAWY WYMAGANE W SYSTEMIE PRZETWARZANIA PARAGONÓW

## 🚨 PRIORYTET 1: NATYCHMIASTOWE NAPRAWY

### 1. BRAK ZAPISYWANIA DO BAZY DANYCH (KRYTYCZNE)

**Problem**: System przetwarza paragony ale nigdy ich nie zapisuje
- `src/tasks/receipt_tasks.py:235-236` - tylko TODO komentarz
- `src/backend/api/v2/endpoints/receipts.py:417-455` - endpoint wyłączony

**Rozwiązanie**: Implementacja zapisywania w Celery task:

```python
# Dodać do src/tasks/receipt_tasks.py

async def save_receipt_to_database(analysis_data: dict, user_id: str = None) -> dict:
    """Save receipt data to database using async session"""
    from backend.core.database import get_async_session_factory
    from backend.models.shopping import ShoppingTrip, Product
    from sqlalchemy.exc import SQLAlchemyError
    
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            # Create shopping trip
            trip = ShoppingTrip(
                trip_date=analysis_data.get('date', datetime.now().date()),
                store_name=analysis_data.get('store_name', 'Unknown Store'),
                total_amount=analysis_data.get('total_amount')
            )
            session.add(trip)
            await session.flush()  # Get trip.id
            
            # Create products
            products_created = 0
            for item in analysis_data.get('items', []):
                product = Product(
                    name=item.get('name', 'Unknown Product'),
                    category=item.get('category'),
                    unit_price=item.get('unit_price'),
                    quantity=item.get('quantity', 1.0),
                    unit=item.get('unit'),
                    trip_id=trip.id
                )
                session.add(product)
                products_created += 1
            
            await session.commit()
            
            return {
                "success": True,
                "trip_id": trip.id,
                "products_count": products_created
            }
            
        except SQLAlchemyError as e:
            await session.rollback()
            raise RuntimeError(f"Database error: {str(e)}")
        except Exception as e:
            await session.rollback()
            raise RuntimeError(f"Unexpected error saving to database: {str(e)}")

# W process_receipt_task zastąpić TODO:
try:
    if analysis_data:
        save_result = await save_receipt_to_database(analysis_data, user_id)
        result["database_save"] = save_result
        logger.info(f"Saved receipt to database: trip_id={save_result['trip_id']}")
except Exception as e:
    logger.error(f"Failed to save to database: {e}")
    result["database_error"] = str(e)
```

### 2. BEZPIECZEŃSTWO - BRAK WALIDACJI PLIKÓW (WYSOKIE)

**Problem**: Tylko sprawdzanie MIME type, brak rzeczywistej walidacji
```python
# Obecne: tylko MIME type
if file.content_type not in ALLOWED_FILE_TYPES:
    raise HTTPException(status_code=400, detail="Unsupported file type")
```

**Rozwiązanie**:
```python
import magic

def validate_file_security(file_bytes: bytes, content_type: str) -> bool:
    """Comprehensive file validation"""
    # Magic number validation
    detected_type = magic.from_buffer(file_bytes, mime=True)
    
    # Sprawdź czy rzeczywisty typ odpowiada deklarowanemu
    type_mapping = {
        'image/jpeg': ['image/jpeg'],
        'image/png': ['image/png'],
        'application/pdf': ['application/pdf']
    }
    
    if detected_type not in type_mapping.get(content_type, []):
        return False
    
    # Sprawdź rozmiar nagłówka (anty-malware)
    if len(file_bytes) < 100:  # Za mały plik
        return False
    
    # PDF validation
    if content_type == 'application/pdf':
        if not file_bytes.startswith(b'%PDF-'):
            return False
    
    # Image validation
    elif content_type.startswith('image/'):
        try:
            from PIL import Image
            import io
            Image.open(io.BytesIO(file_bytes[:1024]))  # Test header
        except Exception:
            return False
    
    return True
```

### 3. OBSŁUGA BŁĘDÓW - BRAK STRUKTURALNEJ KLASYFIKACJI (WYSOKIE)

**Problem**: Generyczne wyjątki tracą kontekst
```python
except Exception as e:
    return JSONResponse(status_code=500, content={"error": str(e)})
```

**Rozwiązanie**:
```python
# Nowy plik: src/backend/core/receipt_exceptions.py

class ReceiptProcessingError(Exception):
    """Base exception for receipt processing"""
    def __init__(self, message: str, error_code: str, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

class OCRProcessingError(ReceiptProcessingError):
    """OCR specific errors"""
    pass

class ReceiptAnalysisError(ReceiptProcessingError):
    """Analysis specific errors"""
    pass

class DatabaseSaveError(ReceiptProcessingError):
    """Database save errors"""
    pass

# Exception handler middleware
@app.exception_handler(ReceiptProcessingError)
async def receipt_error_handler(request: Request, exc: ReceiptProcessingError):
    return JSONResponse(
        status_code=422,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": str(uuid.uuid4())
        }
    )
```

## 🔧 PRIORYTET 2: OPTYMALIZACJE WYDAJNOŚCI

### 1. CACHE REDIS ZAMIAST PAMIĘCI

**Problem**: Cache w pamięci, limitowany do 100 wpisów
```python
# Obecne: w pamięci
_receipt_cache = {}
```

**Rozwiązanie**:
```python
import redis
import json

class ReceiptCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.ttl = 3600  # 1 hour
    
    async def get(self, file_hash: str) -> dict | None:
        cached = self.redis_client.get(f"receipt:{file_hash}")
        return json.loads(cached) if cached else None
    
    async def set(self, file_hash: str, data: dict):
        self.redis_client.setex(
            f"receipt:{file_hash}", 
            self.ttl, 
            json.dumps(data)
        )
```

### 2. STREAMING PROCESSING DLA DUŻYCH PLIKÓW

**Problem**: Całe pliki ładowane do pamięci
```python
file_bytes = await file.read()  # Cały plik w pamięci
```

**Rozwiązanie**:
```python
import tempfile
import aiofiles

async def stream_file_processing(file: UploadFile) -> str:
    """Stream large files to temporary storage"""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp_file:
            temp_path = tmp_file.name
            
        async with aiofiles.open(temp_path, 'wb') as f:
            while chunk := await file.read(8192):  # 8KB chunks
                await f.write(chunk)
        
        return temp_path
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
```

## 🛡️ PRIORYTET 3: BEZPIECZEŃSTWO

### 1. RATE LIMITING

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/process")
@limiter.limit("5/minute")  # Max 5 uploads per minute
async def process_receipt_complete(request: Request, file: UploadFile = File(...)):
    # existing code
```

### 2. INPUT SANITIZATION

```python
import bleach
import re

def sanitize_ocr_text(text: str) -> str:
    """Sanitize OCR text to prevent injection attacks"""
    # Remove potential script tags
    cleaned = bleach.clean(text, tags=[], strip=True)
    
    # Limit length
    if len(cleaned) > 50000:  # 50KB limit
        cleaned = cleaned[:50000]
    
    # Remove control characters except newlines/tabs
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
    
    return cleaned
```

## 📊 PRIORYTET 4: MONITORING I METRYKI

### 1. STRUCTURED LOGGING

```python
import structlog

logger = structlog.get_logger()

# W każdym endpoincie:
logger.info("receipt_processing_started", 
    filename=file.filename,
    file_size=len(file_bytes),
    content_type=file.content_type,
    correlation_id=correlation_id
)
```

### 2. METRYKI PROMETHEUS

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
receipt_processed_total = Counter('receipt_processed_total', 'Total receipts processed')
receipt_processing_duration = Histogram('receipt_processing_duration_seconds', 'Receipt processing time')
receipt_errors_total = Counter('receipt_errors_total', 'Total receipt processing errors', ['error_type'])
```

## 🚀 PLAN IMPLEMENTACJI

### Tydzień 1: Krytyczne naprawy
- [x] Implementacja zapisywania do bazy danych
- [x] Podstawowa walidacja bezpieczeństwa plików
- [x] Strukturalna obsługa błędów

### Tydzień 2: Optymalizacje
- [ ] Redis cache
- [ ] Streaming file processing  
- [ ] Rate limiting

### Tydzień 3: Monitoring
- [ ] Structured logging
- [ ] Metryki Prometheus
- [ ] Health checks

### Tydzień 4: Testy
- [ ] Integration tests
- [ ] Load testing
- [ ] Security testing

## 💾 SZACUNKOWY CZAS IMPLEMENTACJI

- **Krytyczne naprawy**: 20-30 godzin
- **Optymalizacje**: 15-25 godzin  
- **Monitoring**: 10-15 godzin
- **Testy**: 15-20 godzin

**TOTAL**: 60-90 godzin pracy (1.5-2 miesiące part-time)

## 🎯 OCZEKIWANE REZULTATY

Po implementacji:
- ✅ **100% paragonów zapisywanych** do bazy danych
- ✅ **Bezpieczne przetwarzanie** plików
- ✅ **5x szybsze** przetwarzanie przez cache
- ✅ **Zero security vulnerabilities**
- ✅ **Pełne monitoring** operacji