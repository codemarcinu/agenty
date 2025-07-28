# 🔧 Plan Ulepszeń Backend - Integracja Telegram

## 🎯 Cel
Rozszerzenie funkcjonalności backend dla lepszej integracji z Telegram Bot, dodanie nowych endpointów i ulepszenie istniejących.

## 📋 Funkcjonalności do Dodania

### 1. Nowe Endpointy API
```python
# src/backend/api/v2/endpoints/telegram.py

@router.get("/stats")
async def get_telegram_stats() -> JSONResponse:
    """Pobiera statystyki Telegram Bot"""

@router.get("/logs")
async def get_telegram_logs(limit: int = 100) -> JSONResponse:
    """Pobiera logi Telegram Bot"""

@router.post("/send-notification")
async def send_notification(message: str, chat_id: int | None = None) -> JSONResponse:
    """Wysyła powiadomienie do użytkowników"""

@router.get("/users")
async def get_telegram_users() -> JSONResponse:
    """Pobiera listę użytkowników bota"""

@router.post("/broadcast")
async def broadcast_message(message: str) -> JSONResponse:
    """Wysyła wiadomość do wszystkich użytkowników"""
```

### 2. Obsługa Komend
```python
# src/backend/integrations/telegram_commands.py
class TelegramCommandHandler:
    """Handler dla komend Telegram"""
    
    async def handle_start(self, chat_id: int, user_id: int) -> str:
        """Obsługa komendy /start"""
        
    async def handle_help(self, chat_id: int) -> str:
        """Obsługa komendy /help"""
        
    async def handle_receipt(self, chat_id: int) -> str:
        """Obsługa komendy /receipt"""
        
    async def handle_pantry(self, chat_id: int) -> str:
        """Obsługa komendy /pantry"""
        
    async def handle_recipe(self, chat_id: int, query: str) -> str:
        """Obsługa komendy /recipe"""
```

### 3. Obsługa Plików
```python
# src/backend/integrations/telegram_file_handler.py
class TelegramFileHandler:
    """Handler dla plików z Telegram"""
    
    async def handle_photo(self, file_id: str, chat_id: int) -> str:
        """Obsługa zdjęć (paragony)"""
        
    async def handle_document(self, file_id: str, chat_id: int) -> str:
        """Obsługa dokumentów"""
        
    async def handle_voice(self, file_id: str, chat_id: int) -> str:
        """Obsługa wiadomości głosowych"""
```

---

## 🔧 Implementacja

### 1. Rozszerzenie TelegramBotHandler
```python
# src/backend/integrations/telegram_bot.py

class TelegramBotHandler:
    def __init__(self):
        self.command_handler = TelegramCommandHandler()
        self.file_handler = TelegramFileHandler()
        self.stats = TelegramStats()
        
    async def handle_command(self, command: str, chat_id: int, user_id: int, args: str = "") -> str:
        """Obsługuje komendy Telegram"""
        if command == "/start":
            return await self.command_handler.handle_start(chat_id, user_id)
        elif command == "/help":
            return await self.command_handler.handle_help(chat_id)
        elif command == "/receipt":
            return await self.command_handler.handle_receipt(chat_id)
        elif command == "/pantry":
            return await self.command_handler.handle_pantry(chat_id)
        elif command == "/recipe":
            return await self.command_handler.handle_recipe(chat_id, args)
        else:
            return "❌ Nieznana komenda. Użyj /help aby zobaczyć dostępne komendy."
    
    async def handle_file(self, file_data: dict, chat_id: int) -> str:
        """Obsługuje pliki z Telegram"""
        file_type = file_data.get("type")
        file_id = file_data.get("file_id")
        
        if file_type == "photo":
            return await self.file_handler.handle_photo(file_id, chat_id)
        elif file_type == "document":
            return await self.file_handler.handle_document(file_id, chat_id)
        elif file_type == "voice":
            return await self.file_handler.handle_voice(file_id, chat_id)
        else:
            return "❌ Nieobsługiwany typ pliku."
```

