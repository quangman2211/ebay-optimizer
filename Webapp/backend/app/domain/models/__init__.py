"""
Domain Models Package
Contains all domain entities and value objects
"""

# Only import what actually exists
try:
    from .user import User, UserRole, UserRoleEnum
except ImportError:
    User = UserRole = UserRoleEnum = None

try:
    from .listing import Listing, DraftListing, ListingStatusEnum, DraftStatusEnum
except ImportError:
    Listing = DraftListing = ListingStatusEnum = DraftStatusEnum = None

try:
    from .account import Account, AccountStatusEnum, AccountSheet, SheetTypeEnum
except ImportError:
    Account = AccountStatusEnum = AccountSheet = SheetTypeEnum = None

try:
    from .enums import *
except ImportError:
    pass

# Build __all__ with only available models
__all__ = []
if User:
    __all__.extend(["User", "UserRole", "UserRoleEnum"])
if Listing:
    __all__.extend(["Listing", "DraftListing", "ListingStatusEnum", "DraftStatusEnum"])
if Account:
    __all__.extend(["Account", "AccountStatusEnum", "AccountSheet", "SheetTypeEnum"])