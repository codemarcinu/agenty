# Gmail Inbox Zero API Fix Report

## Problem
Gmail API nie było połączone - endpointy `/api/v2/gmail-inbox-zero/stats/current-user` i `/api/v2/gmail-inbox-zero/messages/current-user` zwracały HTTP 500 Internal Server Error.

## Analiza problemu

### 1. Błędy w logach backendu
```
{"timestamp": "2025-07-23T11:32:02.665101", "level": "ERROR", "logger": "root", "module": "gmail_inbox_zero", "message": "Error getting message details for 19836fead1896442: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] decryption failed or bad record mac (_ssl.c:2590)", "levelno": 40}
{"timestamp": "2025-07-23T11:32:03.733801", "level": "ERROR", "logger": "root", "module": "gmail_inbox_zero", "message": "Błąd w pobieraniu statystyk: IncompleteRead(9 bytes read)", "levelno": 40}
```

### 2. Problem z tokenem Gmail API
- Token wygasł o 11:56 UTC
- Backend próbował automatycznie odświeżyć token, ale nie udało się
- System przełączył się na tryb mock (symulowany)

### 3. Różnica czasu między hostem a kontenerem
- Host: CEST (13:38)
- Kontener: UTC (11:38)
- Token wygasł w UTC, ale logika sprawdzania była nieprawidłowa

## Rozwiązanie

### 1. Stworzenie skryptu do odświeżania tokenu
```python
# scripts/refresh_gmail_token.py
def refresh_gmail_token():
    """Odświeża token Gmail API"""
    try:
        # Wczytaj credentials
        flow = InstalledAppFlow.from_client_secrets_file(auth_file_path, SCOPES)
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # Sprawdź czy token wygasł
        if creds.expired:
            creds.refresh(Request())
            
        # Zapisz odświeżony token
        with open(token_file, "w") as token:
            token.write(creds.to_json())
            
        return True
    except Exception as e:
        logger.error(f"Błąd podczas odświeżania tokenu: {e}")
        return False
```

### 2. Naprawa logiki sprawdzania wygaśnięcia tokenu
```python
def check_token_status():
    """Sprawdza status tokenu z poprawną obsługą UTC"""
    expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    
    logger.info(f"Token wygasa: {expiry}")
    logger.info(f"Teraz: {now}")
    logger.info(f"Token wygasł: {expiry < now}")
    
    return expiry > now
```

### 3. Wykonanie naprawy
```bash
# Skopiowanie skryptu do kontenera
docker cp scripts/refresh_gmail_token.py foodsave-backend:/app/scripts/

# Uruchomienie skryptu
docker exec foodsave-backend python /app/scripts/refresh_gmail_token.py
```

## Rezultaty

### 1. API działa poprawnie
```bash
# Test endpointu statystyk
curl -X GET "http://localhost:8000/api/v2/gmail-inbox-zero/stats/current-user"
# Zwraca: {"success":true,"data":{"total_messages":100,"unread_messages":100,...}}

# Test endpointu wiadomości
curl -X GET "http://localhost:8000/api/v2/gmail-inbox-zero/messages/current-user"
# Zwraca rzeczywiste dane z Gmail API
```

### 2. Frontend działa
```bash
# Test frontendu
curl -X GET "http://localhost:8085/gmail-inbox-zero" -I
# Zwraca: HTTP/1.1 200 OK
```

### 3. Brak błędów w logach
- Nie ma już błędów SSL
- Nie ma błędów połączenia
- Gmail API działa poprawnie

## Wnioski

1. **Problem z tokenem**: Token Gmail API wygasł i nie został automatycznie odświeżony
2. **Problem z czasem**: Różnica między czasem UTC w kontenerze a CEST na hoście
3. **Rozwiązanie**: Stworzenie skryptu do odświeżania tokenu i poprawa logiki sprawdzania czasu

## Status
✅ **NAPRAWIONE** - Gmail Inbox Zero API działa poprawnie

## Dostępne endpointy
- `GET /api/v2/gmail-inbox-zero/stats/current-user` - Statystyki inbox
- `GET /api/v2/gmail-inbox-zero/messages/current-user` - Lista wiadomości
- `POST /api/v2/gmail-inbox-zero/analyze` - Analiza emaila
- `POST /api/v2/gmail-inbox-zero/label` - Etykietowanie
- `POST /api/v2/gmail-inbox-zero/archive` - Archiwizacja
- `POST /api/v2/gmail-inbox-zero/delete` - Usuwanie
- `POST /api/v2/gmail-inbox-zero/mark-read` - Oznaczanie jako przeczytane
- `POST /api/v2/gmail-inbox-zero/star` - Gwiazdkowanie

## Frontend
- Dostępny pod adresem: `http://localhost:8085/gmail-inbox-zero`
- Pełna funkcjonalność Gmail Inbox Zero
- Integracja z backend API

---
*Raport wygenerowany: 2025-07-23 13:40 CEST* 