### 2. System Statystyk
```python
# src/backend/integrations/telegram_stats.py
class TelegramStats:
    """System statystyk dla Telegram Bot"""
    
    def __init__(self):
        self.message_count = 0
        self.response_times = []
        self.error_count = 0
        self.user_count = 0
        
    async def record_message(self, user_id: int, response_time: float):
        """Zapisuje statystyki wiadomości"""
        self.message_count += 1
        self.response_times.append(response_time)
        
    async def record_error(self, error_type: str):
        """Zapisuje błędy"""
        self.error_count += 1
        
    async def get_stats(self) -> dict:
        """Pobiera statystyki"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "total_messages": self.message_count,
            "average_response_time": round(avg_response_time, 2),
            "error_count": self.error_count,
            "unique_users": self.user_count,
            "uptime": self.get_uptime()
        }
```

### 3. System Logowania
```python
# src/backend/integrations/telegram_logger.py
class TelegramLogger:
    """System logowania dla Telegram Bot"""
    
    def __init__(self):
        self.log_file = "logs/telegram_bot.log"
        
    async def log_message(self, user_id: int, message: str, response: str, response_time: float):
        """Loguje wiadomość użytkownika"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "message": message,
            "response": response,
            "response_time": response_time,
            "type": "message"
        }
        
        await self._write_log(log_entry)
        
    async def log_error(self, error: str, user_id: int | None = None):
        """Loguje błędy"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "error": error,
            "type": "error"
        }
        
        await self._write_log(log_entry)
```

---

## 🎯 Nowe Funkcjonalności

### 1. Komendy Bot
```python
# Komendy do zaimplementowania
COMMANDS = {
    "/start": "Rozpocznij rozmowę z asystentem",
    "/help": "Pokaż dostępne komendy",
    "/receipt": "Prześlij paragon do analizy",
    "/pantry": "Sprawdź stan spiżarni",
    "/recipe": "Znajdź przepis",
    "/weather": "Sprawdź pogodę",
    "/search": "Wyszukaj informacje",
    "/settings": "Ustawienia użytkownika"
}
```

### 2. Obsługa Plików
```python
# Obsługiwane typy plików
SUPPORTED_FILES = {
    "photo": "Zdjęcia paragonów",
    "document": "Dokumenty PDF",
    "voice": "Wiadomości głosowe"
}
```

### 3. Powiadomienia
```python
# System powiadomień
class TelegramNotificationService:
    """Serwis powiadomień Telegram"""
    
    async def send_notification(self, message: str, chat_id: int | None = None):
        """Wysyła powiadomienie"""
        
    async def send_broadcast(self, message: str):
        """Wysyła wiadomość do wszystkich użytkowników"""
        
    async def send_alert(self, alert_type: str, data: dict):
        """Wysyła alert systemowy"""
```

---

## 🔒 Bezpieczeństwo

### 1. Walidacja Użytkowników
```python
class TelegramUserValidator:
    """Walidacja użytkowników Telegram"""
    
    def __init__(self):
        self.allowed_users = set()  # Lista dozwolonych użytkowników
        self.blocked_users = set()  # Lista zablokowanych użytkowników
        
    async def validate_user(self, user_id: int) -> bool:
        """Sprawdza czy użytkownik ma dostęp"""
        if user_id in self.blocked_users:
            return False
        if self.allowed_users and user_id not in self.allowed_users:
            return False
        return True
```

### 2. Rate Limiting
```python
class TelegramRateLimiter:
    """Rate limiting dla Telegram"""
    
    def __init__(self):
        self.user_limits = {}  # Limit per user
        self.global_limit = 100  # Globalny limit
        
    async def check_rate_limit(self, user_id: int) -> bool:
        """Sprawdza rate limit dla użytkownika"""
        current_time = time.time()
        
        if user_id not in self.user_limits:
            self.user_limits[user_id] = []
            
        # Usuń stare wpisy (starsze niż 1 minuta)
        self.user_limits[user_id] = [
            t for t in self.user_limits[user_id] 
            if current_time - t < 60
        ]
        
        # Sprawdź limit
        if len(self.user_limits[user_id]) >= 30:  # 30 wiadomości na minutę
            return False
            
        self.user_limits[user_id].append(current_time)
        return True
```

