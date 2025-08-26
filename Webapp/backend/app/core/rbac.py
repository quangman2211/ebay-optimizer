"""
Role-Based Access Control (RBAC) System
Multi-role permission management for eBay Optimizer
"""

from typing import List, Dict, Optional, Set
from enum import Enum
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.database_models import User, UserRole
from app.core.security import verify_token
from jose import jwt, JWTError
from app.core.security import SECRET_KEY, ALGORITHM
import json

security = HTTPBearer()

class Permission(str, Enum):
    # Order permissions
    ORDERS_VIEW = "orders.view"
    ORDERS_IMPORT = "orders.import"
    ORDERS_ASSIGN = "orders.assign"
    ORDERS_PROCESS = "orders.process"
    ORDERS_TRACKING = "orders.tracking"
    ORDERS_TRACKING_INPUT = "orders.tracking_input"
    ORDERS_BLACKLIST = "orders.blacklist"
    ORDERS_STATUS = "orders.status"
    ORDERS_STATUS_UPDATE = "orders.status_update"
    ORDERS_SUPPLIER = "orders.supplier"
    ORDERS_BULK = "orders.bulk"
    
    # Sheets permissions
    SHEETS_SYNC = "sheets.sync"
    SHEETS_IMPORT = "sheets.import"
    SHEETS_EXPORT = "sheets.export"
    
    # Admin permissions
    ADMIN_USERS = "admin.users"
    ADMIN_ROLES = "admin.roles"
    ADMIN_BLACKLIST = "admin.blacklist"
    ADMIN_SETTINGS = "admin.settings"
    
    # Listings permissions
    LISTINGS_VIEW = "listings.view"
    LISTINGS_CREATE = "listings.create"
    LISTINGS_UPDATE = "listings.update"
    LISTINGS_DELETE = "listings.delete"
    
    # Analytics permissions
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"


class RolePermissions:
    """Default permission sets for each role"""
    
    ADMIN = [
        # Full access to everything
        Permission.ORDERS_VIEW,
        Permission.ORDERS_IMPORT,
        Permission.ORDERS_ASSIGN,
        Permission.ORDERS_PROCESS,
        Permission.ORDERS_TRACKING,
        Permission.ORDERS_TRACKING_INPUT,
        Permission.ORDERS_BLACKLIST,
        Permission.ORDERS_STATUS,
        Permission.ORDERS_STATUS_UPDATE,
        Permission.ORDERS_SUPPLIER,
        Permission.ORDERS_BULK,
        Permission.SHEETS_SYNC,
        Permission.SHEETS_IMPORT,
        Permission.SHEETS_EXPORT,
        Permission.ADMIN_USERS,
        Permission.ADMIN_ROLES,
        Permission.ADMIN_BLACKLIST,
        Permission.ADMIN_SETTINGS,
        Permission.LISTINGS_VIEW,
        Permission.LISTINGS_CREATE,
        Permission.LISTINGS_UPDATE,
        Permission.LISTINGS_DELETE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
    ]
    
    EBAY_MANAGER = [
        # Import orders, manage tracking, blacklist check
        Permission.ORDERS_VIEW,
        Permission.ORDERS_IMPORT,
        Permission.ORDERS_ASSIGN,
        Permission.ORDERS_TRACKING,
        Permission.ORDERS_BLACKLIST,
        Permission.ORDERS_STATUS,
        Permission.ORDERS_BULK,
        Permission.SHEETS_SYNC,
        Permission.SHEETS_IMPORT,
        Permission.SHEETS_EXPORT,
        Permission.ADMIN_BLACKLIST,  # Can manage blacklist
        Permission.LISTINGS_VIEW,
        Permission.LISTINGS_CREATE,
        Permission.LISTINGS_UPDATE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
    ]
    
    FULFILLMENT_STAFF = [
        # Process orders, supplier communication, tracking input
        Permission.ORDERS_VIEW,
        Permission.ORDERS_PROCESS,
        Permission.ORDERS_SUPPLIER,
        Permission.ORDERS_TRACKING_INPUT,
        Permission.ORDERS_STATUS_UPDATE,
        Permission.LISTINGS_VIEW,  # Read-only listings access
        Permission.ANALYTICS_VIEW,  # Limited analytics
    ]


class RBACService:
    """Role-Based Access Control Service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_with_role(self, user_id: int) -> Optional[User]:
        """Get user with role information"""
        return (
            self.db.query(User)
            .outerjoin(UserRole, User.role_id == UserRole.id)
            .filter(User.id == user_id)
            .first()
        )
    
    def get_user_permissions(self, user: User) -> Set[str]:
        """Get all permissions for a user"""
        if not user or not user.role:
            return set()
        
        # If user is superuser, grant all permissions
        if user.is_superuser:
            return set([perm.value for perm in Permission])
        
        # Get permissions from role
        try:
            if user.role.permissions:
                # Handle both JSON string and already parsed list
                if isinstance(user.role.permissions, str):
                    role_permissions = json.loads(user.role.permissions)
                else:
                    role_permissions = user.role.permissions
                return set(role_permissions)
            else:
                return set()
        except (json.JSONDecodeError, AttributeError, TypeError):
            return set()
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.get_user_permissions(user)
        
        # Check for wildcard permission (admin)
        if "*" in user_permissions:
            return True
            
        return permission in user_permissions
    
    def has_any_permission(self, user: User, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(user, perm) for perm in permissions)
    
    def has_all_permissions(self, user: User, permissions: List[str]) -> bool:
        """Check if user has all specified permissions"""
        return all(self.has_permission(user, perm) for perm in permissions)
    
    def can_access_order(self, user: User, order_user_id: int, assigned_user_id: Optional[int] = None) -> bool:
        """Check if user can access specific order"""
        # Admins can access everything
        if user.is_superuser or self.has_permission(user, Permission.ADMIN_USERS):
            return True
            
        # Users can access their own orders
        if order_user_id == user.id:
            return True
            
        # Users can access orders assigned to them
        if assigned_user_id == user.id:
            return True
            
        # eBay managers can access orders from their assigned accounts
        if self.has_permission(user, Permission.ORDERS_ASSIGN):
            # Check if user has access to the account that created the order
            assigned_accounts = user.assigned_accounts or []
            # This would need to be implemented based on account-order relationship
            return True
            
        return False
    
    def get_accessible_account_ids(self, user: User) -> Optional[List[int]]:
        """Get list of account IDs user can access. None means all accounts."""
        # Admins have access to all accounts
        if user.is_superuser or self.has_permission(user, Permission.ADMIN_USERS):
            return None  # None means access to all
            
        # Return assigned accounts
        return user.assigned_accounts or []


def decode_access_token(token: str):
    """Decode JWT access token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user with role information"""
    try:
        # Decode JWT token
        payload = decode_access_token(credentials.credentials)
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user with role information
    user = (
        db.query(User)
        .outerjoin(UserRole, User.role_id == UserRole.id)
        .filter(User.email == user_email)
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def require_permission(permission: str):
    """Dependency to require specific permission"""
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        rbac = RBACService(db)
        if not rbac.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permission: {permission}"
            )
        return current_user
    return permission_dependency


def require_any_permission(permissions: List[str]):
    """Dependency to require any of the specified permissions"""
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        rbac = RBACService(db)
        if not rbac.has_any_permission(current_user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required any of: {', '.join(permissions)}"
            )
        return current_user
    return permission_dependency


def require_role(role_name: str):
    """Dependency to require specific role"""
    def role_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.role or current_user.role.role_name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {role_name}"
            )
        return current_user
    return role_dependency


def get_rbac_service(db: Session = Depends(get_db)) -> RBACService:
    """Get RBAC service dependency"""
    return RBACService(db)


# Common permission dependencies for easy use
require_admin = require_role("ADMIN")
require_ebay_manager = require_any_permission([Permission.ORDERS_IMPORT, Permission.ORDERS_ASSIGN])
require_fulfillment_staff = require_any_permission([Permission.ORDERS_PROCESS, Permission.ORDERS_SUPPLIER])

# Order management permissions
require_orders_view = require_permission(Permission.ORDERS_VIEW)
require_orders_import = require_permission(Permission.ORDERS_IMPORT)
require_orders_assign = require_permission(Permission.ORDERS_ASSIGN)
require_orders_process = require_permission(Permission.ORDERS_PROCESS)

# Sheets permissions
require_sheets_sync = require_permission(Permission.SHEETS_SYNC)

# Admin permissions
require_admin_users = require_permission(Permission.ADMIN_USERS)
require_admin_blacklist = require_permission(Permission.ADMIN_BLACKLIST)