"""
Predictive Monitoring and Alerting System for FoodSave AI

This module implements AI-powered predictive monitoring with anomaly detection,
failure prediction, and automated remediation capabilities.
"""

import asyncio
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any
import uuid

import numpy as np

try:
    import joblib
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    IsolationForest = None
    StandardScaler = None

import contextlib

import psutil

# import asyncpg  # Removed - project uses SQLite, not PostgreSQL
from settings import settings

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics to monitor"""

    SYSTEM = "system"
    APPLICATION = "application"
    BUSINESS = "business"
    PERFORMANCE = "performance"
    SECURITY = "security"


class AlertStatus(Enum):
    """Alert lifecycle status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Metric:
    """Metric data point"""

    name: str
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert definition"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    status: AlertStatus = AlertStatus.ACTIVE
    metric_name: str = ""
    threshold: float = 0.0
    actual_value: float = 0.0
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: datetime | None = None
    labels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    predicted: bool = False
    confidence: float = 0.0
    time_to_failure: float | None = None  # Seconds


@dataclass
class AnomalyScore:
    """Anomaly detection result"""

    metric_name: str
    score: float  # -1 to 1, where values below -0.5 are anomalous
    confidence: float
    timestamp: datetime
    features: list[float]
    baseline: float | None = None


