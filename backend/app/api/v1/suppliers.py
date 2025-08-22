"""
Supplier Management API Endpoints - SOLID Architecture
RESTful API for comprehensive supplier management with performance tracking
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.supplier_service import SupplierService
from app.schemas.schemas import (
    Supplier, SupplierCreate, SupplierUpdate, SupplierStatus, SupplierBusinessType,
    SupplierPerformanceStats, PaginationParams, FilterParams, APIResponse,
    PaginatedResponse, BulkActionRequest, BulkActionResponse
)
from app.core.auth import get_current_user, require_role
from app.models.database_models import User

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


# ===========================================
# CORE SUPPLIER CRUD ENDPOINTS
# ===========================================

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Create a new supplier
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - Duplicate email validation
    - Initial performance metrics setup
    - Business terms configuration
    """
    try:
        service = SupplierService(db)
        supplier = service.create_supplier(supplier_data)
        
        return APIResponse(
            success=True,
            message="Supplier created successfully",
            data=supplier
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create supplier: {str(e)}"
        )


@router.get("/", response_model=PaginatedResponse)
async def get_suppliers(
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query(None, description="Sort field: name, performance, orders, created"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    
    # Filter parameters
    search: Optional[str] = Query(None, description="Search in name, company, contact, email"),
    status: Optional[SupplierStatus] = Query(None, description="Filter by status"),
    business_type: Optional[SupplierBusinessType] = Query(None, description="Filter by business type"),
    country: Optional[str] = Query(None, description="Filter by country"),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get suppliers with comprehensive filtering and pagination
    
    **Features:**
    - Advanced search across multiple fields
    - Status and business type filtering
    - Country-based filtering
    - Performance-based sorting
    - Pagination with metadata
    """
    try:
        service = SupplierService(db)
        
        pagination = PaginationParams(
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        filters = FilterParams(search=search)
        
        suppliers, total = service.get_suppliers(
            pagination=pagination,
            filters=filters,
            status=status,
            business_type=business_type,
            country=country
        )
        
        return PaginatedResponse(
            items=suppliers,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
            has_next=page * size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch suppliers: {str(e)}"
        )


@router.get("/{supplier_id}", response_model=APIResponse)
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get supplier by ID with full details"""
    try:
        service = SupplierService(db)
        supplier = service.get_supplier(supplier_id)
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        return APIResponse(
            success=True,
            data=supplier
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch supplier: {str(e)}"
        )


@router.put("/{supplier_id}", response_model=APIResponse)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Update supplier information
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - Partial updates support
    - Business terms modification
    - Contact information updates
    """
    try:
        service = SupplierService(db)
        supplier = service.update_supplier(supplier_id, supplier_data)
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        return APIResponse(
            success=True,
            message="Supplier updated successfully",
            data=supplier
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update supplier: {str(e)}"
        )


@router.delete("/{supplier_id}", response_model=APIResponse)
async def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Delete supplier (soft delete if has active products)
    
    **Required Roles:** ADMIN only
    
    **Features:**
    - Soft delete for suppliers with active products
    - Hard delete for suppliers without dependencies
    - Safety checks for data integrity
    """
    try:
        service = SupplierService(db)
        success = service.delete_supplier(supplier_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        return APIResponse(
            success=True,
            message="Supplier deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete supplier: {str(e)}"
        )


# ===========================================
# PERFORMANCE & ANALYTICS ENDPOINTS
# ===========================================

@router.get("/{supplier_id}/performance", response_model=APIResponse)
async def get_supplier_performance(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed performance statistics for a supplier"""
    try:
        service = SupplierService(db)
        stats = service.get_supplier_performance_stats(supplier_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        return APIResponse(
            success=True,
            data=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch supplier performance: {str(e)}"
        )


@router.post("/{supplier_id}/update-performance", response_model=APIResponse)
async def update_supplier_performance(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Manually trigger performance metrics update
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    """
    try:
        service = SupplierService(db)
        success = service.update_supplier_performance(supplier_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        return APIResponse(
            success=True,
            message="Supplier performance updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update supplier performance: {str(e)}"
        )


@router.get("/analytics/top-performers", response_model=APIResponse)
async def get_top_suppliers(
    limit: int = Query(10, ge=1, le=50, description="Number of suppliers to return"),
    metric: str = Query("performance", regex="^(performance|orders|reliability)$", description="Ranking metric"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top performing suppliers by specified metric"""
    try:
        service = SupplierService(db)
        top_suppliers = service.get_top_suppliers(limit=limit, metric=metric)
        
        return APIResponse(
            success=True,
            data={
                "metric": metric,
                "limit": limit,
                "suppliers": top_suppliers
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch top suppliers: {str(e)}"
        )


@router.get("/analytics/overview", response_model=APIResponse)
async def get_supplier_analytics(
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive supplier analytics and insights"""
    try:
        from datetime import datetime, timedelta
        
        service = SupplierService(db)
        date_from = datetime.utcnow() - timedelta(days=days)
        analytics = service.get_supplier_analytics(date_from=date_from)
        
        return APIResponse(
            success=True,
            data={
                "analysis_period_days": days,
                **analytics
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch supplier analytics: {str(e)}"
        )


# ===========================================
# BUSINESS INTELLIGENCE ENDPOINTS
# ===========================================

@router.get("/performance-tiers/{tier}", response_model=APIResponse)
async def get_suppliers_by_tier(
    tier: str = Path(..., regex="^(excellent|good|average|poor)$", description="Performance tier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get suppliers grouped by performance tier"""
    try:
        service = SupplierService(db)
        suppliers = service.get_suppliers_by_performance_tier(tier)
        
        return APIResponse(
            success=True,
            data={
                "tier": tier,
                "count": len(suppliers),
                "suppliers": suppliers
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch suppliers by tier: {str(e)}"
        )


@router.post("/{supplier_id}/contact", response_model=APIResponse)
async def update_contact_date(
    supplier_id: int,
    contact_date: Optional[str] = None,  # ISO format datetime string
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Update last contact date for supplier
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    """
    try:
        from datetime import datetime
        
        service = SupplierService(db)
        
        # Parse contact date if provided
        parsed_date = None
        if contact_date:
            try:
                parsed_date = datetime.fromisoformat(contact_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        success = service.update_contact_date(supplier_id, parsed_date)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        return APIResponse(
            success=True,
            message="Contact date updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact date: {str(e)}"
        )


# ===========================================
# BULK OPERATIONS ENDPOINTS
# ===========================================

@router.post("/bulk/update-performance", response_model=APIResponse)
async def bulk_update_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Bulk update performance metrics for all active suppliers
    
    **Required Roles:** ADMIN only
    
    **Features:**
    - Updates all active suppliers
    - Returns detailed results
    - Safe error handling per supplier
    """
    try:
        service = SupplierService(db)
        results = service.bulk_update_performance()
        
        return APIResponse(
            success=True,
            message=f"Bulk performance update completed: {results['updated']}/{results['total']} successful",
            data=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update performance: {str(e)}"
        )


@router.post("/bulk/actions", response_model=BulkActionResponse)
async def bulk_supplier_actions(
    action_request: BulkActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Perform bulk actions on multiple suppliers
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Supported Actions:**
    - activate: Set status to active
    - deactivate: Set status to inactive 
    - update_priority: Update priority level
    - update_tier: Update discount tier
    """
    try:
        service = SupplierService(db)
        
        successful = 0
        failed = 0
        errors = []
        
        for supplier_id in action_request.ids:
            try:
                supplier_id_int = int(supplier_id)
                supplier = service.get_supplier(supplier_id_int)
                
                if not supplier:
                    errors.append({"id": supplier_id, "error": "Supplier not found"})
                    failed += 1
                    continue
                
                # Handle different actions
                if action_request.action == "activate":
                    service.update_supplier(supplier_id_int, SupplierUpdate(status=SupplierStatus.ACTIVE))
                elif action_request.action == "deactivate":
                    service.update_supplier(supplier_id_int, SupplierUpdate(status=SupplierStatus.INACTIVE))
                elif action_request.action == "update_priority":
                    priority = action_request.data.get("priority", 3) if action_request.data else 3
                    service.update_supplier(supplier_id_int, SupplierUpdate(priority_level=priority))
                elif action_request.action == "update_tier":
                    tier = action_request.data.get("tier", "standard") if action_request.data else "standard"
                    service.update_supplier(supplier_id_int, SupplierUpdate(discount_tier=tier))
                else:
                    errors.append({"id": supplier_id, "error": f"Unknown action: {action_request.action}"})
                    failed += 1
                    continue
                
                successful += 1
                
            except Exception as e:
                errors.append({"id": supplier_id, "error": str(e)})
                failed += 1
        
        return BulkActionResponse(
            total=len(action_request.ids),
            successful=successful,
            failed=failed,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk actions: {str(e)}"
        )


# ===========================================
# SUPPLIER LOOKUP ENDPOINTS
# ===========================================

@router.get("/search/by-email/{email}", response_model=APIResponse)
async def search_supplier_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search supplier by email address"""
    try:
        service = SupplierService(db)
        supplier = service.get_supplier_by_email(email)
        
        if not supplier:
            return APIResponse(
                success=False,
                message="Supplier not found",
                data=None
            )
        
        return APIResponse(
            success=True,
            data=supplier
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search supplier: {str(e)}"
        )


@router.get("/countries", response_model=APIResponse)
async def get_supplier_countries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all countries where suppliers are located"""
    try:
        from sqlalchemy import func
        from app.models.database_models import Supplier
        
        countries = db.query(Supplier.country, func.count(Supplier.id).label('count'))\
            .filter(Supplier.country.isnot(None))\
            .group_by(Supplier.country)\
            .order_by(func.count(Supplier.id).desc())\
            .all()
        
        return APIResponse(
            success=True,
            data=[{"country": c.country, "supplier_count": c.count} for c in countries]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch supplier countries: {str(e)}"
        )