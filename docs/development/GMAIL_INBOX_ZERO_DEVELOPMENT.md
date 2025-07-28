# Gmail Inbox Zero - Dokumentacja Techniczna

## Architektura

### Frontend (React/Next.js)
- **Lokalizacja**: `modern-frontend/src/app/gmail-inbox-zero/`
- **Główny komponent**: `page.tsx`
- **Stylizacja**: Tailwind CSS + shadcn/ui
- **Stan**: React hooks (useState, useEffect)

### Backend (FastAPI)
- **Lokalizacja**: `src/backend/api/v2/endpoints/gmail_inbox_zero.py`
- **Agent**: `src/backend/agents/gmail_inbox_zero_agent.py`
- **Modele danych**: Pydantic schemas

## API Endpoints

### 1. Health Check
```http
GET /api/v2/gmail-inbox-zero/health
```

**Odpowiedź:**
```json
{
  "success": true,
  "message": "Gmail Inbox Zero agent jest dostępny",
  "agent_metadata": {
    "name": "GmailInboxZeroAgent",
    "type": "GmailInboxZeroAgent",
    "capabilities": [
      "email_analysis",
      "label_management", 
      "archive_management",
      "learning_from_interactions",
      "pattern_recognition",
      "inbox_zero_optimization"
    ],
    "learning_data_count": 0,
    "patterns_count": 0,
    "gmail_api_available": false
  }
}
```

### 2. Statystyki użytkownika
```http
GET /api/v2/gmail-inbox-zero/stats/{user_id}
```

**Parametry:**
- `user_id`: ID użytkownika lub "current-user"

**Odpowiedź:**
```json
{
  "success": true,
  "data": {
    "total_messages": 150,
    "unread_messages": 25,
    "labeled_messages": 80,
    "archived_messages": 45,
    "deleted_messages": 10,
    "inbox_zero_percentage": 83.3,
    "learning_accuracy": 0.85,
    "last_analysis": "2025-07-19T20:41:12.682902"
  }
}
```

### 3. Analiza emaila
```http
POST /api/v2/gmail-inbox-zero/analyze
```

**Body:**
```json
{
  "user_id": "current-user",
  "session_id": "1234567890",
  "operation": "analyze",
  "message_id": "email_message_id"
}
```

**Odpowiedź:**
```json
{
  "success": true,
  "data": {
    "analysis": {
      "suggested_labels": ["Praca", "Ważne"],
      "should_archive": false,
      "requires_response": true,
      "priority": "high",
      "reasoning": "Email od szefa zawiera pilne zadanie",
      "confidence": 0.85
    }
  }
}
```

### 4. Aplikowanie etykiet
```http
POST /api/v2/gmail-inbox-zero/label
```

**Body:**
```json
{
  "user_id": "current-user",
  "session_id": "1234567890",
  "operation": "label",
  "message_id": "email_message_id",
  "labels": ["Praca", "Ważne"]
}
```

### 5. Archiwizacja
```http
POST /api/v2/gmail-inbox-zero/archive
```

**Body:**
```json
{
  "user_id": "current-user",
  "session_id": "1234567890",
  "operation": "archive",
  "message_id": "email_message_id"
}
```

### 6. Oznaczanie jako przeczytane
```http
POST /api/v2/gmail-inbox-zero/mark-read
```

**Body:**
```json
{
  "user_id": "current-user",
  "session_id": "1234567890",
  "operation": "mark_read",
  "message_id": "email_message_id"
}
```

## Modele danych

### EmailMessage (Frontend)
```typescript
interface EmailMessage {
  message_id: string;
  subject: string;
  sender: string;
  date: string;
  is_read: boolean;
  is_starred: boolean;
  labels: string[];
  snippet: string;
  priority?: 'high' | 'medium' | 'low';
}
```

### InboxStats (Frontend)
```typescript
interface InboxStats {
  total_messages: number;
  unread_messages: number;
  labeled_messages: number;
  archived_messages: number;
  deleted_messages: number;
  inbox_zero_percentage: number;
  learning_accuracy: number;
  last_analysis?: string;
}
```

### EmailAnalysis (Frontend)
```typescript
interface EmailAnalysis {
  suggested_labels: string[];
  should_archive: boolean;
  requires_response: boolean;
  priority: 'high' | 'medium' | 'low';
  reasoning: string;
  confidence: number;
}
```

## Integracja z Gmail API

### Wymagania
1. **Google Cloud Project** z włączonym Gmail API
2. **OAuth 2.0 credentials**
3. **Uprawnienia**: `https://www.googleapis.com/auth/gmail.modify`

### Konfiguracja
```python
# src/backend/config/gmail_config.py
GMAIL_CREDENTIALS_FILE = "path/to/credentials.json"
GMAIL_TOKEN_FILE = "path/to/token.json"
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly'
]
```

## Agent AI

