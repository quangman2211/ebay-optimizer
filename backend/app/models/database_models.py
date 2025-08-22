"""
SQLAlchemy Database Models cho eBay Optimizer
Chứa tất cả database tables: Users, Listings, Orders, Sources, Accounts
"""

from sqlalchemy import (
    Boolean, Column, Integer, String, Text, Float, DateTime, 
    JSON, ForeignKey, Enum as SQLEnum, Index, DECIMAL, Date
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
import enum
from app.db.database import Base


# Enums cho database
class ListingStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    OPTIMIZED = "optimized"
    ENDED = "ended"
    SOLD = "sold"
    ARCHIVED = "archived"
    PENDING = "pending"


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class AccountStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LIMITED = "limited"
    INACTIVE = "inactive"


class SourceStatusEnum(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SYNCING = "syncing"


class DraftStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
    LISTED = "listed"


class ImageStatusEnum(str, enum.Enum):
    PENDING = "pending"
    EDITED = "edited"
    APPROVED = "approved"


class MessageTypeEnum(str, enum.Enum):
    QUESTION = "question"
    SHIPPING_INFO = "shipping_info"
    RETURN_REQUEST = "return_request"
    GENERAL = "general"


class MessagePriorityEnum(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SheetTypeEnum(str, enum.Enum):
    LISTINGS = "listings"
    ORDERS = "orders"
    MESSAGES = "messages"
    DRAFTS = "drafts"


class UserRoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    EBAY_MANAGER = "EBAY_MANAGER"
    FULFILLMENT_STAFF = "FULFILLMENT_STAFF"


class BlacklistStatusEnum(str, enum.Enum):
    PENDING = "pending"
    CLEAN = "clean"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


class SyncSourceEnum(str, enum.Enum):
    MANUAL = "manual"
    GOOGLE_SHEETS = "google_sheets"
    API = "api"
    EXISTING = "existing"


# Database Models
class User(Base):
    """User authentication và management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=True)
    assigned_accounts = Column(JSON, nullable=True)  # eBay accounts assignment
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    role = relationship("UserRole", back_populates="users")
    listings = relationship("Listing", back_populates="user")
    accounts = relationship("Account", back_populates="user")
    draft_listings = relationship("DraftListing", back_populates="user")
    messages = relationship("Message", back_populates="user")


class Listing(Base):
    """eBay Listings với optimization data"""
    __tablename__ = "listings"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)  # NEW: Multi-account
    source_product_id = Column(String(100), ForeignKey("source_products.id"), nullable=True)  # NEW: Link to source
    draft_listing_id = Column(String(100), ForeignKey("draft_listings.id"), nullable=True)  # NEW: Link to draft
    
    # eBay Info
    ebay_item_id = Column(String(50), unique=True, nullable=True, index=True)  # eBay Item ID (unique per listing)
    title = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    quantity = Column(Integer, default=0)
    sku = Column(String(100), nullable=True)
    condition = Column(String(50), nullable=True)
    
    # Status
    status = Column(SQLEnum(ListingStatusEnum), default=ListingStatusEnum.DRAFT)
    listing_type = Column(String(20), default='fixed')  # fixed, auction
    
    # Metadata
    keywords = Column(JSON, nullable=True)  # List of keywords
    item_specifics = Column(JSON, nullable=True)  # Key-value pairs
    
    # Performance metrics
    views = Column(Integer, default=0)
    watchers = Column(Integer, default=0)
    sold = Column(Integer, default=0)
    performance_score = Column(Float, nullable=True)  # 0-100
    
    # Optimization data
    original_title = Column(String(80), nullable=True)
    optimized_title = Column(String(80), nullable=True)
    seo_score = Column(Float, nullable=True)
    optimization_notes = Column(Text, nullable=True)
    
    # Links
    ebay_url = Column(String(500), nullable=True)  # Direct link to eBay listing
    
    # Google Sheets integration
    sheet_row = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="listings")
    account = relationship("Account", back_populates="listings")
    source_product = relationship("SourceProduct", back_populates="listings")
    draft_listing = relationship("DraftListing", back_populates="listing", uselist=False)
    orders = relationship("Order", back_populates="listing")
    messages = relationship("Message", back_populates="listing")
    
    # Indexes
    __table_args__ = (
        Index('idx_listing_user_status', 'user_id', 'status'),
        Index('idx_listing_account', 'account_id', 'status'),
        Index('idx_listing_category', 'category'),
        Index('idx_listing_performance', 'performance_score'),
        Index('idx_listing_source_product', 'source_product_id'),
    )


class Order(Base):
    """eBay Orders với tracking và customer info"""
    __tablename__ = "orders"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)  # NEW: Multi-account
    listing_id = Column(String(100), ForeignKey("listings.id"), nullable=True)
    
    # eBay Order Info
    ebay_order_id = Column(String(50), unique=True, nullable=True)
    ebay_transaction_id = Column(String(50), nullable=True)
    order_number = Column(String(50), nullable=False, index=True)
    
    # Customer Info
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_username = Column(String(100), nullable=True)
    
    # Product Info
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    
    # Financial
    price_ebay = Column(Float, nullable=True)
    shipping_cost = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    ebay_fees = Column(Float, nullable=True)
    net_profit = Column(Float, nullable=True)
    
    # Shipping & address
    shipping_address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(50), nullable=True)
    
    # Order status & tracking
    status = Column(SQLEnum(OrderStatusEnum), default=OrderStatusEnum.PENDING)
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(50), nullable=True)
    
    # Important dates
    order_date = Column(DateTime(timezone=True), nullable=True)
    expected_ship_date = Column(DateTime(timezone=True), nullable=True)
    actual_ship_date = Column(DateTime(timezone=True), nullable=True)
    delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Alerts & notes
    alerts = Column(JSON, nullable=True)  # List of alert messages
    notes = Column(Text, nullable=True)
    machine = Column(String(50), nullable=True)  # Store identifier
    
    # Multi-role Google Sheets integration fields
    sync_source = Column(String(50), default='manual')  # 'google_sheets', 'manual', 'api'
    sheets_row_id = Column(String(100), nullable=True)  # Track Google Sheets row
    sheets_last_sync = Column(DateTime(timezone=True), nullable=True)  # Last sync timestamp
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Assigned fulfillment staff
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who assigned the order
    assignment_date = Column(DateTime(timezone=True), nullable=True)  # When assigned
    blacklist_checked = Column(Boolean, default=False)  # Address blacklist status
    blacklist_status = Column(String(20), nullable=True)  # 'clean', 'flagged', 'blocked'
    blacklist_reason = Column(Text, nullable=True)  # Why flagged/blocked
    fulfillment_notes = Column(Text, nullable=True)  # Notes from fulfillment staff
    supplier_sent_date = Column(DateTime(timezone=True), nullable=True)  # When sent to supplier
    supplier_name = Column(String(200), nullable=True)  # Which supplier used
    tracking_added_to_ebay = Column(Boolean, default=False)  # Tracking synced to eBay
    ebay_sync_status = Column(String(50), nullable=True)  # eBay sync status
    last_status_change = Column(DateTime(timezone=True), nullable=True)  # Status change tracking
    status_changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who changed status
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    account = relationship("Account", back_populates="orders")
    listing = relationship("Listing", back_populates="orders")
    messages = relationship("Message", back_populates="order")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id])
    status_changed_by_user = relationship("User", foreign_keys=[status_changed_by])
    order_status_history = relationship("OrderStatusHistory", back_populates="order")
    order_items = relationship("OrderItem", back_populates="order")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_user_status', 'user_id', 'status'),
        Index('idx_order_account', 'account_id', 'order_date'),
        Index('idx_order_date', 'order_date'),
        Index('idx_order_tracking', 'tracking_number'),
        Index('idx_order_ebay', 'ebay_order_id', 'ebay_transaction_id'),
        Index('idx_orders_sync_source', 'sync_source'),
        Index('idx_orders_sheets_row', 'sheets_row_id'),
        Index('idx_orders_assigned_to', 'assigned_to_user_id'),
        Index('idx_orders_blacklist', 'blacklist_status'),
        Index('idx_orders_status_change', 'last_status_change'),
    )


class Source(Base):
    """Nguồn hàng - suppliers/dropshipping sources"""
    __tablename__ = "sources"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Source info
    name = Column(String(255), nullable=False)
    website_url = Column(String(500), nullable=True)
    api_endpoint = Column(String(500), nullable=True)
    icon = Column(String(10), nullable=True)  # Emoji or icon identifier
    
    # Connection info
    status = Column(SQLEnum(SourceStatusEnum), default=SourceStatusEnum.DISCONNECTED)
    api_key = Column(String(255), nullable=True)
    secret_key = Column(String(255), nullable=True)
    access_token = Column(Text, nullable=True)
    
    # Statistics
    total_products = Column(Integer, default=0)
    active_products = Column(Integer, default=0)
    average_roi = Column(Float, nullable=True)
    total_revenue = Column(Float, default=0.0)
    
    # Sync info
    last_sync = Column(DateTime(timezone=True), nullable=True)
    sync_frequency = Column(Integer, default=24)  # Hours
    auto_sync = Column(Boolean, default=True)
    
    # Settings
    markup_percentage = Column(Float, default=0.0)
    min_profit_margin = Column(Float, default=0.0)
    max_price = Column(Float, nullable=True)
    excluded_categories = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    products = relationship("SourceProduct", back_populates="source")
    
    # Indexes
    __table_args__ = (
        Index('idx_source_user_status', 'user_id', 'status'),
        Index('idx_source_roi', 'average_roi'),
    )


class SourceProduct(Base):
    """Products từ các nguồn hàng"""
    __tablename__ = "source_products"

    id = Column(String(100), primary_key=True, index=True)
    source_id = Column(String(100), ForeignKey("sources.id"), nullable=False)
    
    # Product Info (Import từ nhà cung cấp)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    sku = Column(String(100), nullable=True)
    
    # Pricing
    source_price = Column(Float, nullable=False)
    suggested_price = Column(Float, nullable=True)
    market_price = Column(Float, nullable=True)
    profit_margin = Column(Float, nullable=True)
    
    # Availability
    in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    min_order_quantity = Column(Integer, default=1)
    
    # Source info
    source_url = Column(String(500), nullable=True)
    image_urls = Column(JSON, nullable=True)
    specifications = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Physical properties
    weight = Column(Float, nullable=True)
    dimensions = Column(JSON, nullable=True)
    
    # Analytics
    views = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    roi = Column(Float, nullable=True)
    
    # Google Drive Images (Original từ supplier)
    gdrive_folder_url = Column(String(500), nullable=True)  # Link to Google Drive folder
    image_notes = Column(Text, nullable=True)  # "6 images, need watermark removal"
    
    # Status
    is_approved = Column(Boolean, default=False)  # Đã duyệt để tạo draft
    
    # Additional field for compatibility
    title = Column(Text, nullable=True)  # Alternative name field
    
    # Relationships
    source = relationship("Source", back_populates="products")
    draft_listings = relationship("DraftListing", back_populates="source_product")
    listings = relationship("Listing", back_populates="source_product")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    source = relationship("Source", back_populates="products")


class Account(Base):
    """eBay Accounts management"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # eBay account info
    ebay_username = Column(String(100), nullable=False, unique=True)
    ebay_user_id = Column(String(50), nullable=True)
    email = Column(String(255), nullable=False)
    
    # Account details
    status = Column(String(20), default='active')
    country = Column(String(10), nullable=True)  # Country code
    site_id = Column(Integer, nullable=True)  # eBay site ID
    store_name = Column(String(255), nullable=True)
    store_url = Column(String(500), nullable=True)
    
    # Google Sheets Integration
    sheet_id = Column(String(100), nullable=True)  # Google Sheet ID cho account này
    sheet_url = Column(String(500), nullable=True)
    
    # eBay API (optional)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Basic Metrics
    health_score = Column(Float, default=0.0)
    feedback_score = Column(Float, default=0.0)  
    feedback_count = Column(Integer, default=0)
    total_listings = Column(Integer, default=0)
    active_listings = Column(Integer, default=0)
    total_sales = Column(Integer, default=0)
    monthly_revenue = Column(Float, default=0.0)
    
    # Limits & restrictions
    monthly_listing_limit = Column(Integer, default=0)
    monthly_revenue_limit = Column(Float, default=0.0)
    used_listing_count = Column(Integer, default=0)
    used_revenue_amount = Column(Float, default=0.0)
    
    # Important dates
    join_date = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Settings
    auto_sync = Column(Boolean, default=True)
    sync_frequency = Column(Integer, default=6)  # Hours
    notifications_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    listings = relationship("Listing", back_populates="account")
    orders = relationship("Order", back_populates="account")
    draft_listings = relationship("DraftListing", back_populates="account")
    messages = relationship("Message", back_populates="account")
    account_sheets = relationship("AccountSheet", back_populates="account")
    
    # Indexes
    __table_args__ = (
        Index('idx_account_user_status', 'user_id', 'status'),
        Index('idx_account_country', 'country'),
    )


class SystemSetting(Base):
    """System-wide settings và configuration"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL = global setting
    
    # Setting info
    key = Column(String(100), nullable=False)
    value = Column(JSON, nullable=True)
    category = Column(String(50), nullable=True)  # api, notifications, optimization
    description = Column(Text, nullable=True)
    
    # Metadata
    is_encrypted = Column(Boolean, default=False)
    is_readonly = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_setting_user_key', 'user_id', 'key', unique=True),
        Index('idx_setting_category', 'category'),
    )


class ActivityLog(Base):
    """Activity logging cho audit trail"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Activity info
    action = Column(String(100), nullable=False)  # create, update, delete, sync
    entity_type = Column(String(50), nullable=False)  # listing, order, account
    entity_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Additional data
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_user_date', 'user_id', 'created_at'),
        Index('idx_activity_entity', 'entity_type', 'entity_id'),
        Index('idx_activity_action', 'action'),
    )


# ===========================================
# SUPPLIER & PRODUCT MANAGEMENT MODELS
# ===========================================

class SupplierStatus(str, enum.Enum):
    """Supplier status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    BLOCKED = "blocked"


class ProductStatus(str, enum.Enum):
    """Product status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    PENDING = "pending"


class PaymentTerms(str, enum.Enum):
    """Payment terms enum"""
    COD = "cod"  # Cash on delivery
    NET_7 = "net_7"  # Payment within 7 days
    NET_15 = "net_15"  # Payment within 15 days
    NET_30 = "net_30"  # Payment within 30 days
    PREPAID = "prepaid"  # Payment before delivery
    CREDIT = "credit"  # Credit terms


class Supplier(Base):
    """Supplier management model"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    supplier_code = Column(String(50), unique=True, index=True)  # NCC001, NCC002, etc.
    company_name = Column(String(200), nullable=False, index=True)
    business_name = Column(String(200), nullable=True)  # Tên giao dịch
    
    # Contact Information
    contact_person = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Address Information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    country = Column(String(100), default="Vietnam")
    postal_code = Column(String(20), nullable=True)
    
    # Business Terms
    payment_terms = Column(String(50), default="NET 30")
    credit_limit = Column(DECIMAL(15, 2), default=0)
    delivery_time_days = Column(Integer, default=7)  # Estimated delivery time
    minimum_order_amount = Column(DECIMAL(10, 2), default=0)
    
    # Performance Metrics
    performance_rating = Column(DECIMAL(3, 2), default=0.0)  # 0.00 to 5.00
    reliability_score = Column(Integer, default=50)  # 0 to 100
    quality_score = Column(Integer, default=50)  # 0 to 100
    delivery_score = Column(Integer, default=50)  # 0 to 100
    communication_score = Column(Integer, default=50)  # 0 to 100
    
    # Statistics
    total_orders = Column(Integer, default=0)
    total_order_value = Column(DECIMAL(15, 2), default=0)
    successful_deliveries = Column(Integer, default=0)
    late_deliveries = Column(Integer, default=0)
    cancelled_orders = Column(Integer, default=0)
    
    # Status and Metadata
    status = Column(String(20), default="active")
    tax_id = Column(String(50), nullable=True)  # Mã số thuế
    bank_account = Column(String(100), nullable=True)
    bank_name = Column(String(100), nullable=True)
    
    # Additional Information
    product_categories = Column(JSON, nullable=True)  # List of categories
    certifications = Column(JSON, nullable=True)  # Quality certifications
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Internal company notes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_contact_date = Column(DateTime(timezone=True), nullable=True)
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    products = relationship("Product", back_populates="primary_supplier")
    supplier_products = relationship("SupplierProduct", back_populates="supplier")
    price_history = relationship("PriceHistory", back_populates="supplier")
    
    # Indexes
    __table_args__ = (
        Index('idx_supplier_status', 'status'),
        Index('idx_supplier_rating', 'performance_rating'),
        Index('idx_supplier_company', 'company_name'),
        Index('idx_supplier_contact', 'email'),
    )


class Product(Base):
    """Product catalog model"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    
    # Product Identification
    sku = Column(String(100), unique=True, index=True)  # Stock Keeping Unit
    barcode = Column(String(50), nullable=True)  # EAN/UPC barcode
    product_name = Column(String(200), nullable=False, index=True)
    
    # Category and Classification
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    model = Column(String(100), nullable=True)
    
    # Product Description
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    specifications = Column(JSON, nullable=True)  # Technical specifications
    
    # Supplier Information
    primary_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier_sku = Column(String(100), nullable=True)  # Supplier's SKU
    
    # Pricing Information
    cost_price = Column(DECIMAL(10, 2), nullable=False, default=0)
    suggested_retail_price = Column(DECIMAL(10, 2), nullable=True)
    current_sell_price = Column(DECIMAL(10, 2), nullable=True)
    profit_margin_percent = Column(DECIMAL(5, 2), nullable=True)  # Calculated field
    
    # Inventory Information
    stock_level = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)  # Orders not yet shipped
    available_stock = Column(Integer, default=0)  # Calculated: stock_level - reserved
    reorder_point = Column(Integer, default=10)  # When to reorder
    max_stock_level = Column(Integer, default=100)
    
    # Physical Properties
    weight_grams = Column(Integer, nullable=True)
    length_cm = Column(DECIMAL(8, 2), nullable=True)
    width_cm = Column(DECIMAL(8, 2), nullable=True)
    height_cm = Column(DECIMAL(8, 2), nullable=True)
    
    # Sales Performance
    total_sold = Column(Integer, default=0)
    total_revenue = Column(DECIMAL(15, 2), default=0)
    average_monthly_sales = Column(Integer, default=0)
    last_sold_date = Column(DateTime(timezone=True), nullable=True)
    
    # Product Status and Lifecycle
    status = Column(String(20), default="active")
    is_featured = Column(Boolean, default=False)
    is_seasonal = Column(Boolean, default=False)
    season_start = Column(Date, nullable=True)
    season_end = Column(Date, nullable=True)
    
    # SEO and Marketing
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    keywords = Column(JSON, nullable=True)  # SEO keywords
    tags = Column(JSON, nullable=True)  # Product tags
    
    # Media
    image_urls = Column(JSON, nullable=True)  # List of image URLs
    video_url = Column(String(500), nullable=True)
    
    # Additional Information
    lead_time_days = Column(Integer, default=1)  # Days to fulfill
    warranty_period_days = Column(Integer, default=0)
    return_policy_days = Column(Integer, default=30)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_restocked_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    primary_supplier = relationship("Supplier", back_populates="products")
    supplier_products = relationship("SupplierProduct", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_status', 'status'),
        Index('idx_product_category', 'category', 'subcategory'),
        Index('idx_product_brand', 'brand'),
        Index('idx_product_supplier', 'primary_supplier_id'),
        Index('idx_product_stock', 'stock_level'),
        Index('idx_product_price', 'current_sell_price'),
    )


class SupplierProduct(Base):
    """Junction table for supplier-product relationships (M:N)"""
    __tablename__ = "supplier_products"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Supplier-specific information
    supplier_sku = Column(String(100), nullable=True)  # Supplier's product code
    supplier_name = Column(String(200), nullable=True)  # Supplier's product name
    supplier_description = Column(Text, nullable=True)
    
    # Pricing and Terms
    supplier_price = Column(DECIMAL(10, 2), nullable=False)
    minimum_order_quantity = Column(Integer, default=1)
    price_per_unit = Column(DECIMAL(10, 2), nullable=True)
    bulk_discount_qty = Column(Integer, nullable=True)
    bulk_discount_price = Column(DECIMAL(10, 2), nullable=True)
    
    # Availability and Lead Time
    is_available = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)  # At supplier
    lead_time_days = Column(Integer, default=7)
    
    # Performance Metrics
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    total_orders = Column(Integer, default=0)
    total_quantity_ordered = Column(Integer, default=0)
    average_delivery_days = Column(Integer, default=0)
    quality_rating = Column(DECIMAL(3, 2), default=0.0)  # 0.00 to 5.00
    
    # Status and Priority
    is_preferred = Column(Boolean, default=False)  # Preferred supplier for this product
    priority_rank = Column(Integer, default=1)  # 1 = highest priority
    status = Column(String(20), default="active")  # active, inactive, discontinued
    
    # Additional Information
    notes = Column(Text, nullable=True)
    last_price_update = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="supplier_products")
    product = relationship("Product", back_populates="supplier_products")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_supplier_product', 'supplier_id', 'product_id', unique=True),
        Index('idx_supplier_product_sku', 'supplier_id', 'supplier_sku'),
        Index('idx_supplier_product_price', 'supplier_price'),
        Index('idx_supplier_product_priority', 'priority_rank'),
    )


