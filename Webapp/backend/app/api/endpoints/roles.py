"""
Multi-Role API Endpoints
Role management, user assignments, permissions
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from app.db.database import get_db
from app.models.database_models import (
    User, UserRole, Order, AddressBlacklist, 
    SheetsSyncLog, OrderStatusHistory
)
from app.schemas.schemas import (
    # Role management
    UserRoleCreate, UserRoleUpdate, UserRoleResponse,
    # User management
    User as UserSchema, UserUpdate,
    # Address blacklist
    AddressBlacklistCreate, AddressBlacklistUpdate, AddressBlacklistResponse,
    AddressCheckRequest, AddressCheckResponse,
    # Order assignments
    OrderAssignmentRequest, OrderAssignmentResponse,
    BulkAddressCheckRequest, BulkAddressCheckResponse,
    # Sync log
    SheetsSyncLogResponse,
    # Order status history
    OrderStatusHistoryResponse,
    # Dashboard stats
    MultiRoleDashboardStats,
    # API responses
    APIResponse, PaginatedResponse
)
from app.core.rbac import (
    get_current_user, require_admin_users, require_admin_blacklist,
    require_orders_assign, require_orders_process, require_sheets_sync,
    RBACService, Permission, RolePermissions
)
from app.core.security import get_password_hash
import json
import re
from datetime import datetime, timedelta

def parse_permissions(permissions_field):
    """Safely parse permissions field that might be JSON string or already parsed"""
    if not permissions_field:
        return []
    if isinstance(permissions_field, str):
        try:
            return json.loads(permissions_field)
        except (json.JSONDecodeError, TypeError):
            return []
    return permissions_field

router = APIRouter(tags=["Multi-Role Management"])

# ===========================================
# ROLE MANAGEMENT
# ===========================================

@router.get("/", response_model=List[UserRoleResponse])
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_users)
):
    """Get all user roles with user counts"""
    roles = (
        db.query(
            UserRole,
            func.count(User.id).label('user_count')
        )
        .outerjoin(User, User.role_id == UserRole.id)
        .group_by(UserRole.id)
        .order_by(UserRole.role_name)
        .all()
    )
    
    result = []
    for role, user_count in roles:
        # Handle permissions parsing
        permissions = parse_permissions(role.permissions)
        
        role_dict = {
            "id": role.id,
            "role_name": role.role_name,
            "description": role.description,
            "permissions": permissions,
            "created_at": role.created_at,
            "user_count": user_count or 0
        }
        result.append(UserRoleResponse(**role_dict))
    
    return result


@router.post("/", response_model=UserRoleResponse)
async def create_role(
    role_data: UserRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_users)
):
    """Create new user role"""
    # Check if role already exists
    existing_role = db.query(UserRole).filter(UserRole.role_name == role_data.role_name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_data.role_name}' already exists"
        )
    
    role = UserRole(
        role_name=role_data.role_name,
        description=role_data.description,
        permissions=json.dumps(role_data.permissions) if role_data.permissions else None
    )
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return UserRoleResponse(
        id=role.id,
        role_name=role.role_name,
        description=role.description,
        permissions=parse_permissions(role.permissions),
        created_at=role.created_at,
        user_count=0
    )


@router.put("/{role_id}", response_model=UserRoleResponse)
async def update_role(
    role_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_users)
):
    """Update user role"""
    role = db.query(UserRole).filter(UserRole.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Update fields
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.permissions is not None:
        role.permissions = json.dumps(role_data.permissions)
    
    db.commit()
    db.refresh(role)
    
    # Get user count
    user_count = db.query(func.count(User.id)).filter(User.role_id == role_id).scalar() or 0
    
    return UserRoleResponse(
        id=role.id,
        role_name=role.role_name,
        description=role.description,
        permissions=parse_permissions(role.permissions),
        created_at=role.created_at,
        user_count=user_count
    )


@router.get("/permissions", response_model=Dict[str, List[str]])
async def get_available_permissions(
    current_user: User = Depends(require_admin_users)
):
    """Get all available permissions grouped by category"""
    permissions = {
        "orders": [p.value for p in Permission if p.value.startswith("orders.")],
        "sheets": [p.value for p in Permission if p.value.startswith("sheets.")],
        "admin": [p.value for p in Permission if p.value.startswith("admin.")],
        "listings": [p.value for p in Permission if p.value.startswith("listings.")],
        "analytics": [p.value for p in Permission if p.value.startswith("analytics.")]
    }
    return permissions


@router.get("/default-permissions", response_model=Dict[str, List[str]])
async def get_default_role_permissions(
    current_user: User = Depends(require_admin_users)
):
    """Get default permission sets for each role"""
    return {
        "ADMIN": [p.value for p in RolePermissions.ADMIN],
        "EBAY_MANAGER": [p.value for p in RolePermissions.EBAY_MANAGER],
        "FULFILLMENT_STAFF": [p.value for p in RolePermissions.FULFILLMENT_STAFF]
    }


# ===========================================
# USER MANAGEMENT
# ===========================================

@router.get("/users", response_model=List[UserSchema])
async def get_users_with_roles(
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_users)
):
    """Get all users with role information"""
    query = (
        db.query(User)
        .outerjoin(UserRole, User.role_id == UserRole.id)
    )
    
    # Apply filters
    if role_id is not None:
        query = query.filter(User.role_id == role_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.order_by(User.created_at.desc()).all()
    
    result = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "role_id": user.role_id,
            "assigned_accounts": user.assigned_accounts,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "role_name": user.role.role_name if user.role else None,
            "permissions": parse_permissions(user.role.permissions if user.role else None)
        }
        result.append(UserSchema(**user_dict))
    
    return result


@router.put("/users/{user_id}/role", response_model=UserSchema)
async def assign_user_role(
    user_id: int,
    role_id: int,
    assigned_accounts: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_users)
):
    """Assign role to user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify role exists
    role = db.query(UserRole).filter(UserRole.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Update user
    user.role_id = role_id
    if assigned_accounts is not None:
        user.assigned_accounts = assigned_accounts
    
    db.commit()
    db.refresh(user)
    
    return UserSchema(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role_id=user.role_id,
        assigned_accounts=user.assigned_accounts,
        created_at=user.created_at,
        updated_at=user.updated_at,
        role_name=user.role.role_name if user.role else None,
        permissions=parse_permissions(user.role.permissions if user.role else None)
    )


# ===========================================
# ADDRESS BLACKLIST MANAGEMENT
# ===========================================

@router.get("/blacklist", response_model=List[AddressBlacklistResponse])
async def get_address_blacklist(
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_blacklist)
):
    """Get address blacklist entries"""
    query = (
        db.query(AddressBlacklist)
        .outerjoin(User, AddressBlacklist.created_by == User.id)
    )
    
    if is_active is not None:
        query = query.filter(AddressBlacklist.is_active == is_active)
    if risk_level:
        query = query.filter(AddressBlacklist.risk_level == risk_level)
    
    entries = query.order_by(desc(AddressBlacklist.created_at)).all()
    
    result = []
    for entry in entries:
        entry_dict = {
            "id": entry.id,
            "address_pattern": entry.address_pattern,
            "match_type": entry.match_type,
            "risk_level": entry.risk_level,
            "reason": entry.reason,
            "created_by": entry.created_by,
            "created_by_user_name": entry.created_by_user.full_name if entry.created_by_user else None,
            "created_at": entry.created_at,
            "is_active": entry.is_active
        }
        result.append(AddressBlacklistResponse(**entry_dict))
    
    return result


