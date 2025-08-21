"""
SQLAlchemy Database Models cho eBay Optimizer
Chứa tất cả database tables: Users, Listings, Orders, Sources, Accounts
"""

from sqlalchemy import (
    Boolean, Column, Integer, String, Text, Float, DateTime, 
    JSON, ForeignKey, Enum as SQLEnum, Index
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    listings = relationship("Listing", back_populates="user")
    accounts = relationship("Account", back_populates="user")


class Listing(Base):
    """eBay Listings với optimization data"""
    __tablename__ = "listings"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic listing info
    title = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    quantity = Column(Integer, default=0)
    
    # eBay specific
    item_id = Column(String(50), nullable=True, index=True)  # eBay Item ID
    sku = Column(String(100), nullable=True)
    condition = Column(String(50), nullable=True)
    
    # Status & metadata
    status = Column(SQLEnum(ListingStatusEnum), default=ListingStatusEnum.DRAFT)
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
    
    # Google Sheets integration
    sheet_row = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="listings")
    orders = relationship("Order", back_populates="listing")
    
    # Indexes
    __table_args__ = (
        Index('idx_listing_user_status', 'user_id', 'status'),
        Index('idx_listing_category', 'category'),
        Index('idx_listing_performance', 'performance_score'),
    )


class Order(Base):
    """eBay Orders với tracking và customer info"""
    __tablename__ = "orders"

    id = Column(String(100), primary_key=True, index=True)
    listing_id = Column(String(100), ForeignKey("listings.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # eBay order info
    order_number = Column(String(50), nullable=False, index=True)
    item_id = Column(String(50), nullable=True)
    transaction_id = Column(String(50), nullable=True)
    
    # Customer info
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_type = Column(String(50), nullable=True)  # New/Repeat/VIP
    username_ebay = Column(String(100), nullable=True)
    
    # Product info
    product_name = Column(String(255), nullable=False)
    product_link = Column(Text, nullable=True)
    product_option = Column(String(255), nullable=True)
    
    # Financial
    price_ebay = Column(Float, nullable=True)
    price_cost = Column(Float, nullable=True) 
    net_profit = Column(Float, nullable=True)
    fees = Column(Float, nullable=True)
    
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
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    listing = relationship("Listing", back_populates="orders")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_user_status', 'user_id', 'status'),
        Index('idx_order_date', 'order_date'),
        Index('idx_order_tracking', 'tracking_number'),
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
    
    # Product info
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
    
    # URLs & images
    source_url = Column(String(500), nullable=True)
    image_urls = Column(JSON, nullable=True)  # List of image URLs
    
    # Metadata
    specifications = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    weight = Column(Float, nullable=True)
    dimensions = Column(JSON, nullable=True)
    
    # Performance
    views = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    roi = Column(Float, nullable=True)
    
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
    status = Column(SQLEnum(AccountStatusEnum), default=AccountStatusEnum.ACTIVE)
    country = Column(String(10), nullable=True)  # Country code
    site_id = Column(Integer, nullable=True)  # eBay site ID
    store_name = Column(String(255), nullable=True)
    store_url = Column(String(500), nullable=True)
    
    # Authentication
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    health_score = Column(Float, default=0.0)  # 0-100
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
    
    # Indexes
    __table_args__ = (
        Index('idx_account_user_status', 'user_id', 'status'),
        Index('idx_account_health', 'health_score'),
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