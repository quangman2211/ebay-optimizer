"""
Pydantic Schemas cho API validation và responses
Tương ứng với SQLAlchemy database models
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# Enums for API
class ListingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    OPTIMIZED = "optimized"
    ARCHIVED = "archived"
    PENDING = "pending"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LIMITED = "limited"
    INACTIVE = "inactive"


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EBAY_MANAGER = "EBAY_MANAGER"
    FULFILLMENT_STAFF = "FULFILLMENT_STAFF"


class BlacklistStatus(str, Enum):
    PENDING = "pending"
    CLEAN = "clean"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


class SyncSource(str, Enum):
    MANUAL = "manual"
    GOOGLE_SHEETS = "google_sheets"
    API = "api"
    EXISTING = "existing"


class SourceStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SYNCING = "syncing"


# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    role_id: Optional[int] = None
    assigned_accounts: Optional[List[int]] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    role_name: Optional[str] = None  # From joined UserRole table
    permissions: Optional[List[str]] = None  # From role permissions
    
    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


# Listing Schemas
class ListingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=4000)
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    keywords: Optional[List[str]] = []
    item_specifics: Optional[Dict[str, str]] = {}
    item_id: Optional[str] = None
    sku: Optional[str] = None
    condition: Optional[str] = None


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=4000)
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    keywords: Optional[List[str]] = None
    item_specifics: Optional[Dict[str, str]] = None
    status: Optional[ListingStatus] = None
    item_id: Optional[str] = None
    sku: Optional[str] = None
    condition: Optional[str] = None


class Listing(ListingBase):
    id: str
    user_id: int
    status: ListingStatus
    views: int = 0
    watchers: int = 0
    sold: int = 0
    performance_score: Optional[float] = None
    original_title: Optional[str] = None
    optimized_title: Optional[str] = None
    seo_score: Optional[float] = None
    optimization_notes: Optional[str] = None
    sheet_row: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Order Schemas
class OrderBase(BaseModel):
    order_number: str = Field(..., min_length=1)
    item_id: Optional[str] = None
    transaction_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    customer_type: Optional[str] = None
    username_ebay: Optional[str] = None
    product_name: str = Field(..., min_length=1)
    product_link: Optional[str] = None
    product_option: Optional[str] = None
    price_ebay: Optional[float] = Field(None, gt=0)
    price_cost: Optional[float] = Field(None, gt=0)
    net_profit: Optional[float] = None
    fees: Optional[float] = Field(None, ge=0)
    shipping_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class OrderCreate(OrderBase):
    listing_id: Optional[str] = None


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    expected_ship_date: Optional[datetime] = None
    actual_ship_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    alerts: Optional[List[str]] = None
    notes: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    
    # Multi-role fields
    sync_source: Optional[SyncSource] = None
    sheets_row_id: Optional[str] = None
    assigned_to_user_id: Optional[int] = None
    blacklist_status: Optional[BlacklistStatus] = None
    blacklist_reason: Optional[str] = None
    fulfillment_notes: Optional[str] = None
    supplier_sent_date: Optional[datetime] = None
    supplier_name: Optional[str] = None
    tracking_added_to_ebay: Optional[bool] = None
    ebay_sync_status: Optional[str] = None


class Order(OrderBase):
    id: str
    user_id: int
    listing_id: Optional[str] = None
    status: OrderStatus
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    order_date: Optional[datetime] = None
    expected_ship_date: Optional[datetime] = None
    actual_ship_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    alerts: Optional[List[str]] = None
    notes: Optional[str] = None
    machine: Optional[str] = None
    
    # Multi-role Google Sheets integration fields
    sync_source: Optional[SyncSource] = SyncSource.MANUAL
    sheets_row_id: Optional[str] = None
    sheets_last_sync: Optional[datetime] = None
    assigned_to_user_id: Optional[int] = None
    assigned_by_user_id: Optional[int] = None
    assignment_date: Optional[datetime] = None
    blacklist_checked: Optional[bool] = False
    blacklist_status: Optional[BlacklistStatus] = BlacklistStatus.PENDING
    blacklist_reason: Optional[str] = None
    fulfillment_notes: Optional[str] = None
    supplier_sent_date: Optional[datetime] = None
    supplier_name: Optional[str] = None
    tracking_added_to_ebay: Optional[bool] = False
    ebay_sync_status: Optional[str] = None
    last_status_change: Optional[datetime] = None
    status_changed_by: Optional[int] = None
    
    # User relationships
    assigned_to_user_name: Optional[str] = None
    assigned_by_user_name: Optional[str] = None
    status_changed_by_user_name: Optional[str] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Source Schemas
class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    website_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    icon: Optional[str] = None
    markup_percentage: float = 0.0
    min_profit_margin: float = 0.0
    max_price: Optional[float] = Field(None, gt=0)
    excluded_categories: Optional[List[str]] = None


class SourceCreate(SourceBase):
    api_key: Optional[str] = None
    secret_key: Optional[str] = None


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    website_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[SourceStatus] = None
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    markup_percentage: Optional[float] = None
    min_profit_margin: Optional[float] = None
    max_price: Optional[float] = Field(None, gt=0)
    excluded_categories: Optional[List[str]] = None
    auto_sync: Optional[bool] = None
    sync_frequency: Optional[int] = Field(None, gt=0)


class Source(SourceBase):
    id: str
    user_id: int
    status: SourceStatus
    total_products: int = 0
    active_products: int = 0
    average_roi: Optional[float] = None
    total_revenue: float = 0.0
    last_sync: Optional[datetime] = None
    sync_frequency: int = 24
    auto_sync: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Source Product Schemas
class SourceProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    source_price: float = Field(..., gt=0)
    suggested_price: Optional[float] = Field(None, gt=0)
    market_price: Optional[float] = Field(None, gt=0)
    in_stock: bool = True
    stock_quantity: int = 0
    min_order_quantity: int = 1
    source_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    specifications: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    weight: Optional[float] = Field(None, gt=0)
    dimensions: Optional[Dict[str, float]] = None


class SourceProductCreate(SourceProductBase):
    source_id: str


class SourceProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    source_price: Optional[float] = Field(None, gt=0)
    suggested_price: Optional[float] = Field(None, gt=0)
    market_price: Optional[float] = Field(None, gt=0)
    in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    source_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    specifications: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class SourceProduct(SourceProductBase):
    id: str
    source_id: str
    profit_margin: Optional[float] = None
    views: int = 0
    conversions: int = 0
    roi: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Account Schemas
class AccountBase(BaseModel):
    ebay_username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    country: Optional[str] = None
    site_id: Optional[int] = None
    store_name: Optional[str] = None
    store_url: Optional[str] = None


class AccountCreate(AccountBase):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class AccountUpdate(BaseModel):
    email: Optional[EmailStr] = None
    status: Optional[AccountStatus] = None
    country: Optional[str] = None
    store_name: Optional[str] = None
    store_url: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    auto_sync: Optional[bool] = None
    sync_frequency: Optional[int] = Field(None, gt=0)
    notifications_enabled: Optional[bool] = None


class Account(AccountBase):
    id: int
    user_id: int
    ebay_user_id: Optional[str] = None
    status: AccountStatus
    health_score: Optional[float] = 0.0
    feedback_score: Optional[float] = 0.0
    feedback_count: Optional[int] = 0
    total_listings: Optional[int] = 0
    active_listings: Optional[int] = 0
    total_sales: Optional[int] = 0
    monthly_revenue: Optional[float] = 0.0
    monthly_listing_limit: Optional[int] = 0
    monthly_revenue_limit: Optional[float] = 0.0
    used_listing_count: Optional[int] = 0
    used_revenue_amount: Optional[float] = 0.0
    join_date: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    auto_sync: bool = True
    sync_frequency: int = 6
    notifications_enabled: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# System Settings Schemas
class SystemSettingBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    description: Optional[str] = None


class SystemSettingCreate(SystemSettingBase):
    user_id: Optional[int] = None
    is_encrypted: bool = False
    is_readonly: bool = False


class SystemSettingUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class SystemSetting(SystemSettingBase):
    id: int
    user_id: Optional[int] = None
    is_encrypted: bool = False
    is_readonly: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Activity Log Schemas  
class ActivityLogBase(BaseModel):
    action: str = Field(..., min_length=1, max_length=100)
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None


class ActivityLogCreate(ActivityLogBase):
    user_id: Optional[int] = None


class ActivityLog(ActivityLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Optimization Schemas (from original listing.py)
class OptimizationRequest(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    keywords: Optional[List[str]] = []
    item_specifics: Optional[Dict[str, str]] = {}


class OptimizationResponse(BaseModel):
    original_title: str
    optimized_title: str
    title_score: float
    original_description: Optional[str] = None
    optimized_description: Optional[str] = None
    suggested_keywords: List[str]
    improvements: List[str]
    seo_score: float


class BulkOptimizationRequest(BaseModel):
    listing_ids: List[str]
    optimize_title: bool = True
    optimize_description: bool = True
    generate_keywords: bool = True


class BulkOptimizationResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[OptimizationResponse]
    errors: Optional[List[Dict[str, str]]] = []


# Dashboard & Analytics Schemas
class DashboardStats(BaseModel):
    total_listings: int = 0
    active_listings: int = 0
    total_orders: int = 0
    pending_orders: int = 0
    processing_orders: int = 0
    shipped_orders: int = 0
    total_revenue: float = 0.0
    monthly_revenue: float = 0.0
    profit_margin: float = 0.0
    tracking_orders: int = 0


class OrderAnalytics(BaseModel):
    daily_orders: List[Dict[str, Union[str, int]]]
    revenue_trend: List[Dict[str, Union[str, float]]]
    top_products: List[Dict[str, Union[str, int, float]]]
    customer_types: Dict[str, int]
    status_distribution: Dict[str, int]


class AccountAnalytics(BaseModel):
    performance_overview: Dict[str, Union[int, float]]
    health_scores: List[Dict[str, Union[str, float]]]
    usage_limits: List[Dict[str, Union[str, int, float]]]
    country_distribution: Dict[str, int]


# Pagination & Filtering
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field("asc", pattern="^(asc|desc)$")


class FilterParams(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


# Bulk Operations
class BulkActionRequest(BaseModel):
    ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., min_length=1)
    data: Optional[Dict[str, Any]] = None


class BulkActionResponse(BaseModel):
    total: int
    successful: int
    failed: int
    errors: Optional[List[Dict[str, str]]] = []


# API Response Wrappers
class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


# ===========================================
# MULTI-ROLE SYSTEM SCHEMAS
# ===========================================

# User Role Management
class UserRoleBase(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleUpdate(BaseModel):
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class UserRoleResponse(UserRoleBase):
    id: int
    created_at: datetime
    user_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# Address Blacklist Management
class AddressBlacklistBase(BaseModel):
    address_pattern: str = Field(..., min_length=1)
    match_type: str = Field("contains", pattern="^(exact|contains|regex)$")
    risk_level: str = Field("medium", pattern="^(low|medium|high|blocked)$")
    reason: Optional[str] = None
    is_active: bool = True


class AddressBlacklistCreate(AddressBlacklistBase):
    pass


class AddressBlacklistUpdate(BaseModel):
    address_pattern: Optional[str] = Field(None, min_length=1)
    match_type: Optional[str] = Field(None, pattern="^(exact|contains|regex)$")
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high|blocked)$")
    reason: Optional[str] = None
    is_active: Optional[bool] = None


class AddressBlacklistResponse(AddressBlacklistBase):
    id: int
    created_by: Optional[int] = None
    created_by_user_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AddressCheckRequest(BaseModel):
    address: str = Field(..., min_length=1)


class AddressCheckResponse(BaseModel):
    is_safe: bool
    risk_level: str
    matched_patterns: List[Dict[str, str]]
    recommendation: str


# Google Sheets Sync Management
class SheetsSyncLogBase(BaseModel):
    sync_type: str = Field(..., pattern="^(import|export|status_update)$")
    spreadsheet_id: Optional[str] = None
    sheet_name: Optional[str] = None
    rows_processed: int = 0
    rows_success: int = 0
    rows_error: int = 0
    error_details: Optional[Dict[str, Any]] = None
    status: str = Field("running", pattern="^(running|completed|failed)$")


class SheetsSyncLogCreate(SheetsSyncLogBase):
    started_by: Optional[int] = None


class SheetsSyncLogResponse(SheetsSyncLogBase):
    id: int
    started_by: Optional[int] = None
    started_by_user_name: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


# Order Status History
class OrderStatusHistoryBase(BaseModel):
    order_id: str = Field(..., min_length=1)
    old_status: Optional[str] = None
    new_status: str = Field(..., min_length=1)
    change_reason: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class OrderStatusHistoryCreate(OrderStatusHistoryBase):
    changed_by: Optional[int] = None


class OrderStatusHistoryResponse(OrderStatusHistoryBase):
    id: int
    changed_by: Optional[int] = None
    changed_by_user_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Role-Based Assignment
class OrderAssignmentRequest(BaseModel):
    order_ids: List[str] = Field(..., min_items=1)
    assigned_to_user_id: int = Field(..., gt=0)
    assignment_reason: Optional[str] = None


class OrderAssignmentResponse(BaseModel):
    successful_assignments: int
    failed_assignments: int
    assignment_details: List[Dict[str, Union[str, bool, str]]]


# Blacklist Bulk Check
class BulkAddressCheckRequest(BaseModel):
    order_ids: List[str] = Field(..., min_items=1)
    auto_assign_safe: bool = False
    target_user_id: Optional[int] = None


class BulkAddressCheckResponse(BaseModel):
    total_checked: int
    safe_orders: int
    flagged_orders: int
    blocked_orders: int
    assignments_made: int
    order_results: List[Dict[str, Union[str, bool, str, List[str]]]]


# Enhanced Dashboard Stats for Multi-Role
class MultiRoleDashboardStats(BaseModel):
    # Order statistics by status
    total_orders: int = 0
    pending_orders: int = 0
    assigned_orders: int = 0
    in_fulfillment: int = 0
    shipped_orders: int = 0
    
    # Assignment statistics
    unassigned_orders: int = 0
    my_assigned_orders: int = 0  # For current user
    overdue_assignments: int = 0
    
    # Blacklist statistics
    pending_blacklist_check: int = 0
    flagged_addresses: int = 0
    blocked_addresses: int = 0
    
    # Revenue and performance
    total_revenue: float = 0.0
    monthly_revenue: float = 0.0
    average_fulfillment_time: Optional[float] = None  # Hours
    
    # Google Sheets sync status
    last_sync: Optional[datetime] = None
    sync_pending: bool = False
    sync_errors: int = 0


# ===========================================
# SUPPLIER MANAGEMENT SCHEMAS
# ===========================================

class SupplierStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class SupplierBusinessType(str, Enum):
    MANUFACTURER = "manufacturer"
    DISTRIBUTOR = "distributor"
    WHOLESALER = "wholesaler"
    DROPSHIPPER = "dropshipper"
    RETAILER = "retailer"


class DiscountTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"


class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    company_name: Optional[str] = Field(None, max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    country: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=200)
    business_type: SupplierBusinessType = SupplierBusinessType.MANUFACTURER
    
    # Business terms
    payment_terms: str = Field("NET 30", max_length=100)
    minimum_order_value: float = Field(0.0, ge=0)
    currency: str = Field("USD", max_length=10)
    discount_tier: DiscountTier = DiscountTier.STANDARD
    
    # Internal tracking
    priority_level: int = Field(3, ge=1, le=5)
    notes: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    company_name: Optional[str] = Field(None, max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    country: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=200)
    business_type: Optional[SupplierBusinessType] = None
    status: Optional[SupplierStatus] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    minimum_order_value: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    discount_tier: Optional[DiscountTier] = None
    priority_level: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)
    last_contact_date: Optional[datetime] = None


class Supplier(SupplierBase):
    id: int
    status: SupplierStatus
    
    # Performance tracking (read-only)
    performance_rating: float = 0.0
    reliability_score: int = 50
    total_orders: int = 0
    successful_orders: int = 0
    average_delivery_days: int = 15
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===========================================
# PRODUCT MANAGEMENT SCHEMAS
# ===========================================

class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"
    PENDING = "pending"


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    REORDER_NEEDED = "reorder_needed"
    DISCONTINUED = "discontinued"


class EbayCondition(str, Enum):
    NEW = "New"
    NEW_OTHER = "New other (see details)"
    NEW_WITH_DEFECTS = "New with defects"
    MANUFACTURER_REFURBISHED = "Manufacturer refurbished"
    SELLER_REFURBISHED = "Seller refurbished"
    USED = "Used"
    FOR_PARTS = "For parts or not working"


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    
    # Supplier relationships
    primary_supplier_id: Optional[int] = None
    backup_supplier_id: Optional[int] = None
    
    # Pricing and costs
    cost_price: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    retail_price: Optional[float] = Field(None, gt=0)
    
    # Physical properties
    weight_kg: Optional[float] = Field(None, gt=0)
    dimensions_cm: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    
    # eBay listing optimization
    ebay_category_id: Optional[str] = Field(None, max_length=20)
    ebay_condition: EbayCondition = EbayCondition.NEW
    shipping_cost: float = Field(0.0, ge=0)
    handling_days: int = Field(1, ge=0)
    
    # Status and metadata
    tags: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class ProductCreate(ProductBase):
    # Inventory management (optional on create)
    stock_level: int = Field(0, ge=0)
    reorder_point: int = Field(10, ge=0)
    max_stock_level: int = Field(100, ge=0)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    primary_supplier_id: Optional[int] = None
    backup_supplier_id: Optional[int] = None
    cost_price: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    retail_price: Optional[float] = Field(None, gt=0)
    stock_level: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    status: Optional[ProductStatus] = None
    weight_kg: Optional[float] = Field(None, gt=0)
    dimensions_cm: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    ebay_category_id: Optional[str] = Field(None, max_length=20)
    ebay_condition: Optional[EbayCondition] = None
    shipping_cost: Optional[float] = Field(None, ge=0)
    handling_days: Optional[int] = Field(None, ge=0)
    tags: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class Product(ProductBase):
    id: int
    status: ProductStatus
    
    # Calculated fields (read-only)
    profit_margin_percent: Optional[float] = None
    
    # Inventory management
    stock_level: int = 0
    reorder_point: int = 10
    max_stock_level: int = 100
    stock_status: StockStatus = StockStatus.IN_STOCK
    
    # Performance tracking (read-only)
    total_sales: int = 0
    total_revenue: float = 0.0
    average_rating: float = 0.0
    return_rate_percent: float = 0.0
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sold_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===========================================
# SUPPLIER-PRODUCT RELATIONSHIP SCHEMAS
# ===========================================

class SupplierProductBase(BaseModel):
    supplier_sku: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=200)
    supplier_cost: Optional[float] = Field(None, gt=0)
    lead_time_days: int = Field(7, ge=0)
    minimum_quantity: int = Field(1, ge=1)
    
    # Quality and reliability
    quality_rating: int = Field(5, ge=1, le=5)
    is_preferred: bool = False
    notes: Optional[str] = None


class SupplierProductCreate(SupplierProductBase):
    supplier_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)


class SupplierProductUpdate(BaseModel):
    supplier_sku: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=200)
    supplier_cost: Optional[float] = Field(None, gt=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    minimum_quantity: Optional[int] = Field(None, ge=1)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    is_preferred: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class SupplierProduct(SupplierProductBase):
    id: int
    supplier_id: int
    product_id: int
    status: str = "active"
    
    # Performance tracking (read-only)
    last_order_date: Optional[datetime] = None
    total_ordered: int = 0
    defect_rate_percent: float = 0.0
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===========================================
# PRICE HISTORY SCHEMAS
# ===========================================

class PriceChangeType(str, Enum):
    COST_INCREASE = "cost_increase"
    COST_DECREASE = "cost_decrease"
    PRICE_UPDATE = "price_update"
    MARKET_ADJUSTMENT = "market_adjustment"
    PROMOTIONAL = "promotional"


class PriceHistoryBase(BaseModel):
    old_cost: Optional[float] = Field(None, ge=0)
    new_cost: Optional[float] = Field(None, ge=0)
    old_selling_price: Optional[float] = Field(None, ge=0)
    new_selling_price: Optional[float] = Field(None, ge=0)
    change_reason: Optional[str] = Field(None, max_length=100)
    change_type: PriceChangeType = PriceChangeType.PRICE_UPDATE
    impact_percent: Optional[float] = None
    changed_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PriceHistoryCreate(PriceHistoryBase):
    product_id: int = Field(..., gt=0)
    supplier_id: Optional[int] = None


class PriceHistory(PriceHistoryBase):
    id: int
    product_id: int
    supplier_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===========================================
# ORDER ITEM SCHEMAS (Enhanced)
# ===========================================

class FulfillmentStatus(str, Enum):
    PENDING = "pending"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class OrderItemBase(BaseModel):
    sku: Optional[str] = Field(None, max_length=50)
    product_name: Optional[str] = Field(None, max_length=200)
    quantity: int = Field(..., gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    unit_cost: Optional[float] = Field(None, gt=0)
    
    # Fulfillment details
    supplier_order_id: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    
    # Quality tracking
    customer_rating: Optional[int] = Field(None, ge=1, le=5)
    customer_feedback: Optional[str] = None
    return_requested: bool = False
    return_reason: Optional[str] = Field(None, max_length=200)


class OrderItemCreate(OrderItemBase):
    order_id: str = Field(..., min_length=1)
    product_id: Optional[int] = None
    supplier_id: Optional[int] = None


class OrderItemUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    unit_cost: Optional[float] = Field(None, gt=0)
    supplier_id: Optional[int] = None
    supplier_order_id: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    fulfillment_status: Optional[FulfillmentStatus] = None
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    customer_rating: Optional[int] = Field(None, ge=1, le=5)
    customer_feedback: Optional[str] = None
    return_requested: Optional[bool] = None
    return_reason: Optional[str] = Field(None, max_length=200)


class OrderItem(OrderItemBase):
    id: int
    order_id: str
    product_id: Optional[int] = None
    supplier_id: Optional[int] = None
    
    # Calculated fields (read-only)
    total_price: Optional[float] = None
    total_cost: Optional[float] = None
    profit_amount: Optional[float] = None
    profit_margin_percent: Optional[float] = None
    
    # Status
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.PENDING
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ===========================================
# ANALYTICS SCHEMAS (Enhanced)
# ===========================================

class SupplierPerformanceStats(BaseModel):
    supplier_id: int
    supplier_name: str
    total_orders: int = 0
    total_revenue: float = 0.0
    average_delivery_days: float = 0.0
    success_rate: float = 0.0
    quality_rating: float = 0.0
    cost_efficiency: float = 0.0
    
    class Config:
        from_attributes = True


class ProductPerformanceStats(BaseModel):
    product_id: int
    sku: str
    name: str
    total_sales: int = 0
    total_revenue: float = 0.0
    profit_margin: float = 0.0
    inventory_turnover: float = 0.0
    return_rate: float = 0.0
    
    class Config:
        from_attributes = True


class ProfitAnalysis(BaseModel):
    total_revenue: float = 0.0
    total_cost: float = 0.0
    total_profit: float = 0.0
    profit_margin: float = 0.0
    top_profitable_products: List[ProductPerformanceStats] = []
    top_profitable_suppliers: List[SupplierPerformanceStats] = []
    monthly_trend: List[Dict[str, Union[str, float]]] = []
    
    class Config:
        from_attributes = True


# User Permission Check
class PermissionCheckRequest(BaseModel):
    action: str = Field(..., min_length=1)
    resource: Optional[str] = None
    resource_id: Optional[str] = None


class PermissionCheckResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    required_role: Optional[str] = None
    user_role: Optional[str] = None


# ===========================================
# BACKUP & SYNC SCHEMAS
# ===========================================

class BackupRequest(BaseModel):
    """Request to create comprehensive backup"""
    includes: Optional[List[str]] = ["all"]  # all, suppliers, products, orders, listings, accounts
    description: Optional[str] = "Comprehensive system backup"
    share_with: Optional[List[str]] = []  # Email addresses to share backup with
    
    class Config:
        from_attributes = True


class BackupResponse(BaseModel):
    """Response from backup creation"""
    success: bool
    message: str
    backup_id: str
    status: str  # in_progress, completed, failed
    includes: List[str]
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class BackupStatus(BaseModel):
    """Status of backup operation"""
    backup_id: str
    status: str  # not_found, in_progress, completed, failed
    progress: int  # 0-100
    message: str
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class SyncRequest(BaseModel):
    """Request to sync data to sheets"""
    account_email: Optional[str] = None
    data_types: List[str] = ["all"]  # all, suppliers, products, orders, listings
    include_suppliers: bool = True
    include_products: bool = True
    clear_existing: bool = False
    
    class Config:
        from_attributes = True


class SyncResponse(BaseModel):
    """Response from sync operation"""
    success: bool
    message: str
    spreadsheet_id: Optional[str] = None
    synced_data: Dict[str, int]  # data_type -> count
    total_records: int
    account_email: Optional[str] = None
    
    class Config:
        from_attributes = True


class GoogleSheetsConfig(BaseModel):
    """Google Sheets configuration"""
    spreadsheet_id: Optional[str] = None
    sheet_name: str = "Listings"
    auto_sync: bool = True
    sync_interval_minutes: int = 30
    backup_enabled: bool = True
    backup_frequency: str = "daily"  # daily, weekly, monthly
    
    class Config:
        from_attributes = True


class EnhancedSheetsStatus(BaseModel):
    """Status of enhanced Google Sheets integration"""
    service_available: bool
    fallback_mode: bool
    account_sheets: int
    backup_sheets: int
    last_sync: Optional[str] = None
    last_backup: Optional[str] = None
    sync_errors: List[str] = []
    
    class Config:
        from_attributes = True


# ===========================================
# AUTOMATION & SCHEDULING SCHEMAS
# ===========================================

class AutomationTaskRequest(BaseModel):
    """Request to create automation task"""
    task_id: str = Field(..., min_length=1, max_length=100)
    task_type: str = Field(..., description="Type of automation task")
    frequency: str = Field(..., description="Execution frequency")
    enabled: bool = True
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class AutomationTaskUpdate(BaseModel):
    """Request to update automation task"""
    enabled: Optional[bool] = None
    frequency: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class AutomationTaskResponse(BaseModel):
    """Response for automation task"""
    task_id: str
    task_type: str
    frequency: str
    enabled: bool
    parameters: Dict[str, Any]
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    status: str
    execution_count: int
    success_count: int
    failure_count: int
    success_rate: float
    last_result: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class TaskExecutionRequest(BaseModel):
    """Request to execute task"""
    task_id: str = Field(..., min_length=1)
    force_execute: bool = False
    parameters_override: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class TaskExecutionResponse(BaseModel):
    """Response from task execution"""
    success: bool
    message: str
    task_id: str
    execution_time: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True


class PerformanceMetric(BaseModel):
    """Individual performance metric"""
    timestamp: str
    value: float
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class PerformanceAlert(BaseModel):
    """Performance alert"""
    metric_name: str
    value: float
    threshold: float
    severity: str
    timestamp: str
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class PerformanceSummaryResponse(BaseModel):
    """Performance monitoring summary"""
    metrics_summary: Dict[str, Any]
    active_alerts: List[PerformanceAlert]
    task_summary: Dict[str, Any]
    period_hours: int
    generated_at: str
    
    class Config:
        from_attributes = True


class AutomationScheduleRequest(BaseModel):
    """Request for automation schedule"""
    action: str = Field(..., description="start, stop, or restart")
    config: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class AutomationScheduleResponse(BaseModel):
    """Response for automation schedule"""
    success: bool
    message: str
    status: str
    active_tasks: int
    total_tasks: int
    
    class Config:
        from_attributes = True


class AutomationDashboardStats(BaseModel):
    """Dashboard statistics for automation"""
    scheduler_status: str
    total_tasks: int
    enabled_tasks: int
    running_tasks: int
    completed_today: int
    failed_today: int
    success_rate_today: float
    active_alerts: int
    performance_score: float
    
    class Config:
        from_attributes = True


class TaskTypeConfig(BaseModel):
    """Configuration for task type"""
    value: str
    label: str
    description: str
    default_parameters: Dict[str, Any] = {}
    required_permissions: List[str] = []
    
    class Config:
        from_attributes = True


class FrequencyConfig(BaseModel):
    """Configuration for frequency"""
    value: str
    label: str
    description: str
    interval_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


# ===========================================
# INTELLIGENT PRICING SCHEMAS
# ===========================================

class IntelligentPricingRequest(BaseModel):
    """Request for intelligent pricing optimization"""
    product_id: int = Field(..., gt=0)
    strategy: Optional[str] = None
    context_override: Optional[Dict[str, Any]] = None
    target_margin: Optional[float] = Field(None, ge=0, le=1)
    
    class Config:
        from_attributes = True


class PricingRecommendationSchema(BaseModel):
    """Pricing recommendation schema"""
    recommended_price: float
    strategy_used: str
    confidence_score: float = Field(..., ge=0, le=1)
    expected_profit_margin: float
    expected_sales_volume: int = Field(..., ge=0)
    risk_assessment: str
    reasoning: str
    alternative_prices: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True


class IntelligentPricingResponse(BaseModel):
    """Response for intelligent pricing optimization"""
    success: bool
    product_id: int
    recommendation: PricingRecommendationSchema
    
    class Config:
        from_attributes = True


class PriceElasticityAnalysis(BaseModel):
    """Price elasticity analysis result"""
    product_id: int
    elasticity_coefficient: float
    elasticity_category: str
    description: str
    price_demand_curve: List[Dict[str, Any]]
    optimal_price_range: Dict[str, float]
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class MarketResponsePrediction(BaseModel):
    """Market response prediction"""
    product_id: int
    current_price: float
    proposed_price: float
    price_change_percent: float
    predictions: Dict[str, Any]
    risk_assessment: List[str]
    confidence_level: float = Field(..., ge=0, le=1)
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class PortfolioPricingRequest(BaseModel):
    """Request for portfolio pricing optimization"""
    category: Optional[str] = None
    supplier_id: Optional[int] = None
    batch_size: int = Field(default=50, ge=1, le=200)
    strategy: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PortfolioPricingResponse(BaseModel):
    """Response for portfolio pricing optimization"""
    success: bool
    optimized_products: int
    total_potential_profit_increase: float
    filters: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    summary_stats: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PricingStrategyConfig(BaseModel):
    """Configuration for pricing strategy"""
    value: str
    label: str
    description: str
    risk_level: str
    suitable_for: List[str] = []
    parameters: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class PricingAnalytics(BaseModel):
    """Pricing analytics for category or supplier"""
    entity_type: str  # "category" or "supplier"
    entity_id: str
    entity_name: str
    total_products: int
    price_range: Dict[str, float]
    margin_analysis: Dict[str, float]
    optimization_opportunities: List[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PriceOptimizationBatch(BaseModel):
    """Batch price optimization request"""
    product_ids: List[int] = Field(..., min_items=1, max_items=100)
    strategy: Optional[str] = None
    apply_changes: bool = False
    context_overrides: Optional[Dict[int, Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class CompetitiveAnalysis(BaseModel):
    """Competitive pricing analysis"""
    product_id: int
    current_price: float
    competitor_prices: List[float]
    market_position: str  # "premium", "competitive", "discount"
    price_gap_analysis: Dict[str, float]
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class DemandForecast(BaseModel):
    """Demand forecasting result"""
    product_id: int
    forecast_period_days: int
    predicted_demand: List[Dict[str, Any]]
    confidence_intervals: Dict[str, List[float]]
    seasonality_factors: Dict[str, float]
    trend_analysis: Dict[str, Any]
    
    class Config:
        from_attributes = True