class PriceHistory(Base):
    """Track price changes for products from suppliers"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    
    # Price Information
    old_price = Column(DECIMAL(10, 2), nullable=True)
    new_price = Column(DECIMAL(10, 2), nullable=False)
    price_change_amount = Column(DECIMAL(10, 2), nullable=True)  # new - old
    price_change_percent = Column(DECIMAL(5, 2), nullable=True)  # % change
    
    # Change Context
    change_reason = Column(String(200), nullable=True)  # "Market fluctuation", "Bulk discount", etc.
    change_type = Column(String(20), nullable=True)  # "increase", "decrease", "initial"
    
    # Who made the change
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    change_source = Column(String(50), default="manual")  # "manual", "import", "api", "bulk_update"
    
    # Effective dates
    effective_date = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Additional context
    notes = Column(Text, nullable=True)
    external_reference = Column(String(100), nullable=True)  # Invoice number, etc.
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="price_history")
    supplier = relationship("Supplier", back_populates="price_history")
    changed_by_user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_price_history_product', 'product_id', 'effective_date'),
        Index('idx_price_history_supplier', 'supplier_id', 'effective_date'),
        Index('idx_price_history_date', 'effective_date'),
    )


class OrderItem(Base):
    """Individual items within an order"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    # Product Information (at time of order)
    product_sku = Column(String(100), nullable=True)
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text, nullable=True)
    
    # Quantity and Pricing
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL(10, 2), nullable=False)  # Price per unit
    unit_cost = Column(DECIMAL(10, 2), nullable=True)  # Cost per unit
    total_price = Column(DECIMAL(10, 2), nullable=False)  # quantity * unit_price
    total_cost = Column(DECIMAL(10, 2), nullable=True)  # quantity * unit_cost
    profit_amount = Column(DECIMAL(10, 2), nullable=True)  # total_price - total_cost
    
    # Supplier Information
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier_sku = Column(String(100), nullable=True)
    supplier_price = Column(DECIMAL(10, 2), nullable=True)
    
    # Fulfillment Status
    status = Column(String(50), default="pending")  # pending, ordered, shipped, delivered, cancelled
    ordered_from_supplier_date = Column(DateTime(timezone=True), nullable=True)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    supplier = relationship("Supplier")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_item_order', 'order_id'),
        Index('idx_order_item_product', 'product_id'),
        Index('idx_order_item_supplier', 'supplier_id'),
        Index('idx_order_item_status', 'status'),
    )


