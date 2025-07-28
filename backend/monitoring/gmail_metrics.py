"""
Gmail Inbox Zero Monitoring and Metrics

Provides comprehensive monitoring and metrics collection for the Gmail Inbox Zero system
including performance metrics, user behavior analytics, and system health monitoring.
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class OperationMetric:
    """Represents a single operation metric"""
    operation_type: str
    user_id: str
    message_id: str
    timestamp: datetime
    duration_ms: int
    success: bool
    error_code: Optional[str] = None
    model_used: Optional[str] = None
    prefiltered: bool = False
    confidence_score: Optional[float] = None
    cost_saved: Optional[float] = None

@dataclass
class SystemMetrics:
    """System-wide metrics"""
    timestamp: datetime
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_response_time_ms: float
    cache_hit_rate: float
    prefilter_rate: float
    cost_optimization_savings: float
    active_users: int
    queue_size: int
    memory_usage_mb: float
    cpu_usage_percent: float

@dataclass
class UserBehaviorMetrics:
    """User behavior and satisfaction metrics"""
    user_id: str
    total_emails_processed: int
    emails_accepted_suggestions: int
    emails_rejected_suggestions: int
    average_time_to_action_seconds: float
    feedback_rating_average: float
    feedback_count: int
    inbox_zero_percentage: float
    learning_accuracy: float
    preferred_actions: Dict[str, int]

class GmailMetricsCollector:
    """Collects and manages Gmail Inbox Zero metrics"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metrics_storage_path = self.config.get("metrics_path", "./logs/gmail_metrics")
        
        # In-memory storage for real-time metrics
        self.operation_metrics = deque(maxlen=10000)  # Last 10k operations
        self.system_metrics_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        self.user_behavior_cache = {}
        
        # Performance tracking
        self.performance_tracker = PerformanceTracker()
        
        # Ensure metrics directory exists
        Path(self.metrics_storage_path).mkdir(parents=True, exist_ok=True)
        
    def record_operation(self, 
                        operation_type: str,
                        user_id: str,
                        message_id: str,
                        duration_ms: int,
                        success: bool,
                        **kwargs) -> None:
        """Record a single operation metric"""
        try:
            metric = OperationMetric(
                operation_type=operation_type,
                user_id=user_id,
                message_id=message_id,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                success=success,
                **kwargs
            )
            
            self.operation_metrics.append(metric)
            
            # Update user behavior metrics
            self._update_user_behavior_metrics(user_id, metric)
            
            # Log to file for persistence
            self._log_metric_to_file(metric)
            
        except Exception as e:
            logger.error(f"Error recording operation metric: {e}")
            
    def record_system_snapshot(self) -> SystemMetrics:
        """Record current system state snapshot"""
        try:
            # Calculate metrics from recent operations
            recent_ops = list(self.operation_metrics)
            if not recent_ops:
                return self._create_empty_system_metrics()
                
            total_ops = len(recent_ops)
            successful_ops = sum(1 for op in recent_ops if op.success)
            failed_ops = total_ops - successful_ops
            
            # Calculate average response time
            avg_response_time = sum(op.duration_ms for op in recent_ops) / total_ops if total_ops > 0 else 0
            
            # Calculate cache hit rate (from prefiltered operations)
            prefiltered_ops = sum(1 for op in recent_ops if op.prefiltered)
            prefilter_rate = prefiltered_ops / total_ops if total_ops > 0 else 0
            
            # Calculate cost savings
            cost_savings = sum(op.cost_saved or 0 for op in recent_ops)
            
            # Count active users (unique users in last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            active_users = len(set(
                op.user_id for op in recent_ops 
                if op.timestamp > one_hour_ago
            ))
            
            # System resource metrics (simplified - in production, use actual system monitoring)
            system_metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                total_operations=total_ops,
                successful_operations=successful_ops,
                failed_operations=failed_ops,
                average_response_time_ms=avg_response_time,
                cache_hit_rate=0.85,  # Placeholder - implement actual cache monitoring
                prefilter_rate=prefilter_rate,
                cost_optimization_savings=cost_savings,
                active_users=active_users,
                queue_size=0,  # Placeholder - implement actual queue monitoring
                memory_usage_mb=128.5,  # Placeholder
                cpu_usage_percent=25.3  # Placeholder
            )
            
            self.system_metrics_history.append(system_metrics)
            self._log_system_metrics_to_file(system_metrics)
            
            return system_metrics
            
        except Exception as e:
            logger.error(f"Error recording system snapshot: {e}")
            return self._create_empty_system_metrics()
            
    def get_user_behavior_metrics(self, user_id: str) -> UserBehaviorMetrics:
        """Get behavior metrics for a specific user"""
        if user_id not in self.user_behavior_cache:
            self.user_behavior_cache[user_id] = self._calculate_user_behavior_metrics(user_id)
        return self.user_behavior_cache[user_id]
        
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        recent_ops = list(self.operation_metrics)
        if not recent_ops:
            return {"message": "No operation data available"}
            
        insights = {
            "total_operations": len(recent_ops),
            "success_rate": sum(1 for op in recent_ops if op.success) / len(recent_ops),
            "average_response_time": sum(op.duration_ms for op in recent_ops) / len(recent_ops),
            "prefilter_efficiency": sum(1 for op in recent_ops if op.prefiltered) / len(recent_ops),
            "model_usage": self._analyze_model_usage(recent_ops),
            "error_analysis": self._analyze_errors(recent_ops),
            "cost_optimization": self._analyze_cost_optimization(recent_ops),
            "recommendations": self._generate_recommendations(recent_ops)
        }
        
        return insights
        
    def export_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Export metrics for a date range"""
        filtered_ops = [
            op for op in self.operation_metrics
            if start_date <= op.timestamp <= end_date
        ]
        
        filtered_system_metrics = [
            m for m in self.system_metrics_history
            if start_date <= m.timestamp <= end_date
        ]
        
        return {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "operation_metrics": [asdict(op) for op in filtered_ops],
            "system_metrics": [asdict(m) for m in filtered_system_metrics],
            "summary": self._generate_metrics_summary(filtered_ops, filtered_system_metrics)
        }
        
    def _update_user_behavior_metrics(self, user_id: str, metric: OperationMetric) -> None:
        """Update user behavior metrics based on operation"""
        # This would typically involve more complex tracking
        # For now, we'll update the cache invalidation
        if user_id in self.user_behavior_cache:
            del self.user_behavior_cache[user_id]
            
    def _calculate_user_behavior_metrics(self, user_id: str) -> UserBehaviorMetrics:
        """Calculate behavior metrics for a user"""
        user_ops = [op for op in self.operation_metrics if op.user_id == user_id]
        
        if not user_ops:
            return UserBehaviorMetrics(
                user_id=user_id,
                total_emails_processed=0,
                emails_accepted_suggestions=0,
                emails_rejected_suggestions=0,
                average_time_to_action_seconds=0,
                feedback_rating_average=0,
                feedback_count=0,
                inbox_zero_percentage=0,
                learning_accuracy=0,
                preferred_actions={}
            )
            
        # Calculate metrics from operations
        total_processed = len([op for op in user_ops if op.operation_type == 'analyze'])
        accepted_suggestions = len([op for op in user_ops if op.operation_type in ['label', 'archive', 'star']])
        
        # Calculate preferred actions
        action_counts = defaultdict(int)
        for op in user_ops:
            action_counts[op.operation_type] += 1
            
        return UserBehaviorMetrics(
            user_id=user_id,
            total_emails_processed=total_processed,
            emails_accepted_suggestions=accepted_suggestions,
            emails_rejected_suggestions=max(0, total_processed - accepted_suggestions),
            average_time_to_action_seconds=30.5,  # Placeholder
            feedback_rating_average=4.2,  # Placeholder
            feedback_count=5,  # Placeholder
            inbox_zero_percentage=75.3,  # Placeholder
            learning_accuracy=0.85,  # Placeholder
            preferred_actions=dict(action_counts)
        )
        
    def _analyze_model_usage(self, operations: List[OperationMetric]) -> Dict[str, Any]:
        """Analyze which models are being used and their performance"""
        model_stats = defaultdict(lambda: {"count": 0, "success_rate": 0, "avg_duration": 0})
        
        for op in operations:
            if op.model_used:
                stats = model_stats[op.model_used]
                stats["count"] += 1
                stats["success_rate"] += 1 if op.success else 0
                stats["avg_duration"] += op.duration_ms
                
        # Calculate averages
        for model, stats in model_stats.items():
            if stats["count"] > 0:
                stats["success_rate"] = stats["success_rate"] / stats["count"]
                stats["avg_duration"] = stats["avg_duration"] / stats["count"]
                
        return dict(model_stats)
        
    def _analyze_errors(self, operations: List[OperationMetric]) -> Dict[str, Any]:
        """Analyze error patterns"""
        error_counts = defaultdict(int)
        error_by_operation = defaultdict(int)
        
        for op in operations:
            if not op.success and op.error_code:
                error_counts[op.error_code] += 1
                error_by_operation[op.operation_type] += 1
                
        return {
            "error_codes": dict(error_counts),
            "errors_by_operation": dict(error_by_operation),
            "total_errors": sum(error_counts.values())
        }
        
    def _analyze_cost_optimization(self, operations: List[OperationMetric]) -> Dict[str, Any]:
        """Analyze cost optimization effectiveness"""
        total_cost_saved = sum(op.cost_saved or 0 for op in operations)
        prefiltered_count = sum(1 for op in operations if op.prefiltered)
        total_operations = len(operations)
        
        return {
            "total_cost_saved": total_cost_saved,
            "prefilter_rate": prefiltered_count / total_operations if total_operations > 0 else 0,
            "estimated_monthly_savings": total_cost_saved * 30,  # Simple extrapolation
            "optimization_effectiveness": "high" if prefiltered_count / total_operations > 0.3 else "medium"
        }
        
    def _generate_recommendations(self, operations: List[OperationMetric]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        if not operations:
            return ["No data available for recommendations"]
            
        # Analyze response times
        avg_duration = sum(op.duration_ms for op in operations) / len(operations)
        if avg_duration > 2000:  # 2 seconds
            recommendations.append("Consider optimizing response times - average duration is high")
            
        # Analyze error rates
        error_rate = sum(1 for op in operations if not op.success) / len(operations)
        if error_rate > 0.05:  # 5% error rate
            recommendations.append("Error rate is elevated - review error handling and API reliability")
            
        # Analyze prefilter effectiveness
        prefilter_rate = sum(1 for op in operations if op.prefiltered) / len(operations)
        if prefilter_rate < 0.2:  # Less than 20% prefiltered
            recommendations.append("Prefilter rules could be expanded to reduce AI processing costs")
            
        return recommendations
        
    def _create_empty_system_metrics(self) -> SystemMetrics:
        """Create empty system metrics for error cases"""
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            total_operations=0,
            successful_operations=0,
            failed_operations=0,
            average_response_time_ms=0,
            cache_hit_rate=0,
            prefilter_rate=0,
            cost_optimization_savings=0,
            active_users=0,
            queue_size=0,
            memory_usage_mb=0,
            cpu_usage_percent=0
        )
        
    def _log_metric_to_file(self, metric: OperationMetric) -> None:
        """Log metric to file for persistence"""
        try:
            log_file = Path(self.metrics_storage_path) / f"operations_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps(asdict(metric), default=str) + "\n")
        except Exception as e:
            logger.error(f"Error logging metric to file: {e}")
            
    def _log_system_metrics_to_file(self, metrics: SystemMetrics) -> None:
        """Log system metrics to file"""
        try:
            log_file = Path(self.metrics_storage_path) / f"system_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps(asdict(metrics), default=str) + "\n")
        except Exception as e:
            logger.error(f"Error logging system metrics to file: {e}")
            
    def _generate_metrics_summary(self, operations: List[OperationMetric], system_metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Generate summary of metrics for export"""
        if not operations:
            return {"message": "No data available"}
            
        return {
            "total_operations": len(operations),
            "success_rate": sum(1 for op in operations if op.success) / len(operations),
            "average_response_time": sum(op.duration_ms for op in operations) / len(operations),
            "unique_users": len(set(op.user_id for op in operations)),
            "operation_breakdown": {
                op_type: len([op for op in operations if op.operation_type == op_type])
                for op_type in set(op.operation_type for op in operations)
            },
            "cost_savings": sum(op.cost_saved or 0 for op in operations)
        }

class PerformanceTracker:
    """Tracks performance of individual operations"""
    
    def __init__(self):
        self.active_operations = {}
        
    def start_operation(self, operation_id: str, operation_type: str, user_id: str) -> None:
        """Start tracking an operation"""
        self.active_operations[operation_id] = {
            "start_time": time.time(),
            "operation_type": operation_type,
            "user_id": user_id
        }
        
    def end_operation(self, operation_id: str, success: bool = True, **kwargs) -> Dict[str, Any]:
        """End tracking an operation and return metrics"""
        if operation_id not in self.active_operations:
            return {"error": "Operation not found"}
            
        operation = self.active_operations.pop(operation_id)
        duration_ms = int((time.time() - operation["start_time"]) * 1000)
        
        return {
            "duration_ms": duration_ms,
            "operation_type": operation["operation_type"],
            "user_id": operation["user_id"],
            "success": success,
            **kwargs
        }

# Global metrics collector instance
metrics_collector = GmailMetricsCollector()