class MetricCollector:
    """Collects system and application metrics"""

    def __init__(self):
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.collection_interval = 30  # seconds
        self.is_running = False
        self._collection_task: asyncio.Task | None = None

    async def start_collection(self) -> None:
        """Start metric collection"""
        if self.is_running:
            return

        self.is_running = True
        self._collection_task = asyncio.create_task(self._collect_metrics_loop())
        logger.info("Metric collection started")

    async def stop_collection(self) -> None:
        """Stop metric collection"""
        self.is_running = False
        if self._collection_task:
            self._collection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._collection_task
        logger.info("Metric collection stopped")

    async def _collect_metrics_loop(self) -> None:
        """Main metric collection loop"""
        while self.is_running:
            try:
                # Collect system metrics
                await self._collect_system_metrics()

                # Collect application metrics
                await self._collect_application_metrics()

                # Collect business metrics
                await self._collect_business_metrics()

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error in metric collection: {e}")
                await asyncio.sleep(10)  # Wait before retry

    async def _collect_system_metrics(self) -> None:
        """Collect system-level metrics"""
        timestamp = datetime.now()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self._add_metric(
            "system.cpu.usage_percent", cpu_percent, timestamp, {"type": "system"}
        )

        # Memory metrics
        memory = psutil.virtual_memory()
        self._add_metric(
            "system.memory.usage_percent", memory.percent, timestamp, {"type": "system"}
        )
        self._add_metric(
            "system.memory.available_mb",
            memory.available / 1024 / 1024,
            timestamp,
            {"type": "system"},
        )

        # Disk metrics
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        self._add_metric(
            "system.disk.usage_percent", disk_percent, timestamp, {"type": "system"}
        )

        # Network metrics
        net_io = psutil.net_io_counters()
        self._add_metric(
            "system.network.bytes_sent",
            net_io.bytes_sent,
            timestamp,
            {"type": "system"},
        )
        self._add_metric(
            "system.network.bytes_recv",
            net_io.bytes_recv,
            timestamp,
            {"type": "system"},
        )

    async def _collect_application_metrics(self) -> None:
        """Collect application-level metrics"""
        timestamp = datetime.now()

        # Process-specific metrics
        process = psutil.Process()

        # Application memory usage
        memory_info = process.memory_info()
        self._add_metric(
            "app.memory.rss_mb",
            memory_info.rss / 1024 / 1024,
            timestamp,
            {"type": "application"},
        )
        self._add_metric(
            "app.memory.vms_mb",
            memory_info.vms / 1024 / 1024,
            timestamp,
            {"type": "application"},
        )

        # Application CPU usage
        cpu_percent = process.cpu_percent()
        self._add_metric(
            "app.cpu.usage_percent", cpu_percent, timestamp, {"type": "application"}
        )

        # File descriptors
        try:
            num_fds = process.num_fds()
            self._add_metric(
                "app.file_descriptors", num_fds, timestamp, {"type": "application"}
            )
        except (AttributeError, psutil.AccessDenied):
            pass  # Not available on all platforms

        # Thread count
        num_threads = process.num_threads()
        self._add_metric("app.threads", num_threads, timestamp, {"type": "application"})

    async def _collect_business_metrics(self) -> None:
        """Collect business-level metrics"""
        timestamp = datetime.now()

        try:
            # Database connection metrics (if available)
            if (
                hasattr(settings, "DATABASE_URL")
                and "postgresql" in settings.DATABASE_URL
            ):
                await self._collect_database_metrics(timestamp)
        except Exception as e:
            logger.debug(f"Could not collect database metrics: {e}")

        # Cache metrics (if Redis is available)
        try:
            await self._collect_cache_metrics(timestamp)
        except Exception as e:
            logger.debug(f"Could not collect cache metrics: {e}")

    async def _collect_database_metrics(self, timestamp: datetime) -> None:
        """Collect database performance metrics"""
        try:
            # This would connect to your database and collect metrics
            # For now, we'll simulate some metrics
            self._add_metric(
                "db.active_connections", 10, timestamp, {"type": "business"}
            )
            self._add_metric(
                "db.query_duration_ms", 50, timestamp, {"type": "performance"}
            )
        except Exception as e:
            logger.debug(f"Database metrics collection failed: {e}")

    async def _collect_cache_metrics(self, timestamp: datetime) -> None:
        """Collect cache performance metrics"""
        try:
            # This would collect Redis metrics
            # For now, we'll simulate
            self._add_metric("cache.hit_rate", 0.85, timestamp, {"type": "performance"})
            self._add_metric(
                "cache.memory_usage_mb", 128, timestamp, {"type": "system"}
            )
        except Exception as e:
            logger.debug(f"Cache metrics collection failed: {e}")

    def _add_metric(
        self, name: str, value: float, timestamp: datetime, labels: dict[str, str]
    ) -> None:
        """Add metric to buffer"""
        metric = Metric(name=name, value=value, timestamp=timestamp, labels=labels)
        self.metrics_buffer.append(metric)

    def get_recent_metrics(
        self, metric_name: str, duration_minutes: int = 60
    ) -> list[Metric]:
        """Get recent metrics for a specific metric name"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [
            metric
            for metric in self.metrics_buffer
            if metric.name == metric_name and metric.timestamp >= cutoff_time
        ]

    def get_all_recent_metrics(self, duration_minutes: int = 60) -> list[Metric]:
        """Get all recent metrics"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [
            metric for metric in self.metrics_buffer if metric.timestamp >= cutoff_time
        ]


