"""
Metrics & Monitoring API Endpoints - Phase 6 Enhanced Testing Strategy
Expose application metrics, health checks, and monitoring data
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.monitoring import metrics_collector, health_checker
from app.core.deps import get_current_user
from app.models.database_models import User
from app.schemas.schemas import APIResponse

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Comprehensive health check endpoint
    Public endpoint - no authentication required
    """
    try:
        health_results = await health_checker.run_health_checks()
        
        # Return appropriate HTTP status based on health
        if health_results["status"] == "healthy":
            status_code = 200
        elif health_results["status"] == "warning":
            status_code = 200  # Still OK, but with warnings
        else:
            status_code = 503  # Service unavailable
        
        # Add basic service info
        health_results["service"] = {
            "name": "eBay Listing Optimizer",
            "version": "2.0.0",
            "environment": "production",
            "api_version": "/api/v1"
        }
        
        return health_results
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/metrics", response_model=APIResponse)
async def get_metrics(
    detailed: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Get application metrics
    
    **Required Authentication:** Yes
    
    **Parameters:**
    - detailed: Include detailed metrics breakdown
    """
    try:
        if detailed:
            # Return full metrics for admin users
            if hasattr(current_user, 'role') and current_user.role == 'admin':
                full_metrics = {
                    "summary": metrics_collector.get_metrics_summary(),
                    "raw_metrics": metrics_collector.metrics,
                    "collection_info": {
                        "startup_time": metrics_collector.metrics["system"]["startup_time"].isoformat(),
                        "data_points": {
                            "response_times": len(metrics_collector.metrics["requests"]["response_times"]),
                            "query_times": len(metrics_collector.metrics["database"]["query_times"]),
                            "score_improvements": len(metrics_collector.metrics["optimization"]["average_score_improvement"])
                        }
                    }
                }
            else:
                # Limited metrics for non-admin users
                summary = metrics_collector.get_metrics_summary()
                full_metrics = {
                    "summary": {
                        "requests": summary["requests"],
                        "uptime_seconds": summary["uptime_seconds"],
                        "optimization": summary["optimization"]
                    }
                }
        else:
            # Basic metrics summary
            full_metrics = metrics_collector.get_metrics_summary()
        
        return APIResponse(
            success=True,
            message="Metrics retrieved successfully",
            data=full_metrics
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving metrics: {str(e)}"
        )


@router.get("/metrics/performance", response_model=APIResponse)
async def get_performance_metrics(
    timeframe_hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """
    Get performance-specific metrics
    
    **Required Authentication:** Yes
    """
    try:
        metrics = metrics_collector.get_metrics_summary()
        
        # Calculate performance indicators
        performance_data = {
            "response_time": {
                "average_ms": metrics["requests"]["avg_response_time"],
                "p95_ms": metrics["requests"]["p95_response_time"],
                "target_threshold": 1000,
                "status": "good" if metrics["requests"]["avg_response_time"] < 1000 else "warning"
            },
            "throughput": {
                "requests_per_minute": metrics["requests"]["requests_per_minute"],
                "total_requests": metrics_collector.metrics["requests"]["total"],
                "success_rate_percent": metrics["requests"]["success_rate"]
            },
            "database": {
                "average_query_time_ms": metrics["database"]["avg_query_time"],
                "total_queries": metrics["database"]["total_queries"],
                "error_rate_percent": metrics["database"]["error_rate"]
            },
            "system": {
                "memory_usage_mb": metrics["system"]["memory_usage_mb"],
                "cpu_usage_percent": metrics["system"]["cpu_usage_percent"],
                "uptime_hours": metrics["uptime_seconds"] / 3600
            },
            "performance_grade": _calculate_performance_grade(metrics)
        }
        
        return APIResponse(
            success=True,
            message="Performance metrics retrieved successfully",
            data=performance_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving performance metrics: {str(e)}"
        )


@router.get("/metrics/business", response_model=APIResponse) 
async def get_business_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get business-relevant metrics
    
    **Required Authentication:** Yes
    """
    try:
        metrics = metrics_collector.get_metrics_summary()
        
        # Calculate business metrics
        business_data = {
            "optimization_activity": {
                "total_optimizations": metrics["optimization"]["total_optimizations"],
                "average_score_improvement": metrics["optimization"]["avg_score_improvement"],
                "optimization_rate_per_hour": (
                    metrics["optimization"]["total_optimizations"] / 
                    max(1, metrics["uptime_seconds"] / 3600)
                )
            },
            "user_engagement": {
                "api_requests": metrics_collector.metrics["requests"]["total"],
                "authentication_success_rate": metrics["authentication"]["success_rate"],
                "active_session_indicators": {
                    "recent_requests": len([
                        t for t in metrics_collector.metrics["requests"]["response_times"][-100:]
                        if t > 0  # Valid response times
                    ])
                }
            },
            "system_reliability": {
                "uptime_hours": metrics["uptime_seconds"] / 3600,
                "error_rate_percent": metrics["requests"]["error_rate"],
                "availability_percent": max(0, 100 - metrics["requests"]["error_rate"])
            },
            "efficiency_indicators": {
                "requests_per_optimization": (
                    metrics_collector.metrics["requests"]["total"] / 
                    max(1, metrics["optimization"]["total_optimizations"])
                ),
                "average_processing_time": metrics["requests"]["avg_response_time"],
                "resource_utilization": {
                    "memory_efficiency": "good" if metrics["system"]["memory_usage_mb"] < 500 else "moderate",
                    "response_efficiency": "excellent" if metrics["requests"]["avg_response_time"] < 500 else "good"
                }
            }
        }
        
        return APIResponse(
            success=True,
            message="Business metrics retrieved successfully",
            data=business_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving business metrics: {str(e)}"
        )


@router.get("/metrics/endpoints", response_model=APIResponse)
async def get_endpoint_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get per-endpoint performance metrics
    
    **Required Authentication:** Yes
    **Required Roles:** Admin users get detailed data
    """
    try:
        endpoint_metrics = metrics_collector.metrics["requests"]["by_endpoint"]
        status_code_metrics = metrics_collector.metrics["requests"]["by_status_code"]
        
        # Format endpoint data
        formatted_endpoints = []
        for endpoint, data in endpoint_metrics.items():
            formatted_endpoints.append({
                "endpoint": endpoint,
                "request_count": data["count"],
                "average_response_time_ms": round(data["avg_response_time"], 2),
                "total_response_time_ms": round(data["total_response_time"], 2),
                "performance_grade": _grade_endpoint_performance(data["avg_response_time"]),
                "requests_per_minute": data["count"] / max(1, metrics_collector.metrics["system"]["uptime_seconds"] / 60)
            })
        
        # Sort by request count
        formatted_endpoints.sort(key=lambda x: x["request_count"], reverse=True)
        
        # Limit data for non-admin users
        if not (hasattr(current_user, 'role') and current_user.role == 'admin'):
            formatted_endpoints = formatted_endpoints[:10]  # Top 10 endpoints only
        
        endpoint_data = {
            "endpoints": formatted_endpoints,
            "status_codes": status_code_metrics,
            "summary": {
                "total_endpoints": len(endpoint_metrics),
                "most_used_endpoint": max(endpoint_metrics.items(), key=lambda x: x[1]["count"])[0] if endpoint_metrics else None,
                "fastest_endpoint": min(endpoint_metrics.items(), key=lambda x: x[1]["avg_response_time"])[0] if endpoint_metrics else None,
                "slowest_endpoint": max(endpoint_metrics.items(), key=lambda x: x[1]["avg_response_time"])[0] if endpoint_metrics else None
            }
        }
        
        return APIResponse(
            success=True,
            message="Endpoint metrics retrieved successfully",
            data=endpoint_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving endpoint metrics: {str(e)}"
        )


@router.post("/metrics/reset", response_model=APIResponse)
async def reset_metrics(
    confirm: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Reset metrics counters (admin only)
    
    **Required Authentication:** Yes
    **Required Roles:** Admin only
    """
    try:
        # Check admin permission
        if not (hasattr(current_user, 'role') and current_user.role == 'admin'):
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required to reset metrics"
            )
        
        if not confirm:
            return APIResponse(
                success=False,
                message="Metrics reset requires confirmation. Use confirm=true parameter."
            )
        
        # Store current metrics for reference
        old_metrics_summary = metrics_collector.get_metrics_summary()
        
        # Reset metrics (keeping startup time)
        startup_time = metrics_collector.metrics["system"]["startup_time"]
        metrics_collector.metrics = {
            "requests": {
                "total": 0,
                "success": 0,
                "errors": 0,
                "by_endpoint": {},
                "by_status_code": {},
                "response_times": []
            },
            "authentication": {
                "login_attempts": 0,
                "login_success": 0,
                "login_failures": 0,
                "token_refreshes": 0
            },
            "database": {
                "queries": 0,
                "query_times": [],
                "connections": 0,
                "errors": 0
            },
            "optimization": {
                "title_optimizations": 0,
                "description_optimizations": 0,
                "bulk_optimizations": 0,
                "average_score_improvement": []
            },
            "system": {
                "startup_time": startup_time,
                "uptime_seconds": 0,
                "memory_usage_mb": 0,
                "cpu_usage_percent": 0
            }
        }
        
        return APIResponse(
            success=True,
            message="Metrics reset successfully",
            data={
                "reset_timestamp": datetime.now().isoformat(),
                "previous_summary": old_metrics_summary,
                "reset_by": current_user.email if hasattr(current_user, 'email') else 'admin'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting metrics: {str(e)}"
        )


# Helper functions

def _calculate_performance_grade(metrics: Dict[str, Any]) -> str:
    """Calculate overall performance grade"""
    score = 100
    
    # Response time scoring (40% weight)
    avg_response_time = metrics["requests"]["avg_response_time"]
    if avg_response_time > 2000:
        score -= 40
    elif avg_response_time > 1000:
        score -= 20
    elif avg_response_time > 500:
        score -= 10
    
    # Error rate scoring (30% weight) 
    error_rate = metrics["requests"]["error_rate"]
    if error_rate > 10:
        score -= 30
    elif error_rate > 5:
        score -= 15
    elif error_rate > 1:
        score -= 5
    
    # Database performance scoring (20% weight)
    db_query_time = metrics["database"]["avg_query_time"]
    if db_query_time > 1000:
        score -= 20
    elif db_query_time > 500:
        score -= 10
    elif db_query_time > 100:
        score -= 5
    
    # System resource scoring (10% weight)
    memory_usage = metrics["system"]["memory_usage_mb"]
    if memory_usage > 1000:
        score -= 10
    elif memory_usage > 500:
        score -= 5
    
    # Convert score to grade
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _grade_endpoint_performance(avg_response_time: float) -> str:
    """Grade individual endpoint performance"""
    if avg_response_time < 100:
        return "A+"
    elif avg_response_time < 300:
        return "A"
    elif avg_response_time < 500:
        return "B"
    elif avg_response_time < 1000:
        return "C"
    elif avg_response_time < 2000:
        return "D"
    else:
        return "F"