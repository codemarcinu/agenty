"""
Local System Optimizer for Offline LLM Operation
Optimizes system performance for local model deployment and processing.
"""

from dataclasses import asdict, dataclass
from enum import Enum
import gc
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class SystemResourceType(str, Enum):
    """Types of system resources to monitor and optimize"""

    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK = "disk"
    NETWORK = "network"


class OptimizationLevel(str, Enum):
    """Levels of system optimization"""

    CONSERVATIVE = "conservative"  # Minimal impact on system
    BALANCED = "balanced"  # Balanced performance/resource usage
    AGGRESSIVE = "aggressive"  # Maximum performance


@dataclass
class SystemMetrics:
    """System performance metrics"""

    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    gpu_available: bool
    gpu_memory_used_percent: float = 0.0
    active_processes: int = 0
    timestamp: float = 0.0


@dataclass
class ModelResourceRequirements:
    """Resource requirements for different model types"""

    model_name: str
    min_memory_gb: float
    recommended_memory_gb: float
    min_cpu_cores: int
    gpu_required: bool = False
    min_gpu_memory_gb: float = 0.0
    estimated_load_time_seconds: float = 30.0


class LocalSystemMonitor:
    """Monitors system resources for optimal local LLM performance"""

    def __init__(self, monitoring_interval: float = 5.0):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: list[SystemMetrics] = []
        self.max_history_size = 720  # 1 hour at 5s intervals
        self.monitoring_active = False
        self.monitor_thread: threading.Thread | None = None

    def start_monitoring(self):
        """Start continuous system monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitor_thread.start()
        logger.info("System monitoring started")

    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("System monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self._add_metrics(metrics)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)

        # Disk metrics
        disk = psutil.disk_usage("/")
        disk_usage_percent = disk.percent

        # GPU metrics (if available)
        gpu_available, gpu_memory_percent = self._get_gpu_metrics()

        # Process count
        active_processes = len(psutil.pids())

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            gpu_available=gpu_available,
            gpu_memory_used_percent=gpu_memory_percent,
            active_processes=active_processes,
            timestamp=time.time(),
        )

    def _get_gpu_metrics(self) -> tuple[bool, float]:
        """Get GPU metrics if available"""
        try:
            import nvidia_ml_py3 as nvml

            nvml.nvmlInit()

            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)

            memory_percent = (memory_info.used / memory_info.total) * 100
            return True, memory_percent

        except (ImportError, Exception):
            return False, 0.0

    def _add_metrics(self, metrics: SystemMetrics):
        """Add metrics to history with size limit"""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size :]

    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        return self._collect_metrics()

    def get_average_metrics(self, minutes: int = 5) -> SystemMetrics | None:
        """Get average metrics over specified time period"""
        if not self.metrics_history:
            return None

        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return None

        return SystemMetrics(
            cpu_percent=sum(m.cpu_percent for m in recent_metrics)
            / len(recent_metrics),
            memory_percent=sum(m.memory_percent for m in recent_metrics)
            / len(recent_metrics),
            memory_available_gb=sum(m.memory_available_gb for m in recent_metrics)
            / len(recent_metrics),
            disk_usage_percent=sum(m.disk_usage_percent for m in recent_metrics)
            / len(recent_metrics),
            gpu_available=any(m.gpu_available for m in recent_metrics),
            gpu_memory_used_percent=sum(
                m.gpu_memory_used_percent for m in recent_metrics
            )
            / len(recent_metrics),
            active_processes=int(
                sum(m.active_processes for m in recent_metrics) / len(recent_metrics)
            ),
            timestamp=time.time(),
        )


class ModelPerformanceOptimizer:
    """Optimizes model performance based on system capabilities"""

    def __init__(self):
        self.model_requirements = {
            "llama3.2:3b": ModelResourceRequirements(
                model_name="llama3.2:3b",
                min_memory_gb=4.0,
                recommended_memory_gb=8.0,
                min_cpu_cores=2,
                gpu_required=False,
                estimated_load_time_seconds=15.0,
            ),
            "llama3.2:8b": ModelResourceRequirements(
                model_name="llama3.2:8b",
                min_memory_gb=8.0,
                recommended_memory_gb=16.0,
                min_cpu_cores=4,
                gpu_required=False,
                estimated_load_time_seconds=30.0,
            ),
            "llava:7b": ModelResourceRequirements(
                model_name="llava:7b",
                min_memory_gb=8.0,
                recommended_memory_gb=16.0,
                min_cpu_cores=4,
                gpu_required=False,
                min_gpu_memory_gb=6.0,
                estimated_load_time_seconds=45.0,
            ),
            "llava:13b": ModelResourceRequirements(
                model_name="llava:13b",
                min_memory_gb=16.0,
                recommended_memory_gb=32.0,
                min_cpu_cores=8,
                gpu_required=False,
                min_gpu_memory_gb=12.0,
                estimated_load_time_seconds=60.0,
            ),
            "aya:8b": ModelResourceRequirements(
                model_name="aya:8b",
                min_memory_gb=8.0,
                recommended_memory_gb=16.0,
                min_cpu_cores=4,
                gpu_required=False,
                estimated_load_time_seconds=30.0,
            ),
        }

        self.optimization_configs = {
            OptimizationLevel.CONSERVATIVE: {
                "num_ctx": 2048,
                "num_thread": min(4, os.cpu_count() or 4),
                "num_gpu": 0,  # CPU only
                "batch_size": 1,
            },
            OptimizationLevel.BALANCED: {
                "num_ctx": 4096,
                "num_thread": min(8, os.cpu_count() or 4),
                "num_gpu": 1 if self._has_gpu() else 0,
                "batch_size": 2,
            },
            OptimizationLevel.AGGRESSIVE: {
                "num_ctx": 8192,
                "num_thread": os.cpu_count() or 4,
                "num_gpu": -1,  # Use all available GPUs
                "batch_size": 4,
            },
        }

    def _has_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import nvidia_ml_py3 as nvml

            nvml.nvmlInit()
            return True
        except (ImportError, Exception):
            return False

    def can_run_model(self, model_name: str, current_metrics: SystemMetrics) -> bool:
        """Check if system can run specified model"""
        if model_name not in self.model_requirements:
            logger.warning(f"Unknown model requirements for: {model_name}")
            return True  # Assume it can run

        requirements = self.model_requirements[model_name]

        # Check memory
        if current_metrics.memory_available_gb < requirements.min_memory_gb:
            logger.warning(
                f"Insufficient memory for {model_name}: "
                f"need {requirements.min_memory_gb}GB, "
                f"available {current_metrics.memory_available_gb:.1f}GB"
            )
            return False

        # Check CPU
        available_cores = os.cpu_count() or 1
        if available_cores < requirements.min_cpu_cores:
            logger.warning(
                f"Insufficient CPU cores for {model_name}: "
                f"need {requirements.min_cpu_cores}, "
                f"available {available_cores}"
            )
            return False

        # Check GPU if required
        if requirements.gpu_required and not current_metrics.gpu_available:
            logger.warning(f"GPU required for {model_name} but not available")
            return False

        return True

    def get_optimal_model_for_system(
        self, task_type: str, current_metrics: SystemMetrics
    ) -> str | None:
        """Get optimal model based on system capabilities"""

        # Model preferences by task type
        task_models = {
            "ocr_vision": ["llava:13b", "llava:7b"],
            "text_analysis": ["llama3.2:8b", "llama3.2:3b"],
            "polish_processing": ["aya:8b", "llama3.2:8b"],
            "fast_processing": ["llama3.2:3b"],
        }

        preferred_models = task_models.get(task_type, ["llama3.2:3b"])

        # Find best model that can run on current system
        for model in preferred_models:
            if self.can_run_model(model, current_metrics):
                return model

        # Fallback to smallest model
        return "llama3.2:3b"

    def get_optimization_config(
        self,
        model_name: str,
        optimization_level: OptimizationLevel,
        current_metrics: SystemMetrics,
    ) -> dict[str, Any]:
        """Get optimized configuration for model"""
        base_config = self.optimization_configs[optimization_level].copy()

        # Adjust based on current system state
        if current_metrics.memory_percent > 80:
            # High memory usage - reduce context
            base_config["num_ctx"] = min(base_config["num_ctx"], 2048)
            base_config["batch_size"] = 1

        if current_metrics.cpu_percent > 80:
            # High CPU usage - reduce threads
            base_config["num_thread"] = max(1, base_config["num_thread"] // 2)

        if (
            current_metrics.gpu_available
            and current_metrics.gpu_memory_used_percent > 80
        ):
            # High GPU memory usage - fallback to CPU
            base_config["num_gpu"] = 0

        return base_config


class LocalCacheManager:
    """Manages local caching for model outputs and intermediate results"""

    def __init__(self, cache_dir: str = "./cache/local_models"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: dict[str, Any] = {}
        self.max_memory_cache_size = 100  # Number of items
        self.max_disk_cache_size_gb = 5.0

    def get_cache_key(
        self, model_name: str, input_hash: str, config: dict[str, Any]
    ) -> str:
        """Generate cache key for model output"""
        config_str = json.dumps(config, sort_keys=True)
        return f"{model_name}_{input_hash}_{hash(config_str)}"

    def get_from_memory_cache(self, cache_key: str) -> Any | None:
        """Get result from memory cache"""
        return self.memory_cache.get(cache_key)

    def put_to_memory_cache(self, cache_key: str, result: Any):
        """Put result to memory cache with size limit"""
        if len(self.memory_cache) >= self.max_memory_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]

        self.memory_cache[cache_key] = result

    def get_from_disk_cache(self, cache_key: str) -> Any | None:
        """Get result from disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading disk cache: {e}")
        return None

    def put_to_disk_cache(self, cache_key: str, result: Any):
        """Put result to disk cache"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # Check and manage disk cache size
            self._manage_disk_cache_size()

        except Exception as e:
            logger.error(f"Error writing disk cache: {e}")

    def _manage_disk_cache_size(self):
        """Manage disk cache size by removing old files"""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
            max_size_bytes = self.max_disk_cache_size_gb * 1024**3

            if total_size > max_size_bytes:
                # Remove oldest files
                cache_files = list(self.cache_dir.glob("*.json"))
                cache_files.sort(key=lambda x: x.stat().st_mtime)

                removed_size = 0
                target_removal = total_size - max_size_bytes

                for file in cache_files:
                    if removed_size >= target_removal:
                        break

                    file_size = file.stat().st_size
                    file.unlink()
                    removed_size += file_size

                logger.info(
                    f"Cleaned disk cache: removed {removed_size / 1024**2:.1f}MB"
                )

        except Exception as e:
            logger.error(f"Error managing disk cache size: {e}")

    def clear_cache(self, cache_type: str = "all"):
        """Clear cache (memory, disk, or all)"""
        if cache_type in ("memory", "all"):
            self.memory_cache.clear()
            logger.info("Memory cache cleared")

        if cache_type in ("disk", "all"):
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Disk cache cleared")


class LocalSystemOptimizer:
    """Main optimizer class for local LLM system"""

    def __init__(self):
        self.monitor = LocalSystemMonitor()
        self.performance_optimizer = ModelPerformanceOptimizer()
        self.cache_manager = LocalCacheManager()
        self.optimization_level = OptimizationLevel.BALANCED
        self.auto_optimization_enabled = True

    def start_optimization(self):
        """Start system optimization"""
        self.monitor.start_monitoring()
        logger.info("Local system optimization started")

    def stop_optimization(self):
        """Stop system optimization"""
        self.monitor.stop_monitoring()
        logger.info("Local system optimization stopped")

    def set_optimization_level(self, level: OptimizationLevel):
        """Set optimization level"""
        self.optimization_level = level
        logger.info(f"Optimization level set to: {level.value}")

    def get_optimal_configuration(
        self, model_name: str, task_type: str = "general"
    ) -> dict[str, Any]:
        """Get optimal configuration for model and task"""
        current_metrics = self.monitor.get_current_metrics()

        # Check if model can run
        if not self.performance_optimizer.can_run_model(model_name, current_metrics):
            # Suggest alternative model
            alternative = self.performance_optimizer.get_optimal_model_for_system(
                task_type, current_metrics
            )
            logger.warning(f"Model {model_name} cannot run, suggesting: {alternative}")
            if alternative:
                model_name = alternative

        # Get optimization config
        config = self.performance_optimizer.get_optimization_config(
            model_name, self.optimization_level, current_metrics
        )

        # Add system-specific adjustments
        config.update(
            {
                "model_name": model_name,
                "optimization_level": self.optimization_level.value,
                "system_metrics": asdict(current_metrics),
            }
        )

        return config

    def optimize_before_inference(self) -> bool:
        """Perform pre-inference system optimization"""
        try:
            # Force garbage collection
            gc.collect()

            # Get current metrics
            current_metrics = self.monitor.get_current_metrics()

            # Check if system needs optimization
            if current_metrics.memory_percent > 85 or current_metrics.cpu_percent > 90:

                logger.warning(
                    "System resources critically high, "
                    "consider reducing load before inference"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error in pre-inference optimization: {e}")
            return False

    def get_system_recommendations(self) -> list[str]:
        """Get system optimization recommendations"""
        current_metrics = self.monitor.get_current_metrics()
        recommendations = []

        if current_metrics.memory_percent > 80:
            recommendations.append(
                "High memory usage detected. Consider:\n"
                "- Reducing model context length\n"
                "- Using smaller models\n"
                "- Clearing model cache"
            )

        if current_metrics.cpu_percent > 80:
            recommendations.append(
                "High CPU usage detected. Consider:\n"
                "- Reducing number of threads\n"
                "- Using GPU acceleration if available\n"
                "- Processing fewer requests concurrently"
            )

        if not current_metrics.gpu_available and current_metrics.memory_percent > 70:
            recommendations.append(
                "GPU not available and memory usage high. Consider:\n"
                "- Installing CUDA and GPU drivers\n"
                "- Using smaller models\n"
                "- Enabling model quantization"
            )

        if current_metrics.disk_usage_percent > 90:
            recommendations.append(
                "Disk space critically low. Consider:\n"
                "- Clearing model cache\n"
                "- Removing unused models\n"
                "- Freeing up disk space"
            )

        return recommendations if recommendations else ["System performance is optimal"]


# Global optimizer instance
local_system_optimizer = LocalSystemOptimizer()