# ===========================================
# NEW TABLES for Multi-Account Support
# ===========================================

class DraftListing(Base):
    """Listings chuẩn bị"""
    __tablename__ = "draft_listings"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    source_product_id = Column(String(100), ForeignKey("source_products.id"), nullable=True)
    
    # Draft Info (Customized per account)
    title = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    quantity = Column(Integer, default=1)
    condition = Column(String(50), default='new')
    
    # Google Drive Images (Edited by employees)
    gdrive_folder_url = Column(String(500), nullable=True)  # Link to edited images folder
    image_status = Column(SQLEnum(ImageStatusEnum), default=ImageStatusEnum.PENDING)
    edited_by = Column(String(100), nullable=True)  # Tên nhân viên edit
    edit_date = Column(DateTime(timezone=True), nullable=True)
    
    # eBay Settings
    listing_type = Column(String(20), default='fixed')
    duration_days = Column(Integer, default=30)
    start_price = Column(Float, nullable=True)  # For auctions
    buy_it_now_price = Column(Float, nullable=True)
    
    # Business
    cost_price = Column(Float, nullable=True)
    profit_margin = Column(Float, nullable=True)
    
    # Status
    status = Column(SQLEnum(DraftStatusEnum), default=DraftStatusEnum.DRAFT)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    account = relationship("Account", back_populates="draft_listings")
    source_product = relationship("SourceProduct", back_populates="draft_listings")
    listing = relationship("Listing", back_populates="draft_listing", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_draft_user_status', 'user_id', 'status'),
        Index('idx_draft_account', 'account_id'),
        Index('idx_draft_source_product', 'source_product_id'),
        Index('idx_draft_image_status', 'image_status'),
    )


