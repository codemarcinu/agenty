# 🔧 Plan Ulepszeń Backend - Integracja Telegram

## 🎯 Cel
Rozszerzenie funkcjonalności backend dla integracji Telegram Bot o zaawansowane możliwości, system komend i obsługę plików.

## 📋 Funkcjonalności do Dodania

### 1. System Komend
```python
# src/backend/integrations/telegram_commands.py
COMMANDS = {
    "/start": "Rozpocznij rozmowę z asystentem",
    "/help": "Pokaż pomoc i dostępne komendy",
    "/receipt": "Prześlij paragon do analizy",
    "/pantry": "Sprawdź stan spiżarni",
    "/recipe": "Znajdź przepis na podstawie składników",
    "/weather": "Sprawdź pogodę w Twojej lokalizacji",
    "/search": "Wyszukaj informacje w internecie",
    "/settings": "Zarządzaj ustawieniami",
    "/stats": "Pokaż statystyki użytkowania"
}
```

### 2. Obsługa Plików
- **Zdjęcia**: Paragony do analizy OCR
- **Dokumenty**: PDF do przetwarzania
- **Głos**: Konwersja na tekst

### 3. Zaawansowane Funkcje
- System powiadomień
- Broadcast do wszystkich użytkowników
- Statystyki i metryki
- Monitoring i alerty

---

## 🔧 Implementacja

### 1. System Komend
```python
# src/backend/integrations/telegram_commands.py
from typing import Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CommandType(Enum):
    START = "start"
    HELP = "help"
    RECEIPT = "receipt"
    PANTRY = "pantry"
    RECIPE = "recipe"
    WEATHER = "weather"
    SEARCH = "search"
    SETTINGS = "settings"
    STATS = "stats"

class TelegramCommandHandler:
    """Handler dla komend Telegram Bot"""
    
    def __init__(self, telegram_bot_handler):
        self.bot_handler = telegram_bot_handler
        self.commands = {
            "/start": self._handle_start,
            "/help": self._handle_help,
            "/receipt": self._handle_receipt,
            "/pantry": self._handle_pantry,
            "/recipe": self._handle_recipe,
            "/weather": self._handle_weather,
            "/search": self._handle_search,
            "/settings": self._handle_settings,
            "/stats": self._handle_stats
        }
    
    async def handle_command(self, message: Dict[str, Any]) -> str:
        """Obsługuje komendę Telegram"""
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        
        # Sprawdź czy to komenda
        if not text.startswith("/"):
            return None
            
        command = text.split()[0].lower()
        
        if command in self.commands:
            try:
                return await self.commands[command](message)
            except Exception as e:
                logger.error(f"Error handling command {command}: {e}")
                return "❌ Wystąpił błąd podczas przetwarzania komendy"
        
        return "❓ Nieznana komenda. Użyj /help aby zobaczyć dostępne komendy"
    
    async def _handle_start(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /start"""
        return """🤖 Witaj w FoodSave AI Assistant!

Jestem inteligentnym asystentem, który pomoże Ci:
• 📷 Analizować paragony
• 🍳 Znajdować przepisy
• 🏠 Zarządzać spiżarnią
• 🌤️ Sprawdzać pogodę
• 🔍 Wyszukiwać informacje

Użyj /help aby zobaczyć wszystkie dostępne komendy!"""
    
    async def _handle_help(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /help"""
        return """📋 Dostępne komendy:

🔹 /start - Rozpocznij rozmowę
🔹 /help - Pokaż pomoc
🔹 /receipt - Prześlij paragon do analizy
🔹 /pantry - Sprawdź stan spiżarni
🔹 /recipe - Znajdź przepis
🔹 /weather - Sprawdź pogodę
🔹 /search - Wyszukaj informacje
🔹 /settings - Ustawienia
🔹 /stats - Statystyki

💡 Możesz też po prostu napisać wiadomość, a ja odpowiem!"""
    
    async def _handle_receipt(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /receipt"""
        return """📷 Analiza paragonów:

Aby przeanalizować paragon:
1. Zrób zdjęcie paragonu
2. Wyślij mi zdjęcie
3. Poczekaj na analizę

Wspierane formaty: JPG, PNG, PDF

💡 Upewnij się, że paragon jest czytelny!"""
    
    async def _handle_pantry(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /pantry"""
        # TODO: Implementacja sprawdzania spiżarni
        return """🏠 Stan spiżarni:

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł sprawdzać stan swojej spiżarni!"""
    
    async def _handle_recipe(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /recipe"""
        text = message.get("text", "")
        ingredients = text.replace("/recipe", "").strip()
        
        if not ingredients:
            return """🍳 Wyszukiwanie przepisów:

Użyj: /recipe [składniki]
Przykład: /recipe jajka mleko chleb

Albo po prostu napisz: "Znajdź przepis na jajecznicę" """
        
        # Przekaż do ChefAgent
        result = await self.bot_handler._process_with_ai(
            f"Znajdź przepis na podstawie składników: {ingredients}",
            "chef"
        )
        return result
    
    async def _handle_weather(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /weather"""
        # TODO: Implementacja sprawdzania pogody
        return """🌤️ Sprawdzanie pogody:

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł sprawdzać pogodę!"""
    
    async def _handle_search(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /search"""
        text = message.get("text", "")
        query = text.replace("/search", "").strip()
        
        if not query:
            return """🔍 Wyszukiwanie informacji:

Użyj: /search [zapytanie]
Przykład: /search najnowsze wiadomości o AI

Albo po prostu napisz swoje pytanie!"""
        
        # Przekaż do SearchAgent
        result = await self.bot_handler._process_with_ai(query, "search")
        return result
    
    async def _handle_settings(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /settings"""
        return """⚙️ Ustawienia:

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł zarządzać ustawieniami przez Telegram!"""
    
    async def _handle_stats(self, message: Dict[str, Any]) -> str:
        """Obsługa komendy /stats"""
        # TODO: Implementacja statystyk
        return """📊 Statystyki:

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł sprawdzać statystyki użytkowania!"""
```