@router.post("/blacklist", response_model=AddressBlacklistResponse)
async def create_blacklist_entry(
    entry_data: AddressBlacklistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_blacklist)
):
    """Create new blacklist entry"""
    entry = AddressBlacklist(
        address_pattern=entry_data.address_pattern,
        match_type=entry_data.match_type,
        risk_level=entry_data.risk_level,
        reason=entry_data.reason,
        is_active=entry_data.is_active,
        created_by=current_user.id
    )
    
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    return AddressBlacklistResponse(
        id=entry.id,
        address_pattern=entry.address_pattern,
        match_type=entry.match_type,
        risk_level=entry.risk_level,
        reason=entry.reason,
        created_by=entry.created_by,
        created_by_user_name=current_user.full_name,
        created_at=entry.created_at,
        is_active=entry.is_active
    )


@router.post("/blacklist/check", response_model=AddressCheckResponse)
async def check_address(
    request: AddressCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_blacklist)
):
    """Check address against blacklist"""
    blacklist_entries = (
        db.query(AddressBlacklist)
        .filter(AddressBlacklist.is_active == True)
        .all()
    )
    
    matched_patterns = []
    highest_risk = "low"
    risk_levels = {"low": 1, "medium": 2, "high": 3, "blocked": 4}
    
    for entry in blacklist_entries:
        is_match = False
        
        if entry.match_type == "exact":
            is_match = entry.address_pattern.lower() == request.address.lower()
        elif entry.match_type == "contains":
            is_match = entry.address_pattern.lower() in request.address.lower()
        elif entry.match_type == "regex":
            try:
                is_match = bool(re.search(entry.address_pattern, request.address, re.IGNORECASE))
            except re.error:
                continue  # Skip invalid regex patterns
        
        if is_match:
            matched_patterns.append({
                "pattern": entry.address_pattern,
                "match_type": entry.match_type,
                "risk_level": entry.risk_level,
                "reason": entry.reason or "No reason provided"
            })
            
            if risk_levels[entry.risk_level] > risk_levels[highest_risk]:
                highest_risk = entry.risk_level
    
    is_safe = highest_risk in ["low", "medium"]
    
    if highest_risk == "blocked":
        recommendation = "BLOCK - Do not process this order"
    elif highest_risk == "high":
        recommendation = "CAUTION - Manual review required"
    elif highest_risk == "medium":
        recommendation = "REVIEW - Verify with customer"
    else:
        recommendation = "SAFE - Proceed normally"
    
    return AddressCheckResponse(
        is_safe=is_safe,
        risk_level=highest_risk,
        matched_patterns=matched_patterns,
        recommendation=recommendation
    )