class Message(Base):
    """Tin nhắn eBay"""
    __tablename__ = "messages"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    listing_id = Column(String(100), ForeignKey("listings.id"), nullable=True)
    order_id = Column(String(100), ForeignKey("orders.id"), nullable=True)
    
    # Message Info
    ebay_message_id = Column(String(50), nullable=True)
    message_type = Column(SQLEnum(MessageTypeEnum), default=MessageTypeEnum.GENERAL)
    subject = Column(String(255), nullable=True)
    message_text = Column(Text, nullable=True)
    
    # Participants
    sender_username = Column(String(100), nullable=True)
    recipient_username = Column(String(100), nullable=True)
    direction = Column(String(10), nullable=True)  # inbound, outbound
    
    # Status
    is_read = Column(Boolean, default=False)
    is_replied = Column(Boolean, default=False)
    priority = Column(SQLEnum(MessagePriorityEnum), default=MessagePriorityEnum.NORMAL)
    
    # Dates
    message_date = Column(DateTime(timezone=True), nullable=True)
    reply_by_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    account = relationship("Account", back_populates="messages")
    listing = relationship("Listing", back_populates="messages")
    order = relationship("Order", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_message_user_date', 'user_id', 'message_date'),
        Index('idx_message_account', 'account_id', 'is_read'),
        Index('idx_message_priority', 'priority', 'is_replied'),
        Index('idx_message_type', 'message_type'),
    )


