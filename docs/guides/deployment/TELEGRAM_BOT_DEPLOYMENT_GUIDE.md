# 🤖 Przewodnik Wdrożenia Telegram Bot - FoodSave AI

**Data:** 2025-06-25  
**Wersja:** 1.0.0  
**Status:** 🚀 **GOTOWY DO WDROŻENIA**

## 📋 Przegląd

Ten przewodnik zawiera szczegółowe instrukcje wdrożenia integracji Telegram Bot dla aplikacji FoodSave AI. Integracja umożliwia użytkownikom komunikację z asystentem AI bezpośrednio przez Telegram.

## 🎯 Funkcjonalności

- ✅ **Webhook Integration**: Automatyczne przetwarzanie wiadomości z Telegram
- ✅ **AI Processing**: Integracja z istniejącym orchestrator AI
- ✅ **Rate Limiting**: Ochrona przed spamem (30 wiadomości/minutę)
- ✅ **Message Splitting**: Automatyczne dzielenie długich wiadomości
- ✅ **Database Storage**: Zapis konwersacji do bazy danych
- ✅ **Error Handling**: Kompleksowa obsługa błędów
- ✅ **Frontend Settings**: Panel konfiguracji w ustawieniach

## 🔧 Wymagania Systemowe

### Backend
- Python 3.12+
- FastAPI
- httpx (dla HTTP requests)
- SQLAlchemy (dla bazy danych)
- Pydantic (dla walidacji)

### Frontend
- Node.js 18+
- React 18+
- TypeScript
- Axios

### Infrastruktura
- HTTPS endpoint (wymagany dla webhook)
- Publiczny adres IP/domena
- Port 8000 (backend)
- Port 3000 (frontend)

## 🚀 Instrukcje Wdrożenia

### Krok 1: Przygotowanie Środowiska

#### A. Zmienne Środowiskowe
Dodaj do pliku `.env`:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v2/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=auto_generated_secret
TELEGRAM_BOT_USERNAME=foodsave_ai_bot
TELEGRAM_BOT_NAME=FoodSave AI Assistant
TELEGRAM_MAX_MESSAGE_LENGTH=4096
TELEGRAM_RATE_LIMIT_PER_MINUTE=30
```

#### B. Zależności Backend
Zależności są już zawarte w `pyproject.toml`:
```toml
httpx = "^0.27.0"
```

### Krok 2: Konfiguracja Bota Telegram

#### A. Utworzenie Bota przez BotFather
1. Otwórz Telegram
2. Znajdź @BotFather
3. Wyślij komendę `/newbot`
4. Podaj nazwę: "FoodSave AI Assistant"
5. Podaj username: "foodsave_ai_bot"
6. Zapisz otrzymany token

#### B. Konfiguracja Webhook
```bash
# Uruchom aplikację
cd myappassistant
source venv/bin/activate
PYTHONPATH=src python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Ustaw webhook (wymagany HTTPS)
curl -X POST "http://localhost:8000/api/v2/telegram/set-webhook" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://your-domain.com/api/v2/telegram/webhook"}'
```

### Krok 3: Testowanie Integracji

#### A. Test Połączenia
```bash
# Sprawdź status webhook
curl "http://localhost:8000/api/v2/telegram/webhook-info"

# Test połączenia z botem
curl "http://localhost:8000/api/v2/telegram/test-connection"
```

#### B. Test Wiadomości
1. Otwórz bota w Telegram
2. Wyślij wiadomość: "Cześć, jak się masz?"
3. Sprawdź odpowiedź AI
4. Sprawdź logi aplikacji

### Krok 4: Frontend Configuration

#### A. Uruchomienie Frontend
```bash
cd myappassistant-chat-frontend
npm install
npm run dev
```

#### B. Konfiguracja w Ustawieniach
1. Otwórz aplikację w przeglądarce
2. Przejdź do Ustawienia → Integracje
3. Wypełnij konfigurację Telegram Bot:
   - Token BotFather
   - Username bota
   - URL webhook
4. Kliknij "Test Połączenia"
5. Kliknij "Ustaw Webhook"
6. Kliknij "Zapisz Ustawienia"

## 🧪 Testy

### Uruchomienie Testów Backend
```bash
# Testy jednostkowe
pytest tests/unit/test_telegram_bot.py -v

# Testy integracyjne
pytest tests/integration/test_telegram_integration.py -v

# Wszystkie testy
pytest tests/ -v --tb=short
```

### Uruchomienie Testów Frontend
```bash
cd myappassistant-chat-frontend
npm test
npm run test:e2e
```

## 📊 Monitoring i Logi

### Logi Aplikacji
```bash
# Sprawdź logi webhook
tail -f logs/backend/telegram_webhook.log

# Sprawdź logi czatu
tail -f logs/backend/chat.log

