"""
Repository Package - Clean Architecture Database Layer
Exports tất cả repository instances để sử dụng trong API endpoints
"""

from .base import CRUDBase
from .user import user_repo, UserRepository
from .listing import listing_repo, ListingRepository
from .order import order_repo, OrderRepository
from .source import source_repo, SourceRepository
from .account import account_repo, AccountRepository

__all__ = [
    # Base
    "CRUDBase",
    
    # Repository classes
    "UserRepository",
    "ListingRepository", 
    "OrderRepository",
    "SourceRepository",
    "AccountRepository",
    
    # Repository instances
    "user_repo",
    "listing_repo",
    "order_repo", 
    "source_repo",
    "account_repo",
]