# Security and Data Backup Implementation Guide

## Overview

This document provides a comprehensive guide to the security and data backup features implemented in the FoodSave AI FastAPI backend. The system includes advanced security measures, encryption, audit logging, and automated backup solutions with cloud integration.

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Encryption System](#encryption-system)
3. [Input Validation and Sanitization](#input-validation-and-sanitization)
4. [Rate Limiting and Access Control](#rate-limiting-and-access-control)
5. [Audit Logging](#audit-logging)
6. [Security Policies](#security-policies)
7. [Backup System](#backup-system)
8. [API Endpoints](#api-endpoints)
9. [Middleware Integration](#middleware-integration)
10. [Monitoring and Alerting](#monitoring-and-alerting)
11. [Environment Configuration](#environment-configuration)
12. [Testing and Validation](#testing-and-validation)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)

## Security Architecture

### Core Components

The security system is built around several key components:

1. **SecurityManager** (`src/backend/core/security_manager.py`)
   - Centralized security management
   - Encryption/decryption services
   - Password validation and hashing
   - Input validation and sanitization
   - Rate limiting and access control
   - Audit logging

2. **EnhancedBackupManager** (`src/backend/core/enhanced_backup_manager.py`)
   - Encrypted backup creation and restoration
   - Cloud storage integration (AWS S3)
   - Automated scheduling
   - Incremental backups
   - Backup verification and integrity checks

3. **Security Middleware** (`src/backend/core/middleware.py`)
   - Security headers injection
   - Request/response logging
   - Error handling and sanitization

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│                    API Security Layer                       │
│  • Input Validation  • Rate Limiting  • Authentication     │
├─────────────────────────────────────────────────────────────┤
│                    Data Security Layer                      │
│  • Encryption  • Hashing  • Audit Logging                  │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                     │
│  • HTTPS  • Firewall  • Network Security                   │
└─────────────────────────────────────────────────────────────┘
```

## Encryption System

### Data Encryption

The system uses Fernet symmetric encryption for sensitive data:

```python
from backend.core.security_manager import security_manager

# Encrypt data
encrypted_data = security_manager.encrypt_data("sensitive information")

# Decrypt data
decrypted_data = security_manager.decrypt_data(encrypted_data)
```

### Password Hashing

Passwords are hashed using bcrypt with salt:

```python
# Hash password
hashed_password = security_manager.hash_password("user_password")

# Verify password
is_valid = security_manager.verify_password("user_password", hashed_password)
```

### Configuration

Encryption settings are configured via environment variables:

```bash
# Encryption keys (auto-generated if not provided)
SECURITY_ENCRYPTION_KEY=your-32-character-encryption-key
SECURITY_KEY_SALT=your-16-character-salt

# Backup encryption
BACKUP_ENCRYPTION_ENABLED=true
BACKUP_ENCRYPTION_KEY=your-backup-encryption-key
```

## Input Validation and Sanitization

### Input Validation

The system validates all user inputs for security threats:

```python
# Validate input
validation_result = security_manager.validate_input(
    user_input,
    max_length=1000
)

if not validation_result["valid"]:
    # Handle validation errors
    errors = validation_result["errors"]
```

### File Upload Validation

File uploads are validated for security:

```python
# Validate file upload
validation_result = await security_manager.validate_file_upload(
    filename="document.pdf",
    file_size=1024000,  # 1MB
    content_type="application/pdf"
)
```

### Sanitization

Input sanitization removes potentially dangerous content:

```python
# Sanitize input
sanitized_input = security_manager.sanitize_input(user_input)
```

## Rate Limiting and Access Control

### Rate Limiting

The system implements rate limiting to prevent abuse:

```python
# Check rate limit
is_allowed = await security_manager.check_rate_limit(
    identifier="user_id_or_ip",
    request_type="api_call"
)
```

### Account Lockout

Failed login attempts trigger account lockout:

```python
# Record failed login
await security_manager.record_failed_login(user_id, ip_address)

# Check if account is locked
is_locked = await security_manager.check_account_lockout(user_id)
```

### Configuration

Rate limiting settings:

```bash
# Rate limiting
SECURITY_MAX_REQUESTS_PER_MINUTE=60
SECURITY_MAX_REQUESTS_PER_HOUR=1000
SECURITY_MAX_LOGIN_ATTEMPTS=5
SECURITY_LOCKOUT_DURATION=15
```

## Audit Logging

### Security Events

All security-relevant events are logged:

```python
# Log security event
await security_manager.log_security_event(
    event_type="login_attempt",
    user_id="user123",
    ip_address="192.168.1.1",
    success=True,
    risk_level="low"
)
```

### Audit Log Format

Audit logs are stored in JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "login_attempt",
  "user_id": "user123",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "resource": "/api/auth/login",
  "action": "POST",
  "success": true,
  "risk_level": "low",
  "details": {
    "login_method": "password"
  }
}
```

### Configuration

Audit logging settings:

```bash
# Audit logging
SECURITY_AUDIT_LOG_ENABLED=true
SECURITY_AUDIT_LOG_PATH=/app/logs/security_audit.log
```

## Security Policies

### Password Policy

Strong password requirements:

```bash
# Password policy
SECURITY_MIN_PASSWORD_LENGTH=12
SECURITY_REQUIRE_UPPERCASE=true
SECURITY_REQUIRE_LOWERCASE=true
SECURITY_REQUIRE_DIGITS=true
SECURITY_REQUIRE_SPECIAL=true
SECURITY_PASSWORD_HISTORY=5
```

### Session Security

Session management settings:

```bash
# Session security
SECURITY_SESSION_TIMEOUT=30
SECURITY_MAX_SESSIONS=3
```

### File Upload Security

File upload restrictions:

```bash
# File upload security
SECURITY_MAX_FILE_SIZE_MB=10
SECURITY_MAX_INPUT_LENGTH=10000
```

## Backup System

### Enhanced Backup Features

The backup system provides comprehensive data protection:

1. **Encrypted Backups**: All backups are encrypted using AES-256
2. **Cloud Integration**: Automatic upload to AWS S3
3. **Incremental Backups**: Only changed data is backed up
4. **Verification**: Checksum verification for data integrity
5. **Automated Scheduling**: Cron-based backup scheduling
6. **Retention Policies**: Configurable retention periods

### Backup Components

The system backs up multiple components:

- **Database**: PostgreSQL database dumps
- **Files**: Application files and uploads
- **Configuration**: Environment and config files
- **Vector Store**: AI model embeddings and indexes
- **Logs**: Application and security logs

### Creating Backups

```python
from backend.core.enhanced_backup_manager import enhanced_backup_manager

# Create backup
result = await enhanced_backup_manager.create_enhanced_backup(
    backup_name="daily_backup_2024_01_15",
    components=["database", "files", "config"],
    encrypt=True,
    upload_to_cloud=True
)
```

### Restoring Backups

```python
# Restore backup
result = await enhanced_backup_manager.restore_enhanced_backup(
    backup_name="daily_backup_2024_01_15",
    components=["database"],
    decrypt=True
)
```

### Backup Configuration

```bash
# Backup settings
BACKUP_LOCAL_DIR=/app/backups
CLOUD_BACKUP_ENABLED=true
CLOUD_PROVIDER=aws
CLOUD_BUCKET=your-backup-bucket
CLOUD_REGION=us-east-1

# Retention policy
BACKUP_DAILY_RETENTION=7
BACKUP_WEEKLY_RETENTION=4
BACKUP_MONTHLY_RETENTION=12
BACKUP_YEARLY_RETENTION=5

# Scheduling
AUTO_BACKUP_ENABLED=true
BACKUP_SCHEDULE_HOUR=2
BACKUP_SCHEDULE_MINUTE=0
```

## API Endpoints

### Security Endpoints

#### GET `/api/v2/security/stats`
Get security statistics and metrics.

**Response:**
```json
{
  "status_code": 200,
  "message": "Security statistics retrieved successfully",
  "data": {
    "rate_limited_requests": 5,
    "locked_accounts": 2,
    "failed_login_attempts": 15,
    "security_events_today": 150,
    "config": {
      "max_requests_per_minute": 60,
      "max_login_attempts": 5
    }
  }
}
```

#### POST `/api/v2/security/validate/password`
Validate password strength.

**Request:**
```json
{
  "password": "MySecurePassword123!"
}
```

**Response:**
```json
{
  "status_code": 200,
  "message": "Password validation completed",
  "data": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "strength_score": 85
  }
}
```

#### POST `/api/v2/security/validate/input`
Validate user input for security threats.

**Request:**
```json
{
  "input_data": "User input to validate",
  "max_length": 1000
}
```

#### POST `/api/v2/security/validate/file`
Validate file upload for security.

**Request:** Multipart form with file and optional content_type.

#### GET `/api/v2/security/audit-logs`
Get security audit logs with filtering.

**Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `event_type`: Filter by event type
- `risk_level`: Filter by risk level
- `limit`: Maximum number of logs (default: 100)
- `offset`: Number of logs to skip (default: 0)

#### POST `/api/v2/security/generate/token`
Generate secure random token.

#### POST `/api/v2/security/generate/api-key`
Generate API key.

#### POST `/api/v2/security/encrypt`
Encrypt data.

#### POST `/api/v2/security/decrypt`
Decrypt data.

### Enhanced Backup Endpoints

#### POST `/api/v2/enhanced-backup/create`
Create enhanced backup with encryption and cloud upload.

**Request:**
```json
{
  "backup_name": "daily_backup_2024_01_15",
  "components": ["database", "files", "config"],
  "encrypt": true,
  "upload_to_cloud": true
}
```

#### GET `/api/v2/enhanced-backup/list`
List all enhanced backups with metadata.

#### POST `/api/v2/enhanced-backup/restore`
Restore from enhanced backup.

**Request:**
```json
{
  "backup_name": "daily_backup_2024_01_15",
  "components": ["database"],
  "decrypt": true
}
```

#### GET `/api/v2/enhanced-backup/stats`
Get comprehensive backup statistics.

#### POST `/api/v2/enhanced-backup/verify/{backup_name}`
Verify backup integrity.

#### DELETE `/api/v2/enhanced-backup/cleanup`
Clean up old backups according to retention policy.

#### GET `/api/v2/enhanced-backup/config`
Get backup configuration.

#### POST `/api/v2/enhanced-backup/schedule`
Schedule automated backups.

## Middleware Integration

### Security Headers Middleware

Automatically adds security headers to all responses:

```python
# Security headers added
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
```

### Request Logging Middleware

Logs all requests and responses for security monitoring:

```python
# Request logging
{
  "request_id": "uuid",
  "method": "POST",
  "url": "/api/v2/security/validate/password",
  "client_ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "status_code": 200,
  "processing_time": 0.15
}
```

### Error Handling Middleware

Centralized error handling with security considerations:

```python
# Error response format
{
  "error": {
    "code": "validation_error",
    "message": "Input validation failed",
    "details": {
      "field": "password",
      "reason": "Password too weak"
    }
  }
}
```

## Monitoring and Alerting

### Security Metrics

The system tracks various security metrics:

- Rate-limited requests
- Failed login attempts
- Account lockouts
- Security events per day
- Input validation failures
- File upload rejections

### Backup Metrics

Backup system metrics:

- Total backups created
- Backup sizes and compression ratios
- Cloud upload success rates
- Backup verification results
- Restore operation statistics

### Alerting

Security alerts are triggered for:

- Multiple failed login attempts
- Suspicious input patterns
- Rate limit violations
- Backup failures
- Encryption errors

## Environment Configuration

### Required Environment Variables

```bash
# Security Configuration
SECURITY_ENCRYPTION_KEY=your-32-character-encryption-key
SECURITY_KEY_SALT=your-16-character-salt
SECURITY_MAX_REQUESTS_PER_MINUTE=60
SECURITY_MAX_REQUESTS_PER_HOUR=1000
SECURITY_MAX_LOGIN_ATTEMPTS=5
SECURITY_LOCKOUT_DURATION=15
SECURITY_MIN_PASSWORD_LENGTH=12
SECURITY_REQUIRE_UPPERCASE=true
SECURITY_REQUIRE_LOWERCASE=true
SECURITY_REQUIRE_DIGITS=true
SECURITY_REQUIRE_SPECIAL=true
SECURITY_PASSWORD_HISTORY=5
SECURITY_SESSION_TIMEOUT=30
SECURITY_MAX_SESSIONS=3
SECURITY_MAX_INPUT_LENGTH=10000
SECURITY_MAX_FILE_SIZE_MB=10
SECURITY_AUDIT_LOG_ENABLED=true
SECURITY_AUDIT_LOG_PATH=/app/logs/security_audit.log

# Backup Configuration
BACKUP_LOCAL_DIR=/app/backups
CLOUD_BACKUP_ENABLED=true
CLOUD_PROVIDER=aws
CLOUD_BUCKET=your-backup-bucket
CLOUD_REGION=us-east-1
BACKUP_ENCRYPTION_ENABLED=true
BACKUP_ENCRYPTION_KEY=your-backup-encryption-key
BACKUP_DAILY_RETENTION=7
BACKUP_WEEKLY_RETENTION=4
BACKUP_MONTHLY_RETENTION=12
BACKUP_YEARLY_RETENTION=5
AUTO_BACKUP_ENABLED=true
BACKUP_SCHEDULE_HOUR=2
BACKUP_SCHEDULE_MINUTE=0
BACKUP_VERIFY_ENABLED=true
BACKUP_CHECKSUM_VERIFICATION=true
BACKUP_COMPRESSION_LEVEL=6
BACKUP_COMPRESSION_TYPE=gzip

# AWS Configuration (for cloud backups)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

### Development vs Production

**Development:**
```bash
ENVIRONMENT=development
SECURITY_AUDIT_LOG_ENABLED=true
CLOUD_BACKUP_ENABLED=false
```

**Production:**
```bash
ENVIRONMENT=production
SECURITY_AUDIT_LOG_ENABLED=true
CLOUD_BACKUP_ENABLED=true
SECURITY_ENCRYPTION_KEY=production-encryption-key
BACKUP_ENCRYPTION_KEY=production-backup-key
```

## Testing and Validation

### Security Testing

```python
import pytest
from backend.core.security_manager import security_manager

async def test_password_validation():
    """Test password strength validation"""
    result = security_manager.validate_password_strength("WeakPassword")
    assert not result["valid"]
    assert "Password too short" in result["errors"]

async def test_input_validation():
    """Test input validation for XSS"""
    result = security_manager.validate_input("<script>alert('xss')</script>")
    assert not result["valid"]
    assert "Suspicious content detected" in result["errors"]

async def test_rate_limiting():
    """Test rate limiting functionality"""
    for i in range(10):
        allowed = await security_manager.check_rate_limit("test_user", "api_call")
        if i < 5:
            assert allowed
        else:
            assert not allowed
```

### Backup Testing

```python
import pytest
from backend.core.enhanced_backup_manager import enhanced_backup_manager

async def test_backup_creation():
    """Test backup creation and verification"""
    result = await enhanced_backup_manager.create_enhanced_backup(
        backup_name="test_backup",
        components=["config"],
        encrypt=True
    )
    assert result["status"] == "success"
    assert result["encrypted"] == True

async def test_backup_restore():
    """Test backup restoration"""
    result = await enhanced_backup_manager.restore_enhanced_backup(
        backup_name="test_backup",
        components=["config"]
    )
    assert result["status"] == "success"
```

## Best Practices

### Security Best Practices

1. **Key Management**
   - Use strong, randomly generated encryption keys
   - Rotate keys regularly
   - Store keys securely (use environment variables)
   - Never commit keys to version control

2. **Password Security**
   - Enforce strong password policies
   - Use bcrypt for password hashing
   - Implement password history
   - Provide password strength feedback

3. **Input Validation**
   - Validate all user inputs
   - Sanitize data before processing
   - Use parameterized queries for database operations
   - Implement content security policies

4. **Rate Limiting**
   - Implement rate limiting on all endpoints
   - Use different limits for different user types
   - Monitor and adjust limits based on usage patterns

5. **Audit Logging**
   - Log all security-relevant events
   - Use structured logging (JSON)
   - Implement log rotation and retention
   - Monitor logs for suspicious activity

### Backup Best Practices

1. **Backup Strategy**
   - Implement automated daily backups
   - Use incremental backups for efficiency
   - Test backup restoration regularly
   - Store backups in multiple locations

2. **Encryption**
   - Encrypt all backups at rest
   - Use strong encryption algorithms
   - Secure encryption key management
   - Verify encryption integrity

3. **Cloud Storage**
   - Use cloud storage for off-site backups
   - Implement proper access controls
   - Monitor cloud storage costs
   - Test cloud restore procedures

4. **Verification**
   - Verify backup integrity after creation
   - Test restore procedures regularly
   - Monitor backup success rates
   - Implement backup health checks

## Troubleshooting

### Common Security Issues

1. **Encryption Errors**
   ```
   Error: Failed to initialize encryption
   Solution: Check SECURITY_ENCRYPTION_KEY and SECURITY_KEY_SALT
   ```

2. **Rate Limiting Issues**
   ```
   Error: Too many requests
   Solution: Check rate limit configuration and user activity
   ```

3. **Password Validation Failures**
   ```
   Error: Password validation failed
   Solution: Review password policy requirements
   ```

### Common Backup Issues

1. **Backup Creation Failures**
   ```
   Error: Backup creation failed
   Solution: Check disk space, permissions, and configuration
   ```

2. **Cloud Upload Failures**
   ```
   Error: Cloud upload failed
   Solution: Verify AWS credentials and bucket permissions
   ```

3. **Restore Failures**
   ```
   Error: Backup restoration failed
   Solution: Check backup integrity and target permissions
   ```

### Debugging Commands

```bash
# Check security configuration
curl -X GET http://localhost:8000/api/v2/security/stats

# Test backup creation
curl -X POST http://localhost:8000/api/v2/enhanced-backup/create \
  -H "Content-Type: application/json" \
  -d '{"backup_name": "test_backup", "components": ["config"]}'

# View audit logs
curl -X GET "http://localhost:8000/api/v2/security/audit-logs?limit=10"

# Check backup health
curl -X GET http://localhost:8000/api/v2/enhanced-backup/health
```

## Resources

### Documentation
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [AWS S3 Backup Best Practices](https://aws.amazon.com/s3/backup-recovery/)

### Tools
- [Cryptography Library](https://cryptography.io/)
- [Bcrypt](https://github.com/pyca/bcrypt/)
- [Boto3 (AWS SDK)](https://boto3.amazonaws.com/)

### Standards
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [ISO 27001 Information Security](https://www.iso.org/isoiec-27001-information-security.html)
- [GDPR Data Protection](https://gdpr.eu/)

---

This security and backup implementation provides comprehensive protection for the FoodSave AI system while maintaining high performance and usability. Regular updates and monitoring ensure the system remains secure and reliable. 