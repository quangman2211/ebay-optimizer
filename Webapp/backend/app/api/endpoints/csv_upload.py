"""
CSV Upload Endpoint for Chrome Extension
Direct CSV data processing without Google OAuth2
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import csv
import io
import logging
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.models.database_models import Order, Listing, Account
from app.repositories.order import order_repo
from app.repositories.listing import listing_repo
from app.repositories.account import account_repo
from app.schemas.schemas import APIResponse
from app.services.sheets_management import SheetsManagementService
from app.core.config import settings

router = APIRouter(prefix="/csv", tags=["CSV Upload"])
logger = logging.getLogger(__name__)

# Pydantic models for CSV upload
class CSVUploadRequest(BaseModel):
    """Request model for CSV upload from Chrome Extension"""
    account_identifier: str = Field(..., description="eBay account username or identifier")
    csv_type: str = Field(..., pattern="^(orders|listings)$", description="Type of CSV data")
    csv_content: str = Field(..., description="Raw CSV content as string")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class CSVRow(BaseModel):
    """Generic CSV row model"""
    data: Dict[str, Any]

def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verify API key from Chrome Extension
    API keys are stored in environment variable as comma-separated values
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Get allowed API keys from environment
    allowed_keys = settings.EXTENSION_API_KEYS.split(",") if hasattr(settings, 'EXTENSION_API_KEYS') else []
    
    # For development, allow a default key
    if not allowed_keys:
        allowed_keys = ["dev-api-key-12345"]
    
    if x_api_key not in allowed_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True

def parse_csv_content(csv_content: str) -> List[Dict[str, Any]]:
    """Parse CSV content string into list of dictionaries"""
    try:
        # Use StringIO to read CSV content
        csv_file = io.StringIO(csv_content)
        csv_reader = csv.DictReader(csv_file)
        
        rows = []
        for row in csv_reader:
            # Clean up field names (remove BOM, trim whitespace)
            cleaned_row = {}
            for key, value in row.items():
                if key:
                    # Remove BOM and whitespace from keys
                    clean_key = key.replace('\ufeff', '').strip()
                    cleaned_row[clean_key] = value.strip() if value else ""
            rows.append(cleaned_row)
        
        return rows
    except Exception as e:
        logger.error(f"Error parsing CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

def map_ebay_order_data(csv_row: Dict[str, Any]) -> Dict[str, Any]:
    """Map eBay CSV order fields to database model"""
    return {
        "order_number": csv_row.get("Order Number", ""),
        "customer_name": csv_row.get("Buyer Name", csv_row.get("Buyer Username", "")),
        "customer_email": csv_row.get("Buyer Email", ""),
        "item_title": csv_row.get("Item Title", ""),
        "item_number": csv_row.get("Item Number", ""),
        "custom_label": csv_row.get("Custom Label", ""),
        "quantity": int(csv_row.get("Quantity", 1)),
        "price_ebay": float(csv_row.get("Total Price", "0").replace("$", "").replace(",", "")),
        "sale_date": csv_row.get("Sale Date", ""),
        "paid_date": csv_row.get("Paid Date", ""),
        "ship_date": csv_row.get("Ship Date", ""),
        "tracking_number": csv_row.get("Tracking Number", ""),
        "status": "pending",  # Default status
        "created_at": datetime.utcnow()
    }

def map_ebay_listing_data(csv_row: Dict[str, Any]) -> Dict[str, Any]:
    """Map eBay CSV listing fields to database model"""
    return {
        "item_number": csv_row.get("Item Number", csv_row.get("ItemID", "")),
        "title": csv_row.get("Title", csv_row.get("Item Title", "")),
        "custom_label": csv_row.get("Custom Label", csv_row.get("SKU", "")),
        "available_quantity": int(csv_row.get("Available Quantity", csv_row.get("Quantity Available", 0))),
        "price": float(csv_row.get("Current Price", csv_row.get("Price", "0")).replace("$", "").replace(",", "")),
        "sold_quantity": int(csv_row.get("Quantity Sold", csv_row.get("Sold", 0))),
        "watchers": int(csv_row.get("Watchers", csv_row.get("Watch Count", 0))),
        "views": int(csv_row.get("Page Views", csv_row.get("Views", 0))),
        "category": csv_row.get("Category", ""),
        "condition": csv_row.get("Condition", ""),
        "format": csv_row.get("Format", csv_row.get("Listing Type", "")),
        "status": "active",  # Default status
        "created_at": datetime.utcnow()
    }

@router.post("/upload", response_model=APIResponse)
async def upload_csv_data(
    request: CSVUploadRequest,
    db: Session = Depends(get_db),
    api_key_valid: bool = Depends(verify_api_key)
):
    """
    Upload CSV data from Chrome Extension
    No OAuth2 required - uses API key authentication
    """
    try:
        logger.info(f"Received CSV upload for account: {request.account_identifier}, type: {request.csv_type}")
        
        # Find or create account
        account = account_repo.get_by_username(db, username=request.account_identifier)
        if not account:
            # Create account if not exists
            account_data = {
                "username": request.account_identifier,
                "account_name": request.account_identifier,
                "email": f"{request.account_identifier}@ebay.com",
                "status": "active",
                "user_id": 1  # Default to admin user, update as needed
            }
            account = account_repo.create_from_dict(db, obj_in=account_data)
            logger.info(f"Created new account: {account.username}")
        
        # Parse CSV content
        csv_rows = parse_csv_content(request.csv_content)
        logger.info(f"Parsed {len(csv_rows)} rows from CSV")
        
        if not csv_rows:
            return APIResponse(
                success=False,
                message="No data found in CSV",
                data={"rows_processed": 0}
            )
        
        processed_count = 0
        skipped_count = 0
        errors = []
        
        # Process based on CSV type
        if request.csv_type == "orders":
            for row in csv_rows:
                try:
                    order_data = map_ebay_order_data(row)
                    order_data["account_id"] = account.id
                    order_data["user_id"] = account.user_id
                    
                    # Check if order exists
                    existing = order_repo.get_by_order_id(
                        db, 
                        order_id=order_data["order_number"],
                        user_id=account.user_id
                    )
                    
                    if not existing and order_data["order_number"]:
                        order_repo.create_from_dict(db, obj_in=order_data)
                        processed_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    errors.append(f"Row error: {str(e)}")
                    continue
                    
        elif request.csv_type == "listings":
            for row in csv_rows:
                try:
                    listing_data = map_ebay_listing_data(row)
                    listing_data["account_id"] = account.id
                    listing_data["user_id"] = account.user_id
                    
                    # Check if listing exists
                    existing = listing_repo.get_by_item_number(
                        db,
                        item_number=listing_data["item_number"],
                        user_id=account.user_id
                    )
                    
                    if existing:
                        # Update existing listing
                        for key, value in listing_data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        db.commit()
                        processed_count += 1
                    elif listing_data["item_number"]:
                        # Create new listing
                        listing_repo.create_from_dict(db, obj_in=listing_data)
                        processed_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    errors.append(f"Row error: {str(e)}")
                    continue
        
        # Update Google Sheets in background (optional)
        try:
            if processed_count > 0:
                sheets_service = SheetsManagementService(db)
                if request.csv_type == "orders":
                    await sheets_service.sync_orders_to_sheets(account_id=account.id)
                else:
                    await sheets_service.sync_listings_to_sheets(account_id=account.id)
        except Exception as e:
            logger.warning(f"Google Sheets sync failed (non-critical): {str(e)}")
        
        return APIResponse(
            success=True,
            message=f"CSV processed successfully",
            data={
                "account": account.username,
                "type": request.csv_type,
                "rows_processed": processed_count,
                "rows_skipped": skipped_count,
                "total_rows": len(csv_rows),
                "errors": errors[:5] if errors else [],  # Return first 5 errors
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@router.get("/health", response_model=APIResponse)
async def health_check(api_key_valid: bool = Depends(verify_api_key)):
    """
    Health check endpoint for Chrome Extension
    Verifies API key and backend connectivity
    """
    return APIResponse(
        success=True,
        message="CSV upload endpoint is healthy",
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": {
                "orders_upload": True,
                "listings_upload": True,
                "google_sheets_sync": True,
                "api_authentication": True
            }
        }
    )

@router.post("/validate", response_model=APIResponse)
async def validate_csv(
    request: CSVUploadRequest,
    api_key_valid: bool = Depends(verify_api_key)
):
    """
    Validate CSV format without processing
    Useful for testing and debugging
    """
    try:
        csv_rows = parse_csv_content(request.csv_content)
        
        if not csv_rows:
            return APIResponse(
                success=False,
                message="No data found in CSV",
                data={"valid": False, "rows": 0}
            )
        
        # Get column headers
        headers = list(csv_rows[0].keys()) if csv_rows else []
        
        # Validate based on type
        required_fields = {
            "orders": ["Order Number", "Buyer Name", "Item Title", "Total Price"],
            "listings": ["Item Number", "Title", "Current Price", "Available Quantity"]
        }
        
        missing_fields = []
        for field in required_fields.get(request.csv_type, []):
            if field not in headers:
                # Check alternative field names
                alternatives = {
                    "Item Number": ["ItemID"],
                    "Current Price": ["Price"],
                    "Available Quantity": ["Quantity Available"],
                    "Buyer Name": ["Buyer Username"]
                }
                found = False
                for alt in alternatives.get(field, []):
                    if alt in headers:
                        found = True
                        break
                if not found:
                    missing_fields.append(field)
        
        return APIResponse(
            success=len(missing_fields) == 0,
            message="CSV validation completed",
            data={
                "valid": len(missing_fields) == 0,
                "rows": len(csv_rows),
                "headers": headers,
                "missing_required_fields": missing_fields,
                "type": request.csv_type
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Validation error: {str(e)}",
            data={"valid": False, "error": str(e)}
        )