from __future__ import annotations

"""
API endpoints for monitoring, health, and status checks.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import structlog

from agents.agent_factory import AgentFactory
from core.alerting import alert_manager
from core.database_optimizer import DatabaseOptimizer
from core.monitoring import AlertSeverity, monitoring
from core.optimized_prompts import OptimizedPrompts
# Perplexity API removed - using DuckDuckGo fallback
from core.search_cache import SearchCache
from infrastructure.database.database import check_database_health

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
logger = structlog.get_logger()


async def check_agents_health() -> dict[str, Any]:
    """Check health of all registered agents"""
    try:
        factory = AgentFactory()
        agent_status = {}

        # Test each registered agent type
        for agent_type in factory.AGENT_REGISTRY:
            try:
                agent = factory.create_agent(agent_type)
                # Check if agent has health check method
                if hasattr(agent, "is_healthy"):
                    is_healthy = agent.is_healthy()
                else:
                    # Basic health check - try to get metadata
                    metadata = agent.get_metadata()
                    is_healthy = metadata is not None

                agent_status[agent_type] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "last_check": datetime.now().isoformat(),
                }
            except Exception as e:
                agent_status[agent_type] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now().isoformat(),
                }

        return {
            "status": (
                "healthy"
                if all(
                    status["status"] == "healthy" for status in agent_status.values()
                )
                else "unhealthy"
            ),
            "agents": agent_status,
        }
    except Exception as e:
        logger.error(f"Agent health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "agents": {}}


async def check_external_apis_health() -> dict[str, Any]:
    """Check health of external APIs - treated as optional components"""
    api_status = {}

    # Perplexity API removed - no longer checking
    api_status["perplexity"] = {
        "status": "removed",
        "note": "Perplexity API has been removed from the system",
        "optional": True,
        "last_check": datetime.now().isoformat(),
    }

    # Check MMLW embeddings (if available) - treated as optional
    try:
        from core.mmlw_embedding_client import mmlw_client

        mmlw_status = await mmlw_client.health_check()
        api_status["mmlw"] = {
            "status": (
                "healthy" if mmlw_status.get("is_available", False) else "unavailable"
            ),
            "details": mmlw_status,
            "optional": True,  # Mark as optional
            "last_check": datetime.now().isoformat(),
        }
    except ImportError:
        api_status["mmlw"] = {
            "status": "unavailable",
            "error": "MMLW client not available",
            "optional": True,  # Mark as optional
            "last_check": datetime.now().isoformat(),
        }
    except Exception as e:
        api_status["mmlw"] = {
            "status": "unavailable",
            "error": str(e),
            "optional": True,  # Mark as optional
            "last_check": datetime.now().isoformat(),
        }

    # External APIs are optional, so overall status is always "healthy"
    return {
        "status": "healthy",  # External APIs are optional
        "apis": api_status,
        "note": "External APIs are optional components",
    }


@router.get("/health")
async def health_check():
    """Get overall system health status."""
    try:
        health_checks = monitoring.health_checks

        # Check if any health checks are unhealthy
        unhealthy_checks = [
            name for name, check in health_checks.items() if check.status == "unhealthy"
        ]

        overall_status = "healthy" if not unhealthy_checks else "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                name: {
                    "status": check.status,
                    "response_time": check.response_time,
                    "last_check": check.last_check.isoformat(),
                    "error_message": check.error_message,
                }
                for name, check in health_checks.items()
            },
            "unhealthy_checks": unhealthy_checks,
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/metrics")
async def get_metrics():
    """Get current system metrics."""
    try:
        return monitoring.get_metrics_summary()
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.get("/performance")
async def get_performance_stats():
    """Get performance statistics."""
    try:
        return monitoring.get_performance_stats()
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance stats")


@router.get("/alerts")
async def get_alerts(active_only: bool = True):
    """Get system alerts."""
    try:
        alerts = monitoring.alerts

        if active_only:
            alerts = [alert for alert in alerts if not alert.resolved]

        return {
            "alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "source": alert.source,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": (
                        alert.resolved_at.isoformat() if alert.resolved_at else None
                    ),
                }
                for alert in alerts
            ],
            "total_alerts": len(alerts),
            "active_alerts": len([a for a in monitoring.alerts if not a.resolved]),
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    try:
        monitoring.resolve_alert(alert_id)
        return {"message": f"Alert {alert_id} resolved successfully"}
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@router.post("/alerts")
async def create_alert(title: str, message: str, severity: str, source: str):
    """Create a new alert."""
    try:
        severity_enum = AlertSeverity(severity.lower())
        monitoring.create_alert(title, message, severity_enum, source)
        return {"message": "Alert created successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid severity level")
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.get("/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data."""
    try:
        # Get all monitoring data
        metrics = monitoring.get_metrics_summary()
        performance = monitoring.get_performance_stats()
        alerts = [a for a in monitoring.alerts if not a.resolved]

        # Get cache performance
        cache_stats = {}
        try:
            search_cache = SearchCache()
            cache_stats["search_cache"] = {
                "size": len(search_cache._cache),
                "max_size": search_cache.max_size,
            }
        except Exception as e:
            logger.warning(f"Could not get search cache stats: {e}")

        # Get database stats
        db_stats = {}
        try:
            db_optimizer = DatabaseOptimizer()
            db_stats = await db_optimizer.get_database_stats()
        except Exception as e:
            logger.warning(f"Could not get database stats: {e}")

        # Get prompt optimization stats
        prompt_stats = {}
        try:
            optimized_prompts = OptimizedPrompts()
            prompt_stats = {
                "cached_prompts": len(optimized_prompts._cache),
                "cache_hits": optimized_prompts._cache_hits,
                "cache_misses": optimized_prompts._cache_misses,
            }
        except Exception as e:
            logger.warning(f"Could not get prompt stats: {e}")

        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "uptime": metrics.get("uptime", 0),
                "total_metrics": metrics.get("total_metrics", 0),
                "recent_metrics": metrics.get("recent_metrics", 0),
            },
            "performance": performance,
            "alerts": {
                "active_count": len(alerts),
                "recent_alerts": [
                    {
                        "title": alert.title,
                        "severity": alert.severity.value,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                    for alert in alerts[-5:]  # Last 5 alerts
                ],
            },
            "health_checks": metrics.get("health_checks", {}),
            "cache_performance": metrics.get("cache_performance", {}),
            "cache_stats": cache_stats,
            "database_stats": db_stats,
            "prompt_stats": prompt_stats,
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@router.get("/system")
async def get_system_info():
    """Get detailed system information."""
    try:
        import psutil

        # CPU info
        cpu_info = {
            "usage_percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        }

        # Memory info
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
        }

        # Disk info
        disk = psutil.disk_usage("/")
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100,
        }

        # Network info
        network = psutil.net_io_counters()
        network_info = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv,
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "network": network_info,
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system info")


