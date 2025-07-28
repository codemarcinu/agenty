"""
Security Manager for FoodSave AI

Centralized security management including:
- Encryption/decryption
- Secret management
- Security policies
- Audit logging
- Rate limiting
- Input validation
"""

from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
import re
import secrets
import time
from typing import Any

import bcrypt
from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class SecurityConfig(BaseModel):
    """Security configuration model"""

    # Encryption settings
    encryption_key: str
    key_derivation_salt: str

    # Rate limiting
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # Password policy
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    password_history_size: int = 5

    # Session security
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 3

    # Input validation
    max_input_length: int = 10000
    allowed_file_types: list[str] = [".txt", ".pdf", ".jpg", ".png", ".jpeg"]
    max_file_size_mb: int = 10

    # Audit logging
    audit_log_enabled: bool = True
    audit_log_path: str = os.getenv(
        "SECURITY_AUDIT_LOG_PATH", "./logs/security_audit.log"
    )

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v):
        if len(v) < 32:
            raise ValueError("Encryption key must be at least 32 characters")
        return v


class SecurityAuditLog(BaseModel):
    """Security audit log entry"""

    timestamp: datetime
    event_type: str
    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource: str | None = None
    action: str | None = None
    success: bool = True
    details: dict[str, Any] | None = None
    risk_level: str = "low"  # low, medium, high, critical


