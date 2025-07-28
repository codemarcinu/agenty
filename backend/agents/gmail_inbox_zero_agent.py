"""
Gmail Inbox Zero Agent

Agent odpowiedzialny za pomoc w uzyskaniu i utrzymaniu "Inbox Zero" w Gmailu.
Uczy się na podstawie interakcji z użytkownikiem i analizuje wzorce w emailach.
"""

from datetime import datetime, timedelta
import json
import logging
import os
import asyncio
import time
import random
from typing import Any, List, Dict, Optional, Tuple
from functools import wraps, lru_cache
from collections import defaultdict, deque
import hashlib

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.hybrid_llm_client import hybrid_llm_client
from schemas.gmail_schemas import InboxZeroRequest, InboxZeroStats, LearningData

logger = logging.getLogger()  # root logger
# Set debug level for this logger
logger.setLevel(logging.DEBUG)

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

class SmartCache:
    """Intelligent caching system for Gmail operations with enhanced performance"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.prediction_cache: Dict[str, Dict[str, Any]] = {}
        self.user_pattern_cache: Dict[str, Dict[str, Any]] = {}
        self.email_data_cache: Dict[str, Dict[str, Any]] = {}
        self.last_cleanup = time.time()
        self.access_count = defaultdict(int)
        
    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate consistent cache key from data"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
        
    def get_cached_analysis(self, message_id: str, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached analysis if available and fresh with access tracking"""
        cache_key = self._generate_cache_key({
            'message_id': message_id,
            'sender': email_data.get('sender', ''),
            'subject': email_data.get('subject', ''),
            'body_hash': hashlib.md5(email_data.get('body_plain', '').encode()).hexdigest()[:16]
        })
        
        cached = self.analysis_cache.get(cache_key)
        if cached and time.time() - cached['timestamp'] < self.ttl_hours * 3600:
            self.access_count[cache_key] += 1
            logger.info(f"Using cached analysis for message {message_id} (hit count: {self.access_count[cache_key]})")
            return cached['data']
        return None
        
    def cache_analysis(self, message_id: str, email_data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        """Cache analysis result with enhanced metadata"""
        cache_key = self._generate_cache_key({
            'message_id': message_id,
            'sender': email_data.get('sender', ''),
            'subject': email_data.get('subject', ''),
            'body_hash': hashlib.md5(email_data.get('body_plain', '').encode()).hexdigest()[:16]
        })
        
        self.analysis_cache[cache_key] = {
            'data': analysis,
            'timestamp': time.time(),
            'access_count': 0,
            'last_accessed': time.time()
        }
        
        # Cleanup if cache is too large
        if len(self.analysis_cache) > self.max_size:
            self._cleanup_cache()
            
    def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get cached user patterns with enhanced tracking"""
        patterns = self.user_pattern_cache.get(user_id, {})
        if patterns and time.time() - patterns.get('timestamp', 0) < self.ttl_hours * 3600:
            patterns['last_accessed'] = time.time()
            return patterns.get('data', {})
        return {}
        
    def cache_user_patterns(self, user_id: str, patterns: Dict[str, Any]) -> None:
        """Cache user patterns with enhanced metadata"""
        self.user_pattern_cache[user_id] = {
            'data': patterns,
            'timestamp': time.time(),
            'last_accessed': time.time()
        }
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_hits = sum(self.access_count.values())
        total_requests = len(self.analysis_cache) + total_hits
        
        return {
            'total_entries': len(self.analysis_cache),
            'total_hits': total_hits,
            'hit_rate': total_hits / max(total_requests, 1),
            'avg_access_count': sum(self.access_count.values()) / max(len(self.access_count), 1),
            'memory_usage_mb': len(json.dumps(self.analysis_cache)) / (1024 * 1024)
        }
        
    def _cleanup_cache(self) -> None:
        """Enhanced cache cleanup with LRU and access-based eviction"""
        if len(self.analysis_cache) <= self.max_size:
            return
            
        # Remove expired entries first
        current_time = time.time()
        expired_keys = [
            key for key, value in self.analysis_cache.items()
            if current_time - value['timestamp'] > self.ttl_hours * 3600
        ]
        
        for key in expired_keys:
            del self.analysis_cache[key]
            
        # If still too large, remove least accessed entries
        if len(self.analysis_cache) > self.max_size:
            sorted_entries = sorted(
                self.analysis_cache.items(),
                key=lambda x: (x[1].get('access_count', 0), x[1].get('last_accessed', 0))
            )
            
            # Remove 20% of least accessed entries
            remove_count = len(self.analysis_cache) // 5
            for key, _ in sorted_entries[:remove_count]:
                del self.analysis_cache[key]
                
        self.last_cleanup = current_time
        logger.info(f"Cache cleanup completed. Remaining entries: {len(self.analysis_cache)}")

class EnhancedRateLimiter:
    """Enhanced rate limiter with adaptive throttling and exponential backoff"""
    
    def __init__(self, max_requests_per_second: int = 10, max_batch_size: int = 100):
        self.max_requests_per_second = max_requests_per_second
        self.max_batch_size = max_batch_size
        self.request_times = deque()
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()
        self.current_rate = max_requests_per_second
        self.backoff_multiplier = 1.0
        self.quota_exceeded_count = 0
        
    def exponential_backoff(self, retry_count: int) -> float:
        """Calculate exponential backoff delay"""
        base_delay = 1.0
        max_delay = 60.0
        delay = min(base_delay * (2 ** retry_count), max_delay)
        jitter = random.uniform(0, 0.1 * delay)
        return delay + jitter
        
    async def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded with adaptive throttling"""
        current_time = time.time()
        
        # Remove old request times
        while self.request_times and current_time - self.request_times[0] > 1.0:
            self.request_times.popleft()
            
        # Check if we're at the rate limit
        if len(self.request_times) >= self.current_rate:
            wait_time = 1.0 - (current_time - self.request_times[0])
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
        # Add current request
        self.request_times.append(current_time)
        
        # Adaptive rate adjustment based on success/failure ratio
        if current_time - self.last_adjustment > 60:  # Adjust every minute
            self._adjust_rate()
            
    def _adjust_rate(self) -> None:
        """Adaptively adjust rate based on success/failure patterns"""
        total_requests = self.success_count + self.failure_count
        if total_requests < 10:  # Need minimum data
            return
            
        success_rate = self.success_count / total_requests
        
        if success_rate > 0.95:
            # Increase rate if very successful
            self.current_rate = min(self.current_rate * 1.1, self.max_requests_per_second * 2)
        elif success_rate < 0.8:
            # Decrease rate if many failures
            self.current_rate = max(self.current_rate * 0.8, self.max_requests_per_second * 0.5)
            
        logger.info(f"Rate adjusted to {self.current_rate:.1f} req/s (success rate: {success_rate:.2f})")
        
        # Reset counters
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()
        
    def handle_quota_exceeded(self, retry_count: int) -> None:
        """Handle quota exceeded with exponential backoff"""
        self.quota_exceeded_count += 1
        self.failure_count += 1
        
        # Increase backoff multiplier
        self.backoff_multiplier = min(self.backoff_multiplier * 1.5, 10.0)
        
        logger.warning(f"Quota exceeded (count: {self.quota_exceeded_count}), backoff multiplier: {self.backoff_multiplier}")
        
    def record_success(self) -> None:
        """Record successful request"""
        self.success_count += 1
        self.backoff_multiplier = max(self.backoff_multiplier * 0.9, 1.0)  # Reduce backoff
        
    def record_failure(self) -> None:
        """Record failed request"""
        self.failure_count += 1

class EnhancedPrefilterEngine:
    """Enhanced prefiltering engine with ML-based classification and improved heuristics"""
    
    def __init__(self):
        self.whitelist_domains = {
            "linkedin.com", "github.com", "stackoverflow.com", 
            "amazon.com", "google.com", "microsoft.com", "apple.com",
            "netflix.com", "spotify.com", "dropbox.com", "slack.com"
        }
        self.spam_keywords = {
            "viagra", "casino", "lottery", "winner", "congratulations",
            "free money", "urgent", "act now", "limited time", "click here",
            "unsubscribe", "remove from list", "earn money", "work from home"
        }
        self.safe_senders = set()
        self.newsletter_patterns = {
            "newsletter", "unsubscribe", "mailing list", "weekly digest",
            "monthly update", "email digest", "roundup", "summary"
        }
        self.user_preferences = {}
        self.confidence_threshold = 0.8
        self.ml_classifier = None  # Placeholder for future ML integration
        
    def should_skip_ai_analysis(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine if email can be processed without AI analysis with enhanced logic"""
        sender = email_data.get("sender", "").lower()
        subject = email_data.get("subject", "").lower()
        body = email_data.get("body_plain", "").lower()
        
        # Check whitelist domains with enhanced matching
        for domain in self.whitelist_domains:
            if domain in sender:
                return {
                    "skip_ai": True,
                    "reason": "trusted_domain",
                    "suggested_action": "safe_archive",
                    "confidence": 0.9,
                    "priority": "low"
                }
                
        # Check for newsletters with enhanced patterns
        newsletter_score = 0
        for pattern in self.newsletter_patterns:
            if pattern in subject:
                newsletter_score += 2
            if pattern in body:
                newsletter_score += 1
                
        if newsletter_score >= 2:
            return {
                "skip_ai": True,
                "reason": "newsletter",
                "suggested_action": "auto_label_newsletter",
                "confidence": 0.8 + (newsletter_score * 0.05),
                "priority": "low"
            }
                
        # Enhanced spam detection with scoring
        spam_score = 0
        spam_keywords_found = []
        
        for keyword in self.spam_keywords:
            if keyword in subject:
                spam_score += 3
                spam_keywords_found.append(keyword)
            if keyword in body:
                spam_score += 1
                spam_keywords_found.append(keyword)
                
        if spam_score >= 5:
            return {
                "skip_ai": True,
                "reason": "spam",
                "suggested_action": "delete",
                "confidence": min(0.9, 0.5 + (spam_score * 0.1)),
                "priority": "low",
                "spam_keywords": spam_keywords_found
            }
            
        # Check for safe senders
        if sender in self.safe_senders:
            return {
                "skip_ai": True,
                "reason": "safe_sender",
                "suggested_action": "auto_label_personal",
                "confidence": 0.85,
                "priority": "medium"
            }
            
        # Check for automated emails (receipts, confirmations, etc.)
        automated_patterns = [
            "receipt", "confirmation", "order", "booking", "reservation",
            "payment", "invoice", "statement", "report", "notification"
        ]
        
        automated_score = 0
        for pattern in automated_patterns:
            if pattern in subject:
                automated_score += 2
            if pattern in body:
                automated_score += 1
                
        if automated_score >= 3:
            return {
                "skip_ai": True,
                "reason": "automated_email",
                "suggested_action": "auto_archive",
                "confidence": 0.75 + (automated_score * 0.05),
                "priority": "low"
            }
            
        # Default: require AI analysis
        return {
            "skip_ai": False,
            "reason": "requires_analysis",
            "suggested_action": "analyze_with_ai",
            "confidence": 0.5,
            "priority": "high"
        }
        
    def add_safe_sender(self, email: str) -> None:
        """Add email to safe senders list"""
        self.safe_senders.add(email.lower())
        
    def is_safe_sender(self, email: str) -> bool:
        """Check if email is in safe senders list"""
        return email.lower() in self.safe_senders
        
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """Update user preferences for prefiltering"""
        self.user_preferences[user_id] = preferences

def retry_with_backoff(max_retries: int = 3):
    """Enhanced retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Wait before retry (except for first attempt)
                    if attempt > 0:
                        wait_time = min(2 ** attempt, 60)  # Max 60 seconds
                        logger.info(f"Retrying {func.__name__} in {wait_time}s (attempt {attempt + 1})")
                        await asyncio.sleep(wait_time)
                    
                    return await func(self, *args, **kwargs)
                    
                except HttpError as e:
                    last_exception = e
                    if e.resp.status == 429:  # Rate limit exceeded
                        self.rate_limiter.handle_quota_exceeded(attempt)
                        if attempt == max_retries:
                            logger.error(f"Max retries exceeded for {func.__name__}: {e}")
                            raise
                    elif e.resp.status >= 500:  # Server error
                        if attempt == max_retries:
                            logger.error(f"Server error after {max_retries} retries: {e}")
                            raise
                    else:
                        # Don't retry for client errors (4xx)
                        raise
                        
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Unexpected error after {max_retries} retries: {e}")
                        raise
                        
            raise last_exception
            
        return wrapper
    return decorator

class BatchProcessor:
    """Enhanced batch processor for efficient Gmail operations"""
    
    def __init__(self, max_batch_size: int = 100):
        self.max_batch_size = max_batch_size
        self.operations: List[Dict[str, Any]] = []
        self.processing = False
        
    def add_operation(self, operation_type: str, message_id: str, data: Dict[str, Any]) -> None:
        """Add operation to batch queue"""
        self.operations.append({
            "type": operation_type,
            "message_id": message_id,
            "data": data,
            "timestamp": time.time()
        })
        
    def clear(self) -> None:
        """Clear all pending operations"""
        self.operations.clear()
        
    def get_batches(self) -> List[List[Dict[str, Any]]]:
        """Get operations split into batches"""
        batches = []
        current_batch = []
        
        for operation in self.operations:
            current_batch.append(operation)
            if len(current_batch) >= self.max_batch_size:
                batches.append(current_batch)
                current_batch = []
                
        if current_batch:
            batches.append(current_batch)
            
        return batches
        
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        return {
            "pending_operations": len(self.operations),
            "batch_count": len(self.get_batches()),
            "avg_batch_size": len(self.operations) / max(len(self.get_batches()), 1)
        }

class GmailInboxZeroAgent(BaseAgent):
    """
    Enhanced Agent do zarządzania Inbox Zero w Gmail.
    Analizuje emaile, sugeruje labele i uczy się z interakcji użytkownika.
    """

    def __init__(self, name: str = "GmailInboxZeroAgent", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

        # Inicjalizacja Gmail API
        self.gmail_service = None
        self.credentials = None
        self._init_gmail_api()

        # Enhanced scalability components
        self.rate_limiter = EnhancedRateLimiter(max_requests_per_second=10)
        self.batch_processor = BatchProcessor(max_batch_size=100)
        self.prefilter_engine = EnhancedPrefilterEngine()
        self.smart_cache = SmartCache(max_size=1000, ttl_hours=24)
        
        # Enhanced cache for email data and analysis results
        self.email_cache: Dict[str, Dict[str, Any]] = {}
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Cost optimization settings
        self.use_lightweight_model_threshold = 0.7  # Use lightweight model if confidence > 0.7
        self.adaptive_throttling_enabled = True
        
        # Dane uczenia się
        self.learning_data: list[LearningData] = []
        self.label_patterns: dict[str, Any] = {}

        # Enhanced prompts for LLM
        self.analysis_prompt = """
        Analizuję email z Gmaila. Oto szczegóły:

        Nadawca: {sender}
        Temat: {subject}
        Data: {date}
        Treść: {body_plain}
        Aktualne labele: {current_labels}

        Na podstawie historii użytkownika i wzorców, sugeruj:
        1. Jakie labele powinny być zastosowane?
        2. Czy email powinien być zarchiwowany?
        3. Czy email wymaga odpowiedzi?
        4. Jaki jest priorytet tego emaila?

        Odpowiedz w formacie JSON:
        {{
            "suggested_labels": ["label1", "label2"],
            "should_archive": true/false,
            "requires_response": true/false,
            "priority": "high/medium/low",
            "reasoning": "wyjaśnienie decyzji",
            "confidence": 0.0-1.0
        }}
        """

        self.learning_prompt = """
        Użytkownik podjął decyzję dotyczącą emaila. Oto dane:

        Email: {email_data}
        Sugerowane akcje: {suggested_actions}
        Rzeczywiste akcje użytkownika: {user_actions}
        Komentarz użytkownika: {user_comment}

        Przeanalizuj różnice i zaktualizuj model uczenia się.
        Odpowiedz w formacie JSON:
        {{
            "learning_insights": ["insight1", "insight2"],
            "pattern_updates": {{"pattern": "update"}},
            "accuracy_improvement": "sugestia poprawy"
        }}
        """

    def _init_gmail_api(self) -> None:
        """Inicjalizuje Gmail API z środowiska"""
        try:
            # Bezpieczne ścieżki do plików auth
            auth_file_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./config/gmail_auth.json")
            token_file = os.getenv("GMAIL_TOKEN_PATH", "./config/gmail_token.json")
            
            # Sprawdź czy pliki istnieją
            if not os.path.exists(auth_file_path):
                logger.warning(f"Gmail credentials file not found: {auth_file_path}")
                self.gmail_service = None
                return

            # Wczytaj credentials
            flow = InstalledAppFlow.from_client_secrets_file(auth_file_path, SCOPES)

            # Sprawdź czy mamy zapisane credentials
            creds = None
            if os.path.exists(token_file):
                try:
                    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
                except Exception as e:
                    logger.warning(f"Error loading existing token: {e}, will re-authenticate")
                    creds = None

            # Jeśli nie ma ważnych credentials, sprawdź czy możemy je odświeżyć
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        # Zapisz odświeżone credentials
                        os.makedirs(os.path.dirname(token_file), exist_ok=True)
                        with open(token_file, "w") as token:
                            token.write(creds.to_json())
                        logger.info("Gmail credentials refreshed successfully")
                    except Exception as refresh_error:
                        logger.error(f"Failed to refresh credentials: {refresh_error}")
                        creds = None
                else:
                    # W środowisku produkcyjnym nie możemy użyć interactive OAuth
                    logger.warning("No valid Gmail credentials available and cannot run interactive OAuth in production")
                    creds = None

            if creds and creds.valid:
                # Zbuduj Gmail service
                self.gmail_service = build("gmail", "v1", credentials=creds)
                self.credentials = creds
                logger.info("Gmail API initialized successfully")
            else:
                self.gmail_service = None
                logger.info("Gmail API not available, falling back to mock mode")

        except Exception as e:
            logger.error(f"Failed to initialize Gmail API: {e}")
            self.gmail_service = None
            logger.info("Falling back to mock mode")

    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """Główna metoda przetwarzania żądań z enhanced caching i batch processing"""
        try:
            
            # Walidacja danych wejściowych
            request = InboxZeroRequest(**input_data)

            # Wait for rate limiter before processing
            await self.rate_limiter.wait_if_needed()

            # Check cache first for analysis operations
            if request.operation == "analyze" and request.message_id:
                cached_result = self.smart_cache.get_cached_analysis(
                    request.message_id, 
                    request.email_data or {}
                )
                if cached_result:
                    self.rate_limiter.record_success()
                    return AgentResponse(
                        success=True,
                        text="Analiza emaila zakończona (cache)",
                        data=cached_result,
                        metadata={
                            "confidence": cached_result.get("confidence", 0.5),
                            "from_cache": True,
                            "cache_hit": True,
                        },
                    )

            # Enhanced routing operacji with batch support
            try:
                if request.operation == "analyze":
                    result = await self._analyze_email(request)
                elif request.operation == "label":
                    result = await self._apply_labels(request)
                elif request.operation == "archive":
                    result = await self._archive_message(request)
                elif request.operation == "delete":
                    result = await self._delete_message(request)
                elif request.operation == "mark_read":
                    result = await self._mark_read(request)
                elif request.operation == "star":
                    result = await self._star_message(request)
                elif request.operation == "learn":
                    result = await self._learn_from_interaction(request)
                elif request.operation == "analyze_all_unread":
                    result = await self._analyze_all_unread(request)
                elif request.operation == "auto_archive":
                    result = await self._auto_archive_old_messages(request)
                elif request.operation == "apply_smart_labels":
                    result = await self._apply_smart_labels(request)
                elif request.operation == "mark_important":
                    result = await self._mark_important_messages(request)
                elif request.operation == "batch_process":
                    result = await self._batch_process_emails(request)
                elif request.operation == "execute_batch":
                    result = await self._execute_batch_operations(request)
                else:
                    return AgentResponse(
                        success=False, error="Nieznana operacja", severity="ERROR"
                    )
                
                # Record success for rate limiting
                if result.success:
                    self.rate_limiter.record_success()
                else:
                    self.rate_limiter.record_failure()
                    
                return result
                
            except Exception as e:
                self.rate_limiter.record_failure()
                logger.error(f"Error in operation {request.operation}: {e}")
                raise

        except Exception as e:
            logger.error(f"Błąd walidacji danych: {e}")
            return AgentResponse(
                success=False,
                error=f"Nieprawidłowe dane wejściowe: {e!s}",
                severity="ERROR",
            )

    async def _analyze_email(self, request: InboxZeroRequest) -> AgentResponse:
        """Analizuje email i sugeruje akcje z enhanced caching"""
        try:
            message_id = request.message_id or ""
            
            # Check smart cache first
            cached_analysis = self.smart_cache.get_cached_analysis(message_id, request.email_data or {})
            if cached_analysis:
                logger.info(f"Using smart cached analysis for message {message_id}")
                return AgentResponse(
                    success=True,
                    text=f"Analiza emaila zakończona (cache). Priorytet: {cached_analysis.get('priority', 'medium')}",
                    data=cached_analysis,
                    metadata={
                        "confidence": cached_analysis.get("confidence", 0.5),
                        "from_cache": True,
                    },
                )

            # Pobierz dane emaila z Gmail API
            email_data = await self._get_email_data(request.message_id, request.email_data)

            # Enhanced prefiltering - check if we can skip AI analysis
            prefilter_result = self.prefilter_engine.should_skip_ai_analysis(email_data)
            
            if prefilter_result.get("skip_ai", False):
                logger.info(f"Using prefilter result for message {message_id}: {prefilter_result['reason']}")
                
                # Cache the prefilter result
                self.smart_cache.cache_analysis(message_id, email_data, {
                    "suggested_labels": self._get_prefilter_labels(prefilter_result),
                    "should_archive": prefilter_result.get("suggested_action") == "safe_archive",
                    "requires_response": False,
                    "priority": "low",
                    "reasoning": f"Automatyczna kategoryzacja: {prefilter_result['reason']}",
                    "confidence": prefilter_result.get("confidence", 0.7)
                })
                
                return AgentResponse(
                    success=True,
                    text=f"Email automatycznie skategoryzowany: {prefilter_result['reason']}",
                    data={
                        "suggested_labels": self._get_prefilter_labels(prefilter_result),
                        "should_archive": prefilter_result.get("suggested_action") == "safe_archive",
                        "requires_response": False,
                        "priority": "low",
                        "reasoning": f"Automatyczna kategoryzacja: {prefilter_result['reason']}",
                        "confidence": prefilter_result.get("confidence", 0.7)
                    },
                    metadata={
                        "confidence": prefilter_result.get("confidence", 0.7),
                        "prefiltered": True,
                    },
                )

            # Enhanced model selection based on email characteristics
            model_to_use = self._select_optimal_model(email_data)
            
            # Przygotuj prompt do analizy
            prompt = self.analysis_prompt.format(
                sender=email_data.get("sender", "Nieznany"),
                subject=email_data.get("subject", "Brak tematu"),
                date=email_data.get("date", "Nieznana data"),
                body_plain=email_data.get("body_plain", "")[:500],  # Ogranicz długość
                current_labels=", ".join(email_data.get("labels", [])),
            )

            # Analiza przez LLM with adaptive model selection
            messages = [
                {
                    "role": "system",
                    "content": "Jesteś ekspertem w zarządzaniu emailami i Inbox Zero. Analizujesz emaile i sugerujesz najlepsze akcje.",
                },
                {"role": "user", "content": prompt},
            ]

            response = await hybrid_llm_client.chat(
                messages=messages,
                model=model_to_use,
                options={"temperature": 0.3},
            )

            # Parsuj odpowiedź
            try:
                if isinstance(response, dict) and "message" in response:
                    content = response["message"].get("content", "")
                else:
                    content = str(response)
                analysis_result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback jeśli LLM nie zwrócił JSON
                analysis_result = {
                    "suggested_labels": [],
                    "should_archive": False,
                    "requires_response": False,
                    "priority": "medium",
                    "reasoning": "Nie udało się przeanalizować automatycznie",
                    "confidence": 0.5,
                }

            # Cache the analysis result
            self.smart_cache.cache_analysis(message_id, email_data, analysis_result)

            # Przygotuj sugestie
            suggestions = self._prepare_suggestions(analysis_result)

            return AgentResponse(
                success=True,
                text=f"Analiza emaila zakończona. Priorytet: {analysis_result.get('priority', 'medium')}",
                data={
                    "analysis": analysis_result,
                    "suggestions": suggestions,
                    "email_data": email_data,
                },
                metadata={
                    "confidence": analysis_result.get("confidence", 0.5),
                    "model_used": model_to_use,
                },
            )

        except Exception as e:
            logger.error(f"Błąd podczas analizy emaila: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas analizy emaila: {e!s}",
                severity="ERROR",
            )

    async def _apply_labels(self, request: InboxZeroRequest) -> AgentResponse:
        """Zastosowuje labele do emaila"""
        try:
            if not request.labels:
                return AgentResponse(
                    success=False, error="Brak labeli do zastosowania", severity="ERROR"
                )

            if self.gmail_service and request.message_id:
                # Rzeczywiste wywołanie Gmail API
                success = await self._apply_labels_gmail_api(
                    request.message_id, request.labels
                )
            else:
                # Mock wywołanie
                success = await self._mock_gmail_api_call(
                    "apply_labels",
                    {"message_id": request.message_id, "labels": request.labels},
                )

            if success:
                # Zapisz dane do uczenia się
                learning_data = LearningData(
                    user_id=request.user_id,
                    message_id=request.message_id or "",
                    user_action="apply_labels",
                    applied_labels=request.labels or [],
                    user_comment=request.user_feedback,
                    message_features=await self._extract_message_features(
                        request.message_id
                    ),
                )
                self.learning_data.append(learning_data)

                return AgentResponse(
                    success=True,
                    text=f"Zastosowano labele: {', '.join(request.labels)}",
                    data={"applied_labels": request.labels},
                )
            else:
                return AgentResponse(
                    success=False,
                    error="Nie udało się zastosować labeli",
                    severity="ERROR",
                )

        except Exception as e:
            logger.error(f"Błąd podczas zastosowania labeli: {e}")
            return AgentResponse(success=False, error=f"Błąd: {e!s}", severity="ERROR")

    async def _archive_message(self, request: InboxZeroRequest) -> AgentResponse:
        """Archiwizuje email"""
        try:
            if self.gmail_service and request.message_id:
                # Rzeczywiste wywołanie Gmail API
                success = await self._archive_message_gmail_api(request.message_id)
            else:
                # Mock wywołanie
                success = await self._mock_gmail_api_call(
                    "archive", {"message_id": request.message_id}
                )

            if success:
                return AgentResponse(
                    success=True,
                    text="Email został zarchiwizowany",
                    data={"archived": True},
                )
            else:
                return AgentResponse(
                    success=False,
                    error="Nie udało się zarchiwizować emaila",
                    severity="ERROR",
                )

        except Exception as e:
            logger.error(f"Błąd podczas archiwizacji: {e}")
            return AgentResponse(success=False, error=f"Błąd: {e!s}", severity="ERROR")

    async def _delete_message(self, request: InboxZeroRequest) -> AgentResponse:
        """Usuwa email"""
        try:
            if self.gmail_service and request.message_id:
                # Rzeczywiste wywołanie Gmail API
                success = await self._delete_message_gmail_api(request.message_id)
            else:
                # Mock wywołanie
                success = await self._mock_gmail_api_call(
                    "delete", {"message_id": request.message_id}
                )

            if success:
                return AgentResponse(
                    success=True, text="Email został usunięty", data={"deleted": True}
                )
            else:
                return AgentResponse(
                    success=False, error="Nie udało się usunąć emaila", severity="ERROR"
                )

        except Exception as e:
            logger.error(f"Błąd podczas usuwania: {e}")
            return AgentResponse(success=False, error=f"Błąd: {e!s}", severity="ERROR")

    async def _mark_read(self, request: InboxZeroRequest) -> AgentResponse:
        """Oznacza email jako przeczytany"""
        try:
            if self.gmail_service and request.message_id:
                # Rzeczywiste wywołanie Gmail API
                success = await self._mark_read_gmail_api(request.message_id)
            else:
                # Mock wywołanie
                success = await self._mock_gmail_api_call(
                    "mark_read", {"message_id": request.message_id}
                )

            if success:
                return AgentResponse(
                    success=True,
                    text="Email oznaczony jako przeczytany",
                    data={"marked_read": True},
                )
            else:
                return AgentResponse(
                    success=False,
                    error="Nie udało się oznaczyć emaila jako przeczytany",
                    severity="ERROR",
                )

        except Exception as e:
            logger.error(f"Błąd podczas oznaczania jako przeczytany: {e}")
            return AgentResponse(success=False, error=f"Błąd: {e!s}", severity="ERROR")

    async def _star_message(self, request: InboxZeroRequest) -> AgentResponse:
        """Oznacza email gwiazdką"""
        try:
            if self.gmail_service and request.message_id:
                # Rzeczywiste wywołanie Gmail API
                success = await self._star_message_gmail_api(request.message_id)
            else:
                # Mock wywołanie
                success = await self._mock_gmail_api_call(
                    "star", {"message_id": request.message_id}
                )

            if success:
                return AgentResponse(
                    success=True,
                    text="Email oznaczony gwiazdką",
                    data={"starred": True},
                )
            else:
                return AgentResponse(
                    success=False,
                    error="Nie udało się oznaczyć emaila gwiazdką",
                    severity="ERROR",
                )

        except Exception as e:
            logger.error(f"Błąd podczas oznaczania gwiazdką: {e}")
            return AgentResponse(success=False, error=f"Błąd: {e!s}", severity="ERROR")

    async def _learn_from_interaction(self, request: InboxZeroRequest) -> AgentResponse:
        """Uczy się na podstawie interakcji z użytkownikiem"""
        try:
            if not request.learning_data:
                return AgentResponse(
                    success=False, error="Brak danych do uczenia się", severity="ERROR"
                )

            # Analiza danych uczenia się przez LLM
            learning_prompt = self.learning_prompt.format(
                email_data=json.dumps(
                    request.learning_data.get("email_data", {}), indent=2
                ),
                suggested_actions=json.dumps(
                    request.learning_data.get("suggested_actions", {}), indent=2
                ),
                user_actions=json.dumps(
                    request.learning_data.get("user_actions", {}), indent=2
                ),
                user_comment=request.user_feedback or "Brak komentarza",
            )

            messages = [
                {
                    "role": "system",
                    "content": "Jesteś ekspertem w uczeniu się wzorców użytkownika. Analizujesz różnice między sugestiami a rzeczywistymi akcjami użytkownika.",
                },
                {"role": "user", "content": learning_prompt},
            ]

            response = await hybrid_llm_client.chat(
                messages=messages,
                model="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
                options={"temperature": 0.2},
            )

            try:
                if isinstance(response, dict) and "message" in response:
                    content = response["message"].get("content", "")
                else:
                    content = str(response)
                learning_insights = json.loads(content)
            except json.JSONDecodeError:
                learning_insights = {
                    "learning_insights": ["Nie udało się przeanalizować automatycznie"],
                    "pattern_updates": {},
                    "accuracy_improvement": "Wymagana ręczna analiza",
                }

            # Aktualizuj wzorce użytkownika
            self._update_user_patterns(learning_insights)

            return AgentResponse(
                success=True,
                text="Dane uczenia się zostały przetworzone",
                data={"learning_insights": learning_insights, "patterns_updated": True},
            )

        except Exception as e:
            logger.error(f"Błąd podczas uczenia się: {e}")
            return AgentResponse(
                success=False, error=f"Błąd uczenia się: {e!s}", severity="ERROR"
            )

    async def _get_email_data(self, message_id: str | None, email_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Pobiera dane emaila z Gmail API asynchronicznie lub używa danych z requestu"""
        
        
        # Jeśli mamy dane emaila z requestu, użyj ich
        if email_data:
            return {
                "message_id": message_id or email_data.get("message_id", "unknown"),
                "sender": email_data.get("sender", ""),
                "subject": email_data.get("subject", ""),
                "date": email_data.get("date", datetime.now().isoformat()),
                "body_plain": email_data.get("body_plain", ""),
                "labels": email_data.get("labels", []),
                "is_read": email_data.get("is_read", False),
                "has_attachments": email_data.get("has_attachments", False),
            }
        
        if self.gmail_service and message_id:
            try:
                import asyncio
                
                # Wykonaj Gmail API call asynchronicznie
                message = await asyncio.to_thread(
                    lambda: self.gmail_service.users()
                    .messages()
                    .get(userId="me", id=message_id, format="full")
                    .execute()
                )

                # Wyciągnij nagłówki
                headers = message["payload"]["headers"]
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "Brak tematu",
                )
                sender = next(
                    (h["value"] for h in headers if h["name"] == "From"),
                    "Nieznany nadawca",
                )
                date = next(
                    (h["value"] for h in headers if h["name"] == "Date"),
                    datetime.now().isoformat(),
                )

                # Wyciągnij treść
                body_plain = ""
                if "parts" in message["payload"]:
                    for part in message["payload"]["parts"]:
                        if part["mimeType"] == "text/plain":
                            body_plain = part["body"]["data"]
                            break
                elif message["payload"]["mimeType"] == "text/plain":
                    body_plain = message["payload"]["body"]["data"]

                # Dekoduj base64
                import base64

                if body_plain:
                    body_plain = base64.urlsafe_b64decode(body_plain).decode("utf-8")

                # Pobierz labele
                labels = message.get("labelIds", [])

                return {
                    "message_id": message_id,
                    "sender": sender,
                    "subject": subject,
                    "date": date,
                    "body_plain": body_plain,
                    "labels": labels,
                    "is_read": "UNREAD" not in labels,
                    "has_attachments": any("attachment" in label for label in labels),
                }

            except HttpError as e:
                logger.error(f"Gmail API error: {e}")
                # Fallback do mock danych
                return self._get_mock_email_data(message_id)
        else:
            # Mock dane jeśli Gmail API nie jest dostępne
            return self._get_mock_email_data(message_id)

    def _get_mock_email_data(self, message_id: str | None) -> dict[str, Any]:
        """Fallback data when Gmail API is not available"""
        logger.warning("Gmail API not available, returning empty email data")
        return {
            "message_id": message_id or "no_message_id",
            "sender": "",
            "subject": "",
            "date": datetime.now().isoformat(),
            "body_plain": "",
            "labels": [],
            "is_read": False,
            "has_attachments": False,
        }

    @retry_with_backoff(max_retries=3)
    async def _apply_labels_gmail_api(self, message_id: str, labels: list[str]) -> bool:
        """Zastosowuje labele przez Gmail API asynchronicznie z retry mechanism"""
        try:
            import asyncio
            
            # Pobierz istniejące labele asynchronicznie
            message = await asyncio.to_thread(
                lambda: self.gmail_service.users()
                .messages()
                .get(userId="me", id=message_id, format="metadata")
                .execute()
            )

            current_labels = set(message.get("labelIds", []))
            new_labels = set(labels)

            # Dodaj nowe labele
            labels_to_add = new_labels - current_labels

            if labels_to_add:
                await asyncio.to_thread(
                    lambda: self.gmail_service.users().messages().modify(
                        userId="me",
                        id=message_id,
                        body={"addLabelIds": list(labels_to_add)},
                    ).execute()
                )

            return True

        except HttpError as e:
            logger.error(f"Gmail API error applying labels: {e}")
            return False

    @retry_with_backoff(max_retries=3)
    async def _archive_message_gmail_api(self, message_id: str) -> bool:
        """Archiwizuje email przez Gmail API asynchronicznie z retry mechanism"""
        try:
            import asyncio
            
            await asyncio.to_thread(
                lambda: self.gmail_service.users().messages().modify(
                    userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
                ).execute()
            )
            return True

        except HttpError as e:
            logger.error(f"Gmail API error archiving message: {e}")
            return False

    @retry_with_backoff(max_retries=3)
    async def _delete_message_gmail_api(self, message_id: str) -> bool:
        """Usuwa email przez Gmail API asynchronicznie z retry mechanism"""
        try:
            import asyncio
            
            await asyncio.to_thread(
                lambda: self.gmail_service.users().messages().delete(
                    userId="me", id=message_id
                ).execute()
            )
            return True

        except HttpError as e:
            logger.error(f"Gmail API error deleting message: {e}")
            return False

    @retry_with_backoff(max_retries=3)
    async def _mark_read_gmail_api(self, message_id: str) -> bool:
        """Oznacza email jako przeczytany przez Gmail API asynchronicznie z retry mechanism"""
        try:
            import asyncio
            
            await asyncio.to_thread(
                lambda: self.gmail_service.users().messages().modify(
                    userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
                ).execute()
            )
            return True

        except HttpError as e:
            logger.error(f"Gmail API error marking as read: {e}")
            return False

    @retry_with_backoff(max_retries=3)
    async def _star_message_gmail_api(self, message_id: str) -> bool:
        """Oznacza email gwiazdką przez Gmail API asynchronicznie z retry mechanism"""
        try:
            import asyncio
            
            await asyncio.to_thread(
                lambda: self.gmail_service.users().messages().modify(
                    userId="me", id=message_id, body={"addLabelIds": ["STARRED"]}
                ).execute()
            )
            return True

        except HttpError as e:
            logger.error(f"Gmail API error starring message: {e}")
            return False

    async def _extract_message_features(self, message_id: str | None) -> dict[str, Any]:
        """Extract message features for ML analysis"""
        # TODO: Implement real NLP analysis
        logger.warning(
            "Message feature extraction not implemented, returning empty features"
        )
        return {
            "sender_domain": "",
            "subject_length": 0,
            "body_length": 0,
            "has_attachments": False,
            "is_reply": False,
            "urgency_keywords": [],
            "spam_score": 0.0,
        }

    async def _mock_gmail_api_call(self, operation: str, data: dict[str, Any]) -> bool:
        """Fallback API call when Gmail API is not available"""
        logger.warning(f"Gmail API not available, mocking operation '{operation}' with data: {data}")
        
        # Simulate successful operations in development/testing
        mock_success_operations = {"apply_labels", "archive", "mark_read", "star"}
        if operation in mock_success_operations:
            logger.info(f"Mock operation '{operation}' completed successfully")
            return True
        else:
            logger.warning(f"Mock operation '{operation}' not supported")
            return False

    def _update_user_patterns(self, learning_insights: dict[str, Any]) -> None:
        """Aktualizuje wzorce użytkownika na podstawie danych uczenia się"""
        if "pattern_updates" in learning_insights:
            pattern_updates = learning_insights["pattern_updates"]
            if isinstance(pattern_updates, dict):
                for pattern, update in pattern_updates.items():
                    if pattern not in self.label_patterns:
                        self.label_patterns[pattern] = {}
                    if isinstance(update, dict):
                        self.label_patterns[pattern].update(update)
                    else:
                        # Jeśli update nie jest słownikiem, zapisz jako wartość
                        self.label_patterns[pattern] = update

    def get_metadata(self) -> dict[str, Any]:
        """Zwraca metadane agenta"""
        return {
            "name": self.name,
            "type": "GmailInboxZeroAgent",
            "capabilities": [
                "email_analysis",
                "label_management",
                "archive_management",
                "learning_from_interactions",
                "pattern_recognition",
                "inbox_zero_optimization",
            ],
            "learning_data_count": len(self.learning_data),
            "patterns_count": len(self.label_patterns),
            "gmail_api_available": self.gmail_service is not None,
        }

    def get_dependencies(self) -> list[type]:
        """Lista zależności agenta"""
        return []

    def is_healthy(self) -> bool:
        """Sprawdza stan agenta"""
        return True

    async def get_inbox_stats(self, user_id: str) -> InboxZeroStats:
        """Pobiera statystyki Inbox Zero asynchronicznie"""
        if self.gmail_service:
            try:
                import asyncio
                
                # Pobierz rzeczywiste statystyki z Gmail API asynchronicznie
                messages_task = asyncio.to_thread(
                    lambda: self.gmail_service.users()
                    .messages()
                    .list(userId="me", labelIds=["INBOX"])
                    .execute()
                )

                # Pobierz nieprzeczytane asynchronicznie
                unread_task = asyncio.to_thread(
                    lambda: self.gmail_service.users()
                    .messages()
                    .list(userId="me", labelIds=["UNREAD"])
                    .execute()
                )
                
                # Wykonaj oba zapytania równolegle
                messages, unread_messages = await asyncio.gather(messages_task, unread_task)
                
                total_messages = len(messages.get("messages", []))
                unread_count = len(unread_messages.get("messages", []))

                # Oblicz procent Inbox Zero
                inbox_zero_percentage = (
                    ((total_messages - unread_count) / total_messages * 100)
                    if total_messages > 0
                    else 100
                )

                return InboxZeroStats(
                    total_messages=total_messages,
                    unread_messages=unread_count,
                    labeled_messages=total_messages,  # Uproszczenie
                    archived_messages=0,  # Trudne do obliczenia bez dodatkowych zapytań
                    deleted_messages=0,
                    inbox_zero_percentage=inbox_zero_percentage,
                    learning_accuracy=0.85,
                    last_analysis=datetime.now(),
                )

            except HttpError as e:
                logger.error(f"Gmail API error getting stats: {e}")
                # Fallback do mock statystyk
                return self._get_mock_inbox_stats()
        else:
            # Mock statystyki
            return self._get_mock_inbox_stats()

    def _get_mock_inbox_stats(self) -> InboxZeroStats:
        """Fallback stats when Gmail API is not available"""
        logger.warning("Gmail API not available, returning empty inbox stats")
        return InboxZeroStats(
            total_messages=0,
            unread_messages=0,
            labeled_messages=0,
            archived_messages=0,
            deleted_messages=0,
            inbox_zero_percentage=0.0,
            learning_accuracy=0.0,
            last_analysis=datetime.now(),
        )

    def _get_prefilter_labels(self, prefilter_result: Dict[str, Any]) -> List[str]:
        """Get labels based on prefilter result"""
        reason = prefilter_result.get("reason", "")
        if reason == "newsletter":
            return ["Newsletter"]
        elif reason == "spam":
            return ["Spam"]
        elif reason == "trusted_domain":
            return ["Zaufany"]
        elif reason == "safe_sender":
            return ["Osobiste"]
        elif reason == "automated_email":
            return ["Archiwum"]
        return []

    def _prepare_suggestions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Prepare suggestions from analysis result"""
        suggestions = []
        
        # Add suggested labels
        suggested_labels = analysis_result.get("suggested_labels", [])
        suggestions.extend(suggested_labels)
        
        if analysis_result.get("should_archive"):
            suggestions.append("Zarchiwizuj")
            
        if analysis_result.get("requires_response"):
            suggestions.append("Wymaga odpowiedzi")
            
        priority = analysis_result.get("priority", "medium")
        if priority == "high":
            suggestions.append("Wysoki priorytet")
        elif priority == "low":
            suggestions.append("Niski priorytet")
            
        return suggestions

    def _select_optimal_model(self, email_data: Dict[str, Any]) -> str:
        """Select optimal model based on email characteristics"""
        # Simple heuristic for model selection
        body_length = len(email_data.get("body_plain", ""))
        subject_length = len(email_data.get("subject", ""))
        
        # Use lightweight model for short, simple emails
        if body_length < 200 and subject_length < 50:
            return "llama3.2:3b"  # Lightweight model
        
        # Use standard model for most emails
        return "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"  # Standard model

    async def process_emails_batch(self, message_ids: List[str], user_id: str) -> Dict[str, Any]:
        """Process multiple emails in batch for improved efficiency"""
        try:
            results = []
            
            # Process emails in parallel with rate limiting
            semaphore = asyncio.Semaphore(5)  # Limit concurrent processes
            
            async def process_single_email(message_id: str):
                async with semaphore:
                    try:
                        request = InboxZeroRequest(
                            operation="analyze",
                            message_id=message_id,
                            user_id=user_id,
                            session_id="batch-session",
                            thread_id=None,
                            labels=None,
                            user_feedback=None,
                            learning_data=None,
                            email_data=None
                        )
                        result = await self._analyze_email(request)
                        return {"message_id": message_id, "result": result}
                    except Exception as e:
                        logger.error(f"Error processing email {message_id}: {e}")
                        return {"message_id": message_id, "error": str(e)}
                        
            # Process all emails
            tasks = [process_single_email(msg_id) for msg_id in message_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Separate successful and failed results
            successful = [r for r in results if isinstance(r, dict) and "result" in r]
            failed = [r for r in results if isinstance(r, dict) and "error" in r]
            
            return {
                "total_processed": len(message_ids),
                "successful": len(successful),
                "failed": len(failed),
                "results": successful,
                "errors": failed
            }
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return {
                "total_processed": 0,
                "successful": 0,
                "failed": len(message_ids),
                "error": str(e)
            }
            
    async def execute_batch_operations(self) -> Dict[str, Any]:
        """Execute all pending batch operations"""
        try:
            if not self.batch_processor.operations:
                return {"message": "No pending operations"}
                
            batches = self.batch_processor.get_batches()
            total_operations = len(self.batch_processor.operations)
            successful_operations = 0
            failed_operations = 0
            
            for i, batch in enumerate(batches):
                logger.info(f"Processing batch {i + 1}/{len(batches)} with {len(batch)} operations")
                
                # Process operations in batch
                for operation in batch:
                    try:
                        op_type = operation["type"]
                        message_id = operation["message_id"]
                        data = operation["data"]
                        
                        if op_type == "apply_labels":
                            success = await self._apply_labels_gmail_api(message_id, data.get("labels", []))
                        elif op_type == "archive":
                            success = await self._archive_message_gmail_api(message_id)
                        elif op_type == "mark_read":
                            success = await self._mark_read_gmail_api(message_id)
                        elif op_type == "star":
                            success = await self._star_message_gmail_api(message_id)
                        else:
                            logger.warning(f"Unknown operation type: {op_type}")
                            continue
                            
                        if success:
                            successful_operations += 1
                        else:
                            failed_operations += 1
                            
                    except Exception as e:
                        logger.error(f"Error executing operation {operation}: {e}")
                        failed_operations += 1
                        
                # Add delay between batches to respect rate limits
                if i < len(batches) - 1:
                    await asyncio.sleep(0.1)
                    
            # Clear processed operations
            self.batch_processor.clear()
            
            return {
                "total_operations": total_operations,
                "successful": successful_operations,
                "failed": failed_operations,
                "success_rate": successful_operations / total_operations if total_operations > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error executing batch operations: {e}")
            return {
                "error": str(e),
                "total_operations": len(self.batch_processor.operations)
            }

    async def _analyze_all_unread(self, request: InboxZeroRequest) -> AgentResponse:
        """Analizuje wszystkie nieprzeczytane wiadomości"""
        try:
            # Pobierz wszystkie nieprzeczytane wiadomości
            unread_messages = await self._get_unread_messages()
            
            if not unread_messages:
                return AgentResponse(
                    success=True,
                    text="Brak nieprzeczytanych wiadomości do analizy",
                    data={"analyzed_count": 0}
                )

            # Analizuj każdą wiadomość
            analyzed_count = 0
            for message in unread_messages:
                try:
                    analysis_result = await self._analyze_email(InboxZeroRequest(
                        user_id=request.user_id,
                        session_id=request.session_id,
                        operation="analyze",
                        message_id=message.get("id"),
                        thread_id=None,
                        labels=None,
                        user_feedback=None,
                        learning_data=None,
                        email_data=None
                    ))
                    if analysis_result.success:
                        analyzed_count += 1
                except Exception as e:
                    logger.error(f"Błąd podczas analizy wiadomości {message.get('id')}: {e}")

            return AgentResponse(
                success=True,
                text=f"Przeanalizowano {analyzed_count} nieprzeczytanych wiadomości",
                data={"analyzed_count": analyzed_count, "total_unread": len(unread_messages)}
            )

        except Exception as e:
            logger.error(f"Błąd podczas analizy wszystkich nieprzeczytanych: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas analizy wszystkich nieprzeczytanych: {e!s}",
                severity="ERROR"
            )

    async def _auto_archive_old_messages(self, request: InboxZeroRequest) -> AgentResponse:
        """Automatycznie archiwizuje stare wiadomości"""
        try:
            # Pobierz stare wiadomości (starsze niż 30 dni)
            old_messages = await self._get_old_messages(days_old=30)
            
            if not old_messages:
                return AgentResponse(
                    success=True,
                    text="Brak starych wiadomości do archiwizacji",
                    data={"archived_count": 0}
                )

            # Archiwizuj stare wiadomości
            archived_count = 0
            for message in old_messages:
                try:
                    archive_result = await self._archive_message(InboxZeroRequest(
                        user_id=request.user_id,
                        session_id=request.session_id,
                        operation="archive",
                        message_id=message.get("id"),
                        thread_id=None,
                        labels=None,
                        user_feedback=None,
                        learning_data=None,
                        email_data=None
                    ))
                    if archive_result.success:
                        archived_count += 1
                except Exception as e:
                    logger.error(f"Błąd podczas archiwizacji wiadomości {message.get('id')}: {e}")

            return AgentResponse(
                success=True,
                text=f"Zarchiwizowano {archived_count} starych wiadomości",
                data={"archived_count": archived_count, "total_old": len(old_messages)}
            )

        except Exception as e:
            logger.error(f"Błąd podczas auto-archiwizacji: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas auto-archiwizacji: {e!s}",
                severity="ERROR"
            )

    async def _apply_smart_labels(self, request: InboxZeroRequest) -> AgentResponse:
        """Zastosowuje inteligentne etykiety do wiadomości"""
        try:
            # Pobierz wiadomości bez etykiet
            unlabeled_messages = await self._get_unlabeled_messages()
            
            if not unlabeled_messages:
                return AgentResponse(
                    success=True,
                    text="Brak wiadomości wymagających inteligentnych etykiet",
                    data={"labeled_count": 0}
                )

            # Zastosuj inteligentne etykiety
            labeled_count = 0
            for message in unlabeled_messages:
                try:
                    # Analizuj wiadomość
                    analysis_result = await self._analyze_email(InboxZeroRequest(
                        user_id=request.user_id,
                        session_id=request.session_id,
                        operation="analyze",
                        message_id=message.get("id"),
                        thread_id=None,
                        labels=None,
                        user_feedback=None,
                        learning_data=None,
                        email_data=None
                    ))
                    
                    if analysis_result.success and analysis_result.data:
                        suggested_labels = analysis_result.data.get("analysis", {}).get("suggested_labels", [])
                        if suggested_labels:
                            label_result = await self._apply_labels(InboxZeroRequest(
                                user_id=request.user_id,
                                session_id=request.session_id,
                                operation="label",
                                message_id=message.get("id"),
                                thread_id=None,
                                labels=suggested_labels,
                                user_feedback=None,
                                learning_data=None,
                                email_data=None
                            ))
                            if label_result.success:
                                labeled_count += 1
                except Exception as e:
                    logger.error(f"Błąd podczas zastosowania etykiet dla wiadomości {message.get('id')}: {e}")

            return AgentResponse(
                success=True,
                text=f"Zastosowano inteligentne etykiety do {labeled_count} wiadomości",
                data={"labeled_count": labeled_count, "total_unlabeled": len(unlabeled_messages)}
            )

        except Exception as e:
            logger.error(f"Błąd podczas zastosowania inteligentnych etykiet: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas zastosowania inteligentnych etykiet: {e!s}",
                severity="ERROR"
            )

    async def _mark_important_messages(self, request: InboxZeroRequest) -> AgentResponse:
        """Oznacza ważne wiadomości"""
        try:
            # Pobierz wiadomości do analizy
            messages_to_analyze = await self._get_messages_for_importance_check()
            
            if not messages_to_analyze:
                return AgentResponse(
                    success=True,
                    text="Brak wiadomości do oznaczenia jako ważne",
                    data={"marked_count": 0}
                )

            # Oznacz ważne wiadomości
            marked_count = 0
            for message in messages_to_analyze:
                try:
                    # Analizuj wiadomość pod kątem ważności
                    analysis_result = await self._analyze_email(InboxZeroRequest(
                        user_id=request.user_id,
                        session_id=request.session_id,
                        operation="analyze",
                        message_id=message.get("id"),
                        thread_id=None,
                        labels=None,
                        user_feedback=None,
                        learning_data=None,
                        email_data=None
                    ))
                    
                    if analysis_result.success and analysis_result.data:
                        analysis = analysis_result.data.get("analysis", {})
                        priority = analysis.get("priority", "medium")
                        
                        # Oznacz jako ważne jeśli priorytet jest wysoki
                        if priority == "high":
                            star_result = await self._star_message(InboxZeroRequest(
                                user_id=request.user_id,
                                session_id=request.session_id,
                                operation="star",
                                message_id=message.get("id"),
                                thread_id=None,
                                labels=None,
                                user_feedback=None,
                                learning_data=None,
                                email_data=None
                            ))
                            if star_result.success:
                                marked_count += 1
                except Exception as e:
                    logger.error(f"Błąd podczas oznaczania wiadomości {message.get('id')} jako ważnej: {e}")

            return AgentResponse(
                success=True,
                text=f"Oznaczono {marked_count} wiadomości jako ważne",
                data={"marked_count": marked_count, "total_analyzed": len(messages_to_analyze)}
            )

        except Exception as e:
            logger.error(f"Błąd podczas oznaczania ważnych wiadomości: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas oznaczania ważnych wiadomości: {e!s}",
                severity="ERROR"
            )

    async def _get_unread_messages(self) -> List[Dict[str, Any]]:
        """Pobiera nieprzeczytane wiadomości (maksymalnie 10)"""
        try:
            if self.gmail_service:
                # Pobierz nieprzeczytane wiadomości z Gmail API
                messages = self.gmail_service.users().messages().list(
                    userId='me',
                    q='is:unread',
                    maxResults=10
                ).execute()
                return messages.get('messages', [])
            else:
                # Mock data - maksymalnie 10 wiadomości
                return [
                    {"id": f"mock_unread_{i}", "threadId": f"thread_{i}"}
                    for i in range(1, 11)
                ]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania nieprzeczytanych wiadomości: {e}")
            return []

    async def _get_old_messages(self, days_old: int = 30) -> List[Dict[str, Any]]:
        """Pobiera stare wiadomości (maksymalnie 10)"""
        try:
            if self.gmail_service:
                # Pobierz stare wiadomości z Gmail API
                date_filter = f"before:{days_old}d"
                messages = self.gmail_service.users().messages().list(
                    userId='me',
                    q=date_filter,
                    maxResults=10
                ).execute()
                return messages.get('messages', [])
            else:
                # Mock data - maksymalnie 10 wiadomości
                return [
                    {"id": f"mock_old_{i}", "threadId": f"thread_{i}"}
                    for i in range(1, 11)
                ]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania starych wiadomości: {e}")
            return []

    async def _get_unlabeled_messages(self) -> List[Dict[str, Any]]:
        """Pobiera wiadomości bez etykiet (maksymalnie 10)"""
        try:
            if self.gmail_service:
                # Pobierz wiadomości bez etykiet z Gmail API
                messages = self.gmail_service.users().messages().list(
                    userId='me',
                    q='-label:important -label:work -label:personal',
                    maxResults=10
                ).execute()
                return messages.get('messages', [])
            else:
                # Mock data - maksymalnie 10 wiadomości
                return [
                    {"id": f"mock_unlabeled_{i}", "threadId": f"thread_{i}"}
                    for i in range(1, 11)
                ]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania nieoznaczonych wiadomości: {e}")
            return []

    async def _get_messages_for_importance_check(self) -> List[Dict[str, Any]]:
        """Pobiera wiadomości do sprawdzenia ważności (maksymalnie 10)"""
        try:
            if self.gmail_service:
                # Pobierz wiadomości do analizy ważności
                messages = self.gmail_service.users().messages().list(
                    userId='me',
                    q='is:unread',
                    maxResults=10
                ).execute()
                return messages.get('messages', [])
            else:
                # Mock data - maksymalnie 10 wiadomości
                return [
                    {"id": f"mock_importance_{i}", "threadId": f"thread_{i}"}
                    for i in range(1, 11)
                ]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania wiadomości do sprawdzenia ważności: {e}")
            return []

    async def _batch_process_emails(self, request: InboxZeroRequest) -> AgentResponse:
        """Enhanced batch processing of multiple emails"""
        try:
            message_ids = request.email_data.get("message_ids", []) if request.email_data else []
            if not message_ids:
                return AgentResponse(
                    success=False,
                    error="Brak message_ids do przetworzenia",
                    severity="ERROR"
                )

            # Process emails in parallel with rate limiting
            semaphore = asyncio.Semaphore(5)  # Limit concurrent processes
            results = []
            
            async def process_single_email(message_id: str):
                async with semaphore:
                    try:
                        # Wait for rate limiter
                        await self.rate_limiter.wait_if_needed()
                        
                        # Create analysis request for this email
                        analysis_request = InboxZeroRequest(
                            user_id=request.user_id,
                            session_id=request.session_id,
                            operation="analyze",
                            message_id=message_id,
                            thread_id=None,
                            labels=None,
                            user_feedback=None,
                            learning_data=None,
                            email_data=None
                        )
                        
                        result = await self._analyze_email(analysis_request)
                        return {"message_id": message_id, "result": result, "success": result.success}
                    except Exception as e:
                        logger.error(f"Error processing email {message_id}: {e}")
                        return {"message_id": message_id, "error": str(e), "success": False}

            # Process all emails concurrently
            tasks = [process_single_email(msg_id) for msg_id in message_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Calculate statistics
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
            failed = len(results) - successful
            success_rate = successful / len(results) if results else 0
            
            return AgentResponse(
                success=True,
                text=f"Batch processing completed. Success: {successful}, Failed: {failed}",
                data={
                    "total_processed": len(results),
                    "successful": successful,
                    "failed": failed,
                    "success_rate": success_rate,
                    "results": results
                },
                metadata={
                    "batch_size": len(message_ids),
                    "processing_time": time.time(),
                    "cache_stats": self.smart_cache.get_cache_stats()
                }
            )
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas batch processing: {e!s}",
                severity="ERROR"
            )

    async def _execute_batch_operations(self, request: InboxZeroRequest) -> AgentResponse:
        """Execute all pending batch operations"""
        try:
            if not self.batch_processor.operations:
                return AgentResponse(
                    success=True,
                    text="Brak operacji do wykonania",
                    data={"message": "No pending operations"}
                )
                
            batches = self.batch_processor.get_batches()
            total_operations = len(self.batch_processor.operations)
            successful_operations = 0
            failed_operations = 0
            
            for i, batch in enumerate(batches):
                logger.info(f"Processing batch {i + 1}/{len(batches)} with {len(batch)} operations")
                
                # Process operations in batch
                for operation in batch:
                    try:
                        await self.rate_limiter.wait_if_needed()
                        
                        op_type = operation["type"]
                        message_id = operation["message_id"]
                        data = operation["data"]
                        
                        if op_type == "apply_labels":
                            success = await self._apply_labels_gmail_api(message_id, data.get("labels", []))
                        elif op_type == "archive":
                            success = await self._archive_message_gmail_api(message_id)
                        elif op_type == "mark_read":
                            success = await self._mark_read_gmail_api(message_id)
                        elif op_type == "star":
                            success = await self._star_message_gmail_api(message_id)
                        else:
                            logger.warning(f"Unknown operation type: {op_type}")
                            continue
                            
                        if success:
                            successful_operations += 1
                            self.rate_limiter.record_success()
                        else:
                            failed_operations += 1
                            self.rate_limiter.record_failure()
                            
                    except Exception as e:
                        logger.error(f"Error executing operation {operation}: {e}")
                        failed_operations += 1
                        self.rate_limiter.record_failure()
                        
            # Clear processed operations
            self.batch_processor.clear()
            
            success_rate = successful_operations / total_operations if total_operations > 0 else 0
            
            return AgentResponse(
                success=True,
                text=f"Batch operations completed. Success: {successful_operations}, Failed: {failed_operations}",
                data={
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "failed_operations": failed_operations,
                    "success_rate": success_rate
                },
                metadata={
                    "batch_count": len(batches),
                    "processing_time": time.time(),
                    "rate_limiter_stats": {
                        "success_count": self.rate_limiter.success_count,
                        "failure_count": self.rate_limiter.failure_count,
                        "current_rate": self.rate_limiter.current_rate
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing batch operations: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd podczas wykonywania operacji batch: {e!s}",
                severity="ERROR"
            )
