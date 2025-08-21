"""
Draft Listings API Endpoints
Handles operations for draft listings management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.repositories.draft_listing import DraftListingRepository
from app.repositories.account import AccountRepository
from app.repositories.source import SourceRepository
from app.models.database_models import User, DraftListing
from app.schemas.schemas import APIResponse
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for request/response
class DraftListingCreate(BaseModel):
    account_id: int
    source_product_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    quantity: int = 1
    condition: str = "new"
    gdrive_folder_url: Optional[str] = None
    cost_price: Optional[float] = None
    profit_margin: Optional[float] = None
    notes: Optional[str] = None

class DraftListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    condition: Optional[str] = None
    gdrive_folder_url: Optional[str] = None
    image_status: Optional[str] = None
    edited_by: Optional[str] = None
    cost_price: Optional[float] = None
    profit_margin: Optional[float] = None
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    notes: Optional[str] = None

class ImageStatusUpdate(BaseModel):
    image_status: str  # pending, edited, approved
    edited_by: Optional[str] = None

class BulkStatusUpdate(BaseModel):
    draft_ids: List[str]
    status: str


@router.get("/", response_model=APIResponse)
async def get_draft_listings(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    image_status: Optional[str] = Query(None, description="Filter by image status"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get draft listings with filtering and pagination"""
    repo = DraftListingRepository(db)
    
    try:
        if search:
            drafts = repo.search_drafts(
                query=search,
                account_id=account_id,
                status=status,
                skip=skip,
                limit=limit
            )
        elif image_status:
            drafts = repo.get_by_image_status(image_status, account_id)
            drafts = drafts[skip:skip+limit]  # Manual pagination
        elif status:
            drafts = repo.get_by_status(status, account_id)
            drafts = drafts[skip:skip+limit]  # Manual pagination
        elif account_id:
            drafts = repo.get_by_account_id(account_id, skip, limit)
        else:
            drafts = repo.get_all(skip=skip, limit=limit)
        
        # Convert to dict for response
        drafts_data = []
        for draft in drafts:
            draft_dict = {
                'id': draft.id,
                'account_id': draft.account_id,
                'source_product_id': draft.source_product_id,
                'title': draft.title,
                'description': draft.description,
                'category': draft.category,
                'price': draft.price,
                'quantity': draft.quantity,
                'condition': draft.condition,
                'gdrive_folder_url': draft.gdrive_folder_url,
                'image_status': draft.image_status,
                'edited_by': draft.edited_by,
                'edit_date': draft.edit_date.isoformat() if draft.edit_date else None,
                'status': draft.status,
                'scheduled_date': draft.scheduled_date.isoformat() if draft.scheduled_date else None,
                'cost_price': draft.cost_price,
                'profit_margin': draft.profit_margin,
                'notes': draft.notes,
                'created_at': draft.created_at.isoformat() if draft.created_at else None,
                'updated_at': draft.updated_at.isoformat() if draft.updated_at else None
            }
            drafts_data.append(draft_dict)
        
        return APIResponse(
            success=True,
            message=f"Found {len(drafts_data)} draft listings",
            data=drafts_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching drafts: {str(e)}"
        )


