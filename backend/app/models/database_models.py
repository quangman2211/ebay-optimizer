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
    ENDED = "ended"
    SOLD = "sold"
    ARCHIVED = "archived"


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
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    account = relationship("Account", back_populates="orders")
    listing = relationship("Listing", back_populates="orders")
    messages = relationship("Message", back_populates="order")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_user_status', 'user_id', 'status'),
        Index('idx_order_account', 'account_id', 'order_date'),
        Index('idx_order_date', 'order_date'),
        Index('idx_order_tracking', 'tracking_number'),
        Index('idx_order_ebay', 'ebay_order_id', 'ebay_transaction_id'),
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
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    sku = Column(String(100), nullable=True)
    
    # Google Drive Images (Original từ supplier)
    gdrive_folder_url = Column(String(500), nullable=True)  # Link to Google Drive folder
    image_notes = Column(Text, nullable=True)  # "6 images, need watermark removal"
    
    # Business
    profit_margin = Column(Float, nullable=True)
    suggested_ebay_price = Column(Float, nullable=True)
    
    # Availability
    in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    
    # Status
    is_approved = Column(Boolean, default=False)  # Đã duyệt để tạo draft
    
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