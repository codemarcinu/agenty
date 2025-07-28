"""
Performance Monitoring System for FoodSave AI
Śledzi metryki wydajności i optymalizacji
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


@dataclass
class PerformanceMetric:
    """Pojedyncza metryka wydajności"""
    operation: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationMetrics:
    """Metryki optymalizacji"""
    cache_hit_rate: float = 0.0
    early_exit_rate: float = 0.0
    parallel_processing_time: float = 0.0
    database_connection_pool_usage: float = 0.0
    response_time_p95: float = 0.0
    rag_confidence_avg: float = 0.0
    memory_usage_mb: float = 0.0


class PerformanceMonitor:
    """System monitorowania wydajności"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.cache_stats = {"hits": 0, "misses": 0}
        self.early_exit_stats = {"total": 0, "early_exits": 0}
        self.parallel_processing_stats = {"total": 0, "total_time": 0.0}
        
    def record_operation(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Zapisuje metrykę operacji"""
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            metadata=metadata or {}
        )
        self.metrics.append(metric)
        self.operation_times[operation].append(duration)
        
        # Ogranicz historię do ostatnich 1000 pomiarów
        if len(self.operation_times[operation]) > 1000:
            self.operation_times[operation] = self.operation_times[operation][-1000:]
    
    def record_cache_hit(self):
        """Zapisuje trafienie w cache"""
        self.cache_stats["hits"] += 1
    
    def record_cache_miss(self):
        """Zapisuje chybię w cache"""
        self.cache_stats["misses"] += 1
    
    def record_early_exit(self):
        """Zapisuje early exit"""
        self.early_exit_stats["early_exits"] += 1
        self.early_exit_stats["total"] += 1
    
    def record_normal_exit(self):
        """Zapisuje normalny exit"""
        self.early_exit_stats["total"] += 1
    
    def record_parallel_processing(self, duration: float):
        """Zapisuje czas przetwarzania równoległego"""
        self.parallel_processing_stats["total"] += 1
        self.parallel_processing_stats["total_time"] += duration
    
    def get_cache_hit_rate(self) -> float:
        """Oblicza procent trafień w cache"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        return (self.cache_stats["hits"] / total * 100) if total > 0 else 0.0
    
    def get_early_exit_rate(self) -> float:
        """Oblicza procent early exit"""
        total = self.early_exit_stats["total"]
        return (self.early_exit_stats["early_exits"] / total * 100) if total > 0 else 0.0
    
    def get_avg_parallel_processing_time(self) -> float:
        """Oblicza średni czas przetwarzania równoległego"""
        total = self.parallel_processing_stats["total"]
        return (self.parallel_processing_stats["total_time"] / total) if total > 0 else 0.0
    
    def get_p95_response_time(self, operation: str = "chat_response") -> float:
        """Oblicza 95% percentyl czasu odpowiedzi"""
        times = self.operation_times.get(operation, [])
        if not times:
            return 0.0
        
        sorted_times = sorted(times)
        p95_index = int(len(sorted_times) * 0.95)
        return sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
    
    def get_optimization_metrics(self) -> OptimizationMetrics:
        """Zwraca wszystkie metryki optymalizacji"""
        return OptimizationMetrics(
            cache_hit_rate=self.get_cache_hit_rate(),
            early_exit_rate=self.get_early_exit_rate(),
            parallel_processing_time=self.get_avg_parallel_processing_time(),
            response_time_p95=self.get_p95_response_time(),
            rag_confidence_avg=self._get_avg_rag_confidence(),
            memory_usage_mb=self._get_memory_usage()
        )
    
    def _get_avg_rag_confidence(self) -> float:
        """Oblicza średnią pewność RAG"""
        rag_metrics = [m for m in self.metrics if m.operation == "rag_search"]
        if not rag_metrics:
            return 0.0
        
        confidences = [m.metadata.get("confidence", 0.0) for m in rag_metrics]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _get_memory_usage(self) -> float:
        """Oblicza użycie pamięci w MB"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generuje raport wydajności"""
        metrics = self.get_optimization_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "optimization_metrics": {
                "cache_hit_rate": f"{metrics.cache_hit_rate:.2f}%",
                "early_exit_rate": f"{metrics.early_exit_rate:.2f}%",
                "parallel_processing_time": f"{metrics.parallel_processing_time:.3f}s",
                "response_time_p95": f"{metrics.response_time_p95:.3f}s",
                "rag_confidence_avg": f"{metrics.rag_confidence_avg:.3f}",
                "memory_usage_mb": f"{metrics.memory_usage_mb:.2f}MB"
            },
            "cache_stats": self.cache_stats,
            "early_exit_stats": self.early_exit_stats,
            "parallel_processing_stats": self.parallel_processing_stats,
            "total_metrics_recorded": len(self.metrics)
        }


# Global instance
performance_monitor = PerformanceMonitor()
