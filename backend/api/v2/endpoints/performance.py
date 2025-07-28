"""
Performance Monitoring Endpoints
Endpoints do monitorowania wydajności i optymalizacji
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.performance_monitor import performance_monitor

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/metrics")
async def get_performance_metrics():
    """Pobiera metryki wydajności"""
    try:
        report = performance_monitor.get_performance_report()
        return JSONResponse(content=report, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to get performance metrics: {str(e)}"},
            status_code=500
        )


@router.get("/optimization")
async def get_optimization_metrics():
    """Pobiera metryki optymalizacji"""
    try:
        metrics = performance_monitor.get_optimization_metrics()
        return JSONResponse(
            content={
                "cache_hit_rate": f"{metrics.cache_hit_rate:.2f}%",
                "early_exit_rate": f"{metrics.early_exit_rate:.2f}%",
                "parallel_processing_time": f"{metrics.parallel_processing_time:.3f}s",
                "response_time_p95": f"{metrics.response_time_p95:.3f}s",
                "rag_confidence_avg": f"{metrics.rag_confidence_avg:.3f}",
                "memory_usage_mb": f"{metrics.memory_usage_mb:.2f}MB"
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to get optimization metrics: {str(e)}"},
            status_code=500
        )


@router.post("/record")
async def record_operation(operation: str, duration: float, metadata: dict = None):
    """Zapisuje metrykę operacji"""
    try:
        performance_monitor.record_operation(operation, duration, metadata or {})
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to record operation: {str(e)}"},
            status_code=500
        )


@router.post("/cache/hit")
async def record_cache_hit():
    """Zapisuje trafienie w cache"""
    try:
        performance_monitor.record_cache_hit()
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to record cache hit: {str(e)}"},
            status_code=500
        )


@router.post("/cache/miss")
async def record_cache_miss():
    """Zapisuje chybię w cache"""
    try:
        performance_monitor.record_cache_miss()
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to record cache miss: {str(e)}"},
            status_code=500
        )


@router.post("/early-exit")
async def record_early_exit():
    """Zapisuje early exit"""
    try:
        performance_monitor.record_early_exit()
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to record early exit: {str(e)}"},
            status_code=500
        )


@router.post("/parallel-processing")
async def record_parallel_processing(duration: float):
    """Zapisuje czas przetwarzania równoległego"""
    try:
        performance_monitor.record_parallel_processing(duration)
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to record parallel processing: {str(e)}"},
            status_code=500
        ) 