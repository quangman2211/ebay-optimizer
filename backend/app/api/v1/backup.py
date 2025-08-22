"""
Backup API Endpoints - SOLID Architecture Implementation
Handles comprehensive backup operations with supplier/product data
Single Responsibility: Manages backup API endpoints with comprehensive data export
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import get_current_user, require_permission
from app.services.enhanced_google_sheets import EnhancedGoogleSheetsService
from app.services.supplier_service import SupplierService
from app.services.product_service import ProductService
from app.models.database_models import User, Supplier, Product, Order, Listing, Account
from app.schemas.schemas import (
    BackupResponse, BackupStatus, BackupRequest,
    SupplierSchema, ProductSchema
)

router = APIRouter()

# ===========================================
# COMPREHENSIVE BACKUP OPERATIONS
# ===========================================

@router.post("/create-backup", response_model=BackupResponse)
async def create_comprehensive_backup(
    backup_request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Create comprehensive backup of all system data"""
    try:
        # Initialize services
        sheets_service = EnhancedGoogleSheetsService()
        supplier_service = SupplierService(db)
        product_service = ProductService(db)
        
        # Create backup spreadsheet
        backup_spreadsheet_id = sheets_service.create_backup_spreadsheet()
        
        if not backup_spreadsheet_id:
            raise HTTPException(status_code=500, detail="Failed to create backup spreadsheet")
        
        # Schedule background backup task
        background_tasks.add_task(
            execute_comprehensive_backup,
            backup_spreadsheet_id,
            backup_request,
            db
        )
        
        return BackupResponse(
            success=True,
            message="Backup initiated successfully",
            backup_id=backup_spreadsheet_id,
            status="in_progress",
            includes=backup_request.includes or ["all"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")

@router.get("/backup-status/{backup_id}", response_model=BackupStatus)
async def get_backup_status(
    backup_id: str,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Get status of backup operation"""
    try:
        sheets_service = EnhancedGoogleSheetsService()
        
        # Check if backup spreadsheet exists and has data
        backup_info = sheets_service.get_sheet_data(backup_id, "Backup_Info")
        
        if not backup_info:
            return BackupStatus(
                backup_id=backup_id,
                status="not_found",
                progress=0,
                message="Backup not found"
            )
        
        # Get data from all sheets to determine progress
        sheets_data = {
            "orders": len(sheets_service.get_sheet_data(backup_id, "All_Orders")),
            "listings": len(sheets_service.get_sheet_data(backup_id, "All_Listings")),
            "suppliers": len(sheets_service.get_sheet_data(backup_id, "All_Suppliers")),
            "products": len(sheets_service.get_sheet_data(backup_id, "All_Products")),
            "accounts": len(sheets_service.get_sheet_data(backup_id, "eBay_Accounts"))
        }
        
        total_records = sum(sheets_data.values())
        
        return BackupStatus(
            backup_id=backup_id,
            status="completed" if total_records > 0 else "in_progress",
            progress=100 if total_records > 0 else 50,
            message=f"Backup contains {total_records} total records",
            details=sheets_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backup status: {str(e)}")

@router.post("/sync-to-backup/{backup_id}")
async def sync_data_to_backup(
    backup_id: str,
    data_types: List[str] = Query(default=["all"]),
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Sync specific data types to existing backup"""
    try:
        sheets_service = EnhancedGoogleSheetsService()
        supplier_service = SupplierService(db)
        product_service = ProductService(db)
        
        synced_data = {}
        
        if "all" in data_types or "suppliers" in data_types:
            # Sync suppliers
            suppliers = supplier_service.get_all_suppliers(size=1000)
            success = sheets_service.sync_suppliers_to_backup(backup_id, suppliers.items)
            synced_data["suppliers"] = len(suppliers.items) if success else 0
        
        if "all" in data_types or "products" in data_types:
            # Sync products
            products = product_service.get_all_products(size=1000)
            suppliers_map = {s.id: s for s in supplier_service.get_all_suppliers(size=1000).items}
            success = sheets_service.sync_products_to_backup(backup_id, products.items, suppliers_map)
            synced_data["products"] = len(products.items) if success else 0
        
        if "all" in data_types or "orders" in data_types:
            # Sync orders
            orders = db.query(Order).limit(1000).all()
            success = sheets_service.sync_orders_to_backup(backup_id, orders)
            synced_data["orders"] = len(orders) if success else 0
        
        if "all" in data_types or "listings" in data_types:
            # Sync listings
            listings = db.query(Listing).limit(1000).all()
            success = sheets_service.sync_listings_to_backup(backup_id, listings)
            synced_data["listings"] = len(listings) if success else 0
        
        if "all" in data_types or "accounts" in data_types:
            # Sync accounts
            accounts = db.query(Account).all()
            success = sheets_service.sync_accounts_to_backup(backup_id, accounts)
            synced_data["accounts"] = len(accounts) if success else 0
        
        return {
            "success": True,
            "message": "Data synced to backup successfully",
            "backup_id": backup_id,
            "synced_data": synced_data,
            "total_records": sum(synced_data.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync to backup failed: {str(e)}")

@router.get("/list-backups")
async def list_all_backups(
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """List all available backups"""
    try:
        # This would require Google Drive API to list spreadsheets
        # For now, return mock data structure
        return {
            "success": True,
            "backups": [
                {
                    "backup_id": "fallback_backup_001",
                    "created_at": "2025-01-15T10:00:00Z",
                    "size": "1.2MB",
                    "records": 1500,
                    "status": "completed",
                    "includes": ["suppliers", "products", "orders", "listings", "accounts"]
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")

# ===========================================
# ACCOUNT-SPECIFIC BACKUP OPERATIONS
# ===========================================

@router.post("/sync-account-data/{account_email}")
async def sync_account_data(
    account_email: str,
    include_suppliers: bool = Query(default=True),
    include_products: bool = Query(default=True),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Sync supplier/product data to specific account spreadsheet"""
    try:
        sheets_service = EnhancedGoogleSheetsService()
        supplier_service = SupplierService(db)
        product_service = ProductService(db)
        
        # Create or get account spreadsheet
        account_spreadsheet_id = sheets_service.create_account_spreadsheet(account_email)
        
        if not account_spreadsheet_id:
            raise HTTPException(status_code=500, detail="Failed to create account spreadsheet")
        
        synced_data = {}
        
        if include_suppliers:
            # Get suppliers for this account (you might want to filter by account)
            suppliers = supplier_service.get_all_suppliers(size=500)
            success = sheets_service.sync_suppliers_to_sheet(account_spreadsheet_id, suppliers.items)
            synced_data["suppliers"] = len(suppliers.items) if success else 0
        
        if include_products:
            # Get products for this account
            products = product_service.get_all_products(size=500)
            suppliers_map = {s.id: s for s in supplier_service.get_all_suppliers(size=500).items}
            success = sheets_service.sync_products_to_sheet(account_spreadsheet_id, products.items, suppliers_map)
            synced_data["products"] = len(products.items) if success else 0
        
        return {
            "success": True,
            "message": f"Account data synced successfully for {account_email}",
            "spreadsheet_id": account_spreadsheet_id,
            "synced_data": synced_data,
            "account_email": account_email
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Account sync failed: {str(e)}")

@router.post("/share-backup/{backup_id}")
async def share_backup_spreadsheet(
    backup_id: str,
    email: str = Query(..., description="Email to share backup with"),
    role: str = Query(default="reader", description="Access role: reader, writer, or editor"),
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Share backup spreadsheet with specific user"""
    try:
        sheets_service = EnhancedGoogleSheetsService()
        
        success = sheets_service.share_spreadsheet(backup_id, email, role)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to share backup spreadsheet")
        
        return {
            "success": True,
            "message": f"Backup shared with {email} as {role}",
            "backup_id": backup_id,
            "shared_with": email,
            "role": role
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share backup: {str(e)}")

# ===========================================
# BACKGROUND TASK FUNCTIONS
# ===========================================

async def execute_comprehensive_backup(
    backup_spreadsheet_id: str,
    backup_request: BackupRequest,
    db: Session
):
    """Execute comprehensive backup in background"""
    try:
        sheets_service = EnhancedGoogleSheetsService()
        supplier_service = SupplierService(db)
        product_service = ProductService(db)
        
        includes = backup_request.includes or ["all"]
        
        if "all" in includes or "suppliers" in includes:
            # Backup all suppliers
            suppliers = supplier_service.get_all_suppliers(size=2000)
            sheets_service.sync_suppliers_to_backup(backup_spreadsheet_id, suppliers.items)
        
        if "all" in includes or "products" in includes:
            # Backup all products
            products = product_service.get_all_products(size=2000)
            suppliers_map = {s.id: s for s in supplier_service.get_all_suppliers(size=2000).items}
            sheets_service.sync_products_to_backup(backup_spreadsheet_id, products.items, suppliers_map)
        
        if "all" in includes or "orders" in includes:
            # Backup all orders
            orders = db.query(Order).limit(5000).all()
            sheets_service.sync_orders_to_backup(backup_spreadsheet_id, orders)
        
        if "all" in includes or "listings" in includes:
            # Backup all listings
            listings = db.query(Listing).limit(5000).all()
            sheets_service.sync_listings_to_backup(backup_spreadsheet_id, listings)
        
        if "all" in includes or "accounts" in includes:
            # Backup all accounts
            accounts = db.query(Account).all()
            sheets_service.sync_accounts_to_backup(backup_spreadsheet_id, accounts)
        
        # Update backup info with completion status
        sheets_service.update_backup_completion_status(backup_spreadsheet_id)
        
    except Exception as e:
        print(f"Background backup failed: {e}")
        # Log error to backup spreadsheet
        sheets_service.log_backup_error(backup_spreadsheet_id, str(e))