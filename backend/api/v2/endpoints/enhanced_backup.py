"""
Enhanced Backup API Endpoints

This module provides API endpoints for enhanced backup management:
- Create encrypted backups
- Cloud storage integration
- Backup verification and integrity checks
- Advanced restore operations
- Backup statistics and monitoring
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.v2.exceptions import (
    InternalServerError,
    NotFoundError,
    UnprocessableEntityError,
)
from auth.auth_middleware import get_current_user
from auth.models import User
from core.enhanced_backup_manager import get_enhanced_backup_manager
from core.security_manager import security_manager

router = APIRouter(prefix="/enhanced-backup", tags=["Enhanced Backup Management"])
logger = logging.getLogger(__name__)


class EnhancedBackupRequest(BaseModel):
    """Enhanced backup request model"""

    backup_name: str | None = None
    components: list[str] | None = None
    encrypt: bool | None = None
    upload_to_cloud: bool | None = None


class EnhancedBackupResponse(BaseModel):
    """Enhanced backup response model"""

    status: str
    backup_name: str
    metadata: dict[str, Any]
    path: str
    size_mb: float
    encrypted: bool
    cloud_uploaded: bool


class EnhancedRestoreRequest(BaseModel):
    """Enhanced restore request model"""

    backup_name: str
    components: list[str] | None = None
    decrypt: bool = True


class EnhancedBackupStatsResponse(BaseModel):
    """Enhanced backup statistics response model"""

    total_backups: int
    total_size_mb: float
    component_sizes_mb: dict[str, float]
    cloud_backups: int
    encrypted_backups: int
    latest_backup: str | None = None
    oldest_backup: str | None = None


@router.post("/create", response_model=EnhancedBackupResponse)
async def create_enhanced_backup(
    request: EnhancedBackupRequest, current_user: User = Depends(get_current_user)
):
    """
    Create enhanced backup with encryption and cloud upload
    """
    try:
        enhanced_backup_manager = get_enhanced_backup_manager()

        # Log security event
        await security_manager.log_security_event(
            event_type="backup_requested",
            resource="enhanced_backup",
            action="create",
            user_id=current_user.id,
            success=True,
            details=request.model_dump(),
            risk_level="low",
        )

        result = await enhanced_backup_manager.create_enhanced_backup(
            backup_name=request.backup_name,
            components=request.components,
            encrypt=request.encrypt,
            upload_to_cloud=request.upload_to_cloud,
        )

        if result["status"] == "failed":
            raise UnprocessableEntityError(
                message="Enhanced backup creation failed",
                details={"error": result["error"]},
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Enhanced backup created successfully",
                "data": result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating enhanced backup: {e}")

        await security_manager.log_security_event(
            event_type="backup_failed",
            resource="enhanced_backup",
            action="create",
            user_id=current_user.id,
            success=False,
            details={"error": str(e)},
            risk_level="high",
        )

        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to create enhanced backup",
                "details": {"error": str(e)},
            },
        )


@router.get("/list")
async def list_enhanced_backups(current_user: User = Depends(get_current_user)):
    """
    List all enhanced backups with metadata
    """
    try:
        enhanced_backup_manager = get_enhanced_backup_manager()
        backups = await enhanced_backup_manager.list_enhanced_backups()

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Enhanced backups retrieved successfully",
                "data": {"backups": backups, "total_count": len(backups)},
            },
        )

    except Exception as e:
        logger.error(f"Error listing enhanced backups: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to list enhanced backups",
                "details": {"error": str(e)},
            },
        )


@router.post("/restore", response_model=dict[str, Any])
async def restore_enhanced_backup(
    request: EnhancedRestoreRequest, current_user: User = Depends(get_current_user)
):
    """
    Restore from enhanced backup
    """
    try:
        enhanced_backup_manager = get_enhanced_backup_manager()

        # Log security event
        await security_manager.log_security_event(
            event_type="backup_restore_requested",
            resource=request.backup_name,
            action="restore",
            user_id=current_user.id,
            success=True,
            details=request.model_dump(),
            risk_level="high",
        )

        result = await enhanced_backup_manager.restore_enhanced_backup(
            backup_name=request.backup_name,
            components=request.components,
            decrypt=request.decrypt,
        )

        if result["status"] == "failed":
            raise UnprocessableEntityError(
                message="Enhanced backup restoration failed",
                details={"error": result["error"]},
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Enhanced backup restored successfully",
                "data": result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring enhanced backup: {e}")

        await security_manager.log_security_event(
            event_type="backup_restore_failed",
            resource=request.backup_name,
            action="restore",
            user_id=current_user.id,
            success=False,
            details={"error": str(e)},
            risk_level="high",
        )

        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to restore enhanced backup",
                "details": {"error": str(e)},
            },
        )


@router.get("/stats", response_model=EnhancedBackupStatsResponse)
async def get_enhanced_backup_stats(current_user: User = Depends(get_current_user)):
    """
    Get comprehensive enhanced backup statistics
    """
    try:
        enhanced_backup_manager = get_enhanced_backup_manager()
        stats = await enhanced_backup_manager.get_backup_stats()

        if "error" in stats:
            raise InternalServerError(
                message="Failed to get enhanced backup statistics",
                details={"error": stats["error"]},
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Enhanced backup statistics retrieved successfully",
                "data": stats,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enhanced backup stats: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get enhanced backup statistics",
                "details": {"error": str(e)},
            },
        )


@router.post("/verify/{backup_name}")
async def verify_enhanced_backup(backup_name: str):
    """
    Verify enhanced backup integrity
    """
    try:
        # Get backup metadata
        backups = await get_enhanced_backup_manager().list_enhanced_backups()
        backup_metadata = None

        for backup in backups:
            if backup["backup_id"] == backup_name:
                backup_metadata = backup
                break

        if not backup_metadata:
            raise NotFoundError(
                message="Enhanced backup not found",
                details={"backup_name": backup_name},
            )

        # Find backup file
        backup_file = None
        for file_path in get_enhanced_backup_manager().backup_dir.glob(
            f"{backup_name}_full.tar.gz*"
        ):
            if file_path.exists():
                backup_file = file_path
                break

        if not backup_file:
            raise NotFoundError(
                message="Enhanced backup file not found",
                details={"backup_name": backup_name},
            )

        # Verify backup integrity
        verification_result = (
            await get_enhanced_backup_manager()._verify_backup_integrity(
                backup_file, backup_metadata
            )
        )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Enhanced backup verification completed",
                "data": {
                    "backup_name": backup_name,
                    "verification_result": verification_result,
                    "metadata": backup_metadata,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying enhanced backup: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to verify enhanced backup",
                "details": {"error": str(e)},
            },
        )


@router.delete("/cleanup")
async def cleanup_enhanced_backups():
    """
    Clean up old enhanced backups based on retention policy
    """
    try:
        await get_enhanced_backup_manager()._cleanup_old_backups()

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Enhanced backup cleanup completed successfully",
                "data": {"action": "cleanup", "timestamp": datetime.now().isoformat()},
            },
        )

    except Exception as e:
        logger.error(f"Error cleaning up enhanced backups: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to cleanup enhanced backups",
                "details": {"error": str(e)},
            },
        )


@router.get("/config")
async def get_enhanced_backup_config():
    """
    Get enhanced backup configuration
    """
    try:
        config = get_enhanced_backup_manager().config.model_dump()

        # Remove sensitive information
        sensitive_keys = ["encryption_key", "cloud_bucket"]
        for key in sensitive_keys:
            if key in config:
                config[key] = "***REDACTED***"

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Enhanced backup configuration retrieved successfully",
                "data": config,
            },
        )

    except Exception as e:
        logger.error(f"Error getting enhanced backup config: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get enhanced backup configuration",
                "details": {"error": str(e)},
            },
        )


@router.get("/health")
async def enhanced_backup_health_check():
    """
    Health check for enhanced backup system
    """
    try:
        # Basic health checks
        checks = {
            "backup_manager": True,
            "backup_directory": get_enhanced_backup_manager().backup_dir.exists(),
            "component_directories": all(
                dir_path.exists()
                for dir_path in get_enhanced_backup_manager().component_dirs.values()
            ),
            "cloud_client": (
                get_enhanced_backup_manager().cloud_client is not None
                if get_enhanced_backup_manager().config.cloud_backup_enabled
                else True
            ),
        }

        # Test backup directory write permissions
        try:
            test_file = get_enhanced_backup_manager().backup_dir / "health_check.tmp"
            test_file.write_text("health_check")
            test_file.unlink()
            checks["write_permissions"] = True
        except Exception as e:
            checks["write_permissions"] = False
            logger.error(f"Write permissions health check failed: {e}")

        # Test cloud connectivity if enabled
        if (
            get_enhanced_backup_manager().config.cloud_backup_enabled
            and get_enhanced_backup_manager().cloud_client
        ):
            try:
                # Simple cloud test
                get_enhanced_backup_manager().cloud_client.list_buckets()
                checks["cloud_connectivity"] = True
            except Exception as e:
                checks["cloud_connectivity"] = False
                logger.error(f"Cloud connectivity health check failed: {e}")
        else:
            checks["cloud_connectivity"] = True  # Not applicable

        overall_status = "healthy" if all(checks.values()) else "unhealthy"

        return JSONResponse(
            status_code=200 if overall_status == "healthy" else 503,
            content={
                "status_code": 200 if overall_status == "healthy" else 503,
                "message": f"Enhanced backup system is {overall_status}",
                "data": {
                    "status": overall_status,
                    "checks": checks,
                    "config": {
                        "cloud_backup_enabled": get_enhanced_backup_manager().config.cloud_backup_enabled,
                        "encrypt_backups": get_enhanced_backup_manager().config.encrypt_backups,
                        "verify_backups": get_enhanced_backup_manager().config.verify_backups,
                    },
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )

    except Exception as e:
        logger.error(f"Enhanced backup health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status_code": 503,
                "error_code": "ENHANCED_BACKUP_SYSTEM_ERROR",
                "message": "Enhanced backup system health check failed",
                "details": {"error": str(e)},
            },
        )


@router.post("/schedule")
async def schedule_enhanced_backup(
    schedule_type: str = Query(
        ..., description="Schedule type: daily, weekly, monthly"
    ),
    hour: int = Query(2, description="Hour of day (0-23)"),
    minute: int = Query(0, description="Minute of hour (0-59)"),
    components: str | None = Query(
        None, description="Comma-separated list of components"
    ),
    encrypt: bool = Query(True, description="Encrypt backup"),
    upload_to_cloud: bool = Query(True, description="Upload to cloud"),
):
    """
    Schedule automated enhanced backups
    """
    try:
        # Parse components
        components_list = None
        if components:
            components_list = [comp.strip() for comp in components.split(",")]

        # TODO: Implement actual scheduling logic
        # This would typically integrate with a task scheduler like Celery or cron

        schedule_info = {
            "schedule_type": schedule_type,
            "hour": hour,
            "minute": minute,
            "components": components_list,
            "encrypt": encrypt,
            "upload_to_cloud": upload_to_cloud,
            "status": "scheduled",
            "next_run": "2025-01-01T02:00:00Z",  # Placeholder
        }

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Enhanced backup scheduled successfully",
                "data": schedule_info,
            },
        )

    except Exception as e:
        logger.error(f"Error scheduling enhanced backup: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to schedule enhanced backup",
                "details": {"error": str(e)},
            },
        )
