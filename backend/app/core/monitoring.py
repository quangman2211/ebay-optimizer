"""
Monitoring & Logging System - Phase 6 Enhanced Testing Strategy
Comprehensive monitoring, metrics collection, and logging for production
"""

import logging
import time
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from functools import wraps

import structlog
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware

# Configure structured logging
def configure_logging(log_level: str = "INFO", environment: str = "production"):
    """Configure structured logging for the application"""
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FILENAME,
                       structlog.processors.CallsiteParameter.LINENO]
        ),
    ]
    
    if environment == "development":
        # Pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


class MetricsCollector:
    """Collect and store application metrics"""
    
    def __init__(self):
        self.metrics = {
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
                "startup_time": datetime.now(),
                "uptime_seconds": 0,
                "memory_usage_mb": 0,
                "cpu_usage_percent": 0
            }
        }
        self.logger = structlog.get_logger(__name__)
    
    def record_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record request metrics"""
        self.metrics["requests"]["total"] += 1
        
        if status_code < 400:
            self.metrics["requests"]["success"] += 1
        else:
            self.metrics["requests"]["errors"] += 1
        
        # Track by endpoint
        endpoint_key = f"{method} {endpoint}"
        if endpoint_key not in self.metrics["requests"]["by_endpoint"]:
            self.metrics["requests"]["by_endpoint"][endpoint_key] = {
                "count": 0,
                "avg_response_time": 0,
                "total_response_time": 0
            }
        
        endpoint_metrics = self.metrics["requests"]["by_endpoint"][endpoint_key]
        endpoint_metrics["count"] += 1
        endpoint_metrics["total_response_time"] += response_time
        endpoint_metrics["avg_response_time"] = (
            endpoint_metrics["total_response_time"] / endpoint_metrics["count"]
        )
        
        # Track by status code
        status_key = str(status_code)
        self.metrics["requests"]["by_status_code"][status_key] = (
            self.metrics["requests"]["by_status_code"].get(status_key, 0) + 1
        )
        
        # Store response time (keep last 1000)
        self.metrics["requests"]["response_times"].append(response_time)
        if len(self.metrics["requests"]["response_times"]) > 1000:
            self.metrics["requests"]["response_times"] = (
                self.metrics["requests"]["response_times"][-1000:]
            )
    
    def record_auth_event(self, event_type: str, success: bool = True):
        """Record authentication events"""
        if event_type == "login":
            self.metrics["authentication"]["login_attempts"] += 1
            if success:
                self.metrics["authentication"]["login_success"] += 1
            else:
                self.metrics["authentication"]["login_failures"] += 1
        elif event_type == "token_refresh":
            self.metrics["authentication"]["token_refreshes"] += 1
    
    def record_database_query(self, query_time: float, success: bool = True):
        """Record database query metrics"""
        self.metrics["database"]["queries"] += 1
        self.metrics["database"]["query_times"].append(query_time)
        
        if not success:
            self.metrics["database"]["errors"] += 1
        
        # Keep last 1000 query times
        if len(self.metrics["database"]["query_times"]) > 1000:
            self.metrics["database"]["query_times"] = (
                self.metrics["database"]["query_times"][-1000:]
            )
    
    def record_optimization(self, optimization_type: str, score_improvement: float = None):
        """Record optimization events"""
        if optimization_type == "title":
            self.metrics["optimization"]["title_optimizations"] += 1
        elif optimization_type == "description":
            self.metrics["optimization"]["description_optimizations"] += 1
        elif optimization_type == "bulk":
            self.metrics["optimization"]["bulk_optimizations"] += 1
        
        if score_improvement is not None:
            self.metrics["optimization"]["average_score_improvement"].append(score_improvement)
            # Keep last 100 improvements
            if len(self.metrics["optimization"]["average_score_improvement"]) > 100:
                self.metrics["optimization"]["average_score_improvement"] = (
                    self.metrics["optimization"]["average_score_improvement"][-100:]
                )
    
    def update_system_metrics(self):
        """Update system metrics"""
        self.metrics["system"]["uptime_seconds"] = (
            datetime.now() - self.metrics["system"]["startup_time"]
        ).total_seconds()
        
        # Try to get system metrics if psutil is available
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            self.metrics["system"]["memory_usage_mb"] = process.memory_info().rss / 1024 / 1024
            self.metrics["system"]["cpu_usage_percent"] = process.cpu_percent()
        except ImportError:
            # psutil not available, use basic metrics
            pass
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        self.update_system_metrics()
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": self.metrics["system"]["uptime_seconds"],
            "requests": {
                "total": self.metrics["requests"]["total"],
                "success_rate": (
                    (self.metrics["requests"]["success"] / max(1, self.metrics["requests"]["total"])) * 100
                ),
                "error_rate": (
                    (self.metrics["requests"]["errors"] / max(1, self.metrics["requests"]["total"])) * 100
                ),
                "avg_response_time": (
                    sum(self.metrics["requests"]["response_times"]) / 
                    max(1, len(self.metrics["requests"]["response_times"]))
                ) if self.metrics["requests"]["response_times"] else 0,
                "p95_response_time": self._percentile(self.metrics["requests"]["response_times"], 95),
                "requests_per_minute": self._calculate_rpm()
            },
            "authentication": {
                "success_rate": (
                    (self.metrics["authentication"]["login_success"] / 
                     max(1, self.metrics["authentication"]["login_attempts"])) * 100
                )
            },
            "database": {
                "avg_query_time": (
                    sum(self.metrics["database"]["query_times"]) / 
                    max(1, len(self.metrics["database"]["query_times"]))
                ) if self.metrics["database"]["query_times"] else 0,
                "total_queries": self.metrics["database"]["queries"],
                "error_rate": (
                    (self.metrics["database"]["errors"] / max(1, self.metrics["database"]["queries"])) * 100
                )
            },
            "optimization": {
                "total_optimizations": (
                    self.metrics["optimization"]["title_optimizations"] +
                    self.metrics["optimization"]["description_optimizations"] +
                    self.metrics["optimization"]["bulk_optimizations"]
                ),
                "avg_score_improvement": (
                    sum(self.metrics["optimization"]["average_score_improvement"]) /
                    max(1, len(self.metrics["optimization"]["average_score_improvement"]))
                ) if self.metrics["optimization"]["average_score_improvement"] else 0
            },
            "system": {
                "memory_usage_mb": self.metrics["system"]["memory_usage_mb"],
                "cpu_usage_percent": self.metrics["system"]["cpu_usage_percent"]
            }
        }
        
        return summary
    
    def _percentile(self, data: list, percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    def _calculate_rpm(self) -> float:
        """Calculate requests per minute"""
        uptime_minutes = max(1, self.metrics["system"]["uptime_seconds"] / 60)
        return self.metrics["requests"]["total"] / uptime_minutes
    
    def log_metrics_summary(self):
        """Log current metrics summary"""
        summary = self.get_metrics_summary()
        self.logger.info("Metrics summary", **summary)


# Global metrics collector instance
metrics_collector = MetricsCollector()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for monitoring and metrics collection"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.logger = structlog.get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Skip monitoring for excluded paths
        if path in self.exclude_paths:
            return await call_next(request)
        
        # Log request start
        self.logger.info(
            "Request started",
            method=method,
            path=path,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Record metrics
            metrics_collector.record_request(path, method, response.status_code, response_time)
            
            # Log successful request
            self.logger.info(
                "Request completed",
                method=method,
                path=path,
                status_code=response.status_code,
                response_time_ms=round(response_time, 2),
                client_ip=client_ip
            )
            
            # Add custom headers
            response.headers["X-Response-Time"] = str(round(response_time, 2))
            response.headers["X-Request-ID"] = f"{int(time.time())}-{hash(f'{method}{path}{start_time}')}"
            
            return response
            
        except Exception as e:
            # Calculate response time for error
            response_time = (time.time() - start_time) * 1000
            
            # Record error metrics
            metrics_collector.record_request(path, method, 500, response_time)
            
            # Log error
            self.logger.error(
                "Request failed",
                method=method,
                path=path,
                error=str(e),
                response_time_ms=round(response_time, 2),
                client_ip=client_ip,
                exc_info=True
            )
            
            raise


class HealthChecker:
    """System health checking and monitoring"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.checks = {}
    
    def register_check(self, name: str, check_func: Callable, timeout: int = 10):
        """Register a health check"""
        self.checks[name] = {"func": check_func, "timeout": timeout}
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {
                "total_checks": len(self.checks),
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        
        for check_name, check_config in self.checks.items():
            try:
                # Run health check with timeout
                check_result = await asyncio.wait_for(
                    check_config["func"](),
                    timeout=check_config["timeout"]
                )
                
                results["checks"][check_name] = check_result
                
                if check_result.get("status") == "healthy":
                    results["summary"]["passed"] += 1
                elif check_result.get("status") == "warning":
                    results["summary"]["warnings"] += 1
                else:
                    results["summary"]["failed"] += 1
                    results["status"] = "unhealthy"
                    
            except Exception as e:
                results["checks"][check_name] = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results["summary"]["failed"] += 1
                results["status"] = "unhealthy"
        
        # Log health check results
        self.logger.info("Health check completed", **results["summary"])
        
        return results


# Database health check
async def database_health_check() -> Dict[str, Any]:
    """Check database connectivity and performance"""
    try:
        from app.db.database import engine
        from sqlalchemy import text
        
        start_time = time.time()
        
        # Simple query to check database
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        
        query_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy" if query_time < 1000 else "warning",
            "message": f"Database query completed in {query_time:.2f}ms",
            "response_time_ms": query_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


# Memory health check
async def memory_health_check() -> Dict[str, Any]:
    """Check memory usage"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()
        
        status = "healthy"
        if memory_percent > 80:
            status = "error"
        elif memory_percent > 60:
            status = "warning"
        
        return {
            "status": status,
            "message": f"Memory usage: {memory_mb:.1f}MB ({memory_percent:.1f}%)",
            "memory_mb": memory_mb,
            "memory_percent": memory_percent,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        return {
            "status": "warning",
            "message": "psutil not available for memory monitoring",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Memory check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


# Disk health check
async def disk_health_check() -> Dict[str, Any]:
    """Check disk usage"""
    try:
        import psutil
        
        # Check disk usage for current directory
        disk_usage = psutil.disk_usage('.')
        free_gb = disk_usage.free / (1024**3)
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        status = "healthy"
        if free_gb < 1:  # Less than 1GB free
            status = "error"
        elif free_gb < 5:  # Less than 5GB free
            status = "warning"
        
        return {
            "status": status,
            "message": f"Disk usage: {used_percent:.1f}% used, {free_gb:.1f}GB free",
            "free_gb": free_gb,
            "used_percent": used_percent,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        return {
            "status": "warning", 
            "message": "psutil not available for disk monitoring",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Disk check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


# Global health checker instance
health_checker = HealthChecker()

# Register default health checks
health_checker.register_check("database", database_health_check)
health_checker.register_check("memory", memory_health_check)
health_checker.register_check("disk", disk_health_check)


@contextmanager
def monitor_operation(operation_name: str, log_result: bool = True):
    """Context manager for monitoring operations"""
    logger = structlog.get_logger(__name__)
    start_time = time.time()
    
    logger.info(f"Starting {operation_name}")
    
    try:
        yield
        
        execution_time = (time.time() - start_time) * 1000
        
        if log_result:
            logger.info(
                f"{operation_name} completed successfully",
                execution_time_ms=round(execution_time, 2)
            )
            
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        
        logger.error(
            f"{operation_name} failed",
            error=str(e),
            execution_time_ms=round(execution_time, 2),
            exc_info=True
        )
        
        raise


def monitor_function(operation_name: Optional[str] = None):
    """Decorator for monitoring function execution"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with monitor_operation(op_name):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with monitor_operation(op_name):
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Import asyncio for async operations
import asyncio