# ===========================================
# ORDER ASSIGNMENT & MANAGEMENT
# ===========================================

@router.post("/orders/assign", response_model=OrderAssignmentResponse)
async def assign_orders(
    request: OrderAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_orders_assign)
):
    """Assign orders to fulfillment staff"""
    # Verify target user exists and has appropriate role
    target_user = db.query(User).filter(User.id == request.assigned_to_user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found"
        )
    
    rbac = RBACService(db)
    if not rbac.has_permission(target_user, Permission.ORDERS_PROCESS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target user does not have order processing permissions"
        )
    
    successful_assignments = 0
    failed_assignments = 0
    assignment_details = []
    
    for order_id in request.order_ids:
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                assignment_details.append({
                    "order_id": order_id,
                    "success": False,
                    "message": "Order not found"
                })
                failed_assignments += 1
                continue
            
            # Check if user can access this order
            if not rbac.can_access_order(current_user, order.user_id, order.assigned_to_user_id):
                assignment_details.append({
                    "order_id": order_id,
                    "success": False,
                    "message": "Access denied to this order"
                })
                failed_assignments += 1
                continue
            
            # Assign order
            order.assigned_to_user_id = request.assigned_to_user_id
            order.assigned_by_user_id = current_user.id
            order.assignment_date = datetime.utcnow()
            
            # Create status history entry
            status_history = OrderStatusHistory(
                order_id=order_id,
                old_status=order.status,
                new_status=order.status,  # Status doesn't change, just assignment
                changed_by=current_user.id,
                change_reason=f"Assigned to {target_user.full_name or target_user.email}",
                additional_data={"assignment_reason": request.assignment_reason}
            )
            db.add(status_history)
            
            assignment_details.append({
                "order_id": order_id,
                "success": True,
                "message": f"Assigned to {target_user.full_name or target_user.email}"
            })
            successful_assignments += 1
            
        except Exception as e:
            assignment_details.append({
                "order_id": order_id,
                "success": False,
                "message": f"Error: {str(e)}"
            })
            failed_assignments += 1
    
    db.commit()
    
    return OrderAssignmentResponse(
        successful_assignments=successful_assignments,
        failed_assignments=failed_assignments,
        assignment_details=assignment_details
    )


