"""
CSV Import API Endpoints
Handles importing CSV data from eBay reports via Google Sheets
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.core.deps import get_db
from app.core.auth import get_current_user
from app.domain.models.user import User
from app.schemas.schemas import (
    CSVImportRequest,
    CSVImportResponse,
    OrderCSVRecord,
    ListingCSVRecord,
    ImportStatus
)
from app.services.csv_import_service import CSVImportService
from app.services.sheets_data_service import SheetsDataService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/import/orders", response_model=CSVImportResponse)
async def import_orders_from_csv(
    import_request: CSVImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import orders from eBay CSV data via Google Sheets
    """
    try:
        logger.info(f"Starting CSV orders import for user {current_user.id}")
        
        csv_service = CSVImportService(db)
        
        # Validate user permissions
        if not current_user.can_import_data():
            raise HTTPException(
                status_code=403,
                detail="User does not have permission to import data"
            )
        
        # Start background import task
        background_tasks.add_task(
            csv_service.import_orders_from_sheets,
            sheet_id=import_request.sheet_id,
            account_id=import_request.account_id,
            user_id=current_user.id,
            import_options=import_request.options
        )
        
        return CSVImportResponse(
            success=True,
            message="Orders import started successfully",
            import_id=f"orders_import_{datetime.now().timestamp()}",
            status=ImportStatus.PROCESSING,
            estimated_records=import_request.estimated_records
        )
        
    except Exception as e:
        logger.error(f"CSV orders import failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )

@router.post("/import/listings", response_model=CSVImportResponse)
async def import_listings_from_csv(
    import_request: CSVImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import listings from eBay CSV data via Google Sheets
    """
    try:
        logger.info(f"Starting CSV listings import for user {current_user.id}")
        
        csv_service = CSVImportService(db)
        
        # Validate user permissions
        if not current_user.can_import_data():
            raise HTTPException(
                status_code=403,
                detail="User does not have permission to import data"
            )
        
        # Start background import task
        background_tasks.add_task(
            csv_service.import_listings_from_sheets,
            sheet_id=import_request.sheet_id,
            account_id=import_request.account_id,
            user_id=current_user.id,
            import_options=import_request.options
        )
        
        return CSVImportResponse(
            success=True,
            message="Listings import started successfully",
            import_id=f"listings_import_{datetime.now().timestamp()}",
            status=ImportStatus.PROCESSING,
            estimated_records=import_request.estimated_records
        )
        
    except Exception as e:
        logger.error(f"CSV listings import failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )

@router.get("/import/status/{import_id}")
async def get_import_status(
    import_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a CSV import operation
    """
    try:
        csv_service = CSVImportService(db)
        status = await csv_service.get_import_status(import_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail="Import operation not found"
            )
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get import status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

@router.get("/sheets/{sheet_id}/preview")
async def preview_sheet_data(
    sheet_id: str,
    sheet_name: str = "Orders",
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview data from a Google Sheet before importing
    """
    try:
        logger.info(f"Previewing sheet data: {sheet_id}/{sheet_name}")
        
        sheets_service = SheetsDataService()
        
        # Get sample data from sheet
        preview_data = await sheets_service.get_sheet_preview(
            sheet_id=sheet_id,
            sheet_name=sheet_name,
            limit=limit
        )
        
        return {
            "success": True,
            "sheet_id": sheet_id,
            "sheet_name": sheet_name,
            "headers": preview_data.get("headers", []),
            "sample_rows": preview_data.get("rows", []),
            "total_rows": preview_data.get("total_rows", 0)
        }
        
    except Exception as e:
        logger.error(f"Sheet preview failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Preview failed: {str(e)}"
        )

@router.post("/import/validate")
async def validate_csv_data(
    validation_request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate CSV data before importing
    """
    try:
        csv_service = CSVImportService(db)
        
        validation_result = await csv_service.validate_csv_data(
            data=validation_request.get("data", []),
            import_type=validation_request.get("type", "orders"),
            account_id=validation_request.get("account_id")
        )
        
        return {
            "success": True,
            "validation_result": validation_result,
            "is_valid": validation_result.get("is_valid", False),
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "valid_records": validation_result.get("valid_records", 0),
            "invalid_records": validation_result.get("invalid_records", 0)
        }
        
    except Exception as e:
        logger.error(f"CSV validation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

@router.get("/import/history")
async def get_import_history(
    limit: int = 20,
    offset: int = 0,
    import_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get CSV import history for the current user
    """
    try:
        csv_service = CSVImportService(db)
        
        history = await csv_service.get_import_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            import_type=import_type
        )
        
        return {
            "success": True,
            "imports": history.get("imports", []),
            "total_count": history.get("total_count", 0),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to get import history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )

@router.post("/sync/from-sheets")
async def sync_from_google_sheets(
    sync_request: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync data from Google Sheets (triggered by Chrome Extension)
    """
    try:
        logger.info(f"Starting sheets sync for user {current_user.id}")
        
        csv_service = CSVImportService(db)
        
        # Validate sync request
        required_fields = ["sheet_id", "account_id", "data_type"]
        for field in required_fields:
            if field not in sync_request:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Start background sync task
        background_tasks.add_task(
            csv_service.sync_from_sheets,
            sheet_id=sync_request["sheet_id"],
            account_id=sync_request["account_id"],
            data_type=sync_request["data_type"],
            user_id=current_user.id,
            sync_options=sync_request.get("options", {})
        )
        
        return {
            "success": True,
            "message": f"Sync started for {sync_request['data_type']} data",
            "sync_id": f"sync_{datetime.now().timestamp()}",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Sheets sync failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )