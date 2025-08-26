"""
Account Domain Models  
Contains eBay account-related entities and business logic
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base import BaseModel
from .enums import AccountStatusEnum, SheetTypeEnum


class Account(BaseModel):
    """
    eBay Account entity representing individual eBay seller accounts
    Each account has its own Google Sheet integration and browser profile
    """
    __tablename__ = "accounts"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # eBay Account Information
    ebay_username = Column(String(100), nullable=False, unique=True)
    ebay_user_id = Column(String(50), nullable=True)
    email = Column(String(255), nullable=False)
    
    # Account Status and Details
    status = Column(SQLEnum(AccountStatusEnum), default=AccountStatusEnum.ACTIVE)
    country = Column(String(10), nullable=True)  # Country code
    site_id = Column(Integer, nullable=True)  # eBay site ID
    store_name = Column(String(255), nullable=True)
    store_url = Column(String(500), nullable=True)
    
    # Google Sheets Integration
    sheet_id = Column(String(100), nullable=True)
    sheet_url = Column(String(500), nullable=True)
    
    # eBay API Integration (optional)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance Metrics
    health_score = Column(Float, default=0.0)
    feedback_score = Column(Float, default=0.0)
    feedback_count = Column(Integer, default=0)
    total_listings = Column(Integer, default=0)
    active_listings = Column(Integer, default=0)
    total_sales = Column(Integer, default=0)
    monthly_revenue = Column(Float, default=0.0)
    
    # Account Limits and Usage
    monthly_listing_limit = Column(Integer, default=0)
    monthly_revenue_limit = Column(Float, default=0.0)
    used_listing_count = Column(Integer, default=0)
    used_revenue_amount = Column(Float, default=0.0)
    
    # Important Dates
    join_date = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Account Settings
    auto_sync = Column(Boolean, default=True)
    sync_frequency = Column(Integer, default=6)  # Hours
    notifications_enabled = Column(Boolean, default=True)
    
    # Relationships - temporarily simplified
    user = relationship("User", back_populates="accounts")
    # listings = relationship("Listing", back_populates="account")
    # orders = relationship("Order", back_populates="account")
    # draft_listings = relationship("DraftListing", back_populates="account")
    # messages = relationship("Message", back_populates="account")
    account_sheets = relationship("AccountSheet", back_populates="account")
    
    # Database Indexes
    __table_args__ = (
        Index('idx_account_user_status', 'user_id', 'status'),
        Index('idx_account_country', 'country'),
    )
    
    def __repr__(self):
        return f"<Account(id={self.id}, ebay_username='{self.ebay_username}')>"
    
    # Business Logic Methods
    def is_active(self) -> bool:
        """Check if account is active and operational"""
        return self.status == AccountStatusEnum.ACTIVE
    
    def is_suspended(self) -> bool:
        """Check if account is suspended"""
        return self.status == AccountStatusEnum.SUSPENDED
    
    def calculate_health_score(self) -> float:
        """Calculate account health score based on various metrics"""
        score = 0.0
        
        # Base score from feedback
        if self.feedback_score >= 98:
            score += 30
        elif self.feedback_score >= 95:
            score += 25
        elif self.feedback_score >= 90:
            score += 20
        else:
            score += 10
        
        # Active listings score
        if self.active_listings >= 100:
            score += 25
        elif self.active_listings >= 50:
            score += 20
        elif self.active_listings >= 10:
            score += 15
        else:
            score += 5
        
        # Sales performance
        if self.total_sales >= 1000:
            score += 25
        elif self.total_sales >= 100:
            score += 20
        elif self.total_sales >= 10:
            score += 15
        else:
            score += 5
        
        # Account age (newer accounts get lower score)
        if self.join_date:
            account_age_days = (datetime.now() - self.join_date).days
            if account_age_days >= 365:
                score += 20
            elif account_age_days >= 180:
                score += 15
            elif account_age_days >= 90:
                score += 10
            else:
                score += 5
        
        return min(score, 100.0)
    
    def update_health_score(self):
        """Update the health score"""
        self.health_score = self.calculate_health_score()
    
    def is_api_token_expired(self) -> bool:
        """Check if eBay API token is expired"""
        if not self.token_expires_at:
            return True
        return datetime.now() > self.token_expires_at
    
    def can_list_more_items(self) -> bool:
        """Check if account can list more items within limits"""
        if self.monthly_listing_limit == 0:  # No limit set
            return True
        return self.used_listing_count < self.monthly_listing_limit
    
    def get_remaining_listing_quota(self) -> int:
        """Get remaining listing quota for the month"""
        if self.monthly_listing_limit == 0:
            return 999999  # Unlimited
        return max(0, self.monthly_listing_limit - self.used_listing_count)
    
    def suspend(self, reason: str = None):
        """Suspend the account"""
        self.status = AccountStatusEnum.SUSPENDED
        self.last_activity = func.now()
        # Could add reason to activity log
    
    def reactivate(self):
        """Reactivate suspended account"""
        self.status = AccountStatusEnum.ACTIVE
        self.last_activity = func.now()
    
    def update_metrics(self, **kwargs):
        """Update account metrics"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Recalculate health score when metrics are updated
        self.update_health_score()