### 2. Obsługa Plików
```python
# src/backend/integrations/telegram_file_handler.py
import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
from PIL import Image
import io
import os

logger = logging.getLogger(__name__)

class TelegramFileHandler:
    """Handler dla plików Telegram (zdjęcia, dokumenty, głos)"""
    
    def __init__(self, telegram_bot_handler):
        self.bot_handler = telegram_bot_handler
        self.supported_photo_formats = ['.jpg', '.jpeg', '.png', '.webp']
        self.supported_document_formats = ['.pdf', '.txt', '.doc', '.docx']
    
    async def handle_file(self, message: Dict[str, Any]) -> str:
        """Obsługuje plik wysłany przez użytkownika"""
        try:
            # Sprawdź typ pliku
            if "photo" in message:
                return await self._handle_photo(message)
            elif "document" in message:
                return await self._handle_document(message)
            elif "voice" in message:
                return await self._handle_voice(message)
            else:
                return "❌ Nieobsługiwany typ pliku"
                
        except Exception as e:
            logger.error(f"Error handling file: {e}")
            return "❌ Błąd podczas przetwarzania pliku"
    
    async def _handle_photo(self, message: Dict[str, Any]) -> str:
        """Obsługa zdjęć (paragony)"""
        try:
            # Pobierz największe zdjęcie
            photos = message["photo"]
            largest_photo = max(photos, key=lambda x: x["file_size"])
            
            # Pobierz plik
            file_info = await self._get_file_info(largest_photo["file_id"])
            file_data = await self._download_file(file_info["file_path"])
            
            # Zapisz tymczasowo
            temp_path = f"temp_uploads/receipt_{message['message_id']}.jpg"
            os.makedirs("temp_uploads", exist_ok=True)
            
            with open(temp_path, "wb") as f:
                f.write(file_data)
            
            # Analizuj paragon
            result = await self._analyze_receipt(temp_path)
            
            # Usuń tymczasowy plik
            os.remove(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            return "❌ Błąd podczas analizy zdjęcia"
    
    async def _handle_document(self, message: Dict[str, Any]) -> str:
        """Obsługa dokumentów"""
        try:
            document = message["document"]
            file_name = document["file_name"]
            file_ext = os.path.splitext(file_name)[1].lower()
            
            if file_ext not in self.supported_document_formats:
                return f"❌ Nieobsługiwany format pliku: {file_ext}"
            
            # Pobierz plik
            file_info = await self._get_file_info(document["file_id"])
            file_data = await self._download_file(file_info["file_path"])
            
            # Przetwórz dokument
            if file_ext == '.pdf':
                return await self._process_pdf(file_data, file_name)
            else:
                return await self._process_text_document(file_data, file_name)
                
        except Exception as e:
            logger.error(f"Error handling document: {e}")
            return "❌ Błąd podczas przetwarzania dokumentu"
    
    async def _handle_voice(self, message: Dict[str, Any]) -> str:
        """Obsługa wiadomości głosowych"""
        try:
            voice = message["voice"]
            
            # Pobierz plik głosowy
            file_info = await self._get_file_info(voice["file_id"])
            file_data = await self._download_file(file_info["file_path"])
            
            # Konwertuj na tekst
            text = await self._convert_voice_to_text(file_data)
            
            # Przetwórz tekst
            result = await self.bot_handler._process_with_ai(text, "general")
            
            return f"🎤 Rozpoznany tekst: {text}\n\n🤖 Odpowiedź: {result}"
            
        except Exception as e:
            logger.error(f"Error handling voice: {e}")
            return "❌ Błąd podczas przetwarzania wiadomości głosowej"
    
    async def _get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Pobiera informacje o pliku z Telegram API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{self.bot_handler.bot_token}/getFile",
                params={"file_id": file_id}
            )
            return response.json()["result"]
    
    async def _download_file(self, file_path: str) -> bytes:
        """Pobiera plik z Telegram"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/file/bot{self.bot_handler.bot_token}/{file_path}"
            )
            return response.content
    
    async def _analyze_receipt(self, image_path: str) -> str:
        """Analizuje paragon z obrazu"""
        try:
            # Użyj ReceiptAnalysisAgent
            result = await self.bot_handler._process_with_ai(
                f"Analizuj paragon z pliku: {image_path}",
                "receipt_analysis"
            )
            return f"📷 Analiza paragonu:\n\n{result}"
            
        except Exception as e:
            logger.error(f"Error analyzing receipt: {e}")
            return "❌ Błąd podczas analizy paragonu"
    
    async def _process_pdf(self, file_data: bytes, file_name: str) -> str:
        """Przetwarza plik PDF"""
        try:
            # TODO: Implementacja przetwarzania PDF
            return f"📄 Plik PDF '{file_name}' otrzymany.\n\nFunkcja przetwarzania PDF w trakcie implementacji..."
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return "❌ Błąd podczas przetwarzania PDF"
    
    async def _process_text_document(self, file_data: bytes, file_name: str) -> str:
        """Przetwarza dokument tekstowy"""
        try:
            text = file_data.decode('utf-8')
            
            # Przetwórz tekst przez AI
            result = await self.bot_handler._process_with_ai(
                f"Przetwórz dokument '{file_name}':\n\n{text}",
                "rag"
            )
            
            return f"📄 Analiza dokumentu '{file_name}':\n\n{result}"
            
        except Exception as e:
            logger.error(f"Error processing text document: {e}")
            return "❌ Błąd podczas przetwarzania dokumentu"
    
    async def _convert_voice_to_text(self, file_data: bytes) -> str:
        """Konwertuje wiadomość głosową na tekst"""
        try:
            # TODO: Implementacja konwersji głosu na tekst
            # Można użyć Whisper API lub lokalnego modelu
            return "Funkcja konwersji głosu na tekst w trakcie implementacji..."
            
        except Exception as e:
            logger.error(f"Error converting voice to text: {e}")
            return "Błąd konwersji głosu na tekst"
```

