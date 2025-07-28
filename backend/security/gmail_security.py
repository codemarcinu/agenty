"""
Gmail Security and Audit Module

Provides security features for Gmail Inbox Zero operations including:
- Token rotation and secure storage
- Audit logging
- Scope validation
- Rate limiting monitoring
"""

import json
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import os
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

class GmailSecurityManager:
    """Manages security aspects of Gmail integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.audit_log_path = self.config.get("audit_log_path", "./logs/gmail_audit.log")
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Security settings
        self.min_token_lifetime = timedelta(hours=1)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        
        # Rate limiting monitoring
        self.rate_limit_warnings = {}
        self.failed_attempts = {}
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secure token storage"""
        key_path = Path("./config/gmail_encryption.key")
        
        if key_path.exists():
            with open(key_path, "rb") as key_file:
                return key_file.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(key_path, "wb") as key_file:
                key_file.write(key)
                
            # Set restrictive permissions
            os.chmod(key_path, 0o600)
            logger.info("Created new encryption key for Gmail tokens")
            return key
            
    def encrypt_credentials(self, credentials: Credentials) -> str:
        """Encrypt OAuth credentials for secure storage"""
        try:
            creds_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "id_token": credentials.id_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            json_data = json.dumps(creds_data)
            encrypted_data = self.fernet.encrypt(json_data.encode())
            
            self.audit_log("CREDENTIALS_ENCRYPTED", {
                "client_id_hash": hashlib.sha256(credentials.client_id.encode()).hexdigest()[:8],
                "scopes": credentials.scopes
            })
            
            return encrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Error encrypting credentials: {e}")
            self.audit_log("CREDENTIALS_ENCRYPTION_FAILED", {"error": str(e)})
            raise
            
    def decrypt_credentials(self, encrypted_data: str) -> Credentials:
        """Decrypt OAuth credentials from secure storage"""
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data.encode())
            creds_data = json.loads(decrypted_data.decode())
            
            # Reconstruct credentials object
            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                id_token=creds_data.get("id_token"),
                token_uri=creds_data.get("token_uri"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
                scopes=creds_data.get("scopes")
            )
            
            # Set expiry if available
            if creds_data.get("expiry"):
                credentials.expiry = datetime.fromisoformat(creds_data["expiry"])
                
            self.audit_log("CREDENTIALS_DECRYPTED", {
                "client_id_hash": hashlib.sha256(credentials.client_id.encode()).hexdigest()[:8]
            })
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error decrypting credentials: {e}")
            self.audit_log("CREDENTIALS_DECRYPTION_FAILED", {"error": str(e)})
            raise
            
    def validate_scopes(self, requested_scopes: List[str], allowed_scopes: List[str]) -> bool:
        """Validate that requested scopes are within allowed limits"""
        try:
            # Check if all requested scopes are in allowed list
            for scope in requested_scopes:
                if scope not in allowed_scopes:
                    self.audit_log("SCOPE_VIOLATION", {
                        "requested_scope": scope,
                        "allowed_scopes": allowed_scopes
                    })
                    return False
                    
            self.audit_log("SCOPE_VALIDATION_PASSED", {
                "requested_scopes": requested_scopes
            })
            return True
            
        except Exception as e:
            logger.error(f"Error validating scopes: {e}")
            self.audit_log("SCOPE_VALIDATION_ERROR", {"error": str(e)})
            return False
            
    def check_token_rotation_needed(self, credentials: Credentials) -> bool:
        """Check if token rotation is needed based on security policy"""
        if not credentials.expiry:
            return True
            
        time_until_expiry = credentials.expiry - datetime.utcnow()
        
        if time_until_expiry < self.min_token_lifetime:
            self.audit_log("TOKEN_ROTATION_NEEDED", {
                "time_until_expiry": str(time_until_expiry)
            })
            return True
            
        return False
        
    def rotate_credentials(self, credentials: Credentials) -> Optional[Credentials]:
        """Rotate OAuth credentials for security"""
        try:
            if credentials.refresh_token:
                from google.auth.transport.requests import Request
                
                credentials.refresh(Request())
                
                self.audit_log("TOKEN_ROTATED", {
                    "client_id_hash": hashlib.sha256(credentials.client_id.encode()).hexdigest()[:8],
                    "new_expiry": credentials.expiry.isoformat() if credentials.expiry else None
                })
                
                return credentials
            else:
                logger.warning("No refresh token available for rotation")
                self.audit_log("TOKEN_ROTATION_FAILED", {"reason": "no_refresh_token"})
                return None
                
        except Exception as e:
            logger.error(f"Error rotating credentials: {e}")
            self.audit_log("TOKEN_ROTATION_ERROR", {"error": str(e)})
            return None
            
    def monitor_rate_limits(self, user_id: str, operation: str) -> bool:
        """Monitor and log rate limit violations"""
        current_time = time.time()
        key = f"{user_id}:{operation}"
        
        # Check if user is locked out
        if key in self.failed_attempts:
            attempts, lockout_until = self.failed_attempts[key]
            if current_time < lockout_until:
                self.audit_log("RATE_LIMIT_LOCKOUT_ACTIVE", {
                    "user_id": user_id,
                    "operation": operation,
                    "lockout_until": datetime.fromtimestamp(lockout_until).isoformat()
                })
                return False
                
        return True
        
    def record_failed_attempt(self, user_id: str, operation: str, error_code: int) -> None:
        """Record failed API attempt for security monitoring"""
        current_time = time.time()
        key = f"{user_id}:{operation}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = [0, 0]
            
        attempts, _ = self.failed_attempts[key]
        attempts += 1
        
        if attempts >= self.max_failed_attempts:
            lockout_until = current_time + self.lockout_duration.total_seconds()
            self.failed_attempts[key] = [attempts, lockout_until]
            
            self.audit_log("USER_LOCKED_OUT", {
                "user_id": user_id,
                "operation": operation,
                "attempts": attempts,
                "error_code": error_code,
                "lockout_until": datetime.fromtimestamp(lockout_until).isoformat()
            })
        else:
            self.failed_attempts[key] = [attempts, 0]
            
            self.audit_log("FAILED_ATTEMPT", {
                "user_id": user_id,
                "operation": operation,
                "attempts": attempts,
                "error_code": error_code
            })
            
    def record_successful_operation(self, user_id: str, operation: str) -> None:
        """Record successful operation and clear failed attempts"""
        key = f"{user_id}:{operation}"
        
        if key in self.failed_attempts:
            del self.failed_attempts[key]
            
        self.audit_log("SUCCESSFUL_OPERATION", {
            "user_id": user_id,
            "operation": operation
        })
        
    def audit_log(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log security events for audit purposes"""
        try:
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "details": details,
                "source": "gmail_inbox_zero"
            }
            
            # Ensure audit log directory exists
            log_path = Path(self.audit_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Append to audit log
            with open(log_path, "a") as log_file:
                log_file.write(json.dumps(audit_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Error writing audit log: {e}")
            
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for monitoring"""
        current_time = time.time()
        
        # Count active lockouts
        active_lockouts = 0
        for key, (attempts, lockout_until) in self.failed_attempts.items():
            if lockout_until > current_time:
                active_lockouts += 1
                
        # Count recent failed attempts (last hour)
        recent_failures = 0
        for key, (attempts, _) in self.failed_attempts.items():
            recent_failures += attempts
            
        return {
            "active_lockouts": active_lockouts,
            "recent_failed_attempts": recent_failures,
            "total_monitored_users": len(self.failed_attempts),
            "audit_log_path": self.audit_log_path,
            "encryption_enabled": True
        }
        
    def cleanup_expired_lockouts(self) -> None:
        """Clean up expired lockouts from memory"""
        current_time = time.time()
        expired_keys = []
        
        for key, (attempts, lockout_until) in self.failed_attempts.items():
            if lockout_until > 0 and lockout_until < current_time:
                expired_keys.append(key)
                
        for key in expired_keys:
            del self.failed_attempts[key]
            
        if expired_keys:
            self.audit_log("LOCKOUTS_CLEANED", {
                "expired_count": len(expired_keys)
            })

class ComplianceChecker:
    """Checks compliance with security and privacy regulations"""
    
    def __init__(self):
        self.gdpr_compliant_operations = {
            "analyze", "label", "archive", "mark_read", "star"
        }
        self.restricted_operations = {
            "delete"  # Requires explicit user consent
        }
        
    def check_gdpr_compliance(self, operation: str, user_consent: bool = False) -> bool:
        """Check if operation is GDPR compliant"""
        if operation in self.gdpr_compliant_operations:
            return True
        elif operation in self.restricted_operations:
            return user_consent
        else:
            return False
            
    def check_data_retention(self, data_age_days: int, max_retention_days: int = 365) -> bool:
        """Check if data retention policy is complied with"""
        return data_age_days <= max_retention_days
        
    def anonymize_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize user data for logging purposes"""
        anonymized = data.copy()
        
        # Hash sensitive fields
        sensitive_fields = ["user_id", "email", "sender", "subject"]
        
        for field in sensitive_fields:
            if field in anonymized:
                value = str(anonymized[field])
                anonymized[field] = hashlib.sha256(value.encode()).hexdigest()[:8]
                
        return anonymized