class AccountSheet(BaseModel):
    """
    Account-to-Google-Sheet mapping entity
    Manages the relationship between eBay accounts and their dedicated Google Sheets
    Supports multi-sheet architecture with browser profiles
    """
    __tablename__ = "account_sheets"
    
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    # Google Sheets Information
    sheet_id = Column(String(100), nullable=False)
    sheet_name = Column(String(255), nullable=False)
    sheet_url = Column(String(500), nullable=True)
    
    # Legacy Sheet Configuration
    sheet_type = Column(SQLEnum(SheetTypeEnum), nullable=True)
    headers = Column(JSON, nullable=True)  # Column headers
    last_row = Column(Integer, default=1)
    
    # Browser Profile Configuration
    vps_id = Column(Integer, nullable=True)  # VPS server (1-5)
    browser_profile = Column(String(100), nullable=True)  # Profile identifier
    browser_type = Column(String(20), nullable=True)  # hidemyacc, multilogin, chrome
    
    # Collection Schedule
    collection_schedule = Column(JSON, nullable=True)  # ["08:00", "14:00", "20:00"]
    sync_interval_minutes = Column(Integer, default=300)  # 5 hours default
    
    # Sheet Structure Configuration (Multi-tab support)
    orders_tab_name = Column(String(50), default="Orders")
    listings_tab_name = Column(String(50), default="Listings")
    messages_tab_name = Column(String(50), default="Messages")
    analytics_tab_name = Column(String(50), default="Analytics")
    config_tab_name = Column(String(50), default="Config")
    
    # Synchronization Configuration
    auto_sync = Column(Boolean, default=True)
    sync_frequency = Column(Integer, default=60)  # minutes (legacy)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(20), default='pending')
    last_error_message = Column(Text, nullable=True)
    sync_error_count = Column(Integer, default=0)
    
    # Performance Metrics
    total_orders_synced = Column(Integer, default=0)
    total_listings_synced = Column(Integer, default=0)
    total_messages_synced = Column(Integer, default=0)
    last_sync_duration_seconds = Column(Float, nullable=True)
    average_sync_duration = Column(Float, nullable=True)
    
    # Chrome Extension Integration
    extension_enabled = Column(Boolean, default=True)
    extension_version = Column(String(20), nullable=True)
    last_extension_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Multi-sheet Configuration
    is_multi_sheet = Column(Boolean, default=True)  # Default to new architecture
    
    # Relationships
    account = relationship("Account", back_populates="account_sheets")
    
    # Database Indexes
    __table_args__ = (
        Index('idx_sheet_account_type', 'account_id', 'sheet_type'),
        Index('idx_sheet_sync', 'auto_sync', 'last_sync'),
        Index('idx_sheet_vps', 'vps_id'),
        Index('idx_sheet_multisheet', 'is_multi_sheet', 'sync_status'),
        Index('idx_sheet_schedule', 'sync_interval_minutes', 'auto_sync'),
    )
    
    def __repr__(self):
        return f"<AccountSheet(id={self.id}, account_id={self.account_id}, sheet_name='{self.sheet_name}')>"
    
    # Business Logic Methods
    def is_sync_due(self) -> bool:
        """Check if synchronization is due"""
        if not self.auto_sync:
            return False
        
        if not self.last_sync:
            return True
        
        next_sync = self.last_sync + timedelta(minutes=self.sync_interval_minutes)
        return datetime.now() >= next_sync
    
    def record_successful_sync(self, duration_seconds: float, orders_count: int = 0, 
                             listings_count: int = 0, messages_count: int = 0):
        """Record a successful synchronization"""
        self.last_sync = func.now()
        self.sync_status = 'success'
        self.sync_error_count = 0
        self.last_error_message = None
        self.last_sync_duration_seconds = duration_seconds
        
        # Update counters
        self.total_orders_synced += orders_count
        self.total_listings_synced += listings_count
        self.total_messages_synced += messages_count
        
        # Update average duration
        if self.average_sync_duration is None:
            self.average_sync_duration = duration_seconds
        else:
            # Simple moving average
            self.average_sync_duration = (self.average_sync_duration + duration_seconds) / 2
    
    def record_sync_error(self, error_message: str):
        """Record a synchronization error"""
        self.sync_status = 'error'
        self.last_error_message = error_message
        self.sync_error_count += 1
    
    def get_collection_times(self) -> List[str]:
        """Get collection schedule times"""
        return self.collection_schedule or []
    
    def set_collection_times(self, times: List[str]):
        """Set collection schedule times"""
        self.collection_schedule = times
    
    def is_healthy(self) -> bool:
        """Check if sheet integration is healthy"""
        # Consider healthy if:
        # 1. No recent errors (less than 5 consecutive errors)
        # 2. Recent successful sync (within 2x interval)
        # 3. Extension is active (if enabled)
        
        if self.sync_error_count >= 5:
            return False
        
        if self.last_sync:
            max_age = timedelta(minutes=self.sync_interval_minutes * 2)
            if datetime.now() - self.last_sync > max_age:
                return False
        
        return True
    
    def get_health_status(self) -> Dict:
        """Get detailed health status"""
        return {
            'is_healthy': self.is_healthy(),
            'sync_status': self.sync_status,
            'error_count': self.sync_error_count,
            'last_sync': self.last_sync,
            'last_error': self.last_error_message,
            'extension_active': self.extension_enabled and self.last_extension_activity,
            'sync_due': self.is_sync_due()
        }