class AccountSheet(Base):
    """Mapping Account với Google Sheets"""
    __tablename__ = "account_sheets"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    # Google Sheets Info
    sheet_id = Column(String(100), nullable=False)
    sheet_name = Column(String(255), nullable=False)
    sheet_url = Column(String(500), nullable=True)
    
    # Sheet Structure
    sheet_type = Column(SQLEnum(SheetTypeEnum), nullable=False)
    headers = Column(JSON, nullable=True)  # ["Column1", "Column2", ...]
    last_row = Column(Integer, default=1)
    
    # Sync Info
    auto_sync = Column(Boolean, default=True)
    sync_frequency = Column(Integer, default=60)  # minutes
    last_sync = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(20), default='pending')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="account_sheets")
    
    # Indexes
    __table_args__ = (
        Index('idx_sheet_account_type', 'account_id', 'sheet_type', unique=True),
        Index('idx_sheet_sync', 'auto_sync', 'last_sync'),
    )


# ===========================================
# NEW MULTI-ROLE TABLES
# ===========================================

class UserRole(Base):
    """User roles for multi-role system"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=True)  # List of permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", back_populates="role")


class AddressBlacklist(Base):
    """Address blacklist management"""
    __tablename__ = "address_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    address_pattern = Column(Text, nullable=False)
    match_type = Column(String(20), default='contains')  # 'exact', 'contains', 'regex'
    risk_level = Column(String(20), default='medium')   # 'low', 'medium', 'high', 'blocked'
    reason = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    created_by_user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_blacklist_active', 'is_active'),
    )


class SheetsSyncLog(Base):
    """Google Sheets sync tracking"""
    __tablename__ = "sheets_sync_log"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50), nullable=True)  # 'import', 'export', 'status_update'
    spreadsheet_id = Column(String(200), nullable=True)
    sheet_name = Column(String(100), nullable=True)
    rows_processed = Column(Integer, default=0)
    rows_success = Column(Integer, default=0)
    rows_error = Column(Integer, default=0)
    error_details = Column(JSON, nullable=True)
    started_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default='running')  # 'running', 'completed', 'failed'
    
    # Relationships
    started_by_user = relationship("User")


class OrderStatusHistory(Base):
    """Order status change history"""
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), ForeignKey("orders.id"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    change_reason = Column(Text, nullable=True)
    additional_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_status_history")
    changed_by_user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_status_history_order', 'order_id'),
    )