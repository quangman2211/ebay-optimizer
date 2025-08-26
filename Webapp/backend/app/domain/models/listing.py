"""
Listing Domain Models
Contains listing-related entities and business logic
"""

from sqlalchemy import Column, String, Text, Float, Integer, JSON, ForeignKey, Index, Boolean
from sqlalchemy import Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Dict, Optional
from .base import BaseModel
from .enums import ListingStatusEnum, DraftStatusEnum


class Listing(BaseModel):
    """
    Listing entity representing eBay listings
    Contains core listing data and optimization information
    """
    __tablename__ = "listings"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    source_product_id = Column(String(100), ForeignKey("source_products.id"), nullable=True)
    draft_listing_id = Column(String(100), ForeignKey("draft_listings.id"), nullable=True)
    
    # eBay Information
    ebay_item_id = Column(String(50), unique=True, nullable=True, index=True)
    title = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    quantity = Column(Integer, default=0)
    sku = Column(String(100), nullable=True)
    condition = Column(String(50), nullable=True)
    
    # Status and Type
    status = Column(SQLEnum(ListingStatusEnum), default=ListingStatusEnum.DRAFT)
    listing_type = Column(String(20), default='fixed')  # fixed, auction
    
    # Metadata
    keywords = Column(JSON, nullable=True)  # List of keywords
    item_specifics = Column(JSON, nullable=True)  # Key-value pairs
    
    # Performance Metrics
    views = Column(Integer, default=0)
    watchers = Column(Integer, default=0)
    sold = Column(Integer, default=0)
    performance_score = Column(Float, nullable=True)  # 0-100
    
    # Optimization Data
    original_title = Column(String(80), nullable=True)
    optimized_title = Column(String(80), nullable=True)
    seo_score = Column(Float, nullable=True)
    optimization_notes = Column(Text, nullable=True)
    
    # External Links
    ebay_url = Column(String(500), nullable=True)
    
    # Integration Data
    sheet_row = Column(Integer, nullable=True)
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships - temporarily simplified for core functionality
    # user = relationship("User", back_populates="listings")
    # account = relationship("Account", back_populates="listings")
    # source_product = relationship("SourceProduct", back_populates="listings")
    # draft_listing = relationship("DraftListing", back_populates="listing", uselist=False)
    # orders = relationship("Order", back_populates="listing")
    # messages = relationship("Message", back_populates="listing")
    
    # Database Indexes
    __table_args__ = (
        Index('idx_listing_user_status', 'user_id', 'status'),
        Index('idx_listing_account', 'account_id', 'status'),
        Index('idx_listing_category', 'category'),
        Index('idx_listing_performance', 'performance_score'),
        Index('idx_listing_source_product', 'source_product_id'),
    )
    
    def __repr__(self):
        return f"<Listing(id='{self.id}', title='{self.title[:30]}...')>"
    
    # Business Logic Methods
    def is_active(self) -> bool:
        """Check if listing is currently active"""
        return self.status == ListingStatusEnum.ACTIVE
    
    def is_sold_out(self) -> bool:
        """Check if listing is sold out"""
        return self.quantity <= 0
    
    def calculate_performance_score(self) -> float:
        """Calculate performance score based on views, watchers, and sales"""
        if self.views == 0:
            return 0.0
        
        # Simple scoring algorithm - can be enhanced
        watch_rate = (self.watchers / self.views) * 100 if self.views > 0 else 0
        sale_rate = (self.sold / self.views) * 100 if self.views > 0 else 0
        
        score = (watch_rate * 0.3) + (sale_rate * 0.7)
        return min(score, 100.0)
    
    def update_performance_metrics(self, views: int = None, watchers: int = None, sold: int = None):
        """Update performance metrics and recalculate score"""
        if views is not None:
            self.views = views
        if watchers is not None:
            self.watchers = watchers
        if sold is not None:
            self.sold = sold
        
        self.performance_score = self.calculate_performance_score()
    
    def optimize_title(self, new_title: str):
        """Apply title optimization"""
        if not self.original_title:
            self.original_title = self.title
        
        self.optimized_title = new_title
        self.title = new_title
    
    def activate(self):
        """Activate the listing"""
        if self.status == ListingStatusEnum.DRAFT:
            self.status = ListingStatusEnum.ACTIVE
    
    def end_listing(self):
        """End the listing"""
        self.status = ListingStatusEnum.ENDED
    
    def mark_as_sold(self):
        """Mark listing as sold"""
        self.status = ListingStatusEnum.SOLD
        self.quantity = 0