### GmailInboxZeroAgent
```python
class GmailInboxZeroAgent(BaseAgent):
    def __init__(self):
        self.gmail_service = None
        self.learning_data = []
        self.patterns = {}
    
    async def get_inbox_stats(self, user_id: str) -> InboxZeroStats:
        """Pobiera statystyki skrzynki odbiorczej"""
        
    async def analyze_email(self, message_id: str) -> EmailAnalysis:
        """Analizuje email za pomocą AI"""
        
    async def apply_labels(self, message_id: str, labels: List[str]):
        """Aplikuje etykiety do emaila"""
        
    async def archive_email(self, message_id: str):
        """Archiwizuje email"""
        
    async def mark_as_read(self, message_id: str):
        """Oznacza email jako przeczytany"""
```

## Uczenie maszynowe

### Wzorce uczenia
Agent uczy się z interakcji użytkownika:
- **Priorytetyzacja**: Jakie emaile są ważne
- **Etykietowanie**: Jakie etykiety stosować
- **Archiwizacja**: Kiedy archiwizować
- **Odpowiedzi**: Które emaile wymagają odpowiedzi

### Dane treningowe
```python
learning_data = {
    "user_id": "user123",
    "message_id": "msg456",
    "action": "archive",
    "ai_suggestion": "archive",
    "user_decision": "archive",
    "timestamp": "2025-07-19T20:41:12.682902"
}
```

## Frontend - Komponenty

### Główny komponent
```typescript
export default function GmailInboxZeroPage() {
  const [stats, setStats] = useState<InboxStats | null>(null);
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null);
  const [analysis, setAnalysis] = useState<EmailAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  
  // Funkcje API
  const fetchStats = async () => { /* ... */ };
  const analyzeEmail = async (email: EmailMessage) => { /* ... */ };
  const applyLabels = async (messageId: string, labels: string[]) => { /* ... */ };
  const archiveEmail = async (messageId: string) => { /* ... */ };
  const markAsRead = async (messageId: string) => { /* ... */ };
}
```

### Tłumaczenia
Wszystkie teksty są przetłumaczone na polski:
- **Priorytety**: WYSOKI, ŚREDNI, NISKI
- **Akcje**: Analizuj, Zarchiwizuj, Oznacz jako Przeczytane
- **Etykiety**: Praca, Osobiste, Finanse, Newsletter

## Testowanie

### Testy jednostkowe
```bash
# Testy agenta
pytest tests/unit/test_gmail_inbox_zero_agent.py

# Testy API
pytest tests/integration/test_gmail_inbox_zero_api.py

# Testy frontendu
npm test -- --testPathPattern=gmail-inbox-zero
```

### Testy E2E
```bash
# Testy pełnego przepływu
pytest tests/e2e/test_gmail_inbox_zero_e2e.py
```

## Deployment

### Docker
```yaml
# docker-compose.yaml
frontend:
  build: ./modern-frontend
  ports:
    - "8085:3000"
  environment:
    - NEXT_PUBLIC_API_URL=http://localhost:8000

backend:
  build: ./src/backend
  ports:
    - "8000:8000"
  environment:
    - GMAIL_CREDENTIALS_FILE=/app/credentials.json
```

### Zmienne środowiskowe
```bash
# Backend
GMAIL_CREDENTIALS_FILE=path/to/credentials.json
GMAIL_TOKEN_FILE=path/to/token.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.modify

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Monitoring

### Metryki
- Liczba analizowanych emaili
- Dokładność sugestii AI
- Czas odpowiedzi API
- Liczba błędów

### Logi
```python
import structlog

logger = structlog.get_logger()
logger.info("Email analyzed", 
           message_id=message_id, 
           priority=priority, 
           confidence=confidence)
```

## Bezpieczeństwo

### Autoryzacja
- OAuth 2.0 dla Gmail API
- JWT tokens dla sesji użytkownika
- Rate limiting na endpointach

### Szyfrowanie
- HTTPS dla wszystkich połączeń
- Szyfrowanie danych w bazie
- Bezpieczne przechowywanie tokenów

## Rozwiązywanie problemów

### Częste problemy

1. **404 na endpointach**
   - Sprawdź czy backend działa na porcie 8000
   - Sprawdź routing w FastAPI

2. **CORS błędy**
   - Sprawdź konfigurację CORS w backendzie
   - Upewnij się, że frontend ma dostęp do API

3. **Błędy Gmail API**
   - Sprawdź uprawnienia OAuth
   - Odśwież tokeny dostępu

4. **Problemy z AI**
   - Sprawdź logi agenta
   - Sprawdź dostępność modeli Ollama

### Debugowanie
```bash
# Logi backendu
docker logs foodsave-backend

# Logi frontendu
docker logs foodsave-frontend

# Test API
curl -v http://localhost:8000/api/v2/gmail-inbox-zero/health
```

## Przyszłe rozszerzenia

### Planowane funkcje
1. **Integracja z kalendarzem** - Automatyczne tworzenie wydarzeń
2. **Szablony odpowiedzi** - AI generuje odpowiedzi
3. **Analiza sentymentu** - Wykrywanie emocji w emailach
4. **Integracja z CRM** - Automatyczne kategoryzowanie klientów
5. **Raporty zaawansowane** - Szczegółowa analityka

### Optymalizacje
1. **Caching** - Redis dla często używanych danych
2. **Batch processing** - Masowe przetwarzanie emaili
3. **Real-time updates** - WebSocket dla live updates
4. **Offline mode** - Praca bez internetu 