@router.post("/", response_model=APIResponse)
async def create_draft_listing(
    draft_data: DraftListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new draft listing"""
    repo = DraftListingRepository(db)
    account_repo = AccountRepository(db)
    
    try:
        # Verify account exists and belongs to user
        account = account_repo.get(draft_data.account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not found or access denied"
            )
        
        # Generate unique draft ID
        import uuid
        draft_id = f"DRAFT_{uuid.uuid4().hex[:8].upper()}"
        
        # Create draft listing
        draft = DraftListing(
            id=draft_id,
            user_id=current_user.id,
            account_id=draft_data.account_id,
            source_product_id=draft_data.source_product_id,
            title=draft_data.title,
            description=draft_data.description,
            category=draft_data.category,
            price=draft_data.price,
            quantity=draft_data.quantity,
            condition=draft_data.condition,
            gdrive_folder_url=draft_data.gdrive_folder_url,
            cost_price=draft_data.cost_price,
            profit_margin=draft_data.profit_margin,
            notes=draft_data.notes,
            status='draft',
            image_status='pending',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created_draft = repo.create(draft)
        
        return APIResponse(
            success=True,
            message="Draft listing created successfully",
            data={
                'id': created_draft.id,
                'account_id': created_draft.account_id,
                'title': created_draft.title,
                'status': created_draft.status,
                'image_status': created_draft.image_status
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error creating draft: {str(e)}"
        )


@router.get("/{draft_id}", response_model=APIResponse)
async def get_draft_listing(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific draft listing"""
    repo = DraftListingRepository(db)
    
    try:
        draft = repo.get_with_account_and_source(draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft listing not found"
            )
        
        draft_data = {
            'id': draft.id,
            'account_id': draft.account_id,
            'source_product_id': draft.source_product_id,
            'title': draft.title,
            'description': draft.description,
            'category': draft.category,
            'price': draft.price,
            'quantity': draft.quantity,
            'condition': draft.condition,
            'gdrive_folder_url': draft.gdrive_folder_url,
            'image_status': draft.image_status,
            'edited_by': draft.edited_by,
            'edit_date': draft.edit_date.isoformat() if draft.edit_date else None,
            'listing_type': draft.listing_type,
            'duration_days': draft.duration_days,
            'cost_price': draft.cost_price,
            'profit_margin': draft.profit_margin,
            'status': draft.status,
            'scheduled_date': draft.scheduled_date.isoformat() if draft.scheduled_date else None,
            'notes': draft.notes,
            'created_at': draft.created_at.isoformat() if draft.created_at else None,
            'updated_at': draft.updated_at.isoformat() if draft.updated_at else None
        }
        
        return APIResponse(
            success=True,
            message="Draft listing retrieved successfully",
            data=draft_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching draft: {str(e)}"
        )


@router.put("/{draft_id}", response_model=APIResponse)
async def update_draft_listing(
    draft_id: str,
    draft_data: DraftListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a draft listing"""
    repo = DraftListingRepository(db)
    
    try:
        draft = repo.get(draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft listing not found"
            )
        
        # Update fields
        update_data = draft_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(draft, field):
                setattr(draft, field, value)
        
        draft.updated_at = datetime.utcnow()
        
        # If image_status is being updated, update edit_date
        if draft_data.image_status:
            draft.edit_date = datetime.utcnow()
        
        updated_draft = repo.update(draft)
        
        return APIResponse(
            success=True,
            message="Draft listing updated successfully",
            data={
                'id': updated_draft.id,
                'status': updated_draft.status,
                'image_status': updated_draft.image_status,
                'updated_at': updated_draft.updated_at.isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error updating draft: {str(e)}"
        )


@router.delete("/{draft_id}", response_model=APIResponse)
async def delete_draft_listing(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a draft listing"""
    repo = DraftListingRepository(db)
    
    try:
        draft = repo.get(draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft listing not found"
            )
        
        repo.delete(draft_id)
        
        return APIResponse(
            success=True,
            message="Draft listing deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error deleting draft: {str(e)}"
        )


@router.patch("/{draft_id}/image-status", response_model=APIResponse)
async def update_image_status(
    draft_id: str,
    status_data: ImageStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update image status of a draft"""
    repo = DraftListingRepository(db)
    
    try:
        draft = repo.get(draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft listing not found"
            )
        
        updated_draft = repo.update_image_status(
            draft_id, 
            status_data.image_status, 
            status_data.edited_by
        )
        
        return APIResponse(
            success=True,
            message="Image status updated successfully",
            data={
                'id': updated_draft.id,
                'image_status': updated_draft.image_status,
                'edited_by': updated_draft.edited_by,
                'edit_date': updated_draft.edit_date.isoformat() if updated_draft.edit_date else None
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error updating image status: {str(e)}"
        )


@router.patch("/bulk-status", response_model=APIResponse)
async def bulk_update_status(
    status_data: BulkStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk update status for multiple drafts"""
    repo = DraftListingRepository(db)
    
    try:
        updated_count = repo.bulk_update_status(status_data.draft_ids, status_data.status)
        
        return APIResponse(
            success=True,
            message=f"Updated {updated_count} draft listings",
            data={'updated_count': updated_count}
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error bulk updating drafts: {str(e)}"
        )


@router.get("/ready/to-list", response_model=APIResponse)
async def get_ready_drafts(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get drafts that are ready to list"""
    repo = DraftListingRepository(db)
    
    try:
        drafts = repo.get_ready_to_list(account_id)
        
        drafts_data = []
        for draft in drafts:
            drafts_data.append({
                'id': draft.id,
                'account_id': draft.account_id,
                'title': draft.title,
                'price': draft.price,
                'status': draft.status,
                'image_status': draft.image_status,
                'scheduled_date': draft.scheduled_date.isoformat() if draft.scheduled_date else None
            })
        
        return APIResponse(
            success=True,
            message=f"Found {len(drafts_data)} drafts ready to list",
            data=drafts_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching ready drafts: {str(e)}"
        )


@router.get("/analytics", response_model=APIResponse)
async def get_draft_analytics(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get draft analytics"""
    repo = DraftListingRepository(db)
    
    try:
        analytics = repo.get_analytics(account_id)
        
        return APIResponse(
            success=True,
            message="Draft analytics retrieved successfully",
            data=analytics
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching analytics: {str(e)}"
        )


@router.get("/by-employee/{employee_name}", response_model=APIResponse)
async def get_drafts_by_employee(
    employee_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get drafts edited by specific employee"""
    repo = DraftListingRepository(db)
    
    try:
        drafts = repo.get_drafts_by_employee(employee_name)
        
        drafts_data = []
        for draft in drafts:
            drafts_data.append({
                'id': draft.id,
                'account_id': draft.account_id,
                'title': draft.title,
                'image_status': draft.image_status,
                'edit_date': draft.edit_date.isoformat() if draft.edit_date else None,
                'status': draft.status
            })
        
        return APIResponse(
            success=True,
            message=f"Found {len(drafts_data)} drafts by {employee_name}",
            data=drafts_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching drafts by employee: {str(e)}"
        )