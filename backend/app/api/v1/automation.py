"""
Automation API Endpoints - SOLID Architecture Implementation
Handles automation scheduling và performance monitoring API
Single Responsibility: Manages automation API endpoints với comprehensive task management
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import get_current_user, require_permission
from app.services.automation_service import (
    AutomationService, AutomationTask, AutomationTaskType, 
    TaskFrequency, TaskStatus, PerformanceMonitor
)
from app.models.database_models import User
from app.schemas.schemas import (
    AutomationTaskRequest, AutomationTaskResponse, AutomationTaskUpdate,
    PerformanceSummaryResponse, TaskExecutionRequest, TaskExecutionResponse,
    AutomationScheduleRequest, AutomationScheduleResponse
)

router = APIRouter()

# Global automation service instance
automation_service = AutomationService()

# ===========================================
# TASK MANAGEMENT ENDPOINTS
# ===========================================

@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_automation_tasks(
    status_filter: Optional[str] = Query(None, description="Filter by task status"),
    task_type_filter: Optional[str] = Query(None, description="Filter by task type"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get all automation tasks"""
    try:
        tasks = automation_service.get_tasks()
        
        # Apply filters
        if status_filter:
            tasks = [t for t in tasks if t["status"] == status_filter]
        
        if task_type_filter:
            tasks = [t for t in tasks if t["task_type"] == task_type_filter]
        
        return tasks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_automation_task(
    task_id: str,
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get specific automation task"""
    try:
        task = automation_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")

@router.post("/tasks", response_model=Dict[str, Any])
async def create_automation_task(
    task_request: AutomationTaskRequest,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Create new automation task"""
    try:
        # Create automation task
        task = AutomationTask(
            task_id=task_request.task_id,
            task_type=AutomationTaskType(task_request.task_type),
            frequency=TaskFrequency(task_request.frequency),
            enabled=task_request.enabled,
            parameters=task_request.parameters or {}
        )
        
        success = automation_service.add_task(task)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create task")
        
        return {
            "success": True,
            "message": f"Task {task_request.task_id} created successfully",
            "task": task.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@router.put("/tasks/{task_id}", response_model=Dict[str, Any])
async def update_automation_task(
    task_id: str,
    task_update: AutomationTaskUpdate,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Update automation task"""
    try:
        task = automation_service.tasks.get(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update task properties
        if task_update.enabled is not None:
            task.enabled = task_update.enabled
        
        if task_update.frequency is not None:
            task.frequency = TaskFrequency(task_update.frequency)
            task.next_run = task.calculate_next_run()
        
        if task_update.parameters is not None:
            task.parameters.update(task_update.parameters)
        
        return {
            "success": True,
            "message": f"Task {task_id} updated successfully",
            "task": task.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@router.delete("/tasks/{task_id}")
async def delete_automation_task(
    task_id: str,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Delete automation task"""
    try:
        success = automation_service.remove_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "message": f"Task {task_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

@router.post("/tasks/{task_id}/enable")
async def enable_automation_task(
    task_id: str,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Enable automation task"""
    try:
        success = automation_service.enable_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "message": f"Task {task_id} enabled successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable task: {str(e)}")

@router.post("/tasks/{task_id}/disable")
async def disable_automation_task(
    task_id: str,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Disable automation task"""
    try:
        success = automation_service.disable_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "message": f"Task {task_id} disabled successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable task: {str(e)}")

# ===========================================
# TASK EXECUTION ENDPOINTS
# ===========================================

@router.post("/tasks/{task_id}/execute", response_model=Dict[str, Any])
async def execute_automation_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Execute automation task immediately"""
    try:
        task = automation_service.tasks.get(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status == TaskStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Task is already running")
        
        # Execute task in background
        background_tasks.add_task(automation_service.execute_task, task)
        
        return {
            "success": True,
            "message": f"Task {task_id} execution started",
            "task_id": task_id,
            "status": "started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute task: {str(e)}")

@router.post("/execute-batch", response_model=Dict[str, Any])
async def execute_batch_tasks(
    task_ids: List[str],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Execute multiple tasks in batch"""
    try:
        results = []
        
        for task_id in task_ids:
            task = automation_service.tasks.get(task_id)
            
            if not task:
                results.append({"task_id": task_id, "status": "error", "message": "Task not found"})
                continue
            
            if task.status == TaskStatus.RUNNING:
                results.append({"task_id": task_id, "status": "skipped", "message": "Already running"})
                continue
            
            # Execute task in background
            background_tasks.add_task(automation_service.execute_task, task)
            results.append({"task_id": task_id, "status": "started", "message": "Execution started"})
        
        return {
            "success": True,
            "message": f"Batch execution started for {len(task_ids)} tasks",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute batch: {str(e)}")

# ===========================================
# PERFORMANCE MONITORING ENDPOINTS
# ===========================================

@router.get("/performance/summary", response_model=Dict[str, Any])
async def get_performance_summary(
    hours: int = Query(default=24, description="Time period in hours"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get comprehensive performance summary"""
    try:
        summary = automation_service.get_performance_summary(hours=hours)
        
        return {
            "success": True,
            "data": summary,
            "period_hours": hours,
            "generated_at": automation_service.performance_monitor.metrics.get("generated_at", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")

@router.get("/performance/metrics/{metric_name}", response_model=Dict[str, Any])
async def get_performance_metric(
    metric_name: str,
    hours: int = Query(default=24, description="Time period in hours"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get specific performance metric"""
    try:
        metrics = automation_service.performance_monitor.metrics.get(metric_name, [])
        
        # Filter by time period
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in metrics 
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]
        
        return {
            "success": True,
            "metric_name": metric_name,
            "data": recent_metrics,
            "count": len(recent_metrics),
            "period_hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metric: {str(e)}")

@router.get("/performance/alerts", response_model=Dict[str, Any])
async def get_performance_alerts(
    hours: int = Query(default=24, description="Time period in hours"),
    severity: Optional[str] = Query(None, description="Filter by severity: high, medium, low"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get performance alerts"""
    try:
        alerts = automation_service.performance_monitor.get_active_alerts(hours=hours)
        
        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "period_hours": hours,
            "severity_filter": severity
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

# ===========================================
# SCHEDULER MANAGEMENT ENDPOINTS
# ===========================================

@router.post("/scheduler/start")
async def start_automation_scheduler(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Start automation scheduler"""
    try:
        if automation_service.running:
            return {
                "success": True,
                "message": "Scheduler is already running",
                "status": "running"
            }
        
        # Start scheduler in background
        background_tasks.add_task(automation_service.run_scheduler)
        
        return {
            "success": True,
            "message": "Automation scheduler started",
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/scheduler/stop")
async def stop_automation_scheduler(
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Stop automation scheduler"""
    try:
        automation_service.stop_scheduler()
        
        return {
            "success": True,
            "message": "Automation scheduler stopped",
            "status": "stopped"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status(
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get automation scheduler status"""
    try:
        return {
            "success": True,
            "status": "running" if automation_service.running else "stopped",
            "total_tasks": len(automation_service.tasks),
            "enabled_tasks": len([t for t in automation_service.tasks.values() if t.enabled]),
            "active_tasks": len([t for t in automation_service.tasks.values() if t.status == TaskStatus.RUNNING])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

# ===========================================
# CONFIGURATION ENDPOINTS
# ===========================================

@router.get("/config/task-types")
async def get_available_task_types(
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get available automation task types"""
    try:
        task_types = [
            {
                "value": task_type.value,
                "label": task_type.value.replace("_", " ").title(),
                "description": _get_task_type_description(task_type)
            }
            for task_type in AutomationTaskType
        ]
        
        return {
            "success": True,
            "task_types": task_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task types: {str(e)}")

@router.get("/config/frequencies")
async def get_available_frequencies(
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get available task frequencies"""
    try:
        frequencies = [
            {
                "value": freq.value,
                "label": freq.value.title(),
                "description": _get_frequency_description(freq)
            }
            for freq in TaskFrequency
        ]
        
        return {
            "success": True,
            "frequencies": frequencies
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get frequencies: {str(e)}")

# ===========================================
# UTILITY FUNCTIONS
# ===========================================

def _get_task_type_description(task_type: AutomationTaskType) -> str:
    """Get description for task type"""
    descriptions = {
        AutomationTaskType.SYNC_SUPPLIERS: "Synchronize supplier data to Google Sheets",
        AutomationTaskType.SYNC_PRODUCTS: "Synchronize product data to Google Sheets",
        AutomationTaskType.SYNC_ORDERS: "Synchronize order data to Google Sheets",
        AutomationTaskType.BACKUP_DATA: "Create comprehensive data backup",
        AutomationTaskType.OPTIMIZE_PRICING: "Optimize product pricing based on algorithms",
        AutomationTaskType.MONITOR_PERFORMANCE: "Monitor system and business performance",
        AutomationTaskType.REORDER_CHECK: "Check for products needing reorder",
        AutomationTaskType.SUPPLIER_EVALUATION: "Evaluate supplier performance metrics"
    }
    return descriptions.get(task_type, "Custom automation task")

def _get_frequency_description(frequency: TaskFrequency) -> str:
    """Get description for frequency"""
    descriptions = {
        TaskFrequency.HOURLY: "Execute every hour",
        TaskFrequency.DAILY: "Execute once per day",
        TaskFrequency.WEEKLY: "Execute once per week",
        TaskFrequency.MONTHLY: "Execute once per month",
        TaskFrequency.CUSTOM: "Execute at custom intervals"
    }
    return descriptions.get(frequency, "Custom frequency")