class DraftListing(BaseModel):
    """
    Draft listing entity for preparing listings before publication
    Supports the workflow of creating, reviewing, and approving listings
    """
    __tablename__ = "draft_listings"
    
    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    source_product_id = Column(String(100), ForeignKey("source_products.id"), nullable=True)
    
    # Draft Content
    title = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    quantity = Column(Integer, default=0)
    sku = Column(String(100), nullable=True)
    condition = Column(String(50), nullable=True)
    
    # Draft Status
    status = Column(SQLEnum(DraftStatusEnum), default=DraftStatusEnum.DRAFT)
    
    # Metadata
    keywords = Column(JSON, nullable=True)
    item_specifics = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True)  # List of image URLs
    
    # Review Process
    review_notes = Column(Text, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Templates and Automation
    template_id = Column(String(100), nullable=True)
    auto_generated = Column(Boolean, default=False)
    
    # Relationships - temporarily simplified
    # user = relationship("User", back_populates="draft_listings")
    # account = relationship("Account", back_populates="draft_listings")
    # source_product = relationship("SourceProduct", back_populates="draft_listings")
    # listing = relationship("Listing", back_populates="draft_listing")
    # reviewer = relationship("User", foreign_keys=[reviewer_id])
    
    def __repr__(self):
        return f"<DraftListing(id='{self.id}', status='{self.status}')>"
    
    # Business Logic Methods
    def submit_for_review(self):
        """Submit draft for review"""
        if self.status == DraftStatusEnum.DRAFT:
            self.status = DraftStatusEnum.UNDER_REVIEW
    
    def approve(self, reviewer_id: int, notes: str = None):
        """Approve the draft listing"""
        self.status = DraftStatusEnum.APPROVED
        self.reviewer_id = reviewer_id
        self.reviewed_at = func.now()
        if notes:
            self.review_notes = notes
    
    def reject(self, reviewer_id: int, notes: str):
        """Reject the draft listing"""
        self.status = DraftStatusEnum.REJECTED
        self.reviewer_id = reviewer_id
        self.reviewed_at = func.now()
        self.review_notes = notes
    
    def publish_to_listing(self) -> Dict:
        """Convert draft to listing data"""
        if self.status != DraftStatusEnum.APPROVED:
            raise ValueError("Draft must be approved before publishing")
        
        return {
            'user_id': self.user_id,
            'account_id': self.account_id,
            'source_product_id': self.source_product_id,
            'draft_listing_id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'quantity': self.quantity,
            'sku': self.sku,
            'condition': self.condition,
            'keywords': self.keywords,
            'item_specifics': self.item_specifics,
            'status': ListingStatusEnum.DRAFT
        }
    
    def is_ready_for_review(self) -> bool:
        """Check if draft has all required fields for review"""
        required_fields = [self.title, self.description, self.price, self.category]
        return all(field is not None for field in required_fields)
    
    def validate_content(self) -> List[str]:
        """Validate draft content and return list of issues"""
        issues = []
        
        if not self.title or len(self.title) < 10:
            issues.append("Title must be at least 10 characters long")
        
        if len(self.title) > 80:
            issues.append("Title cannot exceed 80 characters")
        
        if not self.description:
            issues.append("Description is required")
        
        if not self.price or self.price <= 0:
            issues.append("Price must be greater than 0")
        
        if not self.category:
            issues.append("Category is required")
        
        return issues