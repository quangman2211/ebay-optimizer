"""
Chrome Extension Integration API Endpoints
Kết nối Chrome Extension với eBay Optimizer Webapp
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.database_models import User, Account, Order, Listing, Message
from app.repositories.account import account_repo
from app.repositories.order import order_repo
from app.repositories.listing import listing_repo
from app.schemas.schemas import APIResponse

router = APIRouter(prefix="/extension", tags=["Chrome Extension"])

# Pydantic models for extension data
class ExtensionOrderData(BaseModel):
    orderId: str = Field(..., description="Order ID từ eBay")
    buyer: str = Field(..., description="Tên buyer")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Danh sách items")
    total: str = Field(..., description="Tổng tiền order")
    status: str = Field(..., description="Trạng thái order")
    date: str = Field(..., description="Ngày tạo order")
    shipping: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Thông tin shipping")

class ExtensionListingData(BaseModel):
    itemId: str = Field(..., description="Item ID từ eBay")
    title: str = Field(..., description="Tiêu đề listing")
    sku: Optional[str] = Field(default="", description="SKU code")
    price: str = Field(default="0", description="Giá bán")
    quantity: str = Field(default="0", description="Số lượng")
    views: str = Field(default="0", description="Lượt xem")
    watchers: str = Field(default="0", description="Người theo dõi")
    category: Optional[str] = Field(default="", description="Danh mục")
    condition: Optional[str] = Field(default="", description="Tình trạng")
    status: str = Field(default="active", description="Trạng thái listing")

class ExtensionCollectRequest(BaseModel):
    account_id: int = Field(..., description="ID account eBay")
    orders_data: Optional[List[ExtensionOrderData]] = None
    listings_data: Optional[List[ExtensionListingData]] = None

class AutomationTask(BaseModel):
    task_id: str
    account_ids: List[int]
    status: str  # pending, running, completed, error
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = Field(default_factory=dict)

# In-memory storage for automation tasks (in production, use Redis)
automation_tasks: Dict[str, AutomationTask] = {}


@router.post("/collect/orders")
async def collect_orders_from_extension(
    request: ExtensionCollectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Nhận dữ liệu orders từ Chrome Extension
    """
    try:
        if not request.orders_data:
            raise HTTPException(status_code=400, detail="No orders data provided")
        
        # Verify account ownership
        account = account_repo.get(db, id=request.account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Account not found or not authorized")
        
        processed_orders = []
        skipped_orders = []
        
        for order_data in request.orders_data:
            try:
                # Check for existing order
                existing_order = order_repo.get_by_order_id(
                    db, 
                    order_id=order_data.orderId,
                    user_id=current_user.id
                )
                
                if existing_order:
                    skipped_orders.append(order_data.orderId)
                    continue
                
                # Parse và validate order data
                total_amount = parse_amount(order_data.total)
                order_date = parse_date(order_data.date)
                
                # Create new order
                new_order_data = {
                    "user_id": current_user.id,
                    "account_id": request.account_id,
                    "order_number": order_data.orderId,
                    "customer_name": order_data.buyer,
                    "item_title": ", ".join([item.get("title", "") for item in order_data.items]),
                    "price_ebay": total_amount,
                    "status": map_order_status(order_data.status),
                    "created_at": order_date or datetime.utcnow(),
                    "tracking_number": "",
                    "shipping_info": json.dumps(order_data.shipping) if order_data.shipping else ""
                }
                
                new_order = order_repo.create_from_dict(db, obj_in=new_order_data)
                processed_orders.append(new_order.order_number)
                
            except Exception as e:
                print(f"Error processing order {order_data.orderId}: {str(e)}")
                skipped_orders.append(order_data.orderId)
                continue
        
        return APIResponse(
            success=True,
            message=f"Orders processed: {len(processed_orders)} new, {len(skipped_orders)} skipped",
            data={
                "orders_processed": len(processed_orders),
                "orders_skipped": len(skipped_orders),
                "processed_ids": processed_orders,
                "skipped_ids": skipped_orders,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing orders: {str(e)}")


@router.post("/collect/listings")
async def collect_listings_from_extension(
    request: ExtensionCollectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Nhận dữ liệu listings từ Chrome Extension
    """
    try:
        if not request.listings_data:
            raise HTTPException(status_code=400, detail="No listings data provided")
        
        # Verify account ownership
        account = account_repo.get(db, id=request.account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Account not found or not authorized")
        
        processed_listings = []
        updated_listings = []
        
        for listing_data in request.listings_data:
            try:
                # Check if listing exists
                existing_listing = listing_repo.get_by_item_id(
                    db, 
                    item_id=listing_data.itemId,
                    user_id=current_user.id
                )
                
                # Parse listing data
                price = parse_amount(listing_data.price)
                quantity = int(listing_data.quantity) if listing_data.quantity.isdigit() else 0
                views = int(listing_data.views) if listing_data.views.isdigit() else 0
                watchers = int(listing_data.watchers) if listing_data.watchers.isdigit() else 0
                
                listing_dict = {
                    "user_id": current_user.id,
                    "account_id": request.account_id,
                    "item_id": listing_data.itemId,
                    "title": listing_data.title,
                    "sku": listing_data.sku or "",
                    "price": price,
                    "quantity": quantity,
                    "views": views,
                    "watchers": watchers,
                    "category": listing_data.category or "",
                    "condition": listing_data.condition or "",
                    "status": map_listing_status(listing_data.status),
                    "updated_at": datetime.utcnow()
                }
                
                if existing_listing:
                    # Update existing listing
                    updated_listing = listing_repo.update_from_dict(
                        db, 
                        db_obj=existing_listing,
                        obj_in=listing_dict
                    )
                    updated_listings.append(updated_listing.item_id)
                else:
                    # Create new listing
                    listing_dict["created_at"] = datetime.utcnow()
                    new_listing = listing_repo.create_from_dict(db, obj_in=listing_dict)
                    processed_listings.append(new_listing.item_id)
                    
            except Exception as e:
                print(f"Error processing listing {listing_data.itemId}: {str(e)}")
                continue
        
        return APIResponse(
            success=True,
            message=f"Listings processed: {len(processed_listings)} new, {len(updated_listings)} updated",
            data={
                "listings_created": len(processed_listings),
                "listings_updated": len(updated_listings),
                "created_ids": processed_listings,
                "updated_ids": updated_listings,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing listings: {str(e)}")


@router.get("/accounts/{account_id}/sync-status")
async def get_sync_status(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy trạng thái sync cho account
    """
    try:
        # Verify account ownership
        account = account_repo.get(db, id=account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Get counts
        orders_count = order_repo.count_by_account(db, account_id=account_id, user_id=current_user.id)
        listings_count = listing_repo.count_by_account(db, account_id=account_id, user_id=current_user.id)
        
        # Get latest activity
        latest_order = order_repo.get_latest_by_account(db, account_id=account_id, user_id=current_user.id)
        latest_listing = listing_repo.get_latest_by_account(db, account_id=account_id, user_id=current_user.id)
        
        last_sync = None
        if latest_order and latest_listing:
            last_sync = max(latest_order.updated_at, latest_listing.updated_at)
        elif latest_order:
            last_sync = latest_order.updated_at
        elif latest_listing:
            last_sync = latest_listing.updated_at
        
        return APIResponse(
            success=True,
            data={
                "account_id": account_id,
                "account_name": account.ebay_username,
                "last_sync": last_sync.isoformat() if last_sync else None,
                "sync_status": "completed" if last_sync else "never",
                "orders_count": orders_count,
                "listings_count": listings_count,
                "messages_count": 0,  # TODO: implement when messages table exists
                "health_score": account.health_score or 0,
                "is_active": account.status == "active"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {str(e)}")


@router.post("/automation/start")
async def start_automation(
    account_ids: Optional[List[int]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger automation cho Chrome Extension
    """
    try:
        if account_ids is None:
            # Get all active accounts for user
            active_accounts = account_repo.get_active_accounts(
                db, 
                user_id=current_user.id,
                skip=0,
                limit=100
            )
            account_ids = [acc.id for acc in active_accounts["items"]]
        
        if not account_ids:
            return APIResponse(
                success=False,
                message="No accounts available for automation"
            )
        
        # Validate account ownership
        for account_id in account_ids:
            account = account_repo.get(db, id=account_id)
            if not account or account.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Not authorized to automate account {account_id}"
                )
        
        # Create automation task
        task_id = str(uuid.uuid4())
        task = AutomationTask(
            task_id=task_id,
            account_ids=account_ids,
            status="pending",
            started_at=datetime.utcnow()
        )
        
        # Store task
        automation_tasks[task_id] = task
        
        # Start background task
        background_tasks.add_task(process_automation_task, task_id, db)
        
        return APIResponse(
            success=True,
            message=f"Automation started for {len(account_ids)} accounts",
            data={
                "task_id": task_id,
                "accounts_queued": len(account_ids),
                "estimated_duration": f"{len(account_ids) * 2} minutes",
                "status": "pending"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting automation: {str(e)}")


@router.get("/automation/status/{task_id}")
async def get_automation_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Lấy trạng thái automation task
    """
    try:
        task = automation_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return APIResponse(
            success=True,
            data={
                "task_id": task_id,
                "status": task.status,
                "started_at": task.started_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "accounts_total": len(task.account_ids),
                "accounts_processed": task.results.get("processed", 0),
                "results": task.results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")


@router.get("/health")
async def extension_health():
    """
    Health check endpoint for Chrome Extension
    """
    return APIResponse(
        success=True,
        message="Extension API is healthy",
        data={
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "status": "active"
        }
    )


# Helper functions
def parse_amount(amount_str: str) -> float:
    """Parse amount string to float"""
    if not amount_str:
        return 0.0
    
    # Remove currency symbols and spaces
    clean_amount = amount_str.replace("$", "").replace(",", "").replace(" ", "")
    
    try:
        return float(clean_amount)
    except (ValueError, TypeError):
        return 0.0


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime"""
    if not date_str:
        return None
    
    try:
        # Try different date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None


def map_order_status(ebay_status: str) -> str:
    """Map eBay status to internal status"""
    status_map = {
        "pending": "pending",
        "processing": "processing", 
        "shipped": "shipped",
        "delivered": "delivered",
        "cancelled": "cancelled",
        "completed": "delivered"
    }
    return status_map.get(ebay_status.lower(), "pending")


def map_listing_status(ebay_status: str) -> str:
    """Map eBay listing status to internal status"""
    status_map = {
        "active": "active",
        "inactive": "inactive",
        "ended": "inactive",
        "sold": "sold",
        "draft": "draft"
    }
    return status_map.get(ebay_status.lower(), "active")


async def process_automation_task(task_id: str, db: Session):
    """Background task to process automation"""
    try:
        task = automation_tasks.get(task_id)
        if not task:
            return
        
        task.status = "running"
        task.results = {"processed": 0, "errors": []}
        
        # Simulate processing each account
        for i, account_id in enumerate(task.account_ids):
            try:
                # In real implementation, this would trigger the extension
                # For now, just mark as processed
                task.results["processed"] = i + 1
                
                # Simulate processing time
                await asyncio.sleep(1)
                
            except Exception as e:
                task.results["errors"].append({
                    "account_id": account_id,
                    "error": str(e)
                })
        
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        
    except Exception as e:
        task.status = "error"
        task.completed_at = datetime.utcnow()
        task.results["error"] = str(e)

import asyncio  # Add this import at the top