### 3. System Powiadomień
```python
# src/backend/integrations/telegram_notifications.py
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TelegramNotificationSystem:
    """System powiadomień Telegram"""
    
    def __init__(self, telegram_bot_handler):
        self.bot_handler = telegram_bot_handler
        self.subscribers: List[int] = []  # Lista chat_id subskrybentów
    
    async def send_notification(self, message: str, chat_ids: List[int] = None) -> Dict[str, Any]:
        """Wysyła powiadomienie do użytkowników"""
        try:
            if chat_ids is None:
                chat_ids = self.subscribers
            
            success_count = 0
            error_count = 0
            
            for chat_id in chat_ids:
                try:
                    await self.bot_handler._send_message(chat_id, message)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error sending notification to {chat_id}: {e}")
                    error_count += 1
            
            return {
                "status": "completed",
                "success_count": success_count,
                "error_count": error_count,
                "total_sent": len(chat_ids)
            }
            
        except Exception as e:
            logger.error(f"Error in notification system: {e}")
            return {"status": "error", "error": str(e)}
    
    async def send_broadcast(self, message: str) -> Dict[str, Any]:
        """Wysyła broadcast do wszystkich użytkowników"""
        return await self.send_notification(message, self.subscribers)
    
    async def send_alert(self, alert_type: str, message: str) -> Dict[str, Any]:
        """Wysyła alert systemowy"""
        formatted_message = f"🚨 ALERT [{alert_type.upper()}]: {message}"
        return await self.send_broadcast(formatted_message)
    
    async def send_daily_summary(self) -> Dict[str, Any]:
        """Wysyła dzienne podsumowanie"""
        # TODO: Implementacja dziennego podsumowania
        message = """📊 Dzienne podsumowanie FoodSave AI:

• Wiadomości przetworzone: 0
• Paragony przeanalizowane: 0
• Przepisy wyszukane: 0
• Błędy: 0

Dziękujemy za korzystanie z FoodSave AI! 🤖"""
        
        return await self.send_broadcast(message)
    
    async def send_expiration_warning(self, item_name: str, days_left: int) -> Dict[str, Any]:
        """Wysyła ostrzeżenie o kończącym się terminie"""
        message = f"⚠️ OSTRZEŻENIE: {item_name} kończy się za {days_left} dni!"
        return await self.send_broadcast(message)
    
    async def send_low_stock_alert(self, item_name: str) -> Dict[str, Any]:
        """Wysyła alert o niskim stanie magazynowym"""
        message = f"📦 ALERT: {item_name} - niski stan magazynowy!"
        return await self.send_broadcast(message)
    
    def add_subscriber(self, chat_id: int) -> None:
        """Dodaje subskrybenta"""
        if chat_id not in self.subscribers:
            self.subscribers.append(chat_id)
            logger.info(f"Added subscriber: {chat_id}")
    
    def remove_subscriber(self, chat_id: int) -> None:
        """Usuwa subskrybenta"""
        if chat_id in self.subscribers:
            self.subscribers.remove(chat_id)
            logger.info(f"Removed subscriber: {chat_id}")
    
    def get_subscriber_count(self) -> int:
        """Zwraca liczbę subskrybentów"""
        return len(self.subscribers)
```

### 4. Statystyki i Metryki
```python
# src/backend/integrations/telegram_analytics.py
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class TelegramAnalytics:
    """System analityki dla Telegram Bot"""
    
    def __init__(self):
        self.message_count = 0
        self.command_usage = defaultdict(int)
        self.user_activity = defaultdict(int)
        self.response_times = []
        self.errors = []
        self.start_time = datetime.now()
    
    def record_message(self, chat_id: int, message_type: str = "text") -> None:
        """Zapisuje wiadomość"""
        self.message_count += 1
        self.user_activity[chat_id] += 1
    
    def record_command(self, command: str) -> None:
        """Zapisuje użycie komendy"""
        self.command_usage[command] += 1
    
    def record_response_time(self, response_time: float) -> None:
        """Zapisuje czas odpowiedzi"""
        self.response_times.append(response_time)
    
    def record_error(self, error: str) -> None:
        """Zapisuje błąd"""
        self.errors.append({
            "error": error,
            "timestamp": datetime.now()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki"""
        uptime = datetime.now() - self.start_time
        
        return {
            "total_messages": self.message_count,
            "uptime_seconds": uptime.total_seconds(),
            "messages_per_hour": self.message_count / (uptime.total_seconds() / 3600) if uptime.total_seconds() > 0 else 0,
            "active_users": len(self.user_activity),
            "most_used_commands": dict(sorted(self.command_usage.items(), key=lambda x: x[1], reverse=True)[:5]),
            "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "error_count": len(self.errors),
            "recent_errors": self.errors[-10:] if self.errors else []
        }
    
    def get_user_stats(self, chat_id: int) -> Dict[str, Any]:
        """Zwraca statystyki użytkownika"""
        return {
            "messages_sent": self.user_activity.get(chat_id, 0),
            "commands_used": {cmd: count for cmd, count in self.command_usage.items()},
            "last_activity": datetime.now()  # TODO: Implementacja śledzenia ostatniej aktywności
        }
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Zwraca dzienne statystyki"""
        today = datetime.now().date()
        today_messages = sum(1 for _ in range(self.message_count))  # Uproszczone
        
        return {
            "date": today.isoformat(),
            "messages": today_messages,
            "active_users": len(self.user_activity),
            "errors": len([e for e in self.errors if e["timestamp"].date() == today])
        }
```

