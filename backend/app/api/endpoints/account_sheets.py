"""
Account Sheets API Endpoints
Handles operations for Google Sheets integration per account
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.repositories.account_sheet import AccountSheetRepository
from app.repositories.account import AccountRepository
from app.models.database_models import User, AccountSheet
from app.schemas.schemas import APIResponse
from datetime import datetime
from pydantic import BaseModel
import json

router = APIRouter()

# Pydantic models for request/response
class AccountSheetCreate(BaseModel):
    account_id: int
    sheet_id: str
    sheet_name: str
    sheet_type: str  # listings, orders, messages, drafts
    sheet_url: Optional[str] = None
    headers: Optional[List[str]] = None
    auto_sync: bool = True
    sync_frequency: int = 60  # minutes

class AccountSheetUpdate(BaseModel):
    sheet_name: Optional[str] = None
    sheet_url: Optional[str] = None
    headers: Optional[List[str]] = None
    auto_sync: Optional[bool] = None
    sync_frequency: Optional[int] = None
    last_row: Optional[int] = None
    sync_status: Optional[str] = None

class BulkSyncUpdate(BaseModel):
    sheet_ids: List[int]
    auto_sync: bool

class BulkFrequencyUpdate(BaseModel):
    sheet_ids: List[int]
    frequency_minutes: int

class SyncTrigger(BaseModel):
    sheet_id: int


@router.get("/", response_model=APIResponse)
async def get_account_sheets(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    sheet_type: Optional[str] = Query(None, description="Filter by sheet type"),
    sync_status: Optional[str] = Query(None, description="Filter by sync status"),
    auto_sync: Optional[bool] = Query(None, description="Filter by auto sync enabled"),
    search: Optional[str] = Query(None, description="Search in sheet name/URL"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get account sheets with filtering and pagination"""
    repo = AccountSheetRepository(db)
    
    try:
        if search:
            sheets = repo.search_sheets(search, sheet_type)
        elif sheet_type:
            sheets = repo.get_by_sheet_type(sheet_type)
        elif sync_status:
            sheets = repo.get_sheets_by_sync_status(sync_status)
        elif account_id:
            sheets = repo.get_by_account_id(account_id)
        else:
            sheets = repo.get_all(skip=skip, limit=limit)
        
        # Apply additional filters
        if auto_sync is not None:
            sheets = [s for s in sheets if s.auto_sync == auto_sync]
        
        # Manual pagination for filtered results
        sheets = sheets[skip:skip+limit]
        
        # Convert to dict for response
        sheets_data = []
        for sheet in sheets:
            # Parse headers if they exist
            headers = None
            if sheet.headers:
                try:
                    headers = json.loads(sheet.headers) if isinstance(sheet.headers, str) else sheet.headers
                except:
                    headers = sheet.headers
            
            sheet_dict = {
                'id': sheet.id,
                'account_id': sheet.account_id,
                'sheet_id': sheet.sheet_id,
                'sheet_name': sheet.sheet_name,
                'sheet_url': sheet.sheet_url,
                'sheet_type': sheet.sheet_type,
                'headers': headers,
                'last_row': sheet.last_row,
                'auto_sync': sheet.auto_sync,
                'sync_frequency': sheet.sync_frequency,
                'last_sync': sheet.last_sync.isoformat() if sheet.last_sync else None,
                'sync_status': sheet.sync_status,
                'created_at': sheet.created_at.isoformat() if sheet.created_at else None,
                'updated_at': sheet.updated_at.isoformat() if sheet.updated_at else None
            }
            sheets_data.append(sheet_dict)
        
        return APIResponse(
            success=True,
            message=f"Found {len(sheets_data)} account sheets",
            data=sheets_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching account sheets: {str(e)}"
        )


