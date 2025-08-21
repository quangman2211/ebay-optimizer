"""
Export API Endpoints - Generate reports và export to various formats
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Response
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.schemas import APIResponse
from app.services.export_service import export_service
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.database_models import User

router = APIRouter()


@router.get("/reports", response_model=APIResponse)
async def get_available_reports():
    """
    Get list of available report types
    """
    try:
        reports = export_service.get_available_reports()
        
        return APIResponse(
            success=True,
            message="Available reports retrieved successfully",
            data=reports
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available reports: {str(e)}")


@router.post("/listings")
async def export_listings_report(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    performance_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum performance score"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export listings report
    """
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category
        if performance_min is not None:
            # Note: This would need special handling in repository
            pass
        
        # Generate report
        result = export_service.generate_listings_report(
            db, 
            current_user.id,
            format=format,
            filters=filters
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Return file download
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "X-Total-Records": str(result["records"]),
                "X-File-Size": str(result["size"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting listings report: {str(e)}")


@router.post("/orders")
async def export_orders_report(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format"),
    date_from: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export orders report for specified date range
    """
    try:
        # Generate report
        result = export_service.generate_orders_report(
            db, 
            current_user.id,
            format=format,
            date_from=date_from,
            date_to=date_to
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Return file download
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "X-Total-Records": str(result["records"]),
                "X-File-Size": str(result["size"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting orders report: {str(e)}")


@router.post("/financial")
async def export_financial_report(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format"),
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export financial performance report
    """
    try:
        # Generate report
        result = export_service.generate_financial_report(
            db, 
            current_user.id,
            format=format,
            period_days=period_days
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Return file download
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "X-Total-Records": str(result["records"]),
                "X-File-Size": str(result["size"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting financial report: {str(e)}")


@router.post("/performance")
async def export_performance_report(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export performance analysis report
    """
    try:
        # Generate report
        result = export_service.generate_performance_report(
            db, 
            current_user.id,
            format=format
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Return file download
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "X-Total-Records": str(result["records"]),
                "X-File-Size": str(result["size"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting performance report: {str(e)}")


@router.post("/custom")
async def export_custom_report(
    report_config: Dict[str, Any],
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export custom report based on configuration
    """
    try:
        # TODO: Implement custom report generation
        # This would allow users to create custom reports with specific fields and filters
        
        return APIResponse(
            success=False,
            message="Custom reports not implemented yet"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting custom report: {str(e)}")


@router.get("/templates", response_model=APIResponse)
async def get_export_templates():
    """
    Get available export templates
    """
    try:
        templates = [
            {
                "id": "monthly_summary",
                "name": "Monthly Summary",
                "description": "Complete monthly business summary with all key metrics",
                "includes": ["listings", "orders", "financial", "performance"],
                "format": "multiple_files"
            },
            {
                "id": "tax_report",
                "name": "Tax Report",
                "description": "Financial data formatted for tax reporting",
                "includes": ["orders", "financial"],
                "format": "csv"
            },
            {
                "id": "inventory_report",
                "name": "Inventory Report",
                "description": "Current inventory status and performance",
                "includes": ["listings", "sources"],
                "format": "csv"
            },
            {
                "id": "customer_report",
                "name": "Customer Analysis",
                "description": "Customer behavior and order patterns",
                "includes": ["orders"],
                "format": "csv"
            }
        ]
        
        return APIResponse(
            success=True,
            message="Export templates retrieved successfully",
            data=templates
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting export templates: {str(e)}")


@router.post("/template/{template_id}")
async def export_from_template(
    template_id: str,
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export report using predefined template
    """
    try:
        # Template-based export logic
        if template_id == "monthly_summary":
            # Generate comprehensive monthly report
            result = export_service.generate_performance_report(
                db,
                current_user.id,
                format=format
            )
        elif template_id == "tax_report":
            # Generate tax-focused financial report
            result = export_service.generate_financial_report(
                db,
                current_user.id,
                format=format,
                period_days=365  # Full year for tax
            )
        elif template_id == "inventory_report":
            # Generate inventory-focused listing report
            result = export_service.generate_listings_report(
                db,
                current_user.id,
                format=format,
                filters={"status": "active"}
            )
        elif template_id == "customer_report":
            # Generate customer-focused orders report
            result = export_service.generate_orders_report(
                db,
                current_user.id,
                format=format,
                date_from=date_from,
                date_to=date_to
            )
        else:
            raise HTTPException(status_code=404, detail="Template not found")
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Return file download
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "X-Template-Used": template_id,
                "X-Total-Records": str(result["records"]),
                "X-File-Size": str(result["size"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting from template: {str(e)}")


@router.get("/preview/{report_type}")
async def preview_report(
    report_type: str,
    limit: int = Query(5, ge=1, le=50, description="Number of sample rows"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview report data without generating full export
    """
    try:
        # Generate small sample for preview
        if report_type == "listings":
            result = export_service.generate_listings_report(
                db,
                current_user.id,
                format="json",
                filters={}
            )
        elif report_type == "orders":
            result = export_service.generate_orders_report(
                db,
                current_user.id,
                format="json"
            )
        elif report_type == "financial":
            result = export_service.generate_financial_report(
                db,
                current_user.id,
                format="json",
                period_days=7  # Just 1 week for preview
            )
        elif report_type == "performance":
            result = export_service.generate_performance_report(
                db,
                current_user.id,
                format="json"
            )
        else:
            raise HTTPException(status_code=404, detail="Report type not found")
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Parse JSON and limit rows
        import json
        data = json.loads(result["content"])
        preview_data = data[:limit] if isinstance(data, list) else data
        
        return APIResponse(
            success=True,
            message=f"Report preview generated ({len(preview_data)} of {len(data) if isinstance(data, list) else 1} records)",
            data={
                "preview": preview_data,
                "total_records": len(data) if isinstance(data, list) else 1,
                "columns": list(preview_data[0].keys()) if preview_data and isinstance(preview_data, list) else []
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report preview: {str(e)}")