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
    health_score: float = 0.0
    feedback_score: float = 0.0
    feedback_count: int = 0
    total_listings: int = 0
    active_listings: int = 0
    total_sales: int = 0
    monthly_revenue: float = 0.0
    monthly_listing_limit: int = 0
    monthly_revenue_limit: float = 0.0
    used_listing_count: int = 0
    used_revenue_amount: float = 0.0
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