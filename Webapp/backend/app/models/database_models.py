"""
Database Models - Clean import and export of all models
Re-exports domain models and defines simple missing models
"""

# Import all existing domain models first (these have proper relationships)
from app.domain.models.user import User, UserRole
from app.domain.models.listing import Listing, DraftListing
from app.domain.models.account import Account, AccountSheet

# Import enums
try:
    from app.domain.models.enums import *
except ImportError:
    import enum
    class AccountStatusEnum(str, enum.Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

# Define simple missing models without complex relationships to avoid conflicts
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from app.domain.models.base import BaseModel

class Order(BaseModel):
    __tablename__ = "orders"
    order_number = Column(String(100), unique=True, index=True)
    customer_name = Column(String(200))
    item_title = Column(Text)
    quantity = Column(Integer, default=1)
    price_ebay = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))

class Source(BaseModel):
    __tablename__ = "sources"
    source_name = Column(String(200))
    source_url = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))

class SourceProduct(BaseModel):
    __tablename__ = "source_products" 
    product_name = Column(String(500))
    price = Column(Float)
    source_id = Column(Integer, ForeignKey("sources.id"))

class Product(BaseModel):
    __tablename__ = "products"
    name = Column(String(500))
    sku = Column(String(100))
    price = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))

class Supplier(BaseModel):
    __tablename__ = "suppliers"
    name = Column(String(200))
    contact_email = Column(String(200))
    user_id = Column(Integer, ForeignKey("users.id"))

# Export all models - removing complex models for core functionality
__all__ = [
    'User', 'UserRole', 'Account', 'AccountSheet', 'Listing', 'DraftListing',
    'Order', 'Source', 'SourceProduct', 'Product', 'Supplier'
]