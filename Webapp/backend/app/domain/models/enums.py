"""
Domain Enums
Contains all enumeration types used across the domain
"""

import enum


class ListingStatusEnum(str, enum.Enum):
    """Status of a listing"""
    DRAFT = "draft"
    ACTIVE = "active"
    OPTIMIZED = "optimized"
    ENDED = "ended"
    SOLD = "sold"
    ARCHIVED = "archived"
    PENDING = "pending"


class OrderStatusEnum(str, enum.Enum):
    """Status of an order"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class AccountStatusEnum(str, enum.Enum):
    """Status of an eBay account"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LIMITED = "limited"
    INACTIVE = "inactive"


class SourceStatusEnum(str, enum.Enum):
    """Status of a data source"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SYNCING = "syncing"


class DraftStatusEnum(str, enum.Enum):
    """Status of a draft listing"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class ImageStatusEnum(str, enum.Enum):
    """Status of image processing"""
    PENDING = "pending"
    PROCESSED = "processed"
    ERROR = "error"


class MessageTypeEnum(str, enum.Enum):
    """Type of message"""
    BUYER_INQUIRY = "buyer_inquiry"
    SHIPPING_UPDATE = "shipping_update"
    RETURN_REQUEST = "return_request"
    GENERAL = "general"


class MessagePriorityEnum(str, enum.Enum):
    """Priority level of message"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class SheetTypeEnum(str, enum.Enum):
    """Type of Google Sheet"""
    ORDERS = "orders"
    LISTINGS = "listings"
    MESSAGES = "messages"
    ACCOUNTS = "accounts"


class UserRoleEnum(str, enum.Enum):
    """User role in the system"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class BlacklistStatusEnum(str, enum.Enum):
    """Status of blacklisted address"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class SyncSourceEnum(str, enum.Enum):
    """Source of synchronization"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CHROME_EXTENSION = "chrome_extension"
    BULK_IMPORT = "bulk_import"
    SCHEDULED = "scheduled"


class SupplierStatus(str, enum.Enum):
    """Status of a supplier"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_APPROVAL = "pending_approval"


class ProductStatus(str, enum.Enum):
    """Status of a product"""
    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    RESTRICTED = "restricted"
    SEASONAL = "seasonal"


class PaymentTerms(str, enum.Enum):
    """Payment terms with suppliers"""
    NET_15 = "net_15"
    NET_30 = "net_30"
    NET_45 = "net_45"
    NET_60 = "net_60"
    COD = "cod"
    PREPAID = "prepaid"