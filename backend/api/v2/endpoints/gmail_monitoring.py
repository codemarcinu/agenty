"""
Gmail Inbox Zero Monitoring API Endpoints

Provides API endpoints for monitoring Gmail Inbox Zero system performance,
user behavior analytics, and real-time metrics.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json
import asyncio
from monitoring.gmail_metrics import metrics_collector
from security.gmail_security import GmailSecurityManager
from pydantic import BaseModel

router = APIRouter()

class MetricsQuery(BaseModel):
    """Request model for metrics queries"""
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    operation_type: Optional[str] = None

class FeedbackSubmission(BaseModel):
    """Request model for user feedback"""
    user_id: str
    message_id: str
    analysis_id: str
    rating: str  # 'positive' or 'negative'
    comment: Optional[str] = None
    suggestions_followed: Optional[list] = []

# Initialize security manager
security_manager = GmailSecurityManager()

@router.get("/metrics/system")
async def get_system_metrics():
    """Get current system-wide metrics"""
    try:
        current_metrics = metrics_collector.record_system_snapshot()
        
        return {
            "success": True,
            "data": {
                "timestamp": current_metrics.timestamp,
                "performance": {
                    "total_operations": current_metrics.total_operations,
                    "success_rate": current_metrics.successful_operations / max(current_metrics.total_operations, 1),
                    "average_response_time_ms": current_metrics.average_response_time_ms,
                    "error_rate": current_metrics.failed_operations / max(current_metrics.total_operations, 1)
                },
                "optimization": {
                    "cache_hit_rate": current_metrics.cache_hit_rate,
                    "prefilter_rate": current_metrics.prefilter_rate,
                    "cost_savings": current_metrics.cost_optimization_savings
                },
                "system": {
                    "active_users": current_metrics.active_users,
                    "queue_size": current_metrics.queue_size,
                    "memory_usage_mb": current_metrics.memory_usage_mb,
                    "cpu_usage_percent": current_metrics.cpu_usage_percent
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system metrics: {str(e)}")

@router.get("/metrics/user/{user_id}")
async def get_user_metrics(user_id: str):
    """Get metrics for a specific user"""
    try:
        user_metrics = metrics_collector.get_user_behavior_metrics(user_id)
        
        return {
            "success": True,
            "data": {
                "user_id": user_metrics.user_id,
                "email_processing": {
                    "total_processed": user_metrics.total_emails_processed,
                    "suggestions_accepted": user_metrics.emails_accepted_suggestions,
                    "suggestions_rejected": user_metrics.emails_rejected_suggestions,
                    "acceptance_rate": user_metrics.emails_accepted_suggestions / max(user_metrics.total_emails_processed, 1)
                },
                "behavior": {
                    "average_time_to_action": user_metrics.average_time_to_action_seconds,
                    "preferred_actions": user_metrics.preferred_actions
                },
                "feedback": {
                    "average_rating": user_metrics.feedback_rating_average,
                    "feedback_count": user_metrics.feedback_count
                },
                "inbox_zero": {
                    "percentage": user_metrics.inbox_zero_percentage,
                    "learning_accuracy": user_metrics.learning_accuracy
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user metrics: {str(e)}")

@router.get("/metrics/performance")
async def get_performance_insights():
    """Get performance insights and recommendations"""
    try:
        insights = metrics_collector.get_performance_insights()
        
        return {
            "success": True,
            "data": insights,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance insights: {str(e)}")

@router.post("/metrics/export")
async def export_metrics(query: MetricsQuery):
    """Export metrics for a date range"""
    try:
        # Default to last 7 days if no dates provided
        end_date = query.end_date or datetime.utcnow()
        start_date = query.start_date or (end_date - timedelta(days=7))
        
        exported_data = metrics_collector.export_metrics(start_date, end_date)
        
        # Log the export for audit purposes
        security_manager.audit_log("METRICS_EXPORTED", {
            "user_id": query.user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "operation_count": len(exported_data.get("operation_metrics", []))
        })
        
        return {
            "success": True,
            "data": exported_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting metrics: {str(e)}")

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackSubmission):
    """Submit user feedback for analysis quality"""
    try:
        # Validate feedback rating
        if feedback.rating not in ['positive', 'negative']:
            raise HTTPException(status_code=400, detail="Rating must be 'positive' or 'negative'")
        
        # Record feedback metric
        metrics_collector.record_operation(
            operation_type="feedback",
            user_id=feedback.user_id,
            message_id=feedback.message_id,
            duration_ms=0,  # Feedback doesn't have duration
            success=True,
            feedback_rating=feedback.rating,
            feedback_comment=feedback.comment,
            suggestions_followed=feedback.suggestions_followed
        )
        
        # Log feedback for audit
        security_manager.audit_log("FEEDBACK_SUBMITTED", {
            "user_id": feedback.user_id,
            "message_id": feedback.message_id,
            "rating": feedback.rating,
            "has_comment": bool(feedback.comment)
        })
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "data": {
                "feedback_id": f"{feedback.user_id}_{feedback.message_id}_{datetime.utcnow().timestamp()}",
                "timestamp": datetime.utcnow()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@router.get("/health")
async def get_system_health():
    """Get system health status"""
    try:
        # Get security metrics
        security_metrics = security_manager.get_security_metrics()
        
        # Get basic system metrics
        current_metrics = metrics_collector.record_system_snapshot()
        
        # Calculate health scores
        performance_health = min(100, max(0, 100 - (current_metrics.average_response_time_ms / 50)))  # Good if < 5s
        error_health = min(100, max(0, 100 - (current_metrics.failed_operations * 10)))  # Good if < 10% errors
        security_health = 100 - (security_metrics["active_lockouts"] * 20)  # Decrease for each lockout
        
        overall_health = (performance_health + error_health + security_health) / 3
        
        # Determine status
        if overall_health >= 80:
            status = "healthy"
        elif overall_health >= 60:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "success": True,
            "data": {
                "status": status,
                "overall_health_score": round(overall_health, 1),
                "components": {
                    "performance": {
                        "score": round(performance_health, 1),
                        "response_time_ms": current_metrics.average_response_time_ms,
                        "status": "healthy" if performance_health >= 80 else "warning" if performance_health >= 60 else "critical"
                    },
                    "reliability": {
                        "score": round(error_health, 1),
                        "error_count": current_metrics.failed_operations,
                        "success_rate": current_metrics.successful_operations / max(current_metrics.total_operations, 1),
                        "status": "healthy" if error_health >= 80 else "warning" if error_health >= 60 else "critical"
                    },
                    "security": {
                        "score": round(security_health, 1),
                        "active_lockouts": security_metrics["active_lockouts"],
                        "failed_attempts": security_metrics["recent_failed_attempts"],
                        "status": "healthy" if security_health >= 80 else "warning" if security_health >= 60 else "critical"
                    }
                },
                "last_updated": datetime.utcnow()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system health: {str(e)}")

@router.get("/stream")
async def stream_metrics():
    """Stream real-time metrics via Server-Sent Events"""
    async def generate_metrics_stream():
        """Generate real-time metrics stream"""
        try:
            while True:
                # Get current metrics
                current_metrics = metrics_collector.record_system_snapshot()
                
                # Create SSE event
                event_data = {
                    "type": "metrics_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "total_operations": current_metrics.total_operations,
                        "success_rate": current_metrics.successful_operations / max(current_metrics.total_operations, 1),
                        "response_time": current_metrics.average_response_time_ms,
                        "active_users": current_metrics.active_users,
                        "cost_savings": current_metrics.cost_optimization_savings
                    }
                }
                
                yield f"data: {json.dumps(event_data)}\n\n"
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            pass  # Client disconnected
        except Exception as e:
            error_event = {
                "type": "error",
                "message": f"Stream error: {str(e)}"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_metrics_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@router.get("/alerts")
async def get_active_alerts():
    """Get active system alerts"""
    try:
        current_metrics = metrics_collector.record_system_snapshot()
        security_metrics = security_manager.get_security_metrics()
        
        alerts = []
        
        # Performance alerts
        if current_metrics.average_response_time_ms > 5000:
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": f"High response time: {current_metrics.average_response_time_ms}ms",
                "timestamp": datetime.utcnow()
            })
        
        # Error rate alerts
        error_rate = current_metrics.failed_operations / max(current_metrics.total_operations, 1)
        if error_rate > 0.1:  # 10% error rate
            alerts.append({
                "type": "reliability",
                "severity": "critical" if error_rate > 0.2 else "warning",
                "message": f"High error rate: {error_rate*100:.1f}%",
                "timestamp": datetime.utcnow()
            })
        
        # Security alerts
        if security_metrics["active_lockouts"] > 0:
            alerts.append({
                "type": "security",
                "severity": "warning",
                "message": f"Active user lockouts: {security_metrics['active_lockouts']}",
                "timestamp": datetime.utcnow()
            })
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "last_checked": datetime.utcnow()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")

@router.post("/metrics/record")
async def record_custom_metric(
    operation_type: str = Query(..., description="Type of operation"),
    user_id: str = Query(..., description="User ID"),
    message_id: str = Query(..., description="Message ID"),
    duration_ms: int = Query(..., description="Operation duration in milliseconds"),
    success: bool = Query(True, description="Whether operation was successful"),
    model_used: Optional[str] = Query(None, description="AI model used"),
    prefiltered: bool = Query(False, description="Whether operation was prefiltered"),
    confidence_score: Optional[float] = Query(None, description="AI confidence score"),
    cost_saved: Optional[float] = Query(None, description="Cost saved by optimization")
):
    """Record a custom metric (for internal use)"""
    try:
        metrics_collector.record_operation(
            operation_type=operation_type,
            user_id=user_id,
            message_id=message_id,
            duration_ms=duration_ms,
            success=success,
            model_used=model_used,
            prefiltered=prefiltered,
            confidence_score=confidence_score,
            cost_saved=cost_saved
        )
        
        return {
            "success": True,
            "message": "Metric recorded successfully",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording metric: {str(e)}")