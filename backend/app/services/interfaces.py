"""
Service Interfaces following Interface Segregation Principle (ISP)
Part of SOLID architecture for Google Sheets integration
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class DataSource(str, Enum):
    """Data source types"""
    GOOGLE_SHEETS = "google_sheets"
    MANUAL = "manual"
    API = "api"


class IDataReader(ABC):
    """Interface for reading data - Single Responsibility"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    async def read_data(self, source_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Read data from source"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to data source"""
        pass


class IDataWriter(ABC):
    """Interface for writing data - Single Responsibility"""
    
    @abstractmethod
    async def write_data(self, destination_id: str, data: List[Dict]) -> bool:
        """Write data to destination"""
        pass
    
    @abstractmethod
    async def update_data(self, destination_id: str, row_id: str, data: Dict) -> bool:
        """Update specific row in destination"""
        pass


class IDataValidator(ABC):
    """Interface for data validation - Single Responsibility"""
    
    @abstractmethod
    def validate_order(self, order_data: Dict) -> tuple[bool, List[str]]:
        """Validate order data, return (is_valid, errors)"""
        pass
    
    @abstractmethod
    def validate_address(self, address: str) -> tuple[bool, str]:
        """Validate address, return (is_safe, risk_level)"""
        pass


class IDataTransformer(ABC):
    """Interface for data transformation - Single Responsibility"""
    
    @abstractmethod
    def transform_to_order(self, raw_data: Dict) -> Dict:
        """Transform raw data to order format"""
        pass
    
    @abstractmethod
    def transform_from_order(self, order: Any) -> Dict:
        """Transform order to export format"""
        pass


class ISyncService(ABC):
    """Interface for sync operations - combines reader/writer"""
    
    @abstractmethod
    async def sync_orders(self, source_id: str, account_id: int) -> Dict[str, Any]:
        """Sync orders from source to database"""
        pass
    
    @abstractmethod
    async def export_tracking(self, order_ids: List[str], destination_id: str) -> Dict[str, Any]:
        """Export tracking info to destination"""
        pass
    
    @abstractmethod
    async def get_sync_status(self, sync_id: str) -> Dict[str, Any]:
        """Get status of ongoing sync operation"""
        pass


class INotificationService(ABC):
    """Interface for notifications - Single Responsibility"""
    
    @abstractmethod
    async def notify_new_orders(self, orders: List[Dict]) -> None:
        """Notify about new orders"""
        pass
    
    @abstractmethod
    async def notify_assignment(self, user_id: int, orders: List[str]) -> None:
        """Notify user about order assignment"""
        pass
    
    @abstractmethod
    async def notify_error(self, error: str, context: Dict) -> None:
        """Notify about sync errors"""
        pass


class IBlacklistService(ABC):
    """Interface for blacklist operations - Single Responsibility"""
    
    @abstractmethod
    def check_address(self, address: str) -> Dict[str, Any]:
        """Check address against blacklist"""
        pass
    
    @abstractmethod
    def add_pattern(self, pattern: str, risk_level: str, reason: str) -> bool:
        """Add new blacklist pattern"""
        pass
    
    @abstractmethod
    def get_flagged_orders(self, order_ids: List[str]) -> List[Dict]:
        """Get orders with blacklisted addresses"""
        pass