"""
Accounts API Endpoints - eBay Account Management với SQLite repository
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.schemas import (
    Account, AccountCreate, AccountUpdate, 
    AccountStatus, PaginatedResponse, APIResponse
)
from app.repositories.account import account_repo
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.database_models import User

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[AccountStatus] = Query(None, description="Filter by status"),
    country: Optional[str] = Query(None, description="Filter by country"),
    search: Optional[str] = Query(None, description="Search in username, email, store name"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query("last_activity", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
):
    """
    Get eBay accounts với pagination, filtering, và search
    """
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if country:
            filters["country"] = country
        
        # Calculate skip value
        skip = (page - 1) * size
        
        # Get accounts với repository
        result = account_repo.get_multi(
            db,
            skip=skip,
            limit=size,
            filters=filters,
            search=search,
            search_fields=["ebay_username", "email", "store_name"],
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=current_user.id
        )
        
        # Convert SQLAlchemy models to Pydantic schemas
        pydantic_accounts = [Account.model_validate(account) for account in result["items"]]
        
        # Return PaginatedResponse with converted items
        return {
            "items": pydantic_accounts,
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
            "pages": result["pages"],
            "has_next": result["has_next"],
            "has_prev": result["has_prev"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accounts: {str(e)}")


@router.get("/{account_id}", response_model=Account)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific eBay account by ID
    """
    try:
        account = account_repo.get(db, id=account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Check ownership
        if account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this account")
        
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account: {str(e)}")


@router.post("/", response_model=Account)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new eBay account
    """
    try:
        # Check if username already exists for this user
        existing = account_repo.get_by_username(
            db, 
            ebay_username=account.ebay_username, 
            user_id=current_user.id
        )
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="eBay username already exists"
            )
        
        # Create account với repository
        new_account = account_repo.create(
            db, 
            obj_in=account, 
            user_id=current_user.id
        )
        
        return new_account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating account: {str(e)}")


@router.put("/{account_id}", response_model=Account)
async def update_account(
    account_id: int,
    account_update: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing eBay account
    """
    try:
        # Get current account
        current_account = account_repo.get(db, id=account_id)
        
        if not current_account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Check ownership
        if current_account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this account")
        
        # Update account
        updated_account = account_repo.update(
            db,
            db_obj=current_account,
            obj_in=account_update
        )
        
        return updated_account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating account: {str(e)}")


@router.delete("/{account_id}", response_model=APIResponse)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an eBay account
    """
    try:
        # Get current account
        current_account = account_repo.get(db, id=account_id)
        
        if not current_account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Check ownership
        if current_account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this account")
        
        # Delete account
        account_repo.delete(db, id=account_id)
        
        return APIResponse(
            success=True,
            message="Account deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")


@router.get("/statistics", response_model=APIResponse)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get account statistics for current user
    """
    try:
        stats = account_repo.get_statistics(db, user_id=current_user.id)
        
        return APIResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.get("/active", response_model=PaginatedResponse)
async def get_active_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """
    Get active eBay accounts
    """
    try:
        skip = (page - 1) * size
        result = account_repo.get_active_accounts(
            db, 
            user_id=current_user.id,
            skip=skip,
            limit=size
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active accounts: {str(e)}")


@router.get("/high-health", response_model=List[Account])
async def get_high_health_accounts(
    min_health: float = Query(80.0, ge=0.0, le=100.0, description="Minimum health score"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get accounts với high health score
    """
    try:
        accounts = account_repo.get_high_health_accounts(
            db, 
            user_id=current_user.id,
            min_health=min_health,
            limit=limit
        )
        return accounts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching high health accounts: {str(e)}")


@router.get("/near-limits", response_model=List[Account])
async def get_accounts_near_limits(
    threshold: float = Query(80.0, ge=50.0, le=100.0, description="Usage threshold percentage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get accounts gần đạt listing hoặc revenue limits
    """
    try:
        accounts = account_repo.get_accounts_near_limits(
            db, 
            user_id=current_user.id,
            threshold_percentage=threshold
        )
        return accounts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accounts near limits: {str(e)}")


@router.put("/{account_id}/health-score", response_model=Account)
async def update_health_score(
    account_id: int,
    health_score: float = Query(..., ge=0.0, le=100.0, description="Health score (0-100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update health score for account
    """
    try:
        # Check ownership first
        account = account_repo.get(db, id=account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Update health score
        updated_account = account_repo.update_health_score(
            db,
            account_id=account_id,
            health_score=health_score
        )
        
        return updated_account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating health score: {str(e)}")


@router.put("/{account_id}/metrics", response_model=Account)
async def update_metrics(
    account_id: int,
    feedback_score: Optional[float] = Query(None, ge=0.0, le=100.0),
    feedback_count: Optional[int] = Query(None, ge=0),
    total_listings: Optional[int] = Query(None, ge=0),
    active_listings: Optional[int] = Query(None, ge=0),
    total_sales: Optional[int] = Query(None, ge=0),
    monthly_revenue: Optional[float] = Query(None, ge=0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update account performance metrics
    """
    try:
        # Check ownership first
        account = account_repo.get(db, id=account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Update metrics
        updated_account = account_repo.update_metrics(
            db,
            account_id=account_id,
            feedback_score=feedback_score,
            feedback_count=feedback_count,
            total_listings=total_listings,
            active_listings=active_listings,
            total_sales=total_sales,
            monthly_revenue=monthly_revenue
        )
        
        return updated_account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating metrics: {str(e)}")


@router.post("/sync", response_model=APIResponse)
async def sync_accounts(
    account_ids: List[int] = Query(..., description="Account IDs to sync"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk sync multiple eBay accounts
    """
    try:
        # Validate ownership for all accounts
        for account_id in account_ids:
            account = account_repo.get(db, id=account_id)
            if not account or account.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Not authorized to sync account {account_id}"
                )
        
        # Perform bulk sync
        result = account_repo.bulk_sync(
            db, 
            account_ids=account_ids,
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
        raise HTTPException(status_code=500, detail=f"Error syncing accounts: {str(e)}")


@router.get("/need-sync", response_model=List[Account])
async def get_accounts_need_sync(
    hours_threshold: int = Query(6, ge=1, le=168, description="Hours since last sync"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get accounts cần sync (last_sync > threshold)
    """
    try:
        accounts = account_repo.get_accounts_need_sync(
            db, 
            user_id=current_user.id,
            hours_threshold=hours_threshold
        )
        return accounts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accounts needing sync: {str(e)}")