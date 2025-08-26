"""
Multi-Sheet Sync API Endpoints
Provides API endpoints for managing multi-sheet synchronization
"""

import asyncio
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.deps import get_current_active_user
from app.models.database_models import User
from app.services.multi_sheet.service_factory import (
    get_sync_service, 
    get_adapter_service,
    is_multi_sheet_mode,
    service_factory
)
from config.multi_sheet_config import get_account_config, ACCOUNT_SHEET_MAPPINGS


router = APIRouter()


# Pydantic models for API requests/responses
class SyncAccountRequest(BaseModel):
    account_id: int
    force_sync: bool = False


class SyncStatusResponse(BaseModel):
    is_running: bool
    total_accounts: int
    successful_syncs: int
    last_sync_time: Optional[str]
    current_mode: str
    

class AccountSyncResult(BaseModel):
    account_id: int
    success: bool
    orders_synced: int
    listings_synced: int
    messages_synced: int
    errors: List[str]
    sync_duration: float


class MultiSheetStatusResponse(BaseModel):
    service_available: bool
    sync_running: bool
    total_sheets: int
    accounts_configured: int
    last_cycle_time: Optional[str]
    mode_info: Dict[str, Any]


@router.get("/status", response_model=MultiSheetStatusResponse)
async def get_multi_sheet_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get status of multi-sheet sync service"""
    
    try:
        adapter = get_adapter_service()
        status = await adapter.get_status()
        
        sync_service = get_sync_service()
        sync_running = False
        last_cycle_time = None
        
        if sync_service:
            sync_status = await sync_service.get_sync_status()
            sync_running = sync_status.get('is_running', False)
            # Get most recent sync time
            sync_times = sync_status.get('last_sync_times', {})
            if sync_times:
                recent_times = [t for t in sync_times.values() if t]
                if recent_times:
                    last_cycle_time = max(recent_times)
        
        return MultiSheetStatusResponse(
            service_available=sync_service is not None,
            sync_running=sync_running,
            total_sheets=len(ACCOUNT_SHEET_MAPPINGS),
            accounts_configured=len(ACCOUNT_SHEET_MAPPINGS),
            last_cycle_time=last_cycle_time,
            mode_info=status.get('service_info', {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.post("/sync/account", response_model=AccountSyncResult)
async def sync_specific_account(
    request: SyncAccountRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Sync a specific account's sheet on-demand"""
    
    if not is_multi_sheet_mode():
        raise HTTPException(
            status_code=400, 
            detail="Multi-sheet sync not available in current mode"
        )
    
    sync_service = get_sync_service()
    if not sync_service:
        raise HTTPException(status_code=503, detail="Multi-sheet sync service not available")
    
    # Validate account exists in configuration
    account_config = get_account_config(request.account_id)
    if not account_config:
        raise HTTPException(
            status_code=404, 
            detail=f"Account {request.account_id} not found in configuration"
        )
    
    try:
        # Perform sync
        result = await sync_service.sync_specific_account(request.account_id)
        
        return AccountSyncResult(
            account_id=result.account_id,
            success=result.success,
            orders_synced=result.orders_synced,
            listings_synced=result.listings_synced,
            messages_synced=result.messages_synced,
            errors=result.errors,
            sync_duration=result.sync_duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/accounts")
async def get_configured_accounts(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of all configured accounts for multi-sheet sync"""
    
    accounts = []
    for account_id, config in ACCOUNT_SHEET_MAPPINGS.items():
        accounts.append({
            'account_id': account_id,
            'ebay_username': config.ebay_username,
            'vps_id': config.vps_id,
            'browser_profile': config.browser_profile,
            'sheet_name': config.sheet_name,
            'sync_interval_minutes': config.sync_interval_minutes
        })
    
    return {
        'total_accounts': len(accounts),
        'accounts': accounts
    }


@router.get("/account/{account_id}/status")
async def get_account_status(
    account_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get sync status for a specific account"""
    
    account_config = get_account_config(account_id)
    if not account_config:
        raise HTTPException(status_code=404, detail="Account not found")
    
    sync_service = get_sync_service()
    if not sync_service:
        return {
            'account_id': account_id,
            'status': 'service_unavailable',
            'message': 'Multi-sheet sync service not available'
        }
    
    try:
        # Get sync status
        service_status = await sync_service.get_sync_status()
        last_sync_times = service_status.get('last_sync_times', {})
        sync_stats = service_status.get('sync_stats', {})
        
        account_stats = sync_stats.get(account_id, {})
        last_sync = last_sync_times.get(account_id)
        
        return {
            'account_id': account_id,
            'ebay_username': account_config.ebay_username,
            'sheet_id': account_config.google_sheet_id,
            'last_sync_time': last_sync,
            'total_syncs': account_stats.get('total_syncs', 0),
            'successful_syncs': account_stats.get('successful_syncs', 0),
            'orders_synced': account_stats.get('orders_synced', 0),
            'listings_synced': account_stats.get('listings_synced', 0),
            'messages_synced': account_stats.get('messages_synced', 0),
            'average_sync_time': account_stats.get('average_sync_time', 0),
            'error_count': account_stats.get('error_count', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting account status: {str(e)}")


@router.post("/service/start")
async def start_sync_service(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Start the multi-sheet sync service"""
    
    if not is_multi_sheet_mode():
        raise HTTPException(status_code=400, detail="Not in multi-sheet mode")
    
    sync_service = get_sync_service()
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")
    
    if sync_service.is_running:
        return {'message': 'Sync service already running'}
    
    # Start service in background
    background_tasks.add_task(sync_service.start_continuous_sync)
    
    return {'message': 'Multi-sheet sync service started'}


@router.post("/service/stop")
async def stop_sync_service(
    current_user: User = Depends(get_current_active_user)
):
    """Stop the multi-sheet sync service"""
    
    sync_service = get_sync_service()
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")
    
    if not sync_service.is_running:
        return {'message': 'Sync service already stopped'}
    
    sync_service.stop_sync_service()
    
    return {'message': 'Multi-sheet sync service stopped'}


@router.get("/service/info")
async def get_service_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed service information and configuration"""
    
    try:
        service_info = service_factory.get_service_info()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'factory_info': service_info,
            'multi_sheet_available': is_multi_sheet_mode(),
            'total_configured_accounts': len(ACCOUNT_SHEET_MAPPINGS),
            'vps_distribution': {
                vps_id: len(config['accounts']) 
                for vps_id, config in {
                    1: {'accounts': [1, 2, 3, 4, 5, 6]},
                    2: {'accounts': [7, 8, 9, 10, 11, 12]},
                    3: {'accounts': [13, 14, 15, 16, 17, 18]},
                    4: {'accounts': [19, 20, 21, 22, 23, 24]},
                    5: {'accounts': [25, 26, 27, 28, 29, 30]}
                }.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting service info: {str(e)}")


@router.get("/sheets/validate/{account_id}")
async def validate_sheet_access(
    account_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Validate access to a specific account's Google Sheet"""
    
    account_config = get_account_config(account_id)
    if not account_config:
        raise HTTPException(status_code=404, detail="Account not found")
    
    try:
        adapter = get_adapter_service()
        
        # Try to access the sheet
        if hasattr(adapter.sheets_service, 'validate_sheet_access'):
            access_valid = await adapter.sheets_service.validate_sheet_access(
                account_config.google_sheet_id
            )
        else:
            # Fallback: try to get basic sheet data
            try:
                await adapter.sheets_service.get_sheet_data(
                    account_config.google_sheet_id, 
                    "A1:A1"
                )
                access_valid = True
            except:
                access_valid = False
        
        return {
            'account_id': account_id,
            'sheet_id': account_config.google_sheet_id,
            'access_valid': access_valid,
            'sheet_name': account_config.sheet_name,
            'validation_time': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'account_id': account_id,
            'sheet_id': account_config.google_sheet_id,
            'access_valid': False,
            'error': str(e),
            'validation_time': datetime.utcnow().isoformat()
        }


# Chrome Extension Integration Endpoints
@router.post("/extension/collect")
async def chrome_extension_collect(
    account_id: int,
    data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Receive data collected by Chrome extension"""
    
    account_config = get_account_config(account_id)
    if not account_config:
        raise HTTPException(status_code=404, detail="Account not found")
    
    try:
        # Extract data types
        orders_data = data.get('orders', [])
        listings_data = data.get('listings', [])  
        messages_data = data.get('messages', [])
        
        # Use adapter service to sync data
        adapter = get_adapter_service()
        
        if hasattr(adapter.sheets_service, 'sync_account_data'):
            result = await adapter.sheets_service.sync_account_data(
                account_id=account_id,
                orders_data=orders_data,
                listings_data=listings_data,
                messages_data=messages_data
            )
            
            return {
                'success': result.get('success', False),
                'account_id': account_id,
                'orders_synced': result.get('orders_synced', 0),
                'listings_synced': result.get('listings_synced', 0),
                'messages_synced': result.get('messages_synced', 0),
                'errors': result.get('errors', []),
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=501, detail="Extension sync not supported in current mode")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extension sync failed: {str(e)}")


@router.get("/extension/account-config/{account_id}")
async def get_extension_config(
    account_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get account configuration for Chrome extension"""
    
    account_config = get_account_config(account_id)
    if not account_config:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {
        'account_id': account_id,
        'ebay_username': account_config.ebay_username,
        'sheet_id': account_config.google_sheet_id,
        'vps_id': account_config.vps_id,
        'browser_profile': account_config.browser_profile,
        'collection_schedule': account_config.collection_schedule,
        'sync_interval_minutes': account_config.sync_interval_minutes
    }