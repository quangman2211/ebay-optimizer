"""
Enhanced Authentication & Authorization Module
Supports multi-role system with comprehensive permission management
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.db.database import get_db
from app.models.database_models import User, UserRole
from app.core.config import settings

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY or "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30


# ===========================================
# PASSWORD UTILITIES
# ===========================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


# ===========================================
# JWT TOKEN UTILITIES
# ===========================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except JWTError:
        return None


# ===========================================
# USER AUTHENTICATION
# ===========================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


# ===========================================
# AUTHENTICATION DEPENDENCIES
# ===========================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (wrapper for compatibility)"""
    return current_user


# ===========================================
# ROLE-BASED AUTHORIZATION
# ===========================================

def require_role(allowed_roles: List[str]):
    """
    Create a dependency that requires specific roles
    
    Usage:
    @router.get("/admin-only")
    async def admin_endpoint(
        current_user: User = Depends(require_role(["ADMIN"]))
    ):
    """
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        # Get user role information
        user_role = None
        if current_user.role_id:
            user_role = db.query(UserRole).filter(UserRole.id == current_user.role_id).first()
        
        # Check for superuser override
        if current_user.is_superuser:
            return current_user
        
        # Check role permissions
        if not user_role or user_role.role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return role_dependency


def require_permission(required_permissions: List[str]):
    """
    Create a dependency that requires specific permissions
    
    Usage:
    @router.get("/manage-products")
    async def product_endpoint(
        current_user: User = Depends(require_permission(["manage_products", "view_products"]))
    ):
    """
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Check for superuser override
        if current_user.is_superuser:
            return current_user
        
        # Get user role and permissions
        if not current_user.role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned role"
            )
        
        user_role = db.query(UserRole).filter(UserRole.id == current_user.role_id).first()
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role"
            )
        
        # Parse role permissions
        user_permissions = user_role.permissions or []
        if isinstance(user_permissions, str):
            import json
            try:
                user_permissions = json.loads(user_permissions)
            except:
                user_permissions = []
        
        # Check if user has any of the required permissions
        has_permission = any(perm in user_permissions for perm in required_permissions)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permissions: {', '.join(required_permissions)}"
            )
        
        return current_user
    
    return permission_dependency


# ===========================================
# ADMIN UTILITIES
# ===========================================

def require_admin():
    """Shortcut for admin-only endpoints"""
    return require_role(["ADMIN"])


def require_manager_or_admin():
    """Shortcut for manager or admin access"""
    return require_role(["ADMIN", "EBAY_MANAGER"])


def require_any_staff():
    """Allow any authenticated staff member"""
    return require_role(["ADMIN", "EBAY_MANAGER", "FULFILLMENT_STAFF"])


# ===========================================
# PERMISSION CONSTANTS
# ===========================================

class Permissions:
    """Standard permission constants"""
    
    # User Management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # Supplier Management
    MANAGE_SUPPLIERS = "manage_suppliers"
    VIEW_SUPPLIERS = "view_suppliers"
    
    # Product Management
    MANAGE_PRODUCTS = "manage_products"
    VIEW_PRODUCTS = "view_products"
    UPDATE_INVENTORY = "update_inventory"
    
    # Order Management
    MANAGE_ORDERS = "manage_orders"
    VIEW_ORDERS = "view_orders"
    ASSIGN_ORDERS = "assign_orders"
    UPDATE_ORDER_STATUS = "update_order_status"
    
    # Pricing Management
    MANAGE_PRICING = "manage_pricing"
    VIEW_PRICING = "view_pricing"
    OPTIMIZE_PRICES = "optimize_prices"
    
    # Analytics & Reports
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    
    # System Administration
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_ROLES = "manage_roles"
    SYSTEM_ADMIN = "system_admin"


# ===========================================
# ROLE PERMISSION MAPPINGS
# ===========================================