@router.post("/", response_model=APIResponse)
async def create_account_sheet(
    sheet_data: AccountSheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new account sheet mapping"""
    repo = AccountSheetRepository(db)
    account_repo = AccountRepository(db)
    
    try:
        # Verify account exists and belongs to user
        account = account_repo.get(sheet_data.account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not found or access denied"
            )
        
        # Check if sheet mapping already exists for this account and type
        existing_sheet = repo.get_by_account_and_type(sheet_data.account_id, sheet_data.sheet_type)
        if existing_sheet:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Sheet mapping for {sheet_data.sheet_type} already exists for this account"
            )
        
        # Create account sheet
        sheet = AccountSheet(
            account_id=sheet_data.account_id,
            sheet_id=sheet_data.sheet_id,
            sheet_name=sheet_data.sheet_name,
            sheet_url=sheet_data.sheet_url,
            sheet_type=sheet_data.sheet_type,
            headers=json.dumps(sheet_data.headers) if sheet_data.headers else None,
            auto_sync=sheet_data.auto_sync,
            sync_frequency=sheet_data.sync_frequency,
            sync_status='pending',
            last_row=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created_sheet = repo.create(sheet)
        
        return APIResponse(
            success=True,
            message="Account sheet created successfully",
            data={
                'id': created_sheet.id,
                'account_id': created_sheet.account_id,
                'sheet_name': created_sheet.sheet_name,
                'sheet_type': created_sheet.sheet_type,
                'sync_status': created_sheet.sync_status
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error creating account sheet: {str(e)}"
        )


@router.get("/{sheet_id}", response_model=APIResponse)
async def get_account_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific account sheet"""
    repo = AccountSheetRepository(db)
    
    try:
        sheet = repo.get_with_account(sheet_id)
        if not sheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account sheet not found"
            )
        
        # Check if user has access to this sheet's account
        if sheet.account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this account sheet"
            )
        
        # Parse headers
        headers = None
        if sheet.headers:
            try:
                headers = json.loads(sheet.headers) if isinstance(sheet.headers, str) else sheet.headers
            except:
                headers = sheet.headers
        
        sheet_data = {
            'id': sheet.id,
            'account_id': sheet.account_id,
            'sheet_id': sheet.sheet_id,
            'sheet_name': sheet.sheet_name,
            'sheet_url': sheet.sheet_url,
            'sheet_type': sheet.sheet_type,
            'headers': headers,
            'last_row': sheet.last_row,
            'auto_sync': sheet.auto_sync,
            'sync_frequency': sheet.sync_frequency,
            'last_sync': sheet.last_sync.isoformat() if sheet.last_sync else None,
            'sync_status': sheet.sync_status,
            'created_at': sheet.created_at.isoformat() if sheet.created_at else None,
            'updated_at': sheet.updated_at.isoformat() if sheet.updated_at else None
        }
        
        return APIResponse(
            success=True,
            message="Account sheet retrieved successfully",
            data=sheet_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching account sheet: {str(e)}"
        )


@router.put("/{sheet_id}", response_model=APIResponse)
async def update_account_sheet(
    sheet_id: int,
    sheet_data: AccountSheetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an account sheet"""
    repo = AccountSheetRepository(db)
    
    try:
        sheet = repo.get_with_account(sheet_id)
        if not sheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account sheet not found"
            )
        
        # Check access
        if sheet.account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this account sheet"
            )
        
        # Update fields
        update_data = sheet_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'headers' and value is not None:
                # Convert headers to JSON string
                setattr(sheet, field, json.dumps(value))
            elif hasattr(sheet, field):
                setattr(sheet, field, value)
        
        sheet.updated_at = datetime.utcnow()
        
        updated_sheet = repo.update(sheet)
        
        return APIResponse(
            success=True,
            message="Account sheet updated successfully",
            data={
                'id': updated_sheet.id,
                'sheet_name': updated_sheet.sheet_name,
                'auto_sync': updated_sheet.auto_sync,
                'sync_frequency': updated_sheet.sync_frequency,
                'sync_status': updated_sheet.sync_status,
                'updated_at': updated_sheet.updated_at.isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error updating account sheet: {str(e)}"
        )


@router.delete("/{sheet_id}", response_model=APIResponse)
async def delete_account_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an account sheet"""
    repo = AccountSheetRepository(db)
    
    try:
        sheet = repo.get_with_account(sheet_id)
        if not sheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account sheet not found"
            )
        
        # Check access
        if sheet.account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this account sheet"
            )
        
        repo.delete(sheet_id)
        
        return APIResponse(
            success=True,
            message="Account sheet deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error deleting account sheet: {str(e)}"
        )