@router.post("/cleanup")
async def trigger_cleanup():
    """Trigger manual cleanup of old data."""
    try:
        # This will trigger the cleanup task
        asyncio.create_task(monitoring._cleanup_old_data())
        return {"message": "Cleanup triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger cleanup")


@router.get("/logs")
async def get_recent_logs(limit: int = 100):
    """Get recent application logs."""
    try:
        # This is a simplified version - in production you'd want to read from log files
        return {
            "message": "Log retrieval not implemented in this version",
            "limit": limit,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get logs")


@router.get("/ready", tags=["Health"])
async def ready_check() -> JSONResponse:
    """Readiness check for services like database."""
    db_health = await check_database_health()

    if db_health.get("status") != "healthy":
        logger.warning("readiness.check.failed", database_status=db_health)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "services": {"database": db_health},
                "timestamp": datetime.now().isoformat(),
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "services": {"database": db_health},
            "timestamp": datetime.now().isoformat(),
        },
    )


@router.get("/status", tags=["Monitoring"])
async def detailed_status() -> JSONResponse:
    """Get detailed status of the application components."""
    # Perform comprehensive health checks
    db_health = await check_database_health()
    agents_health = await check_agents_health()
    external_apis_health = await check_external_apis_health()

    # Get system metrics (placeholder)
    import psutil

    memory_usage = psutil.virtual_memory().used
    cpu_usage = psutil.cpu_percent(interval=1)

    # Naprawione: Status systemu zależy tylko od krytycznych komponentów
    # External APIs (Perplexity, MMLW) nie są krytyczne dla działania systemu
    critical_components_healthy = all(
        [
            db_health.get("status") == "healthy",
            agents_health.get("status") == "healthy",
        ]
    )

    return JSONResponse(
        content={
            "service": "FoodSave AI Backend",
            "version": "1.0.0",
            "status": "healthy" if critical_components_healthy else "unhealthy",
            "components": {
                "database": db_health,
                "agents": agents_health,
                "external_apis": external_apis_health,
                "cache": "connected",  # Placeholder
                "orchestrator_pool": "active",  # Placeholder
            },
            "performance": {
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "active_connections": 5,  # Placeholder
            },
            "timestamp": datetime.now().isoformat(),
        }
    )


async def get_alerts() -> list[dict[str, Any]]:
    """Pobiera listę aktywnych alertów."""
    return alert_manager.get_active_alerts()


@router.get("/alerts/history", tags=["Monitoring"])
async def get_alert_history(hours: int = 24) -> list[dict[str, Any]]:
    """Pobiera historię alertów z ostatnich X godzin."""
    return alert_manager.get_alert_history(hours)


@router.post("/alerts/{rule_name}/acknowledge", tags=["Monitoring"])
async def acknowledge_alert(rule_name: str, user: str = "admin") -> dict[str, str]:
    """Potwierdza alert, wyciszając go tymczasowo."""
    alert_manager.acknowledge_alert(rule_name, user)
    return {"status": "ok", "message": f"Alert {rule_name} acknowledged by {user}"}


@router.post("/alerts/{rule_name}/resolve", tags=["Monitoring"])
async def resolve_alert(rule_name: str) -> dict[str, str]:
    """Rozwiązuje alert, usuwając go z aktywnych."""
    alert_manager.resolve_alert(rule_name)
    return {"status": "ok", "message": f"Alert {rule_name} resolved"}


@router.post("/alerts/rules", tags=["Monitoring"])
async def add_alert_rule(rule_data: dict[str, Any]) -> dict[str, str]:
    """Dodaje nową regułę alertu."""
    alert_manager.add_alert_rule(rule_data)
    return {"status": "ok", "message": "Alert rule added"}


@router.delete("/alerts/rules/{rule_name}", tags=["Monitoring"])
async def remove_alert_rule(rule_name: str) -> dict[str, str]:
    """Usuwa regułę alertu."""
    alert_manager.remove_alert_rule(rule_name)
    return {"status": "ok", "message": f"Alert rule {rule_name} removed"}