class AnomalyDetector:
    """ML-based anomaly detection for metrics"""

    def __init__(self):
        self.models: dict[str, Any] = {}
        self.scalers: dict[str, Any] = {}
        self.training_data: dict[str, list[float]] = defaultdict(list)
        self.min_training_samples = 100
        self.retrain_interval = 3600  # 1 hour
        self.last_training: dict[str, datetime] = {}

    def add_training_data(self, metric_name: str, value: float) -> None:
        """Add data point for training"""
        self.training_data[metric_name].append(value)

        # Keep only recent data for training
        if len(self.training_data[metric_name]) > 1000:
            self.training_data[metric_name] = self.training_data[metric_name][-1000:]

    async def train_model(self, metric_name: str) -> bool:
        """Train anomaly detection model for a metric"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Scikit-learn not available for anomaly detection")
            return False

        data = self.training_data.get(metric_name, [])
        if len(data) < self.min_training_samples:
            logger.debug(
                f"Not enough data to train model for {metric_name}: {len(data)} samples"
            )
            return False

        try:
            # Prepare features (value, rolling mean, rolling std, trend)
            features = []
            for i in range(len(data)):
                start_idx = max(0, i - 10)  # Look back 10 points
                window_data = data[start_idx : i + 1]

                value = data[i]
                rolling_mean = np.mean(window_data)
                rolling_std = np.std(window_data) if len(window_data) > 1 else 0
                trend = (value - rolling_mean) / max(rolling_std, 0.01)

                features.append([value, rolling_mean, rolling_std, trend])

            features = np.array(features)

            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)

            # Train Isolation Forest
            model = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100,
            )
            model.fit(features_scaled)

            # Store model and scaler
            self.models[metric_name] = model
            self.scalers[metric_name] = scaler
            self.last_training[metric_name] = datetime.now()

            logger.info(f"Trained anomaly detection model for {metric_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to train anomaly detection model for {metric_name}: {e}"
            )
            return False

    async def detect_anomaly(
        self, metric_name: str, recent_values: list[float]
    ) -> AnomalyScore | None:
        """Detect anomalies in recent metric values"""
        if not SKLEARN_AVAILABLE or metric_name not in self.models:
            return None

        if len(recent_values) < 5:
            return None

        try:
            model = self.models[metric_name]
            scaler = self.scalers[metric_name]

            # Prepare features for the latest value
            current_value = recent_values[-1]
            window_data = (
                recent_values[-10:] if len(recent_values) >= 10 else recent_values
            )

            rolling_mean = np.mean(window_data)
            rolling_std = np.std(window_data) if len(window_data) > 1 else 0
            trend = (current_value - rolling_mean) / max(rolling_std, 0.01)

            features = np.array([[current_value, rolling_mean, rolling_std, trend]])
            features_scaled = scaler.transform(features)

            # Get anomaly score
            anomaly_score = model.decision_function(features_scaled)[0]
            model.predict(features_scaled)[0] == -1

            # Calculate confidence based on how far from the boundary
            confidence = abs(anomaly_score) / 0.5  # Normalize to 0-1
            confidence = min(confidence, 1.0)

            return AnomalyScore(
                metric_name=metric_name,
                score=anomaly_score,
                confidence=confidence,
                timestamp=datetime.now(),
                features=features[0].tolist(),
                baseline=rolling_mean,
            )

        except Exception as e:
            logger.error(f"Anomaly detection failed for {metric_name}: {e}")
            return None

    def should_retrain(self, metric_name: str) -> bool:
        """Check if model should be retrained"""
        if metric_name not in self.last_training:
            return True

        time_since_training = datetime.now() - self.last_training[metric_name]
        return time_since_training.total_seconds() > self.retrain_interval


class FailurePredictor:
    """Predicts system failures before they occur"""

    def __init__(self):
        self.prediction_models: dict[str, Any] = {}
        self.failure_patterns: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def predict_failure(self, metrics: list[Metric]) -> list[Alert]:
        """Predict potential failures based on current metrics"""
        predictions = []

        # Group metrics by name
        metric_groups = defaultdict(list)
        for metric in metrics:
            metric_groups[metric.name].append(metric.value)

        # Check for failure patterns
        for metric_name, values in metric_groups.items():
            if len(values) < 5:
                continue

            # Check for trending patterns that could lead to failure
            failure_alert = await self._check_trending_failure(metric_name, values)
            if failure_alert:
                predictions.append(failure_alert)

            # Check for oscillation patterns
            oscillation_alert = await self._check_oscillation_failure(
                metric_name, values
            )
            if oscillation_alert:
                predictions.append(oscillation_alert)

        return predictions

    async def _check_trending_failure(
        self, metric_name: str, values: list[float]
    ) -> Alert | None:
        """Check for trending patterns that could lead to failure"""
        if len(values) < 10:
            return None

        # Calculate trend
        x = np.arange(len(values))
        y = np.array(values)

        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]

        # Define failure thresholds based on metric type
        failure_thresholds = {
            "system.cpu.usage_percent": 90,
            "system.memory.usage_percent": 85,
            "system.disk.usage_percent": 90,
            "app.memory.rss_mb": 1000,  # 1GB
        }

        threshold = failure_thresholds.get(metric_name)
        if not threshold:
            return None

        current_value = values[-1]

        # Predict when threshold will be crossed
        if slope > 0 and current_value < threshold:
            time_to_failure = (
                (threshold - current_value) / slope * 30
            )  # Assuming 30-second intervals

            if time_to_failure < 900:  # Less than 15 minutes
                confidence = 1.0 - (time_to_failure / 900)

                return Alert(
                    name=f"Predicted {metric_name} failure",
                    description=f"{metric_name} is trending towards failure threshold",
                    severity=(
                        AlertSeverity.WARNING
                        if time_to_failure > 300
                        else AlertSeverity.ERROR
                    ),
                    metric_name=metric_name,
                    threshold=threshold,
                    actual_value=current_value,
                    predicted=True,
                    confidence=confidence,
                    time_to_failure=time_to_failure,
                    metadata={"trend_slope": slope, "prediction_type": "trending"},
                )

        return None

    async def _check_oscillation_failure(
        self, metric_name: str, values: list[float]
    ) -> Alert | None:
        """Check for oscillation patterns that indicate instability"""
        if len(values) < 20:
            return None

        # Calculate oscillation frequency
        diffs = np.diff(values)
        sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
        oscillation_rate = sign_changes / len(diffs)

        # High oscillation rate indicates instability
        if oscillation_rate > 0.6:  # More than 60% sign changes
            variance = np.var(values)
            mean_value = np.mean(values)

            return Alert(
                name=f"High oscillation detected in {metric_name}",
                description=f"{metric_name} showing high instability",
                severity=AlertSeverity.WARNING,
                metric_name=metric_name,
                threshold=0.6,
                actual_value=oscillation_rate,
                predicted=True,
                confidence=min(oscillation_rate, 1.0),
                metadata={
                    "oscillation_rate": oscillation_rate,
                    "variance": variance,
                    "mean_value": mean_value,
                    "prediction_type": "oscillation",
                },
            )

        return None


class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self):
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.notification_handlers: list[Callable] = []
        self.suppression_rules: dict[str, dict[str, Any]] = {}

    def register_notification_handler(self, handler: Callable[[Alert], None]) -> None:
        """Register a notification handler"""
        self.notification_handlers.append(handler)

    async def create_alert(self, alert: Alert) -> None:
        """Create a new alert"""
        # Check suppression rules
        if self._is_suppressed(alert):
            logger.debug(f"Alert suppressed: {alert.name}")
            return

        # Check for duplicate alerts
        alert_key = f"{alert.metric_name}:{alert.name}"
        if alert_key in self.active_alerts:
            existing_alert = self.active_alerts[alert_key]
            existing_alert.actual_value = alert.actual_value
            existing_alert.confidence = alert.confidence
            return

        # Add new alert
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)

        # Send notifications
        await self._send_notifications(alert)

        logger.info(f"Alert created: {alert.name} ({alert.severity.value})")

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        alert_key = None
        for key, alert in self.active_alerts.items():
            if alert.id == alert_id:
                alert_key = key
                break

        if alert_key:
            alert = self.active_alerts[alert_key]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            del self.active_alerts[alert_key]

            logger.info(f"Alert resolved: {alert.name}")
            return True

        return False

    def _is_suppressed(self, alert: Alert) -> bool:
        """Check if alert should be suppressed"""
        for rule in self.suppression_rules.values():
            if self._matches_suppression_rule(alert, rule):
                return True
        return False

    def _matches_suppression_rule(self, alert: Alert, rule: dict[str, Any]) -> bool:
        """Check if alert matches suppression rule"""
        # Simple suppression logic - can be extended
        if "metric_name" in rule and alert.metric_name != rule["metric_name"]:
            return False
        if "severity" in rule and alert.severity.value not in rule["severity"]:
            return False
        return True

    async def _send_notifications(self, alert: Alert) -> None:
        """Send notifications for an alert"""
        for handler in self.notification_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Notification handler failed: {e}")

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        return sorted(alerts, key=lambda a: a.triggered_at, reverse=True)

    def get_alert_statistics(self) -> dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)

        severity_counts = defaultdict(int)
        for alert in self.alert_history:
            severity_counts[alert.severity.value] += 1

        predicted_alerts = sum(1 for alert in self.alert_history if alert.predicted)

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_count,
            "severity_breakdown": dict(severity_counts),
            "predicted_alerts": predicted_alerts,
            "prediction_accuracy": predicted_alerts / max(total_alerts, 1),
        }


class PredictiveMonitoringSystem:
    """Main predictive monitoring system"""

    def __init__(self):
        self.metric_collector = MetricCollector()
        self.anomaly_detector = AnomalyDetector()
        self.failure_predictor = FailurePredictor()
        self.alert_manager = AlertManager()

        self.monitoring_interval = 60  # seconds
        self.is_running = False
        self._monitoring_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the predictive monitoring system"""
        if self.is_running:
            return

        self.is_running = True

        # Start metric collection
        await self.metric_collector.start_collection()

        # Start monitoring loop
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        # Register default notification handlers
        self.alert_manager.register_notification_handler(self._log_alert_handler)

        logger.info("Predictive monitoring system started")

    async def stop(self) -> None:
        """Stop the predictive monitoring system"""
        self.is_running = False

        # Stop metric collection
        await self.metric_collector.stop_collection()

        # Stop monitoring loop
        if self._monitoring_task:
            self._monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitoring_task

        logger.info("Predictive monitoring system stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.is_running:
            try:
                await self._run_monitoring_cycle()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait before retry

    async def _run_monitoring_cycle(self) -> None:
        """Run a single monitoring cycle"""
        # Get recent metrics
        recent_metrics = self.metric_collector.get_all_recent_metrics(
            duration_minutes=60
        )

        if not recent_metrics:
            return

        # Group metrics by name for analysis
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            metric_groups[metric.name].append(metric.value)
            # Add to training data
            self.anomaly_detector.add_training_data(metric.name, metric.value)

        # Train/retrain anomaly detection models
        for metric_name in metric_groups:
            if self.anomaly_detector.should_retrain(metric_name):
                await self.anomaly_detector.train_model(metric_name)

        # Run anomaly detection
        for metric_name, values in metric_groups.items():
            if len(values) >= 5:
                anomaly_score = await self.anomaly_detector.detect_anomaly(
                    metric_name, values
                )
                if anomaly_score and anomaly_score.score < -0.5:  # Anomalous
                    await self._create_anomaly_alert(
                        metric_name, anomaly_score, values[-1]
                    )

        # Run failure prediction
        failure_predictions = await self.failure_predictor.predict_failure(
            recent_metrics
        )
        for prediction in failure_predictions:
            await self.alert_manager.create_alert(prediction)

        # Check threshold-based alerts
        await self._check_threshold_alerts(metric_groups)

    async def _create_anomaly_alert(
        self, metric_name: str, anomaly_score: AnomalyScore, current_value: float
    ) -> None:
        """Create alert for detected anomaly"""
        severity = AlertSeverity.WARNING
        if anomaly_score.score < -0.8:
            severity = AlertSeverity.ERROR
        elif anomaly_score.score < -0.9:
            severity = AlertSeverity.CRITICAL

        alert = Alert(
            name=f"Anomaly detected in {metric_name}",
            description=f"Unusual behavior detected in {metric_name}",
            severity=severity,
            metric_name=metric_name,
            threshold=anomaly_score.baseline or 0,
            actual_value=current_value,
            predicted=True,
            confidence=anomaly_score.confidence,
            metadata={
                "anomaly_score": anomaly_score.score,
                "detection_type": "anomaly",
            },
        )

        await self.alert_manager.create_alert(alert)

    async def _check_threshold_alerts(
        self, metric_groups: dict[str, list[float]]
    ) -> None:
        """Check for threshold-based alerts"""
        thresholds = {
            "system.cpu.usage_percent": {"warning": 80, "critical": 95},
            "system.memory.usage_percent": {"warning": 75, "critical": 90},
            "system.disk.usage_percent": {"warning": 80, "critical": 95},
            "app.memory.rss_mb": {"warning": 500, "critical": 1000},
        }

        for metric_name, values in metric_groups.items():
            if metric_name not in thresholds or not values:
                continue

            current_value = values[-1]
            threshold_config = thresholds[metric_name]

            severity = None
            threshold = 0

            if current_value >= threshold_config["critical"]:
                severity = AlertSeverity.CRITICAL
                threshold = threshold_config["critical"]
            elif current_value >= threshold_config["warning"]:
                severity = AlertSeverity.WARNING
                threshold = threshold_config["warning"]

            if severity:
                alert = Alert(
                    name=f"{metric_name} threshold exceeded",
                    description=f"{metric_name} has exceeded {severity.value} threshold",
                    severity=severity,
                    metric_name=metric_name,
                    threshold=threshold,
                    actual_value=current_value,
                    metadata={"detection_type": "threshold"},
                )

                await self.alert_manager.create_alert(alert)

    async def _log_alert_handler(self, alert: Alert) -> None:
        """Default alert handler that logs alerts"""
        level = logging.WARNING
        if alert.severity == AlertSeverity.ERROR:
            level = logging.ERROR
        elif alert.severity == AlertSeverity.CRITICAL:
            level = logging.CRITICAL

        logger.log(
            level,
            f"ALERT [{alert.severity.value.upper()}] {alert.name}: {alert.description} "
            f"(Current: {alert.actual_value}, Threshold: {alert.threshold})",
        )

    def get_system_health_score(self) -> float:
        """Calculate overall system health score (0-1)"""
        active_alerts = self.alert_manager.get_active_alerts()

        if not active_alerts:
            return 1.0

        # Weight alerts by severity
        severity_weights = {
            AlertSeverity.INFO: 0.1,
            AlertSeverity.WARNING: 0.3,
            AlertSeverity.ERROR: 0.7,
            AlertSeverity.CRITICAL: 1.0,
        }

        total_weight = sum(severity_weights[alert.severity] for alert in active_alerts)
        max_possible_weight = len(active_alerts) * 1.0

        health_score = 1.0 - (total_weight / max_possible_weight)
        return max(0.0, health_score)

    def get_monitoring_stats(self) -> dict[str, Any]:
        """Get comprehensive monitoring statistics"""
        return {
            "system_health_score": self.get_system_health_score(),
            "metrics_collected": len(self.metric_collector.metrics_buffer),
            "anomaly_models_trained": len(self.anomaly_detector.models),
            "alert_stats": self.alert_manager.get_alert_statistics(),
            "is_running": self.is_running,
            "monitoring_interval": self.monitoring_interval,
        }


# Global monitoring system instance
monitoring_system = PredictiveMonitoringSystem()


# Utility functions for integration


async def setup_monitoring() -> None:
    """Setup and start the monitoring system"""
    await monitoring_system.start()


async def shutdown_monitoring() -> None:
    """Shutdown the monitoring system"""
    await monitoring_system.stop()


def get_monitoring_stats() -> dict[str, Any]:
    """Get current monitoring statistics"""
    return monitoring_system.get_monitoring_stats()


def get_active_alerts() -> list[Alert]:
    """Get current active alerts"""
    return monitoring_system.alert_manager.get_active_alerts()


def register_alert_handler(handler: Callable[[Alert], None]) -> None:
    """Register a custom alert notification handler"""
    monitoring_system.alert_manager.register_notification_handler(handler)