ROLE_PERMISSIONS = {
    "ADMIN": [
        # Full access to everything
        Permissions.MANAGE_USERS,
        Permissions.VIEW_USERS,
        Permissions.MANAGE_SUPPLIERS,
        Permissions.VIEW_SUPPLIERS,
        Permissions.MANAGE_PRODUCTS,
        Permissions.VIEW_PRODUCTS,
        Permissions.UPDATE_INVENTORY,
        Permissions.MANAGE_ORDERS,
        Permissions.VIEW_ORDERS,
        Permissions.ASSIGN_ORDERS,
        Permissions.UPDATE_ORDER_STATUS,
        Permissions.MANAGE_PRICING,
        Permissions.VIEW_PRICING,
        Permissions.OPTIMIZE_PRICES,
        Permissions.VIEW_ANALYTICS,
        Permissions.EXPORT_DATA,
        Permissions.MANAGE_SETTINGS,
        Permissions.MANAGE_ROLES,
        Permissions.SYSTEM_ADMIN,
    ],
    
    "EBAY_MANAGER": [
        # Product and supplier management
        Permissions.VIEW_USERS,
        Permissions.MANAGE_SUPPLIERS,
        Permissions.VIEW_SUPPLIERS,
        Permissions.MANAGE_PRODUCTS,
        Permissions.VIEW_PRODUCTS,
        Permissions.UPDATE_INVENTORY,
        Permissions.MANAGE_ORDERS,
        Permissions.VIEW_ORDERS,
        Permissions.ASSIGN_ORDERS,
        Permissions.UPDATE_ORDER_STATUS,
        Permissions.MANAGE_PRICING,
        Permissions.VIEW_PRICING,
        Permissions.OPTIMIZE_PRICES,
        Permissions.VIEW_ANALYTICS,
        Permissions.EXPORT_DATA,
    ],
    
    "FULFILLMENT_STAFF": [
        # Order fulfillment focus
        Permissions.VIEW_SUPPLIERS,
        Permissions.VIEW_PRODUCTS,
        Permissions.UPDATE_INVENTORY,
        Permissions.VIEW_ORDERS,
        Permissions.UPDATE_ORDER_STATUS,
        Permissions.VIEW_PRICING,
        Permissions.VIEW_ANALYTICS,
    ]
}


# ===========================================
# UTILITY FUNCTIONS
# ===========================================

def get_user_permissions(user: User, db: Session) -> List[str]:
    """Get all permissions for a user"""
    if user.is_superuser:
        return list(ROLE_PERMISSIONS["ADMIN"])
    
    if not user.role_id:
        return []
    
    user_role = db.query(UserRole).filter(UserRole.id == user.role_id).first()
    if not user_role:
        return []
    
    # Return permissions from role or default for role name
    if user_role.permissions:
        if isinstance(user_role.permissions, str):
            import json
            try:
                return json.loads(user_role.permissions)
            except:
                return ROLE_PERMISSIONS.get(user_role.role_name, [])
        return user_role.permissions
    
    return ROLE_PERMISSIONS.get(user_role.role_name, [])


def check_user_permission(user: User, permission: str, db: Session) -> bool:
    """Check if user has specific permission"""
    if user.is_superuser:
        return True
    
    user_permissions = get_user_permissions(user, db)
    return permission in user_permissions


def create_user_with_role(
    db: Session,
    email: str,
    password: str,
    role_name: str,
    full_name: Optional[str] = None,
    username: Optional[str] = None
) -> User:
    """Create a new user with specified role"""
    
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise ValueError("User with this email already exists")
    
    # Get or create role
    role = db.query(UserRole).filter(UserRole.role_name == role_name).first()
    if not role:
        # Create role with default permissions
        role = UserRole(
            role_name=role_name,
            description=f"Auto-created role for {role_name}",
            permissions=ROLE_PERMISSIONS.get(role_name, [])
        )
        db.add(role)
        db.commit()
        db.refresh(role)
    
    # Create user
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        username=username or email.split("@")[0],
        full_name=full_name,
        hashed_password=hashed_password,
        role_id=role.id,
        is_active=True,
        is_superuser=(role_name == "ADMIN")
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user