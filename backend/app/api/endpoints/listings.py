from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session

from app.schemas.schemas import (
    Listing, ListingCreate, ListingUpdate, 
    ListingStatus, PaginatedResponse, APIResponse
)
from app.repositories import listing_repo
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.database_models import User

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def get_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[ListingStatus] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title, description, SKU"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
):
    """
    Get listings với pagination, filtering, và search
    """
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category
        
        # Calculate skip value
        skip = (page - 1) * size
        
        # Get listings với repository
        result = listing_repo.get_multi(
            db,
            skip=skip,
            limit=size,
            filters=filters,
            search=search,
            search_fields=["title", "description", "category", "sku"],
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=current_user.id
        )
        
        # Convert SQLAlchemy models to Pydantic schemas
        pydantic_listings = [Listing.from_orm(listing) for listing in result["items"]]
        
        # Return PaginatedResponse with converted items
        return {
            "items": pydantic_listings,
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
            "pages": result["pages"],
            "has_next": result["has_next"],
            "has_prev": result["has_prev"],
            "success": True,
            "message": f"Retrieved {len(pydantic_listings)} listings"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching listings: {str(e)}")


@router.get("/{listing_id}", response_model=Listing)
async def get_listing(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific listing by ID
    """
    try:
        listing = listing_repo.get(db, id=listing_id)
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Check ownership
        if listing.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this listing")
        
        return listing
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching listing: {str(e)}")


@router.post("/", response_model=Listing)
async def create_listing(
    listing: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new listing
    """
    try:
        # Generate unique ID
        from datetime import datetime
        import uuid
        listing_id = f"listing_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Create listing data
        listing_data = listing.dict()
        listing_data['id'] = listing_id
        
        # Create listing với repository
        new_listing = listing_repo.create(
            db, 
            obj_in=listing_data, 
            user_id=current_user.id
        )
        
        return new_listing
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating listing: {str(e)}")


@router.put("/{listing_id}", response_model=Listing)
async def update_listing(
    listing_id: str,
    listing_update: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing listing
    """
    try:
        # Get current listing
        current_listing = listing_repo.get(db, id=listing_id)
        
        if not current_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Check ownership
        if current_listing.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this listing")
        
        # Update listing
        updated_listing = listing_repo.update(
            db,
            db_obj=current_listing,
            obj_in=listing_update
        )
        
        return updated_listing
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating listing: {str(e)}")


@router.delete("/{listing_id}", response_model=APIResponse)
async def delete_listing(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Archive a listing (soft delete)
    """
    try:
        # Get current listing
        current_listing = listing_repo.get(db, id=listing_id)
        
        if not current_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Check ownership
        if current_listing.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this listing")
        
        # Archive listing (soft delete)
        from app.schemas.schemas import ListingUpdate
        listing_repo.update(
            db,
            db_obj=current_listing,
            obj_in=ListingUpdate(status=ListingStatus.ARCHIVED)
        )
        
        return APIResponse(
            success=True,
            message="Listing archived successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error archiving listing: {str(e)}")


@router.get("/statistics", response_model=APIResponse)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get listing statistics for current user
    """
    try:
        stats = listing_repo.get_statistics(db, user_id=current_user.id)
        
        return APIResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.get("/search", response_model=PaginatedResponse)
async def search_listings(
    search: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size")
):
    """
    Search listings by title, description, category, SKU
    """
    try:
        skip = (page - 1) * size
        
        result = listing_repo.search_listings(
            db,
            search=search,
            user_id=current_user.id,
            skip=skip,
            limit=size
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching listings: {str(e)}")


@router.post("/bulk-update", response_model=APIResponse)
async def bulk_update_listings(
    updates: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update multiple listings
    """
    try:
        # Validate ownership for all listings
        listing_ids = [update.get("id") for update in updates if "id" in update]
        
        for listing_id in listing_ids:
            listing = listing_repo.get(db, id=listing_id)
            if not listing or listing.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Not authorized to update listing {listing_id}"
                )
        
        # Perform bulk update
        result = listing_repo.bulk_update(db, updates=updates)
        
        return APIResponse(
            success=True,
            message=f"Bulk update completed: {result['success']} successful, {result['failed']} failed",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk update: {str(e)}")