"""
Service Interfaces (Interface Segregation Principle)
Defines contracts that all service implementations must follow
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class IDataConnectionService(ABC):
    """Interface for data connection services (Google Sheets, Database, etc.)"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to data source"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connection is active"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status"""
        pass


class ISheetsDataService(ABC):
    """Interface for sheets data operations (ISP - focused interface)"""
    
    @abstractmethod
    async def get_sheet_data(self, sheet_name: str, range_name: str) -> List[List[str]]:
        """Get raw data from sheet"""
        pass
    
    @abstractmethod
    async def update_sheet_data(self, sheet_name: str, range_name: str, values: List[List[str]]) -> bool:
        """Update data in sheet"""
        pass
    
    @abstractmethod
    async def append_sheet_data(self, sheet_name: str, values: List[List[str]]) -> bool:
        """Append data to sheet"""
        pass
    
    @abstractmethod
    async def create_sheet(self, sheet_name: str, headers: List[str]) -> bool:
        """Create new sheet with headers"""
        pass


class IListingDataService(ABC):
    """Interface for listing-specific data operations"""
    
    @abstractmethod
    async def get_all_listings(self) -> List[Dict[str, Any]]:
        """Get all listings data"""
        pass
    
    @abstractmethod
    async def get_listing_by_id(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Get single listing by ID"""
        pass
    
    @abstractmethod
    async def create_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new listing"""
        pass
    
    @abstractmethod
    async def update_listing(self, listing_id: str, listing_data: Dict[str, Any]) -> bool:
        """Update existing listing"""
        pass
    
    @abstractmethod
    async def delete_listing(self, listing_id: str) -> bool:
        """Delete/archive listing"""
        pass
    
    @abstractmethod
    async def bulk_update_listings(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update multiple listings"""
        pass


class IOrderDataService(ABC):
    """Interface for order-specific data operations"""
    
    @abstractmethod
    async def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders data"""
        pass
    
    @abstractmethod
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get single order by ID"""
        pass
    
    @abstractmethod
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new order"""
        pass
    
    @abstractmethod
    async def update_order(self, order_id: str, order_data: Dict[str, Any]) -> bool:
        """Update existing order"""
        pass
    
    @abstractmethod
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        pass
    
    @abstractmethod
    async def add_tracking_info(self, order_id: str, tracking_number: str, carrier: str) -> bool:
        """Add tracking information to order"""
        pass


class ISourceDataService(ABC):
    """Interface for source-specific data operations"""
    
    @abstractmethod
    async def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all sources data"""
        pass
    
    @abstractmethod
    async def get_source_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get single source by ID"""
        pass
    
    @abstractmethod
    async def create_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new source"""
        pass
    
    @abstractmethod
    async def update_source(self, source_id: str, source_data: Dict[str, Any]) -> bool:
        """Update existing source"""
        pass
    
    @abstractmethod
    async def sync_source_data(self, source_id: str) -> Dict[str, Any]:
        """Sync data from external source"""
        pass


class IOptimizationService(ABC):
    """Interface for optimization services"""
    
    @abstractmethod
    async def optimize_title(self, title: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize listing title"""
        pass
    
    @abstractmethod
    async def optimize_description(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize listing description"""
        pass
    
    @abstractmethod
    async def extract_keywords(self, content: str, context: Dict[str, Any]) -> List[str]:
        """Extract relevant keywords"""
        pass
    
    @abstractmethod
    async def calculate_seo_score(self, listing_data: Dict[str, Any]) -> float:
        """Calculate SEO score for listing"""
        pass


class INotificationService(ABC):
    """Interface for notification services"""
    
    @abstractmethod
    async def send_notification(self, message: str, recipient: str, notification_type: str = "info") -> bool:
        """Send notification to recipient"""
        pass
    
    @abstractmethod
    async def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send multiple notifications"""
        pass
    
    @abstractmethod
    async def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """Get status of sent notification"""
        pass


class IAnalyticsService(ABC):
    """Interface for analytics services"""
    
    @abstractmethod
    async def get_dashboard_metrics(self, user_id: int, period: str = "month") -> Dict[str, Any]:
        """Get dashboard metrics"""
        pass
    
    @abstractmethod
    async def get_revenue_analytics(self, user_id: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get revenue analytics data"""
        pass
    
    @abstractmethod
    async def get_performance_trends(self, user_id: int, metric: str, period: str) -> Dict[str, Any]:
        """Get performance trend data"""
        pass
    
    @abstractmethod
    async def calculate_conversion_metrics(self, user_id: int) -> Dict[str, Any]:
        """Calculate conversion metrics"""
        pass


class IExportService(ABC):
    """Interface for export services"""
    
    @abstractmethod
    async def export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> bytes:
        """Export data to CSV format"""
        pass
    
    @abstractmethod
    async def export_to_excel(self, data: List[Dict[str, Any]], filename: str) -> bytes:
        """Export data to Excel format"""
        pass
    
    @abstractmethod
    async def export_to_sheets(self, data: List[Dict[str, Any]], sheet_config: Dict[str, Any]) -> bool:
        """Export data to Google Sheets"""
        pass
    
    @abstractmethod
    async def generate_report(self, report_type: str, user_id: int, filters: Dict[str, Any]) -> bytes:
        """Generate formatted report"""
        pass


class ICacheService(ABC):
    """Interface for caching services"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass


class IValidationService(ABC):
    """Interface for validation services"""
    
    @abstractmethod
    async def validate_listing_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate listing data"""
        pass
    
    @abstractmethod
    async def validate_order_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order data"""
        pass
    
    @abstractmethod
    async def sanitize_input(self, data: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Sanitize user input"""
        pass
    
    @abstractmethod
    async def check_business_rules(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check business rule compliance"""
        pass