### 3. Szyfrowanie Danych
```python
class TelegramDataEncryption:
    """Szyfrowanie danych Telegram"""
    
    def __init__(self):
        self.encryption_key = settings.TELEGRAM_ENCRYPTION_KEY
        
    async def encrypt_token(self, token: str) -> str:
        """Szyfruje token bota"""
        
    async def decrypt_token(self, encrypted_token: str) -> str:
        """Deszyfruje token bota"""
        
    async def encrypt_user_data(self, user_data: dict) -> str:
        """Szyfruje dane użytkownika"""
```

---

## 📊 Monitoring i Metryki

### 1. Prometheus Metrics
```python
# src/backend/monitoring/telegram_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metryki Telegram
telegram_messages_total = Counter('telegram_messages_total', 'Total Telegram messages')
telegram_response_time = Histogram('telegram_response_time_seconds', 'Telegram response time')
telegram_errors_total = Counter('telegram_errors_total', 'Total Telegram errors')
telegram_active_users = Gauge('telegram_active_users', 'Active Telegram users')
```

### 2. Grafana Dashboard
```json
// monitoring/grafana/dashboards/telegram-dashboard.json
{
  "dashboard": {
    "title": "Telegram Bot Metrics",
    "panels": [
      {
        "title": "Messages per Hour",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(telegram_messages_total[1h])"
          }
        ]
      },
      {
        "title": "Average Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(telegram_response_time_seconds_sum[5m]) / rate(telegram_response_time_seconds_count[5m])"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "telegram_active_users"
          }
        ]
      }
    ]
  }
}
```

---

## 🧪 Testy

### 1. Unit Tests
```python
# tests/unit/test_telegram_bot.py
class TestTelegramBotHandler:
    """Testy dla TelegramBotHandler"""
    
    async def test_handle_command_start(self):
        """Test obsługi komendy /start"""
        
    async def test_handle_command_help(self):
        """Test obsługi komendy /help"""
        
    async def test_handle_file_photo(self):
        """Test obsługi zdjęć"""
        
    async def test_rate_limiting(self):
        """Test rate limiting"""
        
    async def test_user_validation(self):
        """Test walidacji użytkowników"""
```

### 2. Integration Tests
```python
# tests/integration/test_telegram_integration.py
class TestTelegramIntegration:
    """Testy integracji Telegram"""
    
    async def test_webhook_processing(self):
        """Test przetwarzania webhook"""
        
    async def test_ai_integration(self):
        """Test integracji z AI"""
        
    async def test_file_upload(self):
        """Test uploadu plików"""
        
    async def test_notifications(self):
        """Test powiadomień"""
```

---

## 🚀 Plan Implementacji

### Faza 1: Podstawowe Ulepszenia (2-3 dni)
1. ✅ Rozszerzenie TelegramBotHandler
2. ✅ System komend
3. ✅ Obsługa plików
4. ✅ Rate limiting i walidacja

### Faza 2: Zaawansowane Funkcje (3-4 dni)
1. ✅ System statystyk
2. ✅ System logowania
3. ✅ Powiadomienia
4. ✅ Monitoring i metryki

### Faza 3: Bezpieczeństwo i Testy (2-3 dni)
1. ✅ Szyfrowanie danych
2. ✅ Walidacja użytkowników
3. ✅ Testy jednostkowe i integracyjne
4. ✅ Dokumentacja

---

## 📚 Dokumentacja

### 1. API Documentation
- Kompletna dokumentacja endpointów
- Przykłady użycia
- Kody błędów

### 2. Deployment Guide
- Konfiguracja środowiska
- SSL requirements
- Monitoring setup

### 3. User Guide
- Instrukcje konfiguracji
- Rozwiązywanie problemów
- FAQ

---

## 🎯 Podsumowanie

Po implementacji ulepszeń backend będzie oferował:

1. **Kompletne API** - Wszystkie potrzebne endpointy
2. **Obsługa komend** - System komend Telegram
3. **Obsługa plików** - Zdjęcia, dokumenty, głos
4. **Bezpieczeństwo** - Rate limiting, walidacja, szyfrowanie
5. **Monitoring** - Metryki, logi, alerty
6. **Powiadomienia** - System powiadomień
7. **Testy** - Kompletne pokrycie testami

**Rezultat**: Pełnoprawny, bezpieczny i skalowalny system Telegram Bot z zaawansowanymi funkcjonalnościami. 