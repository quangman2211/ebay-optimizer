"""
Google Sheets Sync API Endpoints
Following Dependency Inversion Principle (DIP) - depends on interfaces, not concrete implementations
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.services.interfaces import ISyncService
from app.services.google_sheets import GoogleSheetsService
from app.services.order_import import OrderImportService, GoogleSheetsOrderImporter, ImportSource
from app.services.sheets_management import (
    MultiTierSheetsManager, SheetConfig, SheetTier, SheetType
)
from app.models.database_models import User, Account, Order, SheetsSyncLog
from app.core.rbac import (
    get_current_user, require_orders_import, require_sheets_sync,
    require_admin_users, RBACService
)
from app.schemas.schemas import (
    SheetsSyncLogResponse, APIResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Google Sheets Sync"])


# ===========================================
# REQUEST/RESPONSE MODELS
# ===========================================

class SheetConfigRequest(BaseModel):
    """Request model for sheet configuration"""
    spreadsheet_id: str = Field(..., min_length=40, description="Google Sheets spreadsheet ID")
    sheet_name: str = Field(..., min_length=1, description="Sheet name/tab")
    range: str = Field("A1:Z1000", description="Cell range to sync")
    auto_sync: bool = Field(True, description="Enable automatic sync")
    sync_interval_minutes: int = Field(15, ge=5, le=1440, description="Sync interval in minutes")


class ImportOrdersRequest(BaseModel):
    """Request model for importing orders"""
    account_id: int = Field(..., gt=0, description="Account ID to import orders for")
    source_type: ImportSource = Field(ImportSource.GOOGLE_SHEETS, description="Import source type")
    source_config: SheetConfigRequest = Field(..., description="Source configuration")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional data filters")
    dry_run: bool = Field(False, description="Validate only, don't import")


class ExportTrackingRequest(BaseModel):
    """Request model for exporting tracking data"""
    order_ids: List[str] = Field(..., min_items=1, description="Order IDs to export tracking for")
    destination_config: SheetConfigRequest = Field(..., description="Destination sheet config")
    include_customer_data: bool = Field(False, description="Include customer information")
    update_existing: bool = Field(True, description="Update existing rows if found")


class SyncAllRequest(BaseModel):
    """Request model for syncing all tiers"""
    accounts: List[int] = Field(..., min_items=1, description="Account IDs to sync")
    include_master_dashboard: bool = Field(True, description="Update master dashboard")
    include_staff_workflows: bool = Field(True, description="Update staff workflows")
    force_full_sync: bool = Field(False, description="Force full sync instead of incremental")


class ImportResponse(BaseModel):
    """Response model for import operations"""
    success: bool
    import_id: str
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[str]
    warnings: List[str]
    metadata: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
    """Response model for export operations"""
    success: bool
    export_id: str
    rows_exported: int
    destination: str
    errors: List[str]


class SyncStatusResponse(BaseModel):
    """Response model for sync status"""
    sync_id: str
    status: str
    progress_percentage: float
    current_operation: str
    total_operations: int
    completed_operations: int
    errors: List[str]
    started_at: str
    estimated_completion: Optional[str] = None


# ===========================================
# DEPENDENCY INJECTION FUNCTIONS
# ===========================================

async def get_sheets_service() -> GoogleSheetsService:
    """Get Google Sheets service instance - DIP"""
    service = GoogleSheetsService()
    await service.connect()
    return service


async def get_order_import_service(
    db: Session = Depends(get_db),
    sheets_service: GoogleSheetsService = Depends(get_sheets_service)
) -> OrderImportService:
    """Get Order Import service with dependencies - DIP"""
    rbac_service = RBACService(db)
    import_service = OrderImportService(db, rbac_service)
    
    # Register Google Sheets importer
    from app.services.order_import import OrderDataValidator, OrderDataTransformer
    validator = OrderDataValidator()
    transformer = OrderDataTransformer()
    
    sheets_importer = GoogleSheetsOrderImporter(
        sheets_service, validator, transformer, db
    )
    import_service.register_importer(sheets_importer)
    
    return import_service


async def get_multi_tier_manager(
    db: Session = Depends(get_db),
    sheets_service: GoogleSheetsService = Depends(get_sheets_service)
) -> MultiTierSheetsManager:
    """Get Multi-Tier Sheets Manager with dependencies - DIP"""
    rbac_service = RBACService(db)
    return MultiTierSheetsManager(sheets_service, rbac_service)


# ===========================================
# ORDER IMPORT ENDPOINTS
# ===========================================

@router.post("/import-orders", response_model=ImportResponse)
async def import_orders(
    request: ImportOrdersRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_orders_import),
    import_service: OrderImportService = Depends(get_order_import_service)
):
    """Import orders from Google Sheets"""
    try:
        # Verify account access
        account = db.query(Account).filter(Account.id == request.account_id).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {request.account_id} not found"
            )
        
        # Check account access permissions
        rbac_service = RBACService(db)
        accessible_accounts = rbac_service.get_accessible_account_ids(current_user)
        if accessible_accounts is not None and request.account_id not in accessible_accounts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this account"
            )
        
        # Prepare source configuration
        source_config = {
            "spreadsheet_id": request.source_config.spreadsheet_id,
            "sheet_name": request.source_config.sheet_name,
            "range": request.source_config.range,
            "filters": request.filters
        }
        
        if request.dry_run:
            # Validate configuration only
            sheets_service = await get_sheets_service()
            importer = import_service.importers.get(request.source_type)
            if not importer:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Importer for {request.source_type} not available"
                )
            
            is_valid, errors = importer.validate_config(source_config)
            return ImportResponse(
                success=is_valid,
                import_id="dry_run",
                total_rows=0,
                successful_imports=0,
                failed_imports=0,
                errors=errors,
                warnings=["Dry run - no data imported"]
            )
        
        # Execute import
        result = await import_service.import_orders(
            request.source_type,
            source_config,
            request.account_id,
            current_user.id
        )
        
        return ImportResponse(
            success=result.status.value in ["completed", "partial"],
            import_id=result.import_id,
            total_rows=result.total_rows,
            successful_imports=result.successful_imports,
            failed_imports=result.failed_imports,
            errors=result.errors,
            warnings=result.warnings,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to import orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get("/import-history", response_model=List[SheetsSyncLogResponse])
async def get_import_history(
    account_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    import_service: OrderImportService = Depends(get_order_import_service)
):
    """Get import history for account or all accounts"""
    try:
        # Check permissions
        rbac_service = RBACService(db)
        accessible_accounts = rbac_service.get_accessible_account_ids(current_user)
        
        # Filter by accessible accounts if not admin
        if accessible_accounts is not None:
            if account_id and account_id not in accessible_accounts:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )
        
        history = await import_service.get_import_history(account_id)
        return history[:limit]
        
    except Exception as e:
        logger.error(f"Failed to get import history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get import history: {str(e)}"
        )


# ===========================================
# EXPORT ENDPOINTS  
# ===========================================

@router.post("/export-tracking", response_model=ExportResponse)
async def export_tracking(
    request: ExportTrackingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sheets_sync),
    sheets_service: GoogleSheetsService = Depends(get_sheets_service)
):
    """Export tracking data to Google Sheets"""
    try:
        # Validate orders access
        orders = db.query(Order).filter(Order.id.in_(request.order_ids)).all()
        if len(orders) != len(request.order_ids):
            missing_orders = set(request.order_ids) - {str(order.id) for order in orders}
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Orders not found: {list(missing_orders)}"
            )
        
        # Check access to orders
        rbac_service = RBACService(db)
        accessible_accounts = rbac_service.get_accessible_account_ids(current_user)
        
        if accessible_accounts is not None:
            for order in orders:
                if order.account_id not in accessible_accounts:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied to order {order.id}"
                    )
        
        # Prepare tracking data
        tracking_data = []
        for order in orders:
            row_data = {
                "Order_ID": order.id,
                "eBay_Order_ID": order.ebay_order_id or "",
                "Tracking_Number": order.tracking_number or "",
                "Carrier": order.carrier or "",
                "Ship_Date": order.actual_ship_date.isoformat() if order.actual_ship_date else "",
                "Status": order.status or "pending",
                "Last_Update": order.updated_at.isoformat() if order.updated_at else ""
            }
            
            if request.include_customer_data:
                row_data.update({
                    "Customer_Name": order.customer_name or "",
                    "Customer_Email": order.customer_email or "",
                    "Shipping_Address": order.shipping_address or ""
                })
            
            tracking_data.append(row_data)
        
        # Export to Google Sheets
        destination_config = {
            "spreadsheet_id": request.destination_config.spreadsheet_id,
            "sheet_name": request.destination_config.sheet_name,
            "range": request.destination_config.range
        }
        
        success = await sheets_service.export_tracking(tracking_data, destination_config)
        
        if success:
            # Create sync log
            sync_log = SheetsSyncLog(
                sync_type="export",
                spreadsheet_id=request.destination_config.spreadsheet_id,
                sheet_name=request.destination_config.sheet_name,
                rows_processed=len(tracking_data),
                rows_success=len(tracking_data),
                rows_error=0,
                started_by=current_user.id,
                status="completed"
            )
            db.add(sync_log)
            db.commit()
        
        return ExportResponse(
            success=success,
            export_id=f"export_{current_user.id}_{len(tracking_data)}",
            rows_exported=len(tracking_data) if success else 0,
            destination=f"{request.destination_config.spreadsheet_id}!{request.destination_config.sheet_name}",
            errors=[] if success else ["Failed to write to Google Sheets"]
        )
        
    except Exception as e:
        logger.error(f"Failed to export tracking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


# ===========================================
# MULTI-TIER SYNC ENDPOINTS
# ===========================================

@router.post("/sync-all-tiers", response_model=Dict[str, Any])
async def sync_all_tiers(
    request: SyncAllRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_users),
    tier_manager: MultiTierSheetsManager = Depends(get_multi_tier_manager)
):
    """Sync all three tiers: Master Dashboard, Account Sheets, Staff Workflows"""
    try:
        # Verify account access
        accounts = db.query(Account).filter(Account.id.in_(request.accounts)).all()
        if len(accounts) != len(request.accounts):
            missing_accounts = set(request.accounts) - {account.id for account in accounts}
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Accounts not found: {list(missing_accounts)}"
            )
        
        # Prepare sync data
        sync_data = {}
        
        # Prepare account sheets data
        if request.include_staff_workflows or True:  # Always include account data
            account_sheets = {}
            for account in accounts:
                orders = (
                    db.query(Order)
                    .filter(Order.account_id == account.id)
                    .order_by(Order.created_at.desc())
                    .limit(1000)
                    .all()
                )
                
                orders_data = []
                for order in orders:
                    orders_data.append({
                        "id": order.id,
                        "ebay_order_id": order.ebay_order_id,
                        "customer_name": order.customer_name,
                        "customer_email": order.customer_email,
                        "customer_phone": order.customer_phone,
                        "shipping_address": order.shipping_address,
                        "product_title": order.product_title,
                        "quantity": order.quantity,
                        "price_ebay": order.price_ebay,
                        "order_date": order.order_date.isoformat() if order.order_date else None,
                        "status": order.status,
                        "assigned_to_user_name": order.assigned_to_user.full_name if order.assigned_to_user else None,
                        "assignment_date": order.assignment_date.isoformat() if order.assignment_date else None,
                        "blacklist_status": order.blacklist_status,
                        "blacklist_reason": order.blacklist_reason,
                        "tracking_number": order.tracking_number,
                        "carrier": order.carrier,
                        "actual_ship_date": order.actual_ship_date.isoformat() if order.actual_ship_date else None,
                        "supplier_name": order.supplier_name,
                        "fulfillment_notes": order.fulfillment_notes
                    })
                
                account_sheets[str(account.id)] = orders_data
            
            sync_data["account_sheets"] = account_sheets
        
        # Prepare staff workflows data
        if request.include_staff_workflows:
            staff_workflows = {}
            staff_users = (
                db.query(User)
                .join(User.role)
                .filter(User.role.has(role_name="FULFILLMENT_STAFF"))
                .all()
            )
            
            for user in staff_users:
                assigned_orders = (
                    db.query(Order)
                    .filter(
                        Order.assigned_to_user_id == user.id,
                        Order.account_id.in_(request.accounts)
                    )
                    .all()
                )
                
                orders_data = []
                for order in assigned_orders:
                    orders_data.append({
                        "id": order.id,
                        "ebay_order_id": order.ebay_order_id,
                        "customer_name": order.customer_name,
                        "product_title": order.product_title,
                        "quantity": order.quantity,
                        "order_date": order.order_date.isoformat() if order.order_date else None,
                        "status": order.status,
                        "supplier_name": order.supplier_name,
                        "tracking_number": order.tracking_number,
                        "carrier": order.carrier,
                        "actual_ship_date": order.actual_ship_date.isoformat() if order.actual_ship_date else None,
                        "fulfillment_notes": order.fulfillment_notes
                    })
                
                if orders_data:  # Only include users with assigned orders
                    staff_workflows[str(user.id)] = orders_data
            
            sync_data["staff_workflows"] = staff_workflows
        
        # Prepare master dashboard data
        if request.include_master_dashboard:
            master_data = []
            for account in accounts:
                # Calculate account statistics
                total_orders = (
                    db.query(Order)
                    .filter(Order.account_id == account.id)
                    .count()
                )
                
                pending_orders = (
                    db.query(Order)
                    .filter(Order.account_id == account.id, Order.status == "pending")
                    .count()
                )
                
                processing_orders = (
                    db.query(Order)
                    .filter(Order.account_id == account.id, Order.status == "processing")
                    .count()
                )
                
                shipped_orders = (
                    db.query(Order)
                    .filter(Order.account_id == account.id, Order.status == "shipped")
                    .count()
                )
                
                # Calculate revenue (simplified)
                total_revenue = (
                    db.query(Order.price_ebay)
                    .filter(Order.account_id == account.id, Order.price_ebay.isnot(None))
                    .scalar() or 0
                )
                
                staff_count = (
                    db.query(Order.assigned_to_user_id)
                    .filter(Order.account_id == account.id, Order.assigned_to_user_id.isnot(None))
                    .distinct()
                    .count()
                )
                
                blacklist_flags = (
                    db.query(Order)
                    .filter(
                        Order.account_id == account.id,
                        Order.blacklist_status.in_(["flagged", "blocked"])
                    )
                    .count()
                )
                
                master_data.append({
                    "id": account.id,
                    "name": account.account_name or f"Account {account.id}",
                    "total_orders": total_orders,
                    "pending_orders": pending_orders,
                    "processing_orders": processing_orders,
                    "shipped_orders": shipped_orders,
                    "revenue_today": 0,  # Would need date filtering
                    "revenue_week": 0,   # Would need date filtering
                    "revenue_month": total_revenue,  # Simplified
                    "staff_count": staff_count,
                    "sync_status": "active",
                    "blacklist_flags": blacklist_flags,
                    "performance_score": min(100, max(0, 100 - (pending_orders * 5)))  # Simple scoring
                })
            
            sync_data["master_dashboard"] = master_data
        
        # Execute sync
        sync_results = await tier_manager.sync_all_tiers(sync_data)
        
        return {
            "success": all(result.get("success", False) for result in sync_results.values() if isinstance(result, dict)),
            "sync_results": sync_results,
            "accounts_synced": len(accounts),
            "tiers_synced": {
                "master_dashboard": request.include_master_dashboard,
                "account_sheets": True,
                "staff_workflows": request.include_staff_workflows
            },
            "sync_timestamp": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Failed to sync all tiers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


# ===========================================
# CONFIGURATION ENDPOINTS
# ===========================================

@router.get("/available-sources", response_model=List[str])
async def get_available_sources(
    current_user: User = Depends(get_current_user),
    import_service: OrderImportService = Depends(get_order_import_service)
):
    """Get list of available import sources"""
    sources = import_service.get_available_sources()
    return [source.value for source in sources]


@router.get("/sync-status/{sync_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    sync_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of sync operation"""
    try:
        # Find sync log by ID or partial match
        sync_log = (
            db.query(SheetsSyncLog)
            .filter(SheetsSyncLog.id == int(sync_id))
            .first()
        )
        
        if not sync_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sync operation {sync_id} not found"
            )
        
        # Calculate progress
        total_rows = sync_log.rows_processed or 0
        success_rows = sync_log.rows_success or 0
        error_rows = sync_log.rows_error or 0
        processed_rows = success_rows + error_rows
        
        progress_percentage = (processed_rows / total_rows * 100) if total_rows > 0 else 0
        
        return SyncStatusResponse(
            sync_id=str(sync_log.id),
            status=sync_log.status,
            progress_percentage=progress_percentage,
            current_operation=f"Processing {sync_log.sync_type}",
            total_operations=total_rows,
            completed_operations=processed_rows,
            errors=sync_log.error_details.get("errors", []) if sync_log.error_details else [],
            started_at=sync_log.started_at.isoformat(),
            estimated_completion=sync_log.completed_at.isoformat() if sync_log.completed_at else None
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sync ID format"
        )
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )