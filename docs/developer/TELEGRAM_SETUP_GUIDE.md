# 🤖 Przewodnik Konfiguracji Telegram Bot - FoodSave AI

## 🎯 Cel
Skonfigurowanie integracji Telegram Bot, aby móc korzystać z asystenta AI bezpośrednio przez Telegram na telefonie.

## 📋 Wymagania
- Telegram na telefonie
- Dostęp do internetu
- Konto Telegram

---

## 🚀 KROK 1: Utworzenie Bota

### 1. Otwórz Telegram na telefonie
### 2. Znajdź @BotFather
- Wyszukaj "BotFather" w Telegram
- Lub kliknij link: https://t.me/botfather

### 3. Utwórz nowego bota
```
Wyślij do BotFather:
/newbot
```

### 4. Podaj nazwę bota
```
Bot name: FoodSave AI Assistant
```

### 5. Podaj username
```
Username: foodsave_ai_bot
```
**Uwaga**: Username musi kończyć się na "bot" i być unikalny

### 6. Zapisz token
BotFather wyśle Ci token w formacie:
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**ZAPISZ TEN TOKEN - będzie potrzebny w następnym kroku!**

---

## 🔧 KROK 2: Konfiguracja w Aplikacji

### 1. Otwórz plik konfiguracyjny
```bash
nano .env
```

### 2. Dodaj konfigurację Telegram
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=twój_token_z_botfather
TELEGRAM_BOT_USERNAME=foodsave_ai_bot
TELEGRAM_BOT_NAME=FoodSave AI Assistant
TELEGRAM_WEBHOOK_URL=https://twoja-domena.com/api/v2/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=auto_generated_secret
TELEGRAM_MAX_MESSAGE_LENGTH=4096
TELEGRAM_RATE_LIMIT_PER_MINUTE=30
```

### 3. Zastąp wartości:
- `twój_token_z_botfather` → token z BotFather
- `twoja-domena.com` → Twój publiczny adres (lub localhost dla testów)

---

## 🌐 KROK 3: Konfiguracja Webhook (Dla Produkcji)

### Opcja A: Lokalny Test (ngrok)
```bash
# 1. Zainstaluj ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz

# 2. Uruchom ngrok
./ngrok http 8000

# 3. Skopiuj HTTPS URL (np. https://abc123.ngrok.io)
# 4. Ustaw webhook
curl -X POST "http://localhost:8000/api/v2/telegram/set-webhook" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://abc123.ngrok.io/api/v2/telegram/webhook"}'
```

### Opcja B: Produkcja (VPS z domeną)
```bash
# 1. Ustaw webhook na produkcji
curl -X POST "http://localhost:8000/api/v2/telegram/set-webhook" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://twoja-domena.com/api/v2/telegram/webhook"}'
```

---

## ✅ KROK 4: Testowanie

### 1. Sprawdź status webhook
```bash
curl "http://localhost:8000/api/v2/telegram/webhook-info"
```

### 2. Test połączenia
```bash
curl "http://localhost:8000/api/v2/telegram/test-connection"
```

### 3. Znajdź bota w Telegram
- Wyszukaj: `@foodsave_ai_bot`
- Lub kliknij link: `https://t.me/foodsave_ai_bot`

### 4. Wyślij pierwszą wiadomość
```
Cześć! Jak się masz?
```

---

## 🔧 KROK 5: Konfiguracja Zaawansowana

### 1. Ustaw komendy bota
```bash
curl -X POST "https://api.telegram.org/botTWÓJ_TOKEN/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "start", "description": "Rozpocznij rozmowę z asystentem"},
      {"command": "help", "description": "Pokaż pomoc"},
      {"command": "receipt", "description": "Prześlij paragon do analizy"},
      {"command": "pantry", "description": "Sprawdź stan spiżarni"},
      {"command": "recipe", "description": "Znajdź przepis"}
    ]
  }'
```

### 2. Ustaw opis bota
```bash
curl -X POST "https://api.telegram.org/botTWÓJ_TOKEN/setMyDescription" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "🤖 Inteligentny asystent AI do zarządzania żywnością, przepisami i zakupami. Prześlij paragon, zapytaj o przepis lub porozmawiaj!"
  }'
```

---

## 🎯 FUNKCJONALNOŚCI

### ✅ Dostępne Komendy
- `/start` - Rozpocznij rozmowę
- `/help` - Pokaż pomoc
- `/receipt` - Prześlij paragon
- `/pantry` - Sprawdź spiżarnię
- `/recipe` - Znajdź przepis

### ✅ Obsługiwane Wiadomości
- **Tekstowe**: Pytania, rozmowy, przepisy
- **Zdjęcia**: Paragony do analizy
- **Pliki**: Dokumenty do przetwarzania

### ✅ Integracja z AI
- **GeneralConversationAgent** - Ogólne rozmowy
- **ChefAgent** - Przepisy kulinarne
- **SearchAgent** - Wyszukiwanie informacji
- **RAGAgent** - Analiza dokumentów
- **ReceiptAnalysisAgent** - Analiza paragonów

---

## 🔒 BEZPIECZEŃSTWO

### ✅ Zaimplementowane Zabezpieczenia
- **Secret Token** - Walidacja webhook
- **Rate Limiting** - 30 wiadomości/minutę
- **Input Sanitization** - Oczyszczanie danych
- **Error Handling** - Obsługa błędów
- **Logging** - Szczegółowe logi

---

## 🛠️ ROZWIĄZYWANIE PROBLEMÓW

### Problem: Bot nie odpowiada
```bash
# 1. Sprawdź token
curl "https://api.telegram.org/botTWÓJ_TOKEN/getMe"

# 2. Sprawdź webhook
curl "http://localhost:8000/api/v2/telegram/webhook-info"

# 3. Sprawdź logi
tail -f logs/backend/server.log
```

### Problem: Webhook nie działa
```bash
# 1. Sprawdź czy aplikacja działa
curl "http://localhost:8000/health"

# 2. Sprawdź porty
netstat -tlnp | grep 8000

# 3. Sprawdź HTTPS (wymagane dla webhook)
# Użyj ngrok lub domeny z SSL
```

### Problem: Błędy w logach
```bash
# Sprawdź szczegółowe logi
tail -f logs/backend/telegram_webhook.log
tail -f logs/backend/chat.log
```

---

## 📊 MONITORING

### Metryki do Sprawdzenia
- Liczba otrzymanych wiadomości
- Czas odpowiedzi AI
- Błędy przetwarzania
- Rate limiting

### Logi do Monitorowania
```bash
# Logi webhook
tail -f logs/backend/telegram_webhook.log

# Logi czatu
tail -f logs/backend/chat.log

# Logi AI
tail -f logs/backend/ai_processing.log
```

---

## 🎉 GOTOWE!

Po wykonaniu wszystkich kroków będziesz mógł:
- ✅ Rozmawiać z asystentem przez Telegram
- ✅ Przesyłać paragony do analizy
- ✅ Pytać o przepisy i porady kulinarne
- ✅ Wyszukiwać informacje
- ✅ Zarządzać spiżarnią

**Bot będzie działał jako mobilny interfejs do Twojego systemu FoodSave AI!** 