@router.post("/orders/bulk-blacklist-check", response_model=BulkAddressCheckResponse)
async def bulk_check_addresses(
    request: BulkAddressCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_blacklist)
):
    """Bulk check addresses against blacklist and optionally assign safe orders"""
    orders = db.query(Order).filter(Order.id.in_(request.order_ids)).all()
    
    total_checked = 0
    safe_orders = 0
    flagged_orders = 0
    blocked_orders = 0
    assignments_made = 0
    order_results = []
    
    for order in orders:
        if not order.shipping_address:
            continue
        
        total_checked += 1
        
        # Check address
        check_result = await check_address(
            AddressCheckRequest(address=order.shipping_address),
            db, current_user
        )
        
        # Update order blacklist status
        order.blacklist_checked = True
        order.blacklist_status = check_result.risk_level
        if check_result.matched_patterns:
            order.blacklist_reason = "; ".join([p["reason"] for p in check_result.matched_patterns])
        
        # Count by risk level
        if check_result.risk_level == "blocked":
            blocked_orders += 1
        elif check_result.risk_level in ["high", "medium"]:
            flagged_orders += 1
        else:
            safe_orders += 1
            
            # Auto-assign safe orders if requested
            if request.auto_assign_safe and request.target_user_id:
                order.assigned_to_user_id = request.target_user_id
                order.assigned_by_user_id = current_user.id
                order.assignment_date = datetime.utcnow()
                assignments_made += 1
        
        order_results.append({
            "order_id": order.id,
            "is_safe": check_result.is_safe,
            "risk_level": check_result.risk_level,
            "recommendation": check_result.recommendation,
            "matched_patterns": [p["pattern"] for p in check_result.matched_patterns],
            "assigned": request.auto_assign_safe and request.target_user_id and check_result.is_safe
        })
    
    db.commit()
    
    return BulkAddressCheckResponse(
        total_checked=total_checked,
        safe_orders=safe_orders,
        flagged_orders=flagged_orders,
        blocked_orders=blocked_orders,
        assignments_made=assignments_made,
        order_results=order_results
    )


# ===========================================
# DASHBOARD & ANALYTICS
# ===========================================