---

## 🚀 Plan Wdrożenia

### Faza 1: System Komend (1-2 dni)
- [ ] Implementacja TelegramCommandHandler
- [ ] Podstawowe komendy (/start, /help, /receipt)
- [ ] Integracja z istniejącymi agentami

### Faza 2: Obsługa Plików (2-3 dni)
- [ ] Implementacja TelegramFileHandler
- [ ] Obsługa zdjęć (paragony)
- [ ] Obsługa dokumentów PDF
- [ ] Konwersja głosu na tekst

### Faza 3: System Powiadomień (1-2 dni)
- [ ] Implementacja TelegramNotificationSystem
- [ ] Broadcast do użytkowników
- [ ] Alerty systemowe
- [ ] Dzienne podsumowania

### Faza 4: Analityka (1 dzień)
- [ ] Implementacja TelegramAnalytics
- [ ] Statystyki użytkowania
- [ ] Metryki wydajności
- [ ] Raporty dzienne

---

## 🎯 Scenariusze Użycia

### 1. Analiza Paragonu
```
Użytkownik: 📷 [zdjęcie paragonu]
Bot: 🤖 Analizuję paragon...
✅ Sklep: Biedronka
✅ Data: 2025-01-15
✅ Produkty: 5 pozycji
✅ Suma: 45.67 zł
```

### 2. Wyszukiwanie Przepisu
```
Użytkownik: /recipe jajecznica
Bot: 🍳 Przepis na jajecznicę:
Składniki:
• 2 jajka
• Masło
• Sól i pieprz
...
```

### 3. Sprawdzenie Spiżarni
```
Użytkownik: /pantry
Bot: 🏠 Stan spiżarni:
• Mleko: 2 szt. (ważne do: 2025-01-20)
• Chleb: 1 szt. (ważny do: 2025-01-18)
⚠️ Alert: Chleb kończy się za 2 dni
```

---

## 🔒 Bezpieczeństwo

### 1. Walidacja Plików
```python
def validate_file(file_info: Dict[str, Any]) -> bool:
    """Waliduje plik przed przetworzeniem"""
    max_size = 10 * 1024 * 1024  # 10MB
    allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
    
    if file_info["file_size"] > max_size:
        return False
    
    if file_info.get("mime_type") not in allowed_types:
        return False
    
    return True
```

### 2. Rate Limiting dla Plików
```python
def check_file_rate_limit(chat_id: int) -> bool:
    """Sprawdza rate limiting dla plików"""
    # Maksymalnie 5 plików na minutę
    return True  # TODO: Implementacja
```

### 3. Skanowanie Antywirusowe
```python
async def scan_file(file_data: bytes) -> bool:
    """Skanuje plik pod kątem wirusów"""
    # TODO: Integracja z antywirusem
    return True
```

---

## 📊 Monitoring

### 1. Metryki do Śledzenia
- Liczba wiadomości dziennie
- Najpopularniejsze komendy
- Czas odpowiedzi
- Błędy przetwarzania
- Użycie plików

### 2. Alerty
- Wysokie użycie zasobów
- Duża liczba błędów
- Problemy z API
- Nieudane przetwarzanie plików

### 3. Raporty
- Dzienne podsumowania
- Raporty tygodniowe
- Analiza trendów
- Rekomendacje optymalizacji

---

## 🎉 Rezultat

Po implementacji będziesz mieć:

1. **🤖 Kompletny System Komend** - Łatwe zarządzanie przez Telegram
2. **📷 Obsługa Plików** - Analiza paragonów i dokumentów
3. **🔔 System Powiadomień** - Alerty i komunikaty
4. **📊 Analityka** - Szczegółowe statystyki
5. **🛡️ Bezpieczeństwo** - Walidacja i ochrona

**Telegram Bot stanie się pełnoprawnym mobilnym interfejsem do Twojego systemu FoodSave AI!** 