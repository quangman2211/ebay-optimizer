"""
Sources API Endpoints - Supplier/Dropshipping Sources Management với SQLite repository
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.schemas import (
    Source, SourceCreate, SourceUpdate, 
    SourceStatus, PaginatedResponse, APIResponse
)
from app.repositories import source_repo
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.database_models import User

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def get_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[SourceStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name, website URL"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query("last_sync", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
):
    """
    Get supplier sources với pagination, filtering, và search
    """
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        
        # Calculate skip value
        skip = (page - 1) * size
        
        # Get sources với repository
        result = source_repo.get_multi(
            db,
            skip=skip,
            limit=size,
            filters=filters,
            search=search,
            search_fields=["name", "website_url"],
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=current_user.id
        )
        
        # Convert SQLAlchemy models to Pydantic schemas
        pydantic_sources = [Source.from_orm(source) for source in result["items"]]
        
        # Return PaginatedResponse with converted items
        return {
            "items": pydantic_sources,
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
            "pages": result["pages"],
            "has_next": result["has_next"],
            "has_prev": result["has_prev"],
            "success": True,
            "message": f"Retrieved {len(pydantic_sources)} sources"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sources: {str(e)}")


@router.get("/{source_id}", response_model=Source)
async def get_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific source by ID
    """
    try:
        source = source_repo.get(db, id=source_id)
        
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Check ownership
        if source.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this source")
        
        return source
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching source: {str(e)}")


@router.post("/", response_model=Source)
async def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new supplier source
    """
    try:
        # Check if name already exists for this user
        existing = source_repo.get_by_name(
            db, 
            name=source.name, 
            user_id=current_user.id
        )
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Source name already exists"
            )
        
        # Generate unique ID
        import uuid
        source_id = f"source_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Create source data
        source_data = source.dict()
        source_data['id'] = source_id
        
        # Create source với repository
        new_source = source_repo.create(
            db, 
            obj_in=source_data, 
            user_id=current_user.id
        )
        
        return new_source
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating source: {str(e)}")


@router.put("/{source_id}", response_model=Source)
async def update_source(
    source_id: str,
    source_update: SourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing source
    """
    try:
        # Get current source
        current_source = source_repo.get(db, id=source_id)
        
        if not current_source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Check ownership
        if current_source.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this source")
        
        # Update source
        updated_source = source_repo.update(
            db,
            db_obj=current_source,
            obj_in=source_update
        )
        
        return updated_source
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating source: {str(e)}")


@router.delete("/{source_id}", response_model=APIResponse)
async def delete_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a supplier source
    """
    try:
        # Get current source
        current_source = source_repo.get(db, id=source_id)
        
        if not current_source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Check ownership
        if current_source.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this source")
        
        # Delete source
        source_repo.delete(db, id=source_id)
        
        return APIResponse(
            success=True,
            message="Source deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting source: {str(e)}")


@router.get("/statistics", response_model=APIResponse)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get source statistics for current user
    """
    try:
        stats = source_repo.get_statistics(db, user_id=current_user.id)
        
        return APIResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.get("/connected", response_model=PaginatedResponse)
async def get_connected_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """
    Get connected sources
    """
    try:
        skip = (page - 1) * size
        result = source_repo.get_connected_sources(
            db, 
            user_id=current_user.id,
            skip=skip,
            limit=size
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching connected sources: {str(e)}")


@router.get("/high-roi", response_model=List[Source])
async def get_high_roi_sources(
    min_roi: float = Query(20.0, ge=0.0, description="Minimum ROI percentage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get sources với high ROI
    """
    try:
        sources = source_repo.get_high_roi_sources(
            db, 
            user_id=current_user.id,
            min_roi=min_roi,
            limit=limit
        )
        return sources
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching high ROI sources: {str(e)}")


@router.get("/need-sync", response_model=List[Source])
async def get_sources_need_sync(
    hours_threshold: int = Query(24, ge=1, le=168, description="Hours since last sync"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sources cần sync (last_sync > threshold)
    """
    try:
        sources = source_repo.get_sources_need_sync(
            db, 
            user_id=current_user.id,
            hours_threshold=hours_threshold
        )
        return sources
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sources needing sync: {str(e)}")


@router.put("/{source_id}/sync", response_model=Source)
async def sync_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync a specific source
    """
    try:
        # Check ownership first
        source = source_repo.get(db, id=source_id)
        if not source or source.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Update sync status
        updated_source = source_repo.update_sync_status(
            db,
            source_id=source_id,
            status=SourceStatus.SYNCING,
            last_sync=datetime.now()
        )
        
        # TODO: Implement actual sync logic here
        # For now, just mark as connected after "sync"
        from app.models.database_models import SourceStatusEnum
        final_source = source_repo.update_sync_status(
            db,
            source_id=source_id,
            status=SourceStatusEnum.CONNECTED
        )
        
        return final_source
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing source: {str(e)}")


@router.post("/bulk-sync", response_model=APIResponse)
async def bulk_sync_sources(
    source_ids: List[str] = Query(..., description="Source IDs to sync"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk sync multiple sources
    """
    try:
        # Validate ownership for all sources
        for source_id in source_ids:
            source = source_repo.get(db, id=source_id)
            if not source or source.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Not authorized to sync source {source_id}"
                )
        
        # Perform bulk sync
        result = source_repo.bulk_sync(
            db, 
            source_ids=source_ids,
            user_id=current_user.id
        )
        
        return APIResponse(
            success=True,
            message=f"Sync completed: {result['success']} successful, {result['failed']} failed",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing sources: {str(e)}")


@router.put("/{source_id}/statistics", response_model=Source)
async def update_statistics(
    source_id: str,
    total_products: Optional[int] = Query(None, ge=0),
    active_products: Optional[int] = Query(None, ge=0),
    total_revenue: Optional[float] = Query(None, ge=0.0),
    average_roi: Optional[float] = Query(None, ge=0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update source statistics
    """
    try:
        # Check ownership first
        source = source_repo.get(db, id=source_id)
        if not source or source.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Update statistics
        updated_source = source_repo.update_statistics(
            db,
            source_id=source_id,
            total_products=total_products,
            active_products=active_products,
            total_revenue=total_revenue,
            average_roi=average_roi
        )
        
        return updated_source
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating statistics: {str(e)}")


@router.put("/{source_id}/calculate-stats", response_model=Source)
async def calculate_statistics(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Auto-calculate statistics based on actual product data
    """
    try:
        # Check ownership first
        source = source_repo.get(db, id=source_id)
        if not source or source.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Update auto-calculated stats
        updated_source = source_repo.update_auto_calculated_stats(
            db,
            source_id=source_id
        )
        
        return updated_source
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}")