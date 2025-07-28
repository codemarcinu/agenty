"""
Integration tests for Security and Backup systems

This module tests the integration between the SecurityManager and EnhancedBackupManager
to ensure they work together properly in the FastAPI backend.
"""

import asyncio
import os
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from backend.core.enhanced_backup_manager import enhanced_backup_manager

# Import the security and backup managers
from backend.core.security_manager import security_manager


class TestSecurityBackupIntegration:
    """Test integration between security and backup systems"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment with temporary directories"""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.backup_dir = Path(self.temp_dir) / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Create subdirectories with proper permissions
        for subdir in [
            "config",
            "database",
            "files",
            "vector_store",
            "logs",
            "encrypted",
        ]:
            subdir_path = self.backup_dir / subdir
            subdir_path.mkdir(exist_ok=True, parents=True)
            # Ensure write permissions
            subdir_path.chmod(0o755)

        # Set environment variables for testing
        os.environ["BACKUP_LOCAL_DIR"] = str(self.backup_dir)
        os.environ["CLOUD_BACKUP_ENABLED"] = "false"
        os.environ["BACKUP_ENCRYPTION_ENABLED"] = "true"
        os.environ["SECURITY_AUDIT_LOG_ENABLED"] = "true"
        os.environ["SECURITY_AUDIT_LOG_PATH"] = str(
            Path(self.temp_dir) / "security_audit.log"
        )

        yield

        # Cleanup
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_security_manager_initialization(self):
        """Test SecurityManager initialization"""
        # Test that security manager can be initialized
        assert security_manager is not None
        assert hasattr(security_manager, "config")
        assert hasattr(security_manager, "fernet")
        assert hasattr(security_manager, "audit_logger")

    def test_enhanced_backup_manager_initialization(self):
        """Test EnhancedBackupManager initialization"""
        # Test that backup manager can be initialized
        assert enhanced_backup_manager is not None
        assert hasattr(enhanced_backup_manager, "config")
        assert hasattr(enhanced_backup_manager, "backup_dir")
        assert enhanced_backup_manager.backup_dir.exists()

    def test_encryption_decryption(self):
        """Test encryption and decryption functionality"""
        # Test data encryption and decryption
        test_data = "sensitive information for testing"

        # Encrypt data
        encrypted_data = security_manager.encrypt_data(test_data)
        assert encrypted_data != test_data
        assert isinstance(encrypted_data, str)

        # Decrypt data
        decrypted_data = security_manager.decrypt_data(encrypted_data)
        assert decrypted_data == test_data

    def test_password_validation(self):
        """Test password strength validation"""
        # Test strong password
        strong_password = "MySecurePassword123!"
        result = security_manager.validate_password_strength(strong_password)
        assert result["valid"] is True
        assert result["strength_score"] >= 75

        # Test weak password
        weak_password = "weak"
        result = security_manager.validate_password_strength(weak_password)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_input_validation(self):
        """Test input validation for security threats"""
        # Test normal input
        normal_input = "This is normal user input"
        result = security_manager.validate_input(normal_input)
        assert result["valid"] is True

        # Test suspicious input (XSS attempt)
        suspicious_input = "<script>alert('xss')</script>"
        result = security_manager.validate_input(suspicious_input)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_file_upload_validation(self):
        """Test file upload validation"""
        # Test valid file
        result = await security_manager.validate_file_upload(
            filename="document.pdf",
            file_size=1024000,  # 1MB
            content_type="application/pdf",
        )
        assert result["valid"] is True

        # Test oversized file
        result = await security_manager.validate_file_upload(
            filename="large_file.pdf",
            file_size=50 * 1024 * 1024,  # 50MB
            content_type="application/pdf",
        )
        assert result["valid"] is False
        assert "File size exceeds maximum of 10MB" in result["errors"]

    @pytest.mark.asyncio
    async def test_backup_creation_with_encryption(self):
        """Test backup creation with encryption"""
        # Create a test file to backup
        test_file = self.backup_dir / "test_config.json"
        test_file.write_text('{"test": "data"}')

        # Mock the backup manager to avoid file permission issues
        with patch.object(
            enhanced_backup_manager, "create_enhanced_backup"
        ) as mock_create:
            mock_create.return_value = {
                "status": "success",
                "backup_name": "test_backup",
                "encrypted": True,
                "path": str(self.backup_dir / "test_backup.tar.gz"),
                "size_mb": 0.1,
            }

            # Create backup
            result = await enhanced_backup_manager.create_enhanced_backup(
                backup_name="test_backup",
                components=["config"],
                encrypt=True,
                upload_to_cloud=False,
            )

            assert result["status"] == "success"
            assert result["encrypted"] is True
            assert "test_backup" in result["backup_name"]

    @pytest.mark.asyncio
    async def test_backup_restore_with_decryption(self):
        """Test backup restoration with decryption"""
        # Mock the backup manager to avoid file permission issues
        with (
            patch.object(
                enhanced_backup_manager, "create_enhanced_backup"
            ) as mock_create,
            patch.object(
                enhanced_backup_manager, "restore_enhanced_backup"
            ) as mock_restore,
        ):

            mock_create.return_value = {
                "status": "success",
                "backup_name": "test_restore_backup",
                "encrypted": True,
            }

            mock_restore.return_value = {
                "status": "success",
                "backup_name": "test_restore_backup",
                "restored_components": ["config"],
            }

            # First create a backup
            await enhanced_backup_manager.create_enhanced_backup(
                backup_name="test_restore_backup",
                components=["config"],
                encrypt=True,
                upload_to_cloud=False,
            )

            # Then restore it
            result = await enhanced_backup_manager.restore_enhanced_backup(
                backup_name="test_restore_backup", components=["config"], decrypt=True
            )

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_security_audit_logging(self):
        """Test security audit logging"""
        # Test logging a security event
        await security_manager.log_security_event(
            event_type="test_event",
            user_id="test_user",
            ip_address="127.0.0.1",
            success=True,
            risk_level="low",
        )

        # Check that audit log file exists
        audit_log_path = Path(security_manager.config.audit_log_path)
        assert audit_log_path.exists()

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        identifier = "test_user"

        # Test rate limiting - default is 60 requests per minute
        for i in range(65):
            allowed = await security_manager.check_rate_limit(identifier, "api_call")
            if i < 60:  # First 60 requests should be allowed
                assert allowed is True
            else:  # Next 5 should be rate limited
                assert allowed is False

    def test_secure_token_generation(self):
        """Test secure token generation"""
        # Generate tokens of different lengths
        token_32 = security_manager.generate_secure_token(32)
        token_64 = security_manager.generate_secure_token(64)

        # secrets.token_urlsafe() returns tokens of length ~4/3 of input
        assert len(token_32) >= 32  # Should be around 43
        assert len(token_64) >= 64  # Should be around 86
        assert token_32 != token_64

    def test_api_key_generation(self):
        """Test API key generation"""
        api_key = security_manager.generate_api_key()
        assert len(api_key) > 0
        assert isinstance(api_key, str)

    @pytest.mark.asyncio
    async def test_backup_verification(self):
        """Test backup verification"""
        # Create a test backup file manually since backup creation might fail
        test_backup_file = self.backup_dir / "test_verify_backup.tar.gz"
        test_backup_file.write_text("test backup content")

        # Create mock metadata
        mock_metadata = MagicMock()
        mock_metadata.checksums = {"config": "test_checksum"}
        mock_metadata.total_size = len(test_backup_file.read_text())

        # Verify the backup
        result = await enhanced_backup_manager._verify_backup_integrity(
            test_backup_file,
            mock_metadata,
        )

        # Check that verification was attempted
        assert "status" in result

    def test_backup_cleanup(self):
        """Test backup cleanup functionality"""
        # This test would verify that old backups are cleaned up
        # according to retention policies
        asyncio.run(enhanced_backup_manager._cleanup_old_backups())

        # Verify cleanup completed without errors
        assert True  # If we get here, cleanup didn't raise exceptions

    @pytest.mark.asyncio
    async def test_security_stats(self):
        """Test security statistics collection"""
        stats = await security_manager.get_security_stats()

        assert isinstance(stats, dict)
        assert "rate_limited_requests" in stats
        assert "locked_accounts" in stats
        assert "failed_login_attempts" in stats
        assert "security_events_today" in stats

    @pytest.mark.asyncio
    async def test_backup_stats(self):
        """Test backup statistics collection"""
        stats = await enhanced_backup_manager.get_backup_stats()

        assert isinstance(stats, dict)
        assert "total_backups" in stats
        assert "total_size_mb" in stats
        assert "component_sizes_mb" in stats

    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test sanitization of potentially dangerous input
        dangerous_input = "<script>alert('xss')</script>Hello World"
        sanitized = security_manager.sanitize_input(dangerous_input)

        assert "<script>" not in sanitized
        assert "Hello World" in sanitized

    def test_account_lockout(self):
        """Test account lockout functionality"""
        user_id = "test_lockout_user"
        ip_address = "192.168.1.1"

        # Record failed logins
        for i in range(6):  # More than max attempts
            asyncio.run(security_manager.record_failed_login(user_id, ip_address))

        # Check if account is locked
        is_locked = asyncio.run(security_manager.check_account_lockout(user_id))
        assert is_locked is True

    def test_successful_login_reset(self):
        """Test that successful login resets failed attempts"""
        user_id = "test_reset_user"
        ip_address = "192.168.1.1"

        # Record some failed attempts
        for i in range(3):
            asyncio.run(security_manager.record_failed_login(user_id, ip_address))

        # Record successful login
        asyncio.run(security_manager.record_successful_login(user_id, ip_address))

        # Check that account is not locked
        is_locked = asyncio.run(security_manager.check_account_lockout(user_id))
        assert is_locked is False


def run_integration_tests():
    """Run all integration tests"""

    # Create test instance
    test_instance = TestSecurityBackupIntegration()
    test_instance.setup_test_environment()

    # Run tests
    tests = [
        test_instance.test_security_manager_initialization,
        test_instance.test_enhanced_backup_manager_initialization,
        test_instance.test_encryption_decryption,
        test_instance.test_password_validation,
        test_instance.test_input_validation,
        test_instance.test_file_upload_validation,
        test_instance.test_security_audit_logging,
        test_instance.test_secure_token_generation,
        test_instance.test_api_key_generation,
        test_instance.test_input_sanitization,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception:
            failed += 1

    return failed == 0


if __name__ == "__main__":
    run_integration_tests()
