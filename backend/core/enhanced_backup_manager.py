"""
Enhanced Backup Manager for FoodSave AI

Advanced backup system with:
- Encryption for sensitive data
- Cloud storage integration
- Automated scheduling
- Incremental backups
- Backup verification and integrity checks
- Disaster recovery procedures
"""

from datetime import datetime, timedelta
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Any
import zipfile

import aiofiles
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel

from core.security_manager import security_manager
from settings import settings

logger = logging.getLogger(__name__)


class BackupConfig(BaseModel):
    """Backup configuration model"""

    # Backup locations
    local_backup_dir: str = os.getenv("BACKUP_LOCAL_DIR", "./backups")
    cloud_backup_enabled: bool = False
    cloud_provider: str = "aws"  # aws, gcp, azure
    cloud_bucket: str | None = None
    cloud_region: str | None = None

    # Encryption
    encrypt_backups: bool = True
    encryption_key: str | None = None

    # Retention policy
    daily_retention_days: int = 7
    weekly_retention_weeks: int = 4
    monthly_retention_months: int = 12
    yearly_retention_years: int = 5

    # Backup scheduling
    auto_backup_enabled: bool = True
    backup_schedule_hour: int = 2  # 2 AM
    backup_schedule_minute: int = 0

    # Verification
    verify_backups: bool = True
    checksum_verification: bool = True

    # Compression
    compression_level: int = 6  # 0-9
    compression_type: str = "gzip"  # gzip, bzip2, lzma

    # Components to backup
    backup_components: list[str] = [
        "database",
        "files",
        "config",
        "vector_store",
        "logs",
    ]

    # Exclude patterns
    exclude_patterns: list[str] = [
        "*.tmp",
        "*.log",
        "__pycache__",
        ".git",
        "node_modules",
        "*.pyc",
        "*.pyo",
        ".DS_Store",
        "Thumbs.db",
    ]


class BackupMetadata(BaseModel):
    """Backup metadata"""

    backup_id: str
    timestamp: datetime
    version: str = "2.0"
    components: dict[str, Any]
    total_size: int
    checksums: dict[str, str]
    encryption_info: dict[str, Any] | None = None
    cloud_locations: list[str] = []
    verification_status: str = "pending"
    retention_policy: str = "daily"


class EnhancedBackupManager:
    """
    Enhanced backup manager with encryption and cloud integration
    """

    def __init__(self) -> None:
        self.config = self._load_backup_config()
        self.backup_dir = Path(self.config.local_backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize cloud client if enabled
        self.cloud_client = None
        if self.config.cloud_backup_enabled:
            self.cloud_client = self._initialize_cloud_client()

        # Backup subdirectories
        self.component_dirs = {
            "database": self.backup_dir / "database",
            "files": self.backup_dir / "files",
            "config": self.backup_dir / "config",
            "vector_store": self.backup_dir / "vector_store",
            "logs": self.backup_dir / "logs",
            "encrypted": self.backup_dir / "encrypted",
        }

        for dir_path in self.component_dirs.values():
            dir_path.mkdir(exist_ok=True)

        logger.info("EnhancedBackupManager initialized successfully")

    def _load_backup_config(self) -> BackupConfig:
        """Load backup configuration from environment"""
        compression_type = os.getenv("BACKUP_COMPRESSION_TYPE", "tar")
        if compression_type not in ["tar", "gz", "bzip2", "lzma"]:
            compression_type = "tar"  # fallback to no compression
        return BackupConfig(
            local_backup_dir=os.getenv("BACKUP_LOCAL_DIR", "./backups"),
            cloud_backup_enabled=os.getenv("CLOUD_BACKUP_ENABLED", "false").lower()
            == "true",
            cloud_provider=os.getenv("CLOUD_PROVIDER", "aws"),
            cloud_bucket=os.getenv("CLOUD_BUCKET"),
            cloud_region=os.getenv("CLOUD_REGION", "us-east-1"),
            encrypt_backups=os.getenv("BACKUP_ENCRYPTION_ENABLED", "true").lower()
            == "true",
            encryption_key=os.getenv("BACKUP_ENCRYPTION_KEY"),
            daily_retention_days=int(os.getenv("BACKUP_DAILY_RETENTION", "7")),
            weekly_retention_weeks=int(os.getenv("BACKUP_WEEKLY_RETENTION", "4")),
            monthly_retention_months=int(os.getenv("BACKUP_MONTHLY_RETENTION", "12")),
            yearly_retention_years=int(os.getenv("BACKUP_YEARLY_RETENTION", "5")),
            auto_backup_enabled=os.getenv("AUTO_BACKUP_ENABLED", "true").lower()
            == "true",
            backup_schedule_hour=int(os.getenv("BACKUP_SCHEDULE_HOUR", "2")),
            backup_schedule_minute=int(os.getenv("BACKUP_SCHEDULE_MINUTE", "0")),
            verify_backups=os.getenv("BACKUP_VERIFY_ENABLED", "true").lower() == "true",
            checksum_verification=os.getenv(
                "BACKUP_CHECKSUM_VERIFICATION", "true"
            ).lower()
            == "true",
            compression_level=int(os.getenv("BACKUP_COMPRESSION_LEVEL", "6")),
            compression_type=compression_type,
        )

    def _initialize_cloud_client(self):
        """Initialize cloud storage client"""
        try:
            if self.config.cloud_provider == "aws":
                return boto3.client(
                    "s3",
                    region_name=self.config.cloud_region,
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                )
            # Add other cloud providers here
            logger.warning(f"Cloud provider {self.config.cloud_provider} not supported")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize cloud client: {e}")
            return None

    async def create_enhanced_backup(
        self,
        backup_name: str | None = None,
        components: list[str] | None = None,
        encrypt: bool | None = None,
        upload_to_cloud: bool | None = None,
    ) -> dict[str, Any]:
        """
        Create enhanced backup with encryption and cloud upload
        """
        if not backup_name:
            backup_name = f"enhanced_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if components is None:
            components = self.config.backup_components

        if encrypt is None:
            encrypt = self.config.encrypt_backups

        if upload_to_cloud is None:
            upload_to_cloud = self.config.cloud_backup_enabled

        logger.info(f"Starting enhanced backup: {backup_name}")

        backup_metadata = BackupMetadata(
            backup_id=backup_name,
            timestamp=datetime.now(),
            components={},
            total_size=0,
            checksums={},
            retention_policy="daily",
        )

        try:
            # 1. Create component backups
            for component in components:
                if component in self.component_dirs:
                    result = await self._backup_component(component, backup_name)
                    backup_metadata.components[component] = result
                    backup_metadata.total_size += result.get("size", 0)

                    if self.config.checksum_verification:
                        checksum = await self._calculate_file_checksum(
                            Path(result["path"])
                        )
                        backup_metadata.checksums[component] = checksum

            # 2. Create backup archive
            archive_path = await self._create_backup_archive(backup_name, components)
            archive_size = archive_path.stat().st_size
            backup_metadata.total_size = archive_size

            # 3. Encrypt backup if enabled
            if encrypt:
                encrypted_path = await self._encrypt_backup(archive_path)
                backup_metadata.encryption_info = {
                    "encrypted": True,
                    "original_size": archive_size,
                    "encrypted_size": encrypted_path.stat().st_size,
                }
                final_backup_path = encrypted_path
            else:
                final_backup_path = archive_path

            # 4. Upload to cloud if enabled
            if upload_to_cloud and self.cloud_client:
                cloud_url = await self._upload_to_cloud(final_backup_path, backup_name)
                backup_metadata.cloud_locations.append(cloud_url)

            # 5. Verify backup integrity
            if self.config.verify_backups:
                verification_result = await self._verify_backup_integrity(
                    final_backup_path, backup_metadata
                )
                backup_metadata.verification_status = verification_result["status"]

            # 6. Save metadata
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            async with aiofiles.open(metadata_path, "w") as f:
                await f.write(backup_metadata.model_dump_json(indent=2))

            # 7. Cleanup old backups
            await self._cleanup_old_backups()

            # 8. Log security event
            await security_manager.log_security_event(
                event_type="backup_created",
                resource=backup_name,
                action="backup",
                success=True,
                details={
                    "size_mb": backup_metadata.total_size / (1024 * 1024),
                    "components": components,
                    "encrypted": encrypt,
                    "cloud_upload": upload_to_cloud,
                },
                risk_level="low",
            )

            logger.info(f"Enhanced backup completed successfully: {backup_name}")

            result = {
                "status": "success",
                "backup_name": backup_name,
                "metadata": backup_metadata.model_dump(),
                "path": str(final_backup_path),
                "size_mb": backup_metadata.total_size / (1024 * 1024),
                "encrypted": encrypt,
                "cloud_uploaded": upload_to_cloud
                and bool(backup_metadata.cloud_locations),
            }
            return result

        except Exception as e:
            logger.error(f"Enhanced backup failed: {e}")

            await security_manager.log_security_event(
                event_type="backup_failed",
                resource=backup_name,
                action="backup",
                success=False,
                details={"error": str(e)},
                risk_level="high",
            )

            return {
                "status": "failed",
                "backup_name": backup_name,
                "error": str(e),
                "encrypted": encrypt,
                "cloud_uploaded": upload_to_cloud,
            }

    async def _backup_component(
        self, component: str, backup_name: str
    ) -> dict[str, Any]:
        """Backup specific component"""
        logger.info(f"Backing up component: {component}")

        if component == "database":
            return await self._backup_database(backup_name)
        if component == "files":
            return await self._backup_files(backup_name)
        if component == "config":
            return await self._backup_configuration(backup_name)
        if component == "vector_store":
            return await self._backup_vector_store(backup_name)
        if component == "logs":
            return await self._backup_logs(backup_name)
        raise ValueError(f"Unknown backup component: {component}")

    async def _backup_database(self, backup_name: str) -> dict[str, Any]:
        """Backup database with enhanced features"""
        backup_file = self.component_dirs["database"] / f"{backup_name}_database.sql"

        try:
            # Extract database connection details
            db_url = settings.DATABASE_URL

            if db_url.startswith("sqlite"):
                # SQLite backup
                db_path = db_url.replace("sqlite:///", "").replace(
                    "sqlite+aiosqlite:///", ""
                )
                shutil.copy2(db_path, backup_file)
            elif db_url.startswith("postgresql"):
                # PostgreSQL backup using pg_dump
                await self._pg_dump_backup(db_url, backup_file)
            else:
                raise ValueError(f"Unsupported database type: {db_url}")

            size = backup_file.stat().st_size
            checksum = await self._calculate_file_checksum(backup_file)

            logger.info(
                f"Database backup created: {backup_file} ({size / 1024:.2f} KB)"
            )

            return {
                "status": "success",
                "path": str(backup_file),
                "size": size,
                "checksum": checksum,
                "type": "database",
            }

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _pg_dump_backup(self, db_url: str, backup_file: Path) -> None:
        """Create PostgreSQL backup using pg_dump"""
        # Parse connection string
        db_parts = db_url.replace("postgresql://", "").split("@")
        user_pass = db_parts[0].split(":")
        host_db = db_parts[1].split("/")

        username = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host_port = host_db[0].split(":")
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        database = host_db[1]

        # Create pg_dump command
        cmd = [
            "pg_dump",
            f"--host={host}",
            f"--port={port}",
            f"--username={username}",
            f"--dbname={database}",
            "--verbose",
            "--clean",
            "--no-owner",
            "--no-privileges",
            f"--file={backup_file}",
        ]

        # Set password environment variable
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        # Execute backup
        result = subprocess.run(
            cmd, check=False, env=env, capture_output=True, text=True
        )

        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")

    async def _backup_files(self, backup_name: str) -> dict[str, Any]:
        """Backup important files with compression"""
        backup_file = self.component_dirs["files"] / f"{backup_name}_files.tar.gz"

        try:
            important_dirs = ["uploads", "documents", "temp_uploads"]

            with tarfile.open(
                backup_file,
                f"w:{self.config.compression_type}",
                compresslevel=self.config.compression_level,
            ) as tar:
                for dir_name in important_dirs:
                    path = Path(dir_name)
                    if path.exists():
                        tar.add(
                            path, arcname=path.name, filter=self._filter_backup_files
                        )

            size = backup_file.stat().st_size
            checksum = await self._calculate_file_checksum(backup_file)

            logger.info(f"Files backup created: {backup_file} ({size / 1024:.2f} KB)")

            return {
                "status": "success",
                "path": str(backup_file),
                "size": size,
                "checksum": checksum,
                "type": "files",
            }

        except Exception as e:
            logger.error(f"Files backup failed: {e}")
            return {"status": "error", "error": str(e)}

    def _filter_backup_files(self, tarinfo):
        """Filter files to exclude from backup"""
        for pattern in self.config.exclude_patterns:
            if pattern in tarinfo.name:
                return None
        return tarinfo

    async def _backup_configuration(self, backup_name: str) -> dict[str, Any]:
        """Backup configuration files"""
        backup_file = self.component_dirs["config"] / f"{backup_name}_config.json"

        try:
            # Collect safe configuration data
            safe_config = {
                "app_name": settings.APP_NAME,
                "environment": settings.ENVIRONMENT,
                "log_level": settings.LOG_LEVEL,
                "backup_config": self.config.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }

            async with aiofiles.open(backup_file, "w") as f:
                await f.write(json.dumps(safe_config, indent=2))

            size = backup_file.stat().st_size
            checksum = await self._calculate_file_checksum(backup_file)

            logger.info(
                f"Configuration backup created: {backup_file} ({size / 1024:.2f} KB)"
            )

            return {
                "status": "success",
                "path": str(backup_file),
                "size": size,
                "checksum": checksum,
                "type": "configuration",
            }

        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _backup_vector_store(self, backup_name: str) -> dict[str, Any]:
        """Backup vector store data"""
        backup_file = (
            self.component_dirs["vector_store"] / f"{backup_name}_vector_store.tar.gz"
        )

        try:
            vector_store_path = Path(settings.RAG_VECTOR_STORE_PATH)

            if vector_store_path.exists():
                with tarfile.open(
                    backup_file,
                    f"w:{self.config.compression_type}",
                    compresslevel=self.config.compression_level,
                ) as tar:
                    tar.add(vector_store_path, arcname=vector_store_path.name)

                size = backup_file.stat().st_size
                checksum = await self._calculate_file_checksum(backup_file)

                logger.info(
                    f"Vector store backup created: {backup_file} ({size / 1024:.2f} KB)"
                )

                return {
                    "status": "success",
                    "path": str(backup_file),
                    "size": size,
                    "checksum": checksum,
                    "type": "vector_store",
                }
            logger.warning("Vector store path does not exist, skipping backup")
            return {
                "status": "skipped",
                "reason": "Vector store path does not exist",
                "type": "vector_store",
            }

        except Exception as e:
            logger.error(f"Vector store backup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _backup_logs(self, backup_name: str) -> dict[str, Any]:
        """Backup log files"""
        backup_file = self.component_dirs["logs"] / f"{backup_name}_logs.tar.gz"

        try:
            log_dirs = ["logs", "src/logs"]

            with tarfile.open(
                backup_file,
                f"w:{self.config.compression_type}",
                compresslevel=self.config.compression_level,
            ) as tar:
                for log_dir in log_dirs:
                    path = Path(log_dir)
                    if path.exists():
                        tar.add(path, arcname=path.name)

            size = backup_file.stat().st_size
            checksum = await self._calculate_file_checksum(backup_file)

            logger.info(f"Logs backup created: {backup_file} ({size / 1024:.2f} KB)")

            return {
                "status": "success",
                "path": str(backup_file),
                "size": size,
                "checksum": checksum,
                "type": "logs",
            }

        except Exception as e:
            logger.error(f"Logs backup failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _create_backup_archive(
        self, backup_name: str, components: list[str]
    ) -> Path:
        """Create a tar archive of the selected backup components"""
        import tarfile

        archive_path = self.backup_dir / f"{backup_name}.tar"
        compression_type = self.config.compression_type
        mode = "w"
        if compression_type == "gz":
            archive_path = archive_path.with_suffix(".tar.gz")
            mode = "w:gz"
        elif compression_type == "bzip2":
            archive_path = archive_path.with_suffix(".tar.bz2")
            mode = "w:bz2"
        elif compression_type == "lzma":
            archive_path = archive_path.with_suffix(".tar.xz")
            mode = "w:xz"
        # else: plain tar
        try:
            # Only pass compresslevel if supported
            compresslevel = self.config.compression_level
            if mode in ["w:gz", "w:bz2", "w:xz"]:
                try:
                    with tarfile.open(
                        archive_path, mode, compresslevel=compresslevel
                    ) as tar:
                        for comp in components:
                            comp_dir = self.component_dirs.get(comp)
                            if comp_dir and comp_dir.exists():
                                tar.add(comp_dir, arcname=comp)
                except TypeError:
                    # compresslevel not supported, fallback without it
                    with tarfile.open(archive_path, mode) as tar:
                        for comp in components:
                            comp_dir = self.component_dirs.get(comp)
                            if comp_dir and comp_dir.exists():
                                tar.add(comp_dir, arcname=comp)
            else:
                with tarfile.open(archive_path, mode) as tar:
                    for comp in components:
                        comp_dir = self.component_dirs.get(comp)
                        if comp_dir and comp_dir.exists():
                            tar.add(comp_dir, arcname=comp)
            return archive_path
        except Exception:
            # Fallback to plain tar if compression fails
            fallback_path = self.backup_dir / f"{backup_name}_plain.tar"
            with tarfile.open(fallback_path, "w") as tar:
                for comp in components:
                    comp_dir = self.component_dirs.get(comp)
                    if comp_dir and comp_dir.exists():
                        tar.add(comp_dir, arcname=comp)
            return fallback_path

    async def _encrypt_backup(self, backup_path: Path) -> Path:
        """Encrypt backup file"""
        encrypted_path = self.component_dirs["encrypted"] / f"{backup_path.name}.enc"

        # Use security manager for encryption
        async with aiofiles.open(backup_path, "rb") as f:
            data = await f.read()

        encrypted_data = security_manager.encrypt_data(data)

        async with aiofiles.open(encrypted_path, "w") as f:
            await f.write(encrypted_data)

        logger.info(f"Backup encrypted: {encrypted_path}")
        return encrypted_path

    async def _upload_to_cloud(self, backup_path: Path, backup_name: str) -> str:
        """Upload backup to cloud storage"""
        if not self.cloud_client or not self.config.cloud_bucket:
            raise ValueError("Cloud client or bucket not configured")

        try:
            key = f"backups/{backup_name}/{backup_path.name}"

            self.cloud_client.upload_file(
                str(backup_path),
                self.config.cloud_bucket,
                key,
                ExtraArgs={
                    "ServerSideEncryption": "AES256",
                    "StorageClass": "STANDARD_IA",
                },
            )

            url = f"s3://{self.config.cloud_bucket}/{key}"
            logger.info(f"Backup uploaded to cloud: {url}")

            return url

        except ClientError as e:
            logger.error(f"Cloud upload failed: {e}")
            raise

    async def _verify_backup_integrity(
        self, backup_path: Path, metadata: BackupMetadata
    ) -> dict[str, Any]:
        """Verify backup integrity"""
        try:
            # Check file exists
            if not backup_path.exists():
                return {"status": "failed", "error": "Backup file not found"}

            # Verify file size
            actual_size = backup_path.stat().st_size
            if actual_size != metadata.total_size:
                return {"status": "failed", "error": "File size mismatch"}

            # Verify checksums
            if self.config.checksum_verification:
                for component, expected_checksum in metadata.checksums.items():
                    component_path = Path(metadata.components[component]["path"])
                    if component_path.exists():
                        actual_checksum = await self._calculate_file_checksum(
                            component_path
                        )
                        if actual_checksum != expected_checksum:
                            return {
                                "status": "failed",
                                "error": f"Checksum mismatch for {component}",
                            }

            # Test archive integrity
            if backup_path.suffix in [
                ".tar.gz",
                ".tar.bz2",
                ".zip",
            ] and not await self._test_archive_integrity(backup_path):
                return {
                    "status": "failed",
                    "error": "Archive integrity test failed",
                }

            logger.info(f"Backup integrity verified: {backup_path}")
            return {"status": "verified"}

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _test_archive_integrity(self, archive_path: Path) -> bool:
        """Test archive integrity"""
        try:
            if archive_path.suffix == ".tar.gz":
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.getmembers()
            elif archive_path.suffix == ".tar.bz2":
                with tarfile.open(archive_path, "r:bz2") as tar:
                    tar.getmembers()
            elif archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zip_file:
                    zip_file.testzip()

            return True
        except Exception as e:
            logger.error(f"Archive integrity test failed: {e}")
            return False

    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()

        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    async def _cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy"""
        logger.info("Cleaning up old backups...")

        now = datetime.now()
        deleted_count = 0

        # Define retention periods
        retention_periods = {
            "daily": timedelta(days=self.config.daily_retention_days),
            "weekly": timedelta(weeks=self.config.weekly_retention_weeks),
            "monthly": timedelta(days=self.config.monthly_retention_months * 30),
            "yearly": timedelta(days=self.config.yearly_retention_years * 365),
        }

        # Find and delete old backups
        for backup_file in self.backup_dir.glob("*_full.tar.gz*"):
            try:
                # Extract timestamp from filename
                filename = backup_file.stem
                if "_full" in filename:
                    timestamp_str = filename.replace("enhanced_backup_", "").replace(
                        "_full", ""
                    )
                    backup_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    # Check if backup is older than retention period
                    age = now - backup_time
                    if age > retention_periods["yearly"]:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old backup: {backup_file}")

            except Exception as e:
                logger.error(f"Error processing backup file {backup_file}: {e}")

        logger.info(f"Cleanup completed: {deleted_count} old backups deleted")

    async def list_enhanced_backups(self) -> list[dict[str, Any]]:
        """List all enhanced backups with metadata"""
        backups = []

        for metadata_file in self.backup_dir.glob("*_metadata.json"):
            try:
                async with aiofiles.open(metadata_file) as f:
                    metadata_content = await f.read()
                    metadata = json.loads(metadata_content)
                    backups.append(metadata)
            except Exception as e:
                logger.error(f"Error reading metadata file {metadata_file}: {e}")

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)

        return backups

    async def restore_enhanced_backup(
        self,
        backup_name: str,
        components: list[str] | None = None,
        decrypt: bool = True,
    ) -> dict[str, Any]:
        """Restore from enhanced backup"""
        logger.info(f"Starting restore from backup: {backup_name}")

        try:
            # Load backup metadata
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            if not metadata_path.exists():
                raise ValueError(f"Backup metadata not found: {backup_name}")

            async with aiofiles.open(metadata_path) as f:
                metadata_content = await f.read()
                metadata = json.loads(metadata_content)

            # Find backup file
            backup_file = None
            for file_path in self.backup_dir.glob(f"{backup_name}_full.tar.gz*"):
                if file_path.exists():
                    backup_file = file_path
                    break

            if not backup_file:
                raise ValueError(f"Backup file not found: {backup_name}")

            # Decrypt if necessary
            if decrypt and metadata.get("encryption_info", {}).get("encrypted"):
                backup_file = await self._decrypt_backup(backup_file)

            # Extract backup
            extract_path = self.backup_dir / f"restore_{backup_name}"
            extract_path.mkdir(exist_ok=True)

            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=extract_path)

            # Restore components
            restored_components = []
            if components is None:
                components = list(metadata["components"].keys())

            for component in components:
                if component in metadata["components"]:
                    result = await self._restore_component(
                        component, extract_path, metadata
                    )
                    restored_components.append(result)

            # Cleanup
            shutil.rmtree(extract_path)

            await security_manager.log_security_event(
                event_type="backup_restored",
                resource=backup_name,
                action="restore",
                success=True,
                details={"components": components},
                risk_level="medium",
            )

            logger.info(f"Backup restore completed: {backup_name}")

            return {
                "status": "success",
                "backup_name": backup_name,
                "restored_components": restored_components,
            }

        except Exception as e:
            logger.error(f"Backup restore failed: {e}")

            await security_manager.log_security_event(
                event_type="backup_restore_failed",
                resource=backup_name,
                action="restore",
                success=False,
                details={"error": str(e)},
                risk_level="high",
            )

            return {"status": "failed", "backup_name": backup_name, "error": str(e)}

    async def _decrypt_backup(self, encrypted_path: Path) -> Path:
        """Decrypt backup file"""
        decrypted_path = encrypted_path.with_suffix("").with_suffix(".tar.gz")

        async with aiofiles.open(encrypted_path) as f:
            encrypted_data = await f.read()

        decrypted_data = security_manager.decrypt_data(encrypted_data)

        async with aiofiles.open(decrypted_path, "wb") as f:
            await f.write(decrypted_data.encode())

        return decrypted_path

    async def _restore_component(
        self, component: str, extract_path: Path, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Restore specific component"""
        try:
            if component == "database":
                return await self._restore_database(extract_path, metadata)
            if component == "files":
                return await self._restore_files(extract_path, metadata)
            if component == "config":
                return await self._restore_configuration(extract_path, metadata)
            if component == "vector_store":
                return await self._restore_vector_store(extract_path, metadata)
            return {
                "status": "skipped",
                "reason": f"Component {component} not supported for restore",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_backup_stats(self) -> dict[str, Any]:
        """Get comprehensive backup statistics"""
        try:
            backups = await self.list_enhanced_backups()

            total_backups = len(backups)
            total_size = sum(backup.get("total_size", 0) for backup in backups)

            # Calculate storage usage by component
            component_sizes = {}
            for backup in backups:
                for component, info in backup.get("components", {}).items():
                    if component not in component_sizes:
                        component_sizes[component] = 0
                    component_sizes[component] += info.get("size", 0)

            # Cloud storage stats
            cloud_backups = sum(
                1 for backup in backups if backup.get("cloud_locations")
            )

            return {
                "total_backups": total_backups,
                "total_size_mb": total_size / (1024 * 1024),
                "component_sizes_mb": {
                    component: size / (1024 * 1024)
                    for component, size in component_sizes.items()
                },
                "cloud_backups": cloud_backups,
                "encrypted_backups": sum(
                    1 for backup in backups if backup.get("encryption_info")
                ),
                "latest_backup": backups[0]["timestamp"] if backups else None,
                "oldest_backup": backups[-1]["timestamp"] if backups else None,
            }

        except Exception as e:
            logger.error(f"Failed to get backup stats: {e}")
            return {"error": str(e)}


# Global enhanced backup manager instance - lazy singleton
_enhanced_backup_manager_instance = None


def get_enhanced_backup_manager() -> EnhancedBackupManager:
    """Get or create the global enhanced backup manager instance"""
    global _enhanced_backup_manager_instance
    if _enhanced_backup_manager_instance is None:
        _enhanced_backup_manager_instance = EnhancedBackupManager()
    return _enhanced_backup_manager_instance


# For backward compatibility - create instance immediately
enhanced_backup_manager = get_enhanced_backup_manager()