# Sprawdź logi błędów
tail -f logs/backend/error.log
```

### Metryki Telegram
- Liczba otrzymanych wiadomości
- Czas odpowiedzi
- Błędy przetwarzania
- Rate limiting

## 🔒 Bezpieczeństwo

### Walidacja Webhook
- Secret token verification
- Rate limiting per user
- Input sanitization
- Error handling

### Ochrona Danych
- Szyfrowanie tokenów
- Bezpieczne przechowywanie konwersacji
- Logowanie bez danych wrażliwych
- CORS configuration

## 🐛 Rozwiązywanie Problemów

### Problem: Webhook nie działa
**Objawy:** Bot nie odpowiada na wiadomości

**Rozwiązanie:**
1. Sprawdź czy HTTPS jest skonfigurowany
2. Sprawdź logi webhook: `tail -f logs/backend/telegram_webhook.log`
3. Sprawdź status webhook: `curl "http://localhost:8000/api/v2/telegram/webhook-info"`
4. Ustaw ponownie webhook: `curl -X POST "http://localhost:8000/api/v2/telegram/set-webhook" -H "Content-Type: application/json" -d '{"webhook_url": "https://your-domain.com/api/v2/telegram/webhook"}'`

### Problem: Błąd autoryzacji
**Objawy:** "Unauthorized" w logach

**Rozwiązanie:**
1. Sprawdź czy token jest poprawny
2. Sprawdź czy bot jest aktywny
3. Testuj połączenie: `curl "http://localhost:8000/api/v2/telegram/test-connection"`

### Problem: Rate limiting
**Objawy:** "Zbyt wiele wiadomości" w odpowiedzi

**Rozwiązanie:**
1. Sprawdź ustawienie `TELEGRAM_RATE_LIMIT_PER_MINUTE`
2. Poczekaj minutę przed wysłaniem kolejnej wiadomości
3. Sprawdź czy nie ma wielu instancji aplikacji

### Problem: Długie wiadomości nie są wysyłane
**Objawy:** Wiadomości są obcinane

**Rozwiązanie:**
1. Sprawdź ustawienie `TELEGRAM_MAX_MESSAGE_LENGTH`
2. Sprawdź logi podziału wiadomości
3. Sprawdź czy webhook obsługuje długie wiadomości

## 📈 Optymalizacja Wydajności

### Rate Limiting
```python
# Domyślne ustawienia
TELEGRAM_RATE_LIMIT_PER_MINUTE = 30  # Wiadomości na minutę
TELEGRAM_MAX_MESSAGE_LENGTH = 4096    # Maksymalna długość wiadomości
```

### Caching
- Rate limiter cache w pamięci
- Bot settings cache
- Webhook status cache

### Monitoring
- Metryki odpowiedzi
- Metryki błędów
- Metryki wydajności

## 🔄 Aktualizacje

### Aktualizacja Konfiguracji
```bash
# Zatrzymaj aplikację
pkill -f "uvicorn backend.main:app"

# Zaktualizuj zmienne środowiskowe
# Uruchom ponownie
PYTHONPATH=src python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Aktualizacja Kodu
```bash
# Pull najnowszych zmian
git pull origin main

# Zaktualizuj zależności
poetry install

# Uruchom testy
pytest tests/ -v

# Uruchom aplikację
PYTHONPATH=src python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 📞 Wsparcie

### Dokumentacja
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram Bot Tutorial](https://core.telegram.org/bots/tutorial)
- [FoodSave AI Documentation](./README.md)

### Logi i Debugging
- Sprawdź logi aplikacji
- Użyj endpoint `/api/v2/telegram/test-connection`
- Sprawdź status webhook przez `/api/v2/telegram/webhook-info`

### Kontakt
- Zespół FoodSave AI Development
- GitHub Issues: [FoodSave AI Repository](https://github.com/foodsave-ai)

## ✅ Checklist Wdrożenia

- [ ] Zmienne środowiskowe skonfigurowane
- [ ] Bot utworzony przez BotFather
- [ ] Token skonfigurowany
- [ ] HTTPS endpoint dostępny
- [ ] Webhook ustawiony
- [ ] Test połączenia przechodzi
- [ ] Frontend skonfigurowany
- [ ] Testy przechodzą
- [ ] Monitoring skonfigurowany
- [ ] Dokumentacja zaktualizowana

## 🎉 Podsumowanie

Integracja Telegram Bot została pomyślnie wdrożona i jest gotowa do użycia. Użytkownicy mogą teraz komunikować się z asystentem AI bezpośrednio przez Telegram, korzystając z wszystkich funkcjonalności FoodSave AI.

**Status:** 🚀 **WDROŻENIE ZAKOŃCZONE POMYŚLNIE**

---

**Przewodnik przygotowany zgodnie z regułami `.cursorrules`**  
**Data:** 2025-06-25  
**Autor:** FoodSave AI Development Team 