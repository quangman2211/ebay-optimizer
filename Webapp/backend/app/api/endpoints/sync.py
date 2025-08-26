"""
Sync API Endpoints - Bi-directional SQLite ↔ Google Sheets Synchronization
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
import json

from app.schemas.schemas import APIResponse
from app.services.sync_service import sync_service
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.database_models import User
from app.core.config import settings

router = APIRouter()


@router.post("/listings/to-sheets", response_model=APIResponse)
async def sync_listings_to_sheets(
    sheet_name: Optional[str] = Query(None, description="Target sheet name (uses config default if not specified)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export SQLite listings to Google Sheets
    """
    try:
        result = sync_service.sync_listings_to_sheets(db, current_user.id, sheet_name)
        
        return APIResponse(
            success=result["success"],
            message=result["message"],
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing listings to sheets: {str(e)}")


@router.post("/listings/from-sheets", response_model=APIResponse)
async def sync_listings_from_sheets(
    sheet_name: Optional[str] = Query(None, description="Source sheet name (uses config default if not specified)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import Google Sheets listings to SQLite
    """
    try:
        result = sync_service.sync_listings_from_sheets(db, current_user.id, sheet_name)
        
        return APIResponse(
            success=result["success"],
            message=result["message"],
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing listings from sheets: {str(e)}")


@router.post("/orders/to-sheets", response_model=APIResponse)
async def sync_orders_to_sheets(
    sheet_name: Optional[str] = Query(None, description="Target sheet name (uses ORDERS_SHEET_NAME config if not specified)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export orders to Google Sheets for reporting
    """
    try:
        result = sync_service.sync_orders_to_sheets(db, current_user.id, sheet_name)
        
        return APIResponse(
            success=result["success"],
            message=result["message"],
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting orders to sheets: {str(e)}")


@router.post("/sources/to-sheets", response_model=APIResponse)
async def sync_sources_to_sheets(
    sheet_name: Optional[str] = Query(None, description="Target sheet name (uses SOURCES_SHEET_NAME config if not specified)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export sources to Google Sheets for tracking
    """
    try:
        result = sync_service.sync_sources_to_sheets(db, current_user.id, sheet_name)
        
        return APIResponse(
            success=result["success"],
            message=result["message"],
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting sources to sheets: {str(e)}")


@router.post("/full-sync", response_model=APIResponse)
async def full_sync(
    direction: str = Query("bidirectional", pattern="^(to_sheets|from_sheets|bidirectional)$", description="Sync direction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform full synchronization between SQLite and Google Sheets
    
    Directions:
    - to_sheets: Export SQLite data to Google Sheets
    - from_sheets: Import Google Sheets data to SQLite
    - bidirectional: Both import and export
    """
    try:
        result = sync_service.full_sync(db, current_user.id, direction)
        
        return APIResponse(
            success=result["success"],
            message=result["message"],
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing full sync: {str(e)}")


@router.get("/status", response_model=APIResponse)
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current synchronization status and statistics
    """
    try:
        result = sync_service.get_sync_status(db, current_user.id)
        
        return APIResponse(
            success=result["success"],
            message="Sync status retrieved successfully",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {str(e)}")


@router.post("/auto-sync", response_model=APIResponse)
async def trigger_auto_sync(
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger automatic synchronization
    """
    try:
        success = sync_service.schedule_auto_sync(current_user.id)
        
        if success:
            return APIResponse(
                success=True,
                message="Auto-sync completed successfully"
            )
        else:
            return APIResponse(
                success=False,
                message="Auto-sync failed or is disabled"
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering auto-sync: {str(e)}")


@router.get("/config", response_model=APIResponse)
async def get_sync_config():
    """
    Get synchronization configuration
    """
    try:
        return APIResponse(
            success=True,
            message="Sync configuration retrieved successfully",
            data=sync_service.sync_config
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync config: {str(e)}")


@router.put("/config", response_model=APIResponse)
async def update_sync_config(
    enabled: Optional[bool] = Query(None, description="Enable/disable sync"),
    auto_sync_interval: Optional[int] = Query(None, ge=300, le=86400, description="Auto-sync interval in seconds"),
    conflict_resolution: Optional[str] = Query(None, pattern="^(sqlite_wins|sheets_wins|manual)$", description="Conflict resolution strategy")
):
    """
    Update synchronization configuration
    """
    try:
        if enabled is not None:
            sync_service.sync_config["enabled"] = enabled
        
        if auto_sync_interval is not None:
            sync_service.sync_config["auto_sync_interval"] = auto_sync_interval
        
        if conflict_resolution is not None:
            sync_service.sync_config["conflict_resolution"] = conflict_resolution
        
        return APIResponse(
            success=True,
            message="Sync configuration updated successfully",
            data=sync_service.sync_config
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating sync config: {str(e)}")


@router.post("/test-connection", response_model=APIResponse)
async def test_sheets_connection():
    """
    Test Google Sheets API connection
    """
    try:
        # Test by trying to get listings
        sheets_service = sync_service.sheets_service
        
        if sheets_service.use_fallback:
            return APIResponse(
                success=False,
                message="Using fallback mode - Google Sheets not available",
                data={"fallback_mode": True}
            )
        
        # Try to access sheets
        listings = sheets_service.get_all_listings()
        
        return APIResponse(
            success=True,
            message="Google Sheets connection successful",
            data={
                "connection_status": "connected",
                "listings_found": len(listings) if listings else 0,
                "fallback_mode": False
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Google Sheets connection failed: {str(e)}",
            data={"connection_status": "failed", "error": str(e)}
        )


@router.get("/history", response_model=APIResponse)
async def get_sync_history(
    limit: int = Query(20, ge=1, le=100, description="Number of sync records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get synchronization history
    """
    try:
        from app.models.database_models import ActivityLog
        from sqlalchemy import desc, and_
        
        # Get sync-related activities
        sync_activities = db.query(ActivityLog).filter(
            and_(
                ActivityLog.user_id == current_user.id,
                ActivityLog.action.in_([
                    "sync_export", "sync_import", "full_sync", 
                    "sync_listings", "sync_orders"
                ])
            )
        ).order_by(desc(ActivityLog.created_at)).limit(limit).all()
        
        # Format history
        history = []
        for activity in sync_activities:
            history.append({
                "id": activity.id,
                "action": activity.action,
                "entity_type": activity.entity_type,
                "description": activity.description,
                "success": activity.success,
                "timestamp": activity.created_at.isoformat(),
                "details": activity.new_values,
                "error": activity.error_message
            })
        
        return APIResponse(
            success=True,
            message="Sync history retrieved successfully",
            data=history
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync history: {str(e)}")


@router.delete("/clear-history", response_model=APIResponse)
async def clear_sync_history(
    days: int = Query(30, ge=1, le=365, description="Clear history older than N days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear old synchronization history
    """
    try:
        from app.models.database_models import ActivityLog
        from sqlalchemy import and_
        from datetime import datetime, timedelta
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Delete old sync activities
        deleted = db.query(ActivityLog).filter(
            and_(
                ActivityLog.user_id == current_user.id,
                ActivityLog.action.in_([
                    "sync_export", "sync_import", "full_sync", 
                    "sync_listings", "sync_orders"
                ]),
                ActivityLog.created_at < cutoff_date
            )
        ).delete()
        
        db.commit()
        
        return APIResponse(
            success=True,
            message=f"Cleared {deleted} sync history records older than {days} days"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing sync history: {str(e)}")


@router.post("/create-sheets", response_model=APIResponse)
async def create_google_sheets():
    """
    Create all required Google Sheets (Orders, Sources, Accounts) if they don't exist
    """
    try:
        sheets_service = sync_service.sheets_service
        
        if sheets_service.use_fallback:
            return APIResponse(
                success=False,
                message="Using fallback mode - Google Sheets not available",
                data={"fallback_mode": True}
            )
        
        # Create all required sheets
        results = sheets_service.create_all_required_sheets()
        
        if "error" in results:
            return APIResponse(
                success=False,
                message=results["error"],
                data=results
            )
        
        success_count = sum(1 for success in results.values() if success)
        total_sheets = len(results)
        
        return APIResponse(
            success=True,
            message=f"Sheet creation completed: {success_count}/{total_sheets} sheets ready",
            data={
                "results": results,
                "success_count": success_count,
                "total_sheets": total_sheets,
                "sheets_created": [name for name, success in results.items() if success]
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error creating Google Sheets: {str(e)}",
            data={"error": str(e)}
        )


@router.post("/force-sync-listings", response_model=APIResponse)
async def force_sync_all_listings(
    clear_first: bool = Query(False, description="Clear existing data before sync"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Force sync all listings from SQLite to Google Sheets (bypass smart merge)
    """
    try:
        from app.repositories import listing_repo
        
        # Get all listings from SQLite
        result = listing_repo.get_multi(db, skip=0, limit=1000, user_id=current_user.id)
        sqlite_listings = result["items"]
        
        if not sqlite_listings:
            return APIResponse(
                success=True,
                message="No listings found to sync",
                data={"synced_count": 0}
            )
        
        # Get sheets service
        sheets_service = sync_service.sheets_service
        target_sheet = getattr(settings, 'SHEET_NAME', 'Listings')
        
        # Create sheet if needed
        if not sheets_service.create_sheet_if_not_exists(target_sheet, "listings"):
            return APIResponse(
                success=False,
                message="Failed to create Listings sheet"
            )
        
        # Convert all listings to optimized sheets format (20 columns)
        sheets_data = []
        for listing in sqlite_listings:
            sheets_row = [
                str(listing.id),                                             # Listing ID
                listing.item_id or "",                                      # eBay Item ID  
                listing.sku or "",                                          # SKU
                listing.title or "",                                        # Current Title
                listing.optimized_title or "",                              # Optimized Title
                listing.description or "",                                  # Description
                listing.category or "",                                     # Category
                str(listing.price) if listing.price else "",               # Price
                str(listing.quantity) if listing.quantity else "0",        # Quantity
                listing.condition or "",                                    # Condition
                listing.status.value,                                       # Status
                ",".join(listing.keywords) if listing.keywords else "",    # Keywords
                json.dumps(listing.item_specifics) if listing.item_specifics else "{}", # Item Specifics
                str(listing.views) if listing.views else "0",              # Views
                str(listing.watchers) if listing.watchers else "0",        # Watchers
                str(listing.sold) if listing.sold else "0",                # Sold
                str(listing.performance_score) if listing.performance_score else "", # Performance Score
                str(listing.seo_score) if listing.seo_score else "",       # SEO Score
                listing.created_at.isoformat() if listing.created_at else "", # Created
                listing.updated_at.isoformat() if listing.updated_at else ""  # Last Updated
            ]
            sheets_data.append(sheets_row)
        
        # Write to Google Sheets
        if sheets_service.service and sheets_service.spreadsheet_id:
            if clear_first:
                # Clear existing data (except headers)
                clear_range = f"{target_sheet}!A2:T"
                sheets_service.service.spreadsheets().values().clear(
                    spreadsheetId=sheets_service.spreadsheet_id,
                    range=clear_range
                ).execute()
            
            # Write all data
            body = {
                'values': sheets_data
            }
            
            range_name = f"{target_sheet}!A2:T{len(sheets_data) + 1}"
            sheets_service.service.spreadsheets().values().update(
                spreadsheetId=sheets_service.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
        
        return APIResponse(
            success=True,
            message=f"Force sync completed: {len(sheets_data)} listings exported with full SQLite data",
            data={
                "synced_count": len(sheets_data),
                "target_sheet": target_sheet,
                "cleared_first": clear_first,
                "columns_count": 20
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Force sync failed: {str(e)}",
            data={"error": str(e)}
        )


@router.post("/validate-sheets", response_model=APIResponse)
async def validate_sheet_structure():
    """
    Validate that all required sheets exist with correct structure
    """
    try:
        sheets_service = sync_service.sheets_service
        
        if sheets_service.use_fallback:
            return APIResponse(
                success=False,
                message="Using fallback mode - Google Sheets not available",
                data={"fallback_mode": True}
            )
        
        validation_results = {}
        
        # Check Listings sheet
        try:
            listings = sheets_service.get_all_listings()
            validation_results["listings"] = {
                "exists": True,
                "row_count": len(listings) if listings else 0,
                "status": "OK"
            }
        except Exception as e:
            validation_results["listings"] = {
                "exists": False,
                "error": str(e),
                "status": "ERROR"
            }
        
        # Check Orders sheet
        try:
            orders = sheets_service.get_all_orders()
            validation_results["orders"] = {
                "exists": True,
                "row_count": len(orders) if orders else 0,
                "status": "OK"
            }
        except Exception as e:
            validation_results["orders"] = {
                "exists": False,
                "error": str(e),
                "status": "ERROR"
            }
        
        # Check Sources sheet
        try:
            sources = sheets_service.get_all_sources()
            validation_results["sources"] = {
                "exists": True,
                "row_count": len(sources) if sources else 0,
                "status": "OK"
            }
        except Exception as e:
            validation_results["sources"] = {
                "exists": False,
                "error": str(e),
                "status": "ERROR"
            }
        
        all_valid = all(result["status"] == "OK" for result in validation_results.values())
        
        return APIResponse(
            success=all_valid,
            message="Sheet validation completed" if all_valid else "Some sheets have issues",
            data=validation_results
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error validating sheets: {str(e)}",
            data={"error": str(e)}
        )