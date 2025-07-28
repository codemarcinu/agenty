"""
Hallucination monitor for real-time detection and tracking.

Implements monitoring and alerting for potential hallucinations
with metrics collection and trend analysis.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import statistics
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HallucinationEvent:
    """Represents a hallucination detection event"""

    timestamp: datetime
    agent_name: str
    confidence_score: float
    validation_failed: bool
    error_type: str
    details: dict[str, Any]
    severity: str = "medium"


@dataclass
class HallucinationMetrics:
    """Metrics for hallucination monitoring"""

    total_events: int = 0
    high_severity_events: int = 0
    average_confidence: float = 0.0
    validation_failure_rate: float = 0.0
    agent_failure_rates: dict[str, float] = field(default_factory=dict)
    recent_events: deque = field(default_factory=lambda: deque(maxlen=100))
    hourly_trends: dict[str, int] = field(default_factory=dict)


class HallucinationMonitor:
    """
    Real-time hallucination detection and monitoring system.

    Tracks potential hallucinations across all agents and provides
    metrics, alerts, and trend analysis.
    """

    def __init__(self, **kwargs):
        self.alert_threshold = kwargs.get("alert_threshold", 0.3)  # 30% failure rate
        self.confidence_threshold = kwargs.get("confidence_threshold", 0.7)
        self.monitoring_window = kwargs.get("monitoring_window", 3600)  # 1 hour
        self.max_events = kwargs.get("max_events", 1000)

        # Metrics storage
        self.metrics = HallucinationMetrics()
        self.events: list[HallucinationEvent] = []
        self.agent_stats = defaultdict(
            lambda: {"events": 0, "failures": 0, "total_confidence": 0.0}
        )

        # Alert handlers
        self.alert_handlers: list[callable] = []

        # Performance tracking
        self.performance_metrics = {
            "processing_times": deque(maxlen=100),
            "memory_usage": deque(maxlen=100),
            "error_counts": defaultdict(int),
        }

    def log_agent_response(
        self,
        agent_name: str,
        confidence: float,
        validated: bool,
        error_type: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an agent response for hallucination monitoring.

        Args:
            agent_name: Name of the agent
            confidence: Confidence score
            validated: Whether validation passed
            error_type: Type of error if any
            details: Additional details
        """
        timestamp = datetime.now()

        # Determine if this is a potential hallucination
        validation_failed = not validated or confidence < self.confidence_threshold
        severity = self._determine_severity(confidence, validation_failed, error_type)

        # Create event
        event = HallucinationEvent(
            timestamp=timestamp,
            agent_name=agent_name,
            confidence_score=confidence,
            validation_failed=validation_failed,
            error_type=error_type,
            details=details or {},
            severity=severity,
        )

        # Store event
        self._store_event(event)

        # Update metrics
        self._update_metrics(event)

        # Check for alerts
        self._check_alerts()

        logger.debug(
            f"Logged agent response: {agent_name} - confidence: {confidence}, validated: {validated}"
        )

    def _determine_severity(
        self, confidence: float, validation_failed: bool, error_type: str
    ) -> str:
        """Determine severity of the event."""
        if validation_failed and confidence < 0.5:
            return "high"
        if validation_failed or confidence < self.confidence_threshold:
            return "medium"
        return "low"

    def _store_event(self, event: HallucinationEvent) -> None:
        """Store event in memory."""
        self.events.append(event)
        self.metrics.recent_events.append(event)

        # Maintain event list size
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

    def _update_metrics(self, event: HallucinationEvent) -> None:
        """Update monitoring metrics."""
        # Update agent statistics
        agent_stats = self.agent_stats[event.agent_name]
        agent_stats["events"] += 1
        agent_stats["total_confidence"] += event.confidence_score

        if event.validation_failed:
            agent_stats["failures"] += 1

        # Update overall metrics
        self.metrics.total_events += 1

        if event.severity == "high":
            self.metrics.high_severity_events += 1

        # Update hourly trends
        hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
        self.metrics.hourly_trends[hour_key] = (
            self.metrics.hourly_trends.get(hour_key, 0) + 1
        )

        # Clean old hourly data
        cutoff_time = datetime.now() - timedelta(hours=24)
        cutoff_key = cutoff_time.strftime("%Y-%m-%d %H:00")
        self.metrics.hourly_trends = {
            k: v for k, v in self.metrics.hourly_trends.items() if k > cutoff_key
        }

    def _check_alerts(self) -> None:
        """Check for conditions that require alerts."""
        # Calculate current failure rate
        recent_window = datetime.now() - timedelta(seconds=self.monitoring_window)
        recent_events = [e for e in self.events if e.timestamp >= recent_window]

        if not recent_events:
            return

        failure_rate = sum(1 for e in recent_events if e.validation_failed) / len(
            recent_events
        )

        if failure_rate > self.alert_threshold:
            self._trigger_alert(
                "high_failure_rate",
                {
                    "failure_rate": failure_rate,
                    "threshold": self.alert_threshold,
                    "recent_events": len(recent_events),
                },
            )

        # Check for high severity events
        high_severity_count = sum(1 for e in recent_events if e.severity == "high")
        if high_severity_count > 5:
            self._trigger_alert(
                "high_severity_events",
                {"count": high_severity_count, "time_window": self.monitoring_window},
            )

    def _trigger_alert(self, alert_type: str, details: dict[str, Any]) -> None:
        """Trigger an alert."""
        alert_data = {
            "type": alert_type,
            "timestamp": datetime.now(),
            "details": details,
            "metrics": self.get_current_metrics(),
        }

        # Log alert
        logger.warning(f"Hallucination alert triggered: {alert_type} - {details}")

        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Error in alert handler: {e!s}")

    def add_alert_handler(self, handler: callable) -> None:
        """Add an alert handler function."""
        self.alert_handlers.append(handler)

    def get_hallucination_rate(self, time_window: int | None = None) -> float:
        """
        Get hallucination rate for the specified time window.

        Args:
            time_window: Time window in seconds (default: monitoring_window)

        Returns:
            Hallucination rate as a percentage
        """
        if time_window is None:
            time_window = self.monitoring_window

        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_time]

        if not recent_events:
            return 0.0

        failed_events = sum(1 for e in recent_events if e.validation_failed)
        return failed_events / len(recent_events)

    def get_agent_performance(self, agent_name: str) -> dict[str, Any]:
        """
        Get performance metrics for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Performance metrics dictionary
        """
        agent_stats = self.agent_stats[agent_name]

        if agent_stats["events"] == 0:
            return {
                "agent_name": agent_name,
                "total_events": 0,
                "failure_rate": 0.0,
                "average_confidence": 0.0,
                "recent_performance": [],
            }

        failure_rate = agent_stats["failures"] / agent_stats["events"]
        average_confidence = agent_stats["total_confidence"] / agent_stats["events"]

        # Get recent performance (last 10 events)
        recent_events = [e for e in self.events if e.agent_name == agent_name][-10:]

        recent_performance = [
            {
                "timestamp": e.timestamp.isoformat(),
                "confidence": e.confidence_score,
                "validation_failed": e.validation_failed,
                "severity": e.severity,
            }
            for e in recent_events
        ]

        return {
            "agent_name": agent_name,
            "total_events": agent_stats["events"],
            "failure_rate": failure_rate,
            "average_confidence": average_confidence,
            "recent_performance": recent_performance,
        }

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current monitoring metrics."""
        # Calculate average confidence
        if self.events:
            recent_events = self.events[-100:]  # Last 100 events
            average_confidence = statistics.mean(
                e.confidence_score for e in recent_events
            )
        else:
            average_confidence = 0.0

        # Calculate validation failure rate
        validation_failure_rate = self.get_hallucination_rate()

        # Calculate agent failure rates
        agent_failure_rates = {}
        for agent_name, stats in self.agent_stats.items():
            if stats["events"] > 0:
                agent_failure_rates[agent_name] = stats["failures"] / stats["events"]

        return {
            "total_events": self.metrics.total_events,
            "high_severity_events": self.metrics.high_severity_events,
            "average_confidence": average_confidence,
            "validation_failure_rate": validation_failure_rate,
            "agent_failure_rates": agent_failure_rates,
            "recent_events_count": len(self.metrics.recent_events),
            "hourly_trends": dict(self.metrics.hourly_trends),
        }

    def get_trend_analysis(self, hours: int = 24) -> dict[str, Any]:
        """
        Get trend analysis for the specified time period.

        Args:
            hours: Number of hours to analyze

        Returns:
            Trend analysis dictionary
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_time]

        if not recent_events:
            return {
                "period_hours": hours,
                "total_events": 0,
                "failure_rate": 0.0,
                "confidence_trend": [],
                "severity_distribution": {},
                "agent_performance": {},
            }

        # Calculate failure rate trend
        hourly_failure_rates = defaultdict(lambda: {"events": 0, "failures": 0})
        for event in recent_events:
            hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
            hourly_failure_rates[hour_key]["events"] += 1
            if event.validation_failed:
                hourly_failure_rates[hour_key]["failures"] += 1

        confidence_trend = [
            {
                "hour": hour,
                "failure_rate": (
                    data["failures"] / data["events"] if data["events"] > 0 else 0.0
                ),
                "event_count": data["events"],
            }
            for hour, data in sorted(hourly_failure_rates.items())
        ]

        # Calculate severity distribution
        severity_distribution = defaultdict(int)
        for event in recent_events:
            severity_distribution[event.severity] += 1

        # Calculate agent performance
        agent_performance = {}
        for agent_name in {e.agent_name for e in recent_events}:
            agent_performance[agent_name] = self.get_agent_performance(agent_name)

        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "failure_rate": self.get_hallucination_rate(hours * 3600),
            "confidence_trend": confidence_trend,
            "severity_distribution": dict(severity_distribution),
            "agent_performance": agent_performance,
        }

    def get_recommendations(self) -> list[str]:
        """Get recommendations based on current metrics."""
        recommendations = []
        metrics = self.get_current_metrics()

        # High failure rate recommendation
        if metrics["validation_failure_rate"] > 0.5:
            recommendations.append(
                "High validation failure rate detected. Consider reviewing agent configurations and validation thresholds."
            )

        # Low confidence recommendation
        if metrics["average_confidence"] < 0.6:
            recommendations.append(
                "Low average confidence detected. Consider improving input quality or adjusting confidence thresholds."
            )

        # Agent-specific recommendations
        for agent_name, failure_rate in metrics["agent_failure_rates"].items():
            if failure_rate > 0.3:
                recommendations.append(
                    f"Agent {agent_name} has high failure rate ({failure_rate:.1%}). Consider investigation."
                )

        # High severity events recommendation
        if metrics["high_severity_events"] > 10:
            recommendations.append(
                "Multiple high severity events detected. Consider immediate system review."
            )

        return recommendations

    def reset_metrics(self) -> None:
        """Reset all monitoring metrics."""
        self.events.clear()
        self.metrics = HallucinationMetrics()
        self.agent_stats.clear()
        self.performance_metrics = {
            "processing_times": deque(maxlen=100),
            "memory_usage": deque(maxlen=100),
            "error_counts": defaultdict(int),
        }
        logger.info("Hallucination monitoring metrics reset")

    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in the specified format.

        Args:
            format: Export format ("json" or "csv")

        Returns:
            Exported metrics string
        """
        metrics = self.get_current_metrics()

        if format.lower() == "json":
            import json

            return json.dumps(metrics, indent=2, default=str)
        if format.lower() == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(["Metric", "Value"])

            # Write metrics
            for key, value in metrics.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"{key}.{sub_key}", sub_value])
                else:
                    writer.writerow([key, value])

            return output.getvalue()
        raise ValueError(f"Unsupported format: {format}")