class SecurityManager:
    """
    Centralized security management for FoodSave AI
    """

    def __init__(self) -> None:
        super().__init__()
        self.config = self._load_security_config()
        self.fernet = self._initialize_encryption()
        self.rate_limit_cache: dict[str, list[float]] = {}
        self.failed_login_attempts: dict[str, list[float]] = {}
        self.locked_accounts: dict[str, datetime] = {}
        self.audit_logger = self._setup_audit_logger()

        # Security policies
        self.suspicious_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"union\s+select",
            r"drop\s+table",
            r"delete\s+from",
            r"insert\s+into",
            r"update\s+set",
            r"exec\s*\(",
            r"eval\s*\(",
        ]

        logger.info("SecurityManager initialized successfully")

    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment"""
        return SecurityConfig(
            encryption_key=os.getenv(
                "SECURITY_ENCRYPTION_KEY", secrets.token_urlsafe(32)
            ),
            key_derivation_salt=os.getenv(
                "SECURITY_KEY_SALT", secrets.token_urlsafe(16)
            ),
            max_requests_per_minute=int(
                os.getenv("SECURITY_MAX_REQUESTS_PER_MINUTE", "60")
            ),
            max_requests_per_hour=int(
                os.getenv("SECURITY_MAX_REQUESTS_PER_HOUR", "1000")
            ),
            max_login_attempts=int(os.getenv("SECURITY_MAX_LOGIN_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("SECURITY_LOCKOUT_DURATION", "15")),
            min_password_length=int(os.getenv("SECURITY_MIN_PASSWORD_LENGTH", "12")),
            require_uppercase=os.getenv("SECURITY_REQUIRE_UPPERCASE", "true").lower()
            == "true",
            require_lowercase=os.getenv("SECURITY_REQUIRE_LOWERCASE", "true").lower()
            == "true",
            require_digits=os.getenv("SECURITY_REQUIRE_DIGITS", "true").lower()
            == "true",
            require_special_chars=os.getenv("SECURITY_REQUIRE_SPECIAL", "true").lower()
            == "true",
            password_history_size=int(os.getenv("SECURITY_PASSWORD_HISTORY", "5")),
            session_timeout_minutes=int(os.getenv("SECURITY_SESSION_TIMEOUT", "30")),
            max_concurrent_sessions=int(os.getenv("SECURITY_MAX_SESSIONS", "3")),
            max_input_length=int(os.getenv("SECURITY_MAX_INPUT_LENGTH", "10000")),
            max_file_size_mb=int(os.getenv("SECURITY_MAX_FILE_SIZE_MB", "10")),
            audit_log_enabled=os.getenv("SECURITY_AUDIT_LOG_ENABLED", "true").lower()
            == "true",
            audit_log_path=os.getenv(
                "SECURITY_AUDIT_LOG_PATH", "./logs/security_audit.log"
            ),
        )

    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption with Fernet"""
        try:
            # Generate a proper Fernet key from the encryption key
            import base64

            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

            # Derive key from password using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.config.key_derivation_salt.encode(),
                iterations=100000,
            )
            key = kdf.derive(self.config.encryption_key.encode())

            # Convert to base64 for Fernet
            fernet_key = base64.urlsafe_b64encode(key)
            return Fernet(fernet_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise

    def _setup_audit_logger(self) -> logging.Logger:
        """Setup audit logger"""
        if not self.config.audit_log_enabled:
            return logging.getLogger("security_audit_disabled")

        audit_logger = logging.getLogger("security_audit")
        audit_logger.setLevel(logging.INFO)

        # Create log directory if it doesn't exist
        log_path = Path(self.config.audit_log_path)
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            # Ensure proper permissions
            log_path.parent.chmod(0o777)
        except Exception as e:
            logger.warning(f"Could not create log directory: {e}")
            # Fallback to console logging only
            return audit_logger

        # File handler with error handling
        try:
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.INFO)
        except PermissionError:
            logger.warning(
                f"Permission denied for log file: {log_path}. Using console logging only."
            )
            return audit_logger
        except Exception as e:
            logger.warning(
                f"Could not create file handler: {e}. Using console logging only."
            )
            return audit_logger

        # JSON formatter
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )
        file_handler.setFormatter(formatter)

        audit_logger.addHandler(file_handler)
        audit_logger.propagate = False

        return audit_logger

    async def log_security_event(
        self,
        event_type: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource: str | None = None,
        action: str | None = None,
        success: bool = True,
        details: dict[str, Any] | None = None,
        risk_level: str = "low",
    ) -> None:
        """Log security event to audit log"""
        if not self.config.audit_log_enabled:
            return

        audit_entry = SecurityAuditLog(
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            success=success,
            details=details,
            risk_level=risk_level,
        )

        log_message = f"SECURITY_EVENT: {audit_entry.model_dump_json()}"
        self.audit_logger.info(log_message)

        # Log to console for high-risk events
        if risk_level in ["high", "critical"]:
            logger.warning(f"High-risk security event: {event_type} - {details}")

    def encrypt_data(self, data: str | bytes) -> str:
        """Encrypt sensitive data"""
        try:
            if isinstance(data, str):
                data = data.encode()

            encrypted_data = self.fernet.encrypt(data)
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Data encryption failed",
            )

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = encrypted_data.encode()
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Data decryption failed",
            )

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode(), salt)
            return hashed.decode()
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode(), hashed_password.encode())
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

    def validate_password_strength(self, password: str) -> dict[str, Any]:
        """Validate password strength according to security policy"""
        errors = []
        warnings = []

        if len(password) < self.config.min_password_length:
            errors.append(
                f"Password must be at least {self.config.min_password_length} characters"
            )

        if self.config.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if self.config.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if self.config.require_digits and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        if self.config.require_special_chars and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            errors.append("Password must contain at least one special character")

        # Check for common patterns
        if re.search(r"(password|123|qwerty|admin)", password.lower()):
            warnings.append("Password contains common patterns")

        if len(set(password)) < len(password) * 0.6:
            warnings.append("Password has limited character variety")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "strength_score": self._calculate_password_strength(password),
        }

    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0

        # Length bonus
        score += min(len(password) * 2, 40)

        # Character variety bonus
        if re.search(r"[A-Z]", password):
            score += 10
        if re.search(r"[a-z]", password):
            score += 10
        if re.search(r"\d", password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 15

        # Penalty for repeated characters
        repeated_chars = len(password) - len(set(password))
        score -= repeated_chars * 2

        return max(0, min(100, score))

    def validate_input(
        self, input_data: str, max_length: int | None = None
    ) -> dict[str, Any]:
        """Validate user input for security threats"""
        max_len = max_length or self.config.max_input_length
        errors = []
        warnings = []

        if len(input_data) > max_len:
            errors.append(f"Input exceeds maximum length of {max_len} characters")

        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                errors.append(f"Input contains suspicious pattern: {pattern}")

        # Check for potential SQL injection
        sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            r"(--|\b(and|or)\b\s+\d+\s*=\s*\d+)",
            r"(\b(exec|execute|eval)\s*\()",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                warnings.append("Input may contain SQL injection attempt")

        # Check for XSS patterns
        xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                errors.append("Input contains potential XSS pattern")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized": self.sanitize_input(input_data) if len(errors) == 0 else None,
        }

    def sanitize_input(self, input_data: str) -> str:
        """Sanitize input data"""
        # Remove or escape potentially dangerous characters
        sanitized = input_data

        # HTML entity encoding for dangerous characters
        dangerous_chars = {
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "&": "&amp;",
        }

        for char, entity in dangerous_chars.items():
            sanitized = sanitized.replace(char, entity)

        return sanitized

    async def check_rate_limit(
        self, identifier: str, request_type: str = "general"
    ) -> bool:
        """Check rate limiting for identifier"""
        now = time.time()
        cache_key = f"{identifier}:{request_type}"

        if cache_key not in self.rate_limit_cache:
            self.rate_limit_cache[cache_key] = []

        # Clean old entries
        window_start = now - 60  # 1 minute window
        self.rate_limit_cache[cache_key] = [
            timestamp
            for timestamp in self.rate_limit_cache[cache_key]
            if timestamp > window_start
        ]

        # Check limits
        if request_type == "login":
            max_requests = self.config.max_login_attempts
        elif request_type == "api":
            max_requests = self.config.max_requests_per_minute
        else:
            max_requests = self.config.max_requests_per_minute

        if len(self.rate_limit_cache[cache_key]) >= max_requests:
            return False

        # Add current request
        self.rate_limit_cache[cache_key].append(now)
        return True

    async def check_account_lockout(self, user_id: str) -> bool:
        """Check if account is locked due to failed login attempts"""
        if user_id in self.locked_accounts:
            lockout_time = self.locked_accounts[user_id]
            if datetime.now() < lockout_time:
                return True
            # Remove expired lockout
            del self.locked_accounts[user_id]
            if user_id in self.failed_login_attempts:
                del self.failed_login_attempts[user_id]

        return False

    async def record_failed_login(self, user_id: str, ip_address: str) -> None:
        """Record failed login attempt"""
        now = datetime.now()

        if user_id not in self.failed_login_attempts:
            self.failed_login_attempts[user_id] = []

        self.failed_login_attempts[user_id].append(now.timestamp())

        # Clean old attempts
        window_start = now - timedelta(minutes=self.config.lockout_duration_minutes)
        self.failed_login_attempts[user_id] = [
            timestamp
            for timestamp in self.failed_login_attempts[user_id]
            if timestamp > window_start.timestamp()
        ]

        # Check if account should be locked
        if len(self.failed_login_attempts[user_id]) >= self.config.max_login_attempts:
            lockout_end = now + timedelta(minutes=self.config.lockout_duration_minutes)
            self.locked_accounts[user_id] = lockout_end

            await self.log_security_event(
                event_type="account_locked",
                user_id=user_id,
                ip_address=ip_address,
                action="login_failed",
                success=False,
                details={"failed_attempts": len(self.failed_login_attempts[user_id])},
                risk_level="high",
            )

    async def record_successful_login(self, user_id: str, ip_address: str) -> None:
        """Record successful login and clear failed attempts"""
        if user_id in self.failed_login_attempts:
            del self.failed_login_attempts[user_id]

        if user_id in self.locked_accounts:
            del self.locked_accounts[user_id]

        await self.log_security_event(
            event_type="login_successful",
            user_id=user_id,
            ip_address=ip_address,
            action="login",
            success=True,
            risk_level="low",
        )

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)

    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"fs_{secrets.token_urlsafe(32)}"

    async def validate_file_upload(
        self, filename: str, file_size: int, content_type: str | None = None
    ) -> dict[str, Any]:
        """Validate file upload for security"""
        errors = []
        warnings = []

        # Check file size
        max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            errors.append(
                f"File size exceeds maximum of {self.config.max_file_size_mb}MB"
            )

        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.config.allowed_file_types:
            errors.append(f"File type {file_ext} is not allowed")

        # Check for double extensions (potential security risk)
        if filename.count(".") > 1:
            warnings.append("File has multiple extensions")

        # Check for suspicious filenames
        suspicious_patterns = [
            r"\.(php|asp|jsp|exe|bat|cmd|sh|py|rb|pl)$",
            r"(\.\.|/|\\|:|<|>|\||\?)",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                errors.append("Filename contains suspicious characters")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "safe_filename": (
                self._generate_safe_filename(filename) if len(errors) == 0 else None
            ),
        }

    def _generate_safe_filename(self, filename: str) -> str:
        """Generate safe filename"""
        # Remove path components
        safe_name = Path(filename).name

        # Replace dangerous characters
        safe_name = re.sub(r"[^\w\-_.]", "_", safe_name)

        # Add timestamp to prevent conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(safe_name)

        return f"{name}_{timestamp}{ext}"

    async def get_security_stats(self) -> dict[str, Any]:
        """Get security statistics"""
        return {
            "rate_limited_requests": len(self.rate_limit_cache),
            "locked_accounts": len(self.locked_accounts),
            "failed_login_attempts": len(self.failed_login_attempts),
            "security_events_today": await self._count_security_events_today(),
            "config": {
                "max_requests_per_minute": self.config.max_requests_per_minute,
                "max_login_attempts": self.config.max_login_attempts,
                "lockout_duration_minutes": self.config.lockout_duration_minutes,
                "audit_log_enabled": self.config.audit_log_enabled,
            },
        }

    async def _count_security_events_today(self) -> int:
        """Count security events from today"""
        if not self.config.audit_log_enabled:
            return 0

        try:
            log_path = Path(self.config.audit_log_path)
            if not log_path.exists():
                return 0

            today = datetime.now().date()
            count = 0

            with open(log_path) as f:
                for line in f:
                    if today.isoformat() in line:
                        count += 1

            return count
        except Exception as e:
            logger.error(f"Failed to count security events: {e}")
            return 0


# Global security manager instance
security_manager = SecurityManager()