@router.post("/account/{account_id}/create-defaults", response_model=APIResponse)
async def create_default_sheets(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create default sheets for an account"""
    repo = AccountSheetRepository(db)
    account_repo = AccountRepository(db)
    
    try:
        # Verify account exists and belongs to user
        account = account_repo.get(account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not found or access denied"
            )
        
        # Check if sheets already exist
        existing_sheets = repo.get_by_account_id(account_id)
        if existing_sheets:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sheets already exist for this account"
            )
        
        # Create default sheets
        created_sheets = repo.create_default_sheets_for_account(account_id)
        
        sheets_data = [
            {
                'id': sheet.id,
                'sheet_name': sheet.sheet_name,
                'sheet_type': sheet.sheet_type,
                'sync_frequency': sheet.sync_frequency
            }
            for sheet in created_sheets
        ]
        
        return APIResponse(
            success=True,
            message=f"Created {len(created_sheets)} default sheets for account",
            data=sheets_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error creating default sheets: {str(e)}"
        )


@router.get("/sync/needed", response_model=APIResponse)
async def get_sheets_needing_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sheets that need synchronization"""
    repo = AccountSheetRepository(db)
    
    try:
        sheets = repo.get_sheets_needing_sync()
        
        sheets_data = []
        for sheet in sheets:
            sheets_data.append({
                'id': sheet.id,
                'account_id': sheet.account_id,
                'sheet_name': sheet.sheet_name,
                'sheet_type': sheet.sheet_type,
                'last_sync': sheet.last_sync.isoformat() if sheet.last_sync else None,
                'sync_frequency': sheet.sync_frequency,
                'sync_status': sheet.sync_status
            })
        
        return APIResponse(
            success=True,
            message=f"Found {len(sheets_data)} sheets needing sync",
            data=sheets_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error getting sheets needing sync: {str(e)}"
        )


@router.post("/sync/trigger", response_model=APIResponse)
async def trigger_sync(
    sync_data: SyncTrigger,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger sync for a sheet"""
    repo = AccountSheetRepository(db)
    
    try:
        sheet = repo.get_with_account(sync_data.sheet_id)
        if not sheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account sheet not found"
            )
        
        # Check access
        if sheet.account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this account sheet"
            )
        
        # Update sync status (in real implementation, this would trigger actual Google Sheets sync)
        updated_sheet = repo.update_sync_status(sync_data.sheet_id, 'syncing')
        
        # Simulate successful sync after a moment
        import time
        time.sleep(0.1)  # Simulate processing time
        
        updated_sheet = repo.update_sync_status(sync_data.sheet_id, 'success', datetime.utcnow())
        
        return APIResponse(
            success=True,
            message="Sync triggered successfully",
            data={
                'sheet_id': updated_sheet.id,
                'sync_status': updated_sheet.sync_status,
                'last_sync': updated_sheet.last_sync.isoformat() if updated_sheet.last_sync else None
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Update sync status to error
        try:
            repo.update_sync_status(sync_data.sheet_id, 'error')
        except:
            pass
        
        return APIResponse(
            success=False,
            message=f"Error triggering sync: {str(e)}"
        )


@router.patch("/bulk-sync", response_model=APIResponse)
async def bulk_update_sync(
    sync_data: BulkSyncUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk enable/disable auto sync for multiple sheets"""
    repo = AccountSheetRepository(db)
    
    try:
        updated_count = repo.bulk_enable_sync(sync_data.sheet_ids, sync_data.auto_sync)
        
        return APIResponse(
            success=True,
            message=f"Updated auto sync for {updated_count} sheets",
            data={
                'updated_count': updated_count,
                'auto_sync': sync_data.auto_sync
            }
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error bulk updating sync settings: {str(e)}"
        )


@router.patch("/bulk-frequency", response_model=APIResponse)
async def bulk_update_frequency(
    frequency_data: BulkFrequencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk update sync frequency for multiple sheets"""
    repo = AccountSheetRepository(db)
    
    try:
        updated_count = repo.bulk_update_sync_frequency(frequency_data.sheet_ids, frequency_data.frequency_minutes)
        
        return APIResponse(
            success=True,
            message=f"Updated sync frequency for {updated_count} sheets",
            data={
                'updated_count': updated_count,
                'frequency_minutes': frequency_data.frequency_minutes
            }
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error bulk updating sync frequency: {str(e)}"
        )


@router.get("/analytics", response_model=APIResponse)
async def get_sheet_analytics(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get account sheet analytics"""
    repo = AccountSheetRepository(db)
    
    try:
        analytics = repo.get_analytics(account_id)
        
        return APIResponse(
            success=True,
            message="Sheet analytics retrieved successfully",
            data=analytics
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching sheet analytics: {str(e)}"
        )


@router.get("/errors/list", response_model=APIResponse)
async def get_sheets_with_errors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sheets with sync errors"""
    repo = AccountSheetRepository(db)
    
    try:
        error_sheets = repo.get_sheets_with_errors()
        
        sheets_data = []
        for sheet in error_sheets:
            sheets_data.append({
                'id': sheet.id,
                'account_id': sheet.account_id,
                'sheet_name': sheet.sheet_name,
                'sheet_type': sheet.sheet_type,
                'sync_status': sheet.sync_status,
                'last_sync': sheet.last_sync.isoformat() if sheet.last_sync else None,
                'updated_at': sheet.updated_at.isoformat() if sheet.updated_at else None
            })
        
        return APIResponse(
            success=True,
            message=f"Found {len(sheets_data)} sheets with errors",
            data=sheets_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error getting sheets with errors: {str(e)}"
        )