@router.get("/dashboard", response_model=MultiRoleDashboardStats)
async def get_multi_role_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for multi-role system"""
    rbac = RBACService(db)
    
    # Base query for orders user can access
    orders_query = db.query(Order)
    
    # Filter by user's access level
    accessible_account_ids = rbac.get_accessible_account_ids(current_user)
    if accessible_account_ids is not None:  # None means access to all
        orders_query = orders_query.filter(Order.account_id.in_(accessible_account_ids))
    
    # Order status counts
    status_counts = (
        orders_query
        .group_by(Order.status)
        .with_entities(Order.status, func.count(Order.id))
        .all()
    )
    
    status_dict = dict(status_counts)
    
    # Assignment statistics
    unassigned_orders = orders_query.filter(Order.assigned_to_user_id.is_(None)).count()
    my_assigned_orders = orders_query.filter(Order.assigned_to_user_id == current_user.id).count()
    
    # Overdue assignments (orders assigned > 48 hours ago without status update)
    overdue_cutoff = datetime.utcnow() - timedelta(hours=48)
    overdue_assignments = (
        orders_query
        .filter(
            and_(
                Order.assigned_to_user_id.isnot(None),
                Order.assignment_date < overdue_cutoff,
                Order.status.in_(["pending", "processing"])
            )
        )
        .count()
    )
    
    # Blacklist statistics
    pending_blacklist_check = orders_query.filter(Order.blacklist_checked == False).count()
    flagged_addresses = orders_query.filter(Order.blacklist_status.in_(["medium", "high"])).count()
    blocked_addresses = orders_query.filter(Order.blacklist_status == "blocked").count()
    
    # Revenue calculations
    revenue_data = (
        orders_query
        .filter(Order.price_ebay.isnot(None))
        .with_entities(
            func.sum(Order.price_ebay).label('total_revenue'),
            func.sum(
                func.case(
                    [(Order.order_date >= datetime.utcnow() - timedelta(days=30), Order.price_ebay)],
                    else_=0
                )
            ).label('monthly_revenue')
        )
        .first()
    )
    
    # Average fulfillment time
    avg_fulfillment = (
        orders_query
        .filter(
            and_(
                Order.assignment_date.isnot(None),
                Order.actual_ship_date.isnot(None)
            )
        )
        .with_entities(
            func.avg(
                func.julianday(Order.actual_ship_date) - func.julianday(Order.assignment_date)
            ).label('avg_days')
        )
        .scalar()
    )
    
    # Google Sheets sync status
    last_sync_log = (
        db.query(SheetsSyncLog)
        .order_by(desc(SheetsSyncLog.started_at))
        .first()
    )
    
    sync_errors = (
        db.query(func.count(SheetsSyncLog.id))
        .filter(
            and_(
                SheetsSyncLog.status == "failed",
                SheetsSyncLog.started_at >= datetime.utcnow() - timedelta(hours=24)
            )
        )
        .scalar() or 0
    )
    
    return MultiRoleDashboardStats(
        total_orders=sum(status_dict.values()),
        pending_orders=status_dict.get("pending", 0),
        assigned_orders=orders_query.filter(Order.assigned_to_user_id.isnot(None)).count(),
        in_fulfillment=status_dict.get("processing", 0),
        shipped_orders=status_dict.get("shipped", 0),
        
        unassigned_orders=unassigned_orders,
        my_assigned_orders=my_assigned_orders,
        overdue_assignments=overdue_assignments,
        
        pending_blacklist_check=pending_blacklist_check,
        flagged_addresses=flagged_addresses,
        blocked_addresses=blocked_addresses,
        
        total_revenue=float(revenue_data.total_revenue or 0),
        monthly_revenue=float(revenue_data.monthly_revenue or 0),
        average_fulfillment_time=float(avg_fulfillment * 24) if avg_fulfillment else None,  # Convert to hours
        
        last_sync=last_sync_log.started_at if last_sync_log else None,
        sync_pending=last_sync_log.status == "running" if last_sync_log else False,
        sync_errors=sync_errors
    )


# ===========================================
# SYNC LOG MANAGEMENT
# ===========================================

@router.get("/sync-logs", response_model=List[SheetsSyncLogResponse])
async def get_sync_logs(
    limit: int = Query(20, ge=1, le=100, description="Number of logs to return"),
    sync_type: Optional[str] = Query(None, description="Filter by sync type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sheets_sync)
):
    """Get Google Sheets sync logs"""
    query = (
        db.query(SheetsSyncLog)
        .outerjoin(User, SheetsSyncLog.started_by == User.id)
        .order_by(desc(SheetsSyncLog.started_at))
        .limit(limit)
    )
    
    if sync_type:
        query = query.filter(SheetsSyncLog.sync_type == sync_type)
    
    logs = query.all()
    
    result = []
    for log in logs:
        duration_seconds = None
        if log.completed_at and log.started_at:
            duration_seconds = int((log.completed_at - log.started_at).total_seconds())
        
        log_dict = {
            "id": log.id,
            "sync_type": log.sync_type,
            "spreadsheet_id": log.spreadsheet_id,
            "sheet_name": log.sheet_name,
            "rows_processed": log.rows_processed,
            "rows_success": log.rows_success,
            "rows_error": log.rows_error,
            "error_details": log.error_details,
            "started_by": log.started_by,
            "started_by_user_name": log.started_by_user.full_name if log.started_by_user else None,
            "started_at": log.started_at,
            "completed_at": log.completed_at,
            "status": log.status,
            "duration_seconds": duration_seconds
        }
        result.append(SheetsSyncLogResponse(